import pytest
from sqlmodel import SQLModel, Session, create_engine, Field
from typing import Optional
from datetime import datetime
from src.decorator.transactional import transactional
from src.repository.crud.crud_operations import BasicOperations
from src.exception.decorator_exception import TransactionError


# Modelo de prueba
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    balance: int
    updated_at: datetime = Field(default_factory=datetime.now)


# Fixtures
@pytest.fixture(name="engine")
def fixture_engine():
    """Configura el motor de base de datos para MariaDB."""
    DATABASE_URL = "mysql+pymysql://root:oracle@localhost:3306/sqlmodel_db"
    engine = create_engine(DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture(autouse=True)
def cleanup_database(engine):
    """Limpia la base de datos antes de cada test."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="session")
def fixture_session(engine):
    """Crea una sesión para la base de datos MariaDB."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def crud():
    """Crea una instancia del CRUDOperations para el modelo User."""
    return BasicOperations(User)


# Decoradores transaccionales para CRUD
@transactional
def create_user(session: Session, crud: BasicOperations, user: User):
    print(f"✅ Creando usuario: {user.name} con balance 💵 {user.balance}")
    crud.save(session, user)


@transactional
def get_all_users(session: Session, crud: BasicOperations):
    users = crud.get_all(session)
    print(f"📋 Usuarios en la base de datos: {[user.name for user in users]}")
    return users


@transactional
def delete_user(session: Session, crud: BasicOperations, user_id: int):
    print(f"❌ Eliminando usuario con ID: {user_id}")
    return crud.delete(session, user_id)


@transactional
def update_user_balance(
    session: Session, crud: BasicOperations, user_id: int, amount: int
):
    user = session.get(User, user_id)
    if not user:
        raise ValueError(f"⚠️ Usuario con ID {user_id} no encontrado")
    print(f"🔄 Actualizando balance para usuario {user.name}. Cambio: {amount:+}")
    if user.balance + amount < 0:
        raise ValueError("🚫 Saldo insuficiente")
    user.balance += amount
    crud.save(session, user)


# Tests
def test_crud_operations(session: Session, crud: BasicOperations):
    """Prueba básica de operaciones CRUD con transacciones."""
    print("\n🛠️ Iniciando test_crud_operations")
    # Crear usuarios
    user1 = User(name="Alice", balance=100)
    user2 = User(name="Bob", balance=50)
    create_user(session, crud, user1)
    create_user(session, crud, user2)

    # Leer todos los usuarios
    users = get_all_users(session, crud)
    assert len(users) == 2

    # Actualizar saldo de un usuario
    update_user_balance(session, crud, user_id=user1.id, amount=-30)
    user1_updated = session.get(User, user1.id)
    print(f"💰 Nuevo balance para {user1_updated.name}: {user1_updated.balance}")
    assert user1_updated.balance == 70

    # Eliminar un usuario
    success = delete_user(session, crud, user2.id)
    print(f"🗑️ Eliminación exitosa: {success}")
    assert success is True
    users_after_deletion = get_all_users(session, crud)
    assert len(users_after_deletion) == 1


def test_concurrent_transactions(engine, crud: BasicOperations):
    """Prueba de transacciones concurrentes."""
    print("\n⚙️ Iniciando test_concurrent_transactions")
    # Crear usuarios
    user1 = User(name="Charlie", balance=200)
    user2 = User(name="Dave", balance=100)
    with Session(engine) as session:
        create_user(session, crud, user1)
        create_user(session, crud, user2)
        user1_id, user2_id = user1.id, user2.id

    # Función concurrente
    @transactional(auto_concurrent=True)
    def concurrent_update(session: Session, user_id: int, amount: int):
        update_user_balance(session, crud, user_id, amount)

    # Ejecutar transacciones concurrentes
    from threading import Thread

    def worker():
        with Session(engine) as session:
            print(f"🏃‍♂️ Worker ejecutando actualizaciones concurrentes")
            concurrent_update(session, user1_id, -50)
            concurrent_update(session, user2_id, 50)

    t1 = Thread(target=worker)
    t2 = Thread(target=worker)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    # Verificar resultados finales
    with Session(engine) as session:
        user1_final = session.get(User, user1_id)
        user2_final = session.get(User, user2_id)
        print(
            f"📊 Resultados finales: User1 ({user1_final.name}) balance: {user1_final.balance}, User2 ({user2_final.name}) balance: {user2_final.balance}"
        )
        assert (
            user1_final.balance == 100
        ), f"Saldo final incorrecto para User1: {user1_final.balance}"
        assert (
            user2_final.balance == 200
        ), f"Saldo final incorrecto para User2: {user2_final.balance}"


def test_transaction_rollback_on_error(session: Session, crud: BasicOperations):
    """Prueba de rollback en caso de error."""
    print("\n🔄 Iniciando test_transaction_rollback_on_error")
    
    # Crear usuarios
    user1 = User(name="Eve", balance=100)
    user2 = User(name="Frank", balance=50)
    create_user(session, crud, user1)
    create_user(session, crud, user2)

    # Guardar balances originales
    original_balance1 = user1.balance
    original_balance2 = user2.balance

    # Intentar realizar una operación no válida
    try:
        update_user_balance(session, crud, user_id=user1.id, amount=-200)
        pytest.fail("Se esperaba una excepción TransactionError")
    except TransactionError as e:
        print(f"❌ Error esperado: {e}")
        
        # Verificar que no se aplicaron los cambios
        session.refresh(user1)
        session.refresh(user2)
        
        print(
            f"📉 Balance después de rollback: User1 ({user1.name}) "
            f"balance: {user1.balance}, User2 ({user2.name}) balance: {user2.balance}"
        )
        
        # Verificar que los balances no cambiaron
        assert user1.balance == original_balance1, "El balance de user1 no debería cambiar"
        assert user2.balance == original_balance2, "El balance de user2 no debería cambiar"
