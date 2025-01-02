import pytest
from sqlmodel import Field, SQLModel, Session, create_engine, text
from base_repository.decorator.store_procedure import store_procedure, DatabaseType
from base_repository.decorator.transactional import transactional

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
        """Test for phone insertion procedure."""
        print("\n🔍 Test: Inserting Phone")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        @transactional
        @store_procedure(
            name="sp_insert_phone",
            db_type=DatabaseType.POSTGRESQL,
            scalar=True  # Indicating that it returns a scalar value
        )
        def insert_phone(
            session: Session,
            model: str,
            brand: str,
            price: float,
            available: bool,
            success: bool = None  # OUT parameter
        ) -> bool:
            """The decorator will handle the execution"""
            pass
        
        # Execute procedure
        success = insert_phone(
            session=session,
            model="iPhone 18",
            brand="Apple",
            price=1099.99,
            available=True,
            success=None  # OUT parameter must be passed
        )
        
        # Verify procedure result
        assert success is True, "The insertion should be successful"
        print("✅ Test completed successfully")
        
        
    def test_add_phone_procedure(self, session):
        """Test for adding a phone procedure."""
        print("\n🔍 Test: Adding Phone")
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
            """The decorator will handle the execution"""
            pass
        
        # Case 1: Successful insertion
        print("Test 1: Successful Insertion")
        add_phone(
            session=session,
            model="iPhone 15 Pro Max",
            brand="Apple",
            price=999.99,
            available=True
        )
        
        # Verify in database
        phone = session.execute(
            text("SELECT * FROM phones WHERE model = 'iPhone 15 Pro Max'")
        ).fetchone()
        
        assert phone is not None, "The phone should exist"
        assert phone.brand == "Apple"
        assert float(phone.price) == 999.99
        assert phone.available is True
        
        print("✅ Test completed successfully")
