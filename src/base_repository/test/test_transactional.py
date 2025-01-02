import pytest
from sqlmodel import SQLModel, Session, create_engine, Field
from typing import Optional
from datetime import datetime
from base_repository.decorator.transactional import transactional
from base_repository.repository.crud.crud_operations import BasicOperations
from base_repository.exception.decorator_exception import TransactionError


# Test model
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    balance: int
    updated_at: datetime = Field(default_factory=datetime.now)


# Fixtures
@pytest.fixture(name="engine")
def fixture_engine():
    """Configures the database engine for MariaDB."""
    DATABASE_URL = "mysql+pymysql://root:oracle@localhost:3306/sqlmodel_db"
    engine = create_engine(DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture(autouse=True)
def cleanup_database(engine):
    """Cleans up the database before each test."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="session")
def fixture_session(engine):
    """Creates a session for the MariaDB database."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def crud():
    """Creates an instance of CRUDOperations for the User model."""
    return BasicOperations(User)


# Transactional decorators for CRUD
@transactional
def create_user(session: Session, crud: BasicOperations, user: User):
    print(f"✅ Creating user: {user.name} with balance 💵 {user.balance}")
    crud.save(session, user)


@transactional
def get_all_users(session: Session, crud: BasicOperations):
    users = crud.get_all(session)
    print(f"📋 Users in the database: {[user.name for user in users]}")
    return users


@transactional
def delete_user(session: Session, crud: BasicOperations, user_id: int):
    print(f"❌ Deleting user with ID: {user_id}")
    return crud.delete(session, user_id)


@transactional
def update_user_balance(
    session: Session, crud: BasicOperations, user_id: int, amount: int
):
    user = session.get(User, user_id)
    if not user:
        raise ValueError(f"⚠️ User with ID {user_id} not found")
    print(f"🔄 Updating balance for user {user.name}. Change: {amount:+}")
    if user.balance + amount < 0:
        raise ValueError("🚫 Insufficient balance")
    user.balance += amount
    crud.save(session, user)


# Tests
def test_crud_operations(session: Session, crud: BasicOperations):
    """Basic test for CRUD operations with transactions."""
    print("\n🛠️ Starting test_crud_operations")
    # Create users
    user1 = User(name="Alice", balance=100)
    user2 = User(name="Bob", balance=50)
    create_user(session, crud, user1)
    create_user(session, crud, user2)

    # Read all users
    users = get_all_users(session, crud)
    assert len(users) == 2

    # Update balance of a user
    update_user_balance(session, crud, user_id=user1.id, amount=-30)
    user1_updated = session.get(User, user1.id)
    print(f"💰 New balance for {user1_updated.name}: {user1_updated.balance}")
    assert user1_updated.balance == 70

    # Delete a user
    success = delete_user(session, crud, user2.id)
    print(f"🗑️ Deletion successful: {success}")
    assert success is True
    users_after_deletion = get_all_users(session, crud)
    assert len(users_after_deletion) == 1


def test_concurrent_transactions(engine, crud: BasicOperations):
    """Test for concurrent transactions."""
    print("\n⚙️ Starting test_concurrent_transactions")
    # Create users
    user1 = User(name="Charlie", balance=200)
    user2 = User(name="Dave", balance=100)
    with Session(engine) as session:
        create_user(session, crud, user1)
        create_user(session, crud, user2)
        user1_id, user2_id = user1.id, user2.id

    # Concurrent function
    @transactional(auto_concurrent=True)
    def concurrent_update(session: Session, user_id: int, amount: int):
        update_user_balance(session, crud, user_id, amount)

    # Run concurrent transactions
    from threading import Thread

    def worker():
        with Session(engine) as session:
            print(f"🏃‍♂️ Worker running concurrent updates")
            concurrent_update(session, user1_id, -50)
            concurrent_update(session, user2_id, 50)

    t1 = Thread(target=worker)
    t2 = Thread(target=worker)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    # Verify final results
    with Session(engine) as session:
        user1_final = session.get(User, user1_id)
        user2_final = session.get(User, user2_id)
        print(
            f"📊 Final results: User1 ({user1_final.name}) balance: {user1_final.balance}, User2 ({user2_final.name}) balance: {user2_final.balance}"
        )
        assert (
            user1_final.balance == 100
        ), f"Incorrect final balance for User1: {user1_final.balance}"
        assert (
            user2_final.balance == 200
        ), f"Incorrect final balance for User2: {user2_final.balance}"


def test_transaction_rollback_on_error(session: Session, crud: BasicOperations):
    """Test for rollback in case of an error."""
    print("\n🔄 Starting test_transaction_rollback_on_error")
    
    # Create users
    user1 = User(name="Eve", balance=100)
    user2 = User(name="Frank", balance=50)
    create_user(session, crud, user1)
    create_user(session, crud, user2)

    # Save original balances
    original_balance1 = user1.balance
    original_balance2 = user2.balance

    # Try to perform an invalid operation
    try:
        update_user_balance(session, crud, user_id=user1.id, amount=-200)
        pytest.fail("TransactionError expected")
    except TransactionError as e:
        print(f"❌ Expected error: {e}")
        
        # Verify that no changes were applied
        session.refresh(user1)
        session.refresh(user2)
        
        print(
            f"📉 Balance after rollback: User1 ({user1.name}) "
            f"balance: {user1.balance}, User2 ({user2.name}) balance: {user2.balance}"
        )
        
        # Verify that balances did not change
        assert user1.balance == original_balance1, "User1's balance should not change"
        assert user2.balance == original_balance2, "User2's balance should not change"
