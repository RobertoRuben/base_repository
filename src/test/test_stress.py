import pytest
from sqlmodel import SQLModel, Session, Field, create_engine
from datetime import datetime
from src.repository.crud.crud_operations import BasicOperations
from src.decorator.transactional import transactional
from typing import Optional
from threading import Thread
import time

# Modelo de prueba
class StressUser(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    balance: int
    created_at: datetime = Field(default_factory=datetime.now)

# Fixtures
@pytest.fixture(name="stress_engine")
def fixture_engine():
    """Configura el motor de base de datos para pruebas de estrés."""
    DATABASE_URL = "mysql+pymysql://root:oracle@localhost:3306/sqlmodel_db"
    engine = create_engine(DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="stress_session")
def fixture_session(stress_engine):
    """Crea una sesión para la base de datos."""
    with Session(stress_engine) as session:
        yield session


@pytest.fixture
def stress_crud():
    """Crea una instancia del CRUD para el modelo StressUser."""
    return BasicOperations(StressUser)


# Decoradores transaccionales
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


# Test de estrés
def test_stress_operations(stress_engine, stress_crud):
    """Test de estrés con operaciones CRUD concurrentes."""
    print("\n🚀 Iniciando test de estrés")
    NUM_USERS = 10000  # Número de usuarios a crear
    NUM_THREADS = 50  # Número de hilos para concurrencia
    BALANCE_INIT = 100  # Balance inicial por usuario
    BATCH_SIZE = 500  # Tamaño de lote para creación de usuarios

    start_time = time.time()  # Inicia el cronómetro

    # Crear usuarios iniciales en lotes
    with Session(stress_engine) as session:
        for i in range(0, NUM_USERS, BATCH_SIZE):
            for j in range(BATCH_SIZE):
                user_id = i + j + 1
                if user_id > NUM_USERS:
                    break
                create_user(session, stress_crud, name=f"User_{user_id}", balance=BALANCE_INIT)
                print(f"🛠️ Creando Usuario {user_id}")
            session.commit()

    # Función de trabajo para los hilos
    def worker(thread_id: int):
        with Session(stress_engine) as session:
            for user_id in range(1, NUM_USERS + 1):
                # Alternar entre actualizar y consultar balances
                if user_id % 2 == 0:
                    update_user_balance(session, stress_crud, user_id=user_id, amount=10)
                else:
                    balance = get_user_balance(session, user_id)
                    print(f"[Thread-{thread_id}] Balance User-{user_id}: {balance}")

    # Crear y ejecutar hilos
    threads = [Thread(target=worker, args=(i,)) for i in range(NUM_THREADS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Verificar balances finales
    with Session(stress_engine) as session:
        final_balances = [get_user_balance(session, user_id) for user_id in range(1, NUM_USERS + 1)]
        for user_id, balance in enumerate(final_balances, start=1):
            print(f"✅ Usuario {user_id} - Balance final: {balance}")

    end_time = time.time()  # Termina el cronómetro
    print(f"⏱️ Tiempo total de ejecución: {end_time - start_time:.2f} segundos")
