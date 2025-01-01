import pytest
from sqlmodel import Field, SQLModel, Session, create_engine, text
from src.decorator.query import query
from src.decorator.transactional import transactional
from typing import Dict, Any, List

# Model definition for the test table
class TestUser(SQLModel, table=True):
    __tablename__ = "test_users"
    id: int | None = Field(default=None, primary_key=True)
    name: str

# Fixtures
@pytest.fixture(name="engine")
def fixture_engine():
    """Configures the database engine for PostgreSQL."""
    DATABASE_URL = "postgresql+psycopg2://postgres:oracle@localhost:5432/sqlmodel_db"
    engine = create_engine(DATABASE_URL, echo=False)
    yield engine
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="session")
def fixture_session(engine):
    """Creates a session for the database."""
    # Create tables before running the tests
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    # Clean up after tests
    SQLModel.metadata.drop_all(engine)

class TestQueryDecorator:
    
    def test_select_query(self, session):
        """Test for a SELECT query."""
        print("\n🔍 Test: SELECT Query")
        print("━━━━━━━━━━━━━━━━━━━━━━━")
        # Prepare data
        session.add_all([TestUser(name="Alice"), TestUser(name="Bob")])
        session.commit()
        
        @transactional(read_only=True)
        @query(value="SELECT * FROM test_users ORDER BY name")
        def get_users(session: Session) -> List[Dict[str, Any]]:
            pass
            
        result = get_users(session=session)
        print(f"📦 Users found: {result}")
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"
        print("✅ Test completed successfully")

    def test_scalar_query(self, session):
        """Test for a scalar query."""
        print("\n🔍 Test: Scalar Query (COUNT)")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        session.add(TestUser(name="Alice"))
        session.commit()
        
        @transactional(read_only=True)
        @query(value="SELECT COUNT(*) FROM test_users", scalar=True)
        def count_users(session: Session) -> int:
            pass
            
        result = count_users(session=session)
        print(f"📊 Total users: {result}")
        assert result == 1
        print("✅ Test completed successfully")

    def test_parameterized_query(self, session):
        """Test for a parameterized query."""
        print("\n🔍 Test: Parameterized Query")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        session.add(TestUser(name="Alice"))
        session.commit()
        
        @transactional(read_only=True)
        @query(value="SELECT * FROM test_users WHERE name = :name")
        def find_by_name(session: Session, name: str) -> List[Dict[str, Any]]:
            """
            Query that retrieves a user by name.
            :param session: SQLAlchemy session
            :param name: The name of the user to search for
            :return: List of users matching the name
            """
            pass
            
        result = find_by_name(session=session, name="Alice")
        print(f"📦 User found: {result}")
        assert len(result) == 1
        assert result[0]["name"] == "Alice"
        print("✅ Test completed successfully")

    def test_insert_query(self, session):
        """Test for an insert query."""
        print("\n🖋️ Test: Inserting User")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        @transactional
        @query(value="INSERT INTO test_users (name) VALUES (:name)")
        def create_user(session: Session, name: str) -> None:
            pass
            
        create_user(session=session, name="Carol")
        
        # Fix this line using text()
        result = session.execute(text("SELECT * FROM test_users")).fetchall()
        print(f"📦 Users in the database: {result}")
        assert len(result) == 1
        assert result[0][1] == "Carol"
