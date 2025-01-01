import pytest
from sqlmodel import Field, SQLModel, Session, create_engine, text
from src.decorator.store_procedure import store_procedure, DatabaseType
from src.decorator.transactional import transactional

class Phone(SQLModel, table=True):
    __tablename__ = "phones"
    id: int | None = Field(default=None, primary_key=True)
    model: str
    brand: str
    price: float
    available: bool = Field(default=True)

@pytest.fixture(name="engine")
def fixture_engine():
    DATABASE_URL = "postgresql+psycopg2://postgres:oracle@localhost:5432/sqlmodel_db"
    engine = create_engine(DATABASE_URL, echo=False)
    return engine

@pytest.fixture(name="session")
def fixture_session(engine):
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        return session

class TestStoreProcedureDecorator:
    def test_insert_phone_procedure(self, session):
        """Test para procedimiento de inserción de teléfono."""
        print("\n🔍 Test: Inserción de teléfono")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        @transactional
        @store_procedure(
            name="sp_insert_phone",
            db_type=DatabaseType.POSTGRESQL,
            scalar=True  # Indicamos que devuelve un valor escalar
        )
        def insert_phone(
            session: Session,
            model: str,
            brand: str,
            price: float,
            available: bool,
            success: bool = None  # Parámetro OUT
        ) -> bool:
            """El decorador manejará la ejecución"""
            pass
        
        # Ejecutar procedimiento
        success = insert_phone(
            session=session,
            model="iPhone 18",
            brand="Apple",
            price=1099.99,
            available=True,
            success=None  # Parámetro OUT debe ser pasado
        )
        
        # Verificar resultado del procedimiento
        assert success is True, "La inserción debería ser exitosa"
        print("✅ Test completado con éxito")
        
        
        
    def test_add_phone_procedure(self, session):
        """Test para procedimiento de inserción de teléfono."""
        print("\n🔍 Test: Inserción de teléfono")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        @transactional
        @store_procedure(
            name="sp_add_phone",
            db_type=DatabaseType.POSTGRESQL
        )
        def add_phone(
            session: Session,
            model: str,
            brand: str,
            price: float,
            available: bool
        ) -> None:
            """El decorador manejará la ejecución"""
            pass
        
        # Caso 1: Inserción exitosa
        print("Test 1: Inserción exitosa")
        add_phone(
            session=session,
            model="iPhone 15 Pro Max",
            brand="Apple",
            price=999.99,
            available=True
        )
        
        # Verificar en base de datos
        phone = session.execute(
            text("SELECT * FROM phones WHERE model = 'iPhone 15 Pro Max'")
        ).fetchone()
        
        assert phone is not None, "El teléfono debería existir"
        assert phone.brand == "Apple"
        assert float(phone.price) == 999.99
        assert phone.available is True
        
        print("✅ Test completado con éxito")