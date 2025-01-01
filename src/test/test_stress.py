import pytest
from sqlmodel import SQLModel, Session, Field, create_engine
from datetime import datetime
from src.repository.crud.crud_operations import BasicOperations
from src.decorator.transactional import transactional
from typing import Optional
from threading import Thread
import time

# Test model
class StressUser(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    balance: int
    created_at: datetime = Field(default_factory=datetime.now)

# Fixtures
@pytest.fixture(name="stress_engine")
def fixture_engine():
    """Configures the database engine for stress testing."""
    DATABASE_URL = "mysql+pymysql://root:oracle@localhost:3306/sqlmodel_db"
    engine = create_engine(DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="stress_session")
def fixture_session(stress_engine):
    """Creates a session for the database."""
    with Session(stress_engine) as session:
        yield session


@pytest.fixture
def stress_crud():
    """Creates an instance of CRUD for the StressUser model."""
    return BasicOperations(StressUser)


# Transactional decorators
@transactional
def create_user(session: Session, crud: BasicOperations, name: str, balance: int):
    user = StressUser(name=name, balance=balance)
    crud.save(session, user)


@transactional
def update_user_balance(session: Session, crud: BasicOperations, user_id: int, amount: int):
    user = session.get(StressUser, user_id)
    if user:
        user.balance += amount
        crud.save(session, user)


@transactional
def get_user_balance(session: Session, user_id: int) -> int:
    user = session.get(StressUser, user_id)
    return user.balance if user else 0


# Stress test
def test_stress_operations(stress_engine, stress_crud):
    """Stress test with concurrent CRUD operations."""
    print("\n🚀 Starting stress test")
    NUM_USERS = 10000  # Number of users to create
    NUM_THREADS = 50  # Number of threads for concurrency
    BALANCE_INIT = 100  # Initial balance per user
    BATCH_SIZE = 500  # Batch size for creating users

    start_time = time.time()  # Start the timer

    # Create initial users in batches
    with Session(stress_engine) as session:
        for i in range(0, NUM_USERS, BATCH_SIZE):
            for j in range(BATCH_SIZE):
                user_id = i + j + 1
                if user_id > NUM_USERS:
                    break
                create_user(session, stress_crud, name=f"User_{user_id}", balance=BALANCE_INIT)
                print(f"🛠️ Creating User {user_id}")
            session.commit()

    # Worker function for the threads
    def worker(thread_id: int):
        with Session(stress_engine) as session:
            for user_id in range(1, NUM_USERS + 1):
                # Alternate between updating and checking balances
                if user_id % 2 == 0:
                    update_user_balance(session, stress_crud, user_id=user_id, amount=10)
                else:
                    balance = get_user_balance(session, user_id)
                    print(f"[Thread-{thread_id}] Balance User-{user_id}: {balance}")

    # Create and run threads
    threads = [Thread(target=worker, args=(i,)) for i in range(NUM_THREADS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Verify final balances
    with Session(stress_engine) as session:
        final_balances = [get_user_balance(session, user_id) for user_id in range(1, NUM_USERS + 1)]
        for user_id, balance in enumerate(final_balances, start=1):
            print(f"✅ User {user_id} - Final balance: {balance}")

    end_time = time.time()  # End the timer
    print(f"⏱️ Total execution time: {end_time - start_time:.2f} seconds")
