import pytest
from sqlmodel import Field, SQLModel, Session, create_engine, text
from src.decorator.query import query
from src.decorator.transactional import transactional
from typing import Dict, Any, List

# Definición de modelo para la tabla de prueba
class TestUser(SQLModel, table=True):
    __tablename__ = "test_users"
    id: int | None = Field(default=None, primary_key=True)
    name: str

# Fixtures
@pytest.fixture(name="engine")
def fixture_engine():
    """Configura el motor de base de datos para PostgreSQL."""
    DATABASE_URL = "postgresql+psycopg2://postgres:oracle@localhost:5432/sqlmodel_db"
    engine = create_engine(DATABASE_URL, echo=False)
    yield engine
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="session")
def fixture_session(engine):
    """Crea una sesión para la base de datos."""
    # Crear tablas antes de ejecutar las pruebas
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    # Limpiar después de las pruebas
    SQLModel.metadata.drop_all(engine)

class TestQueryDecorator:
    
    def test_select_query(self, session):
        """Test para una consulta SELECT."""
        print("\n🔍 Test: Consulta SELECT")
        print("━━━━━━━━━━━━━━━━━━━━━━━")
        # Preparar datos
        session.add_all([TestUser(name="Alice"), TestUser(name="Bob")])
        session.commit()
        
        @transactional(read_only=True)
        @query(value="SELECT * FROM test_users ORDER BY name")
        def get_users(session: Session) -> List[Dict[str, Any]]:
            pass
            
        result = get_users(session=session)
        print(f"📦 Usuarios encontrados: {result}")
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"
        print("✅ Test completado con éxito")

    def test_scalar_query(self, session):
        """Test para una consulta escalar."""
        print("\n🔍 Test: Consulta escalar (COUNT)")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        session.add(TestUser(name="Alice"))
        session.commit()
        
        @transactional(read_only=True)
        @query(value="SELECT COUNT(*) FROM test_users", scalar=True)
        def count_users(session: Session) -> int:
            pass
            
        result = count_users(session=session)
        print(f"📊 Total de usuarios: {result}")
        assert result == 1
        print("✅ Test completado con éxito")

    def test_parameterized_query(self, session):
        """Test para una consulta parametrizada."""
        print("\n🔍 Test: Consulta parametrizada")
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
            
        result = find_by_name(session=session, name = "Alice")
        print(f"📦 Usuario encontrado: {result}")
        assert len(result) == 1
        assert result[0]["name"] == "Alice"
        print("✅ Test completado con éxito")

    def test_insert_query(self, session):
        """Test para una consulta de inserción."""
        print("\n🖋️ Test: Inserción de usuario")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        @transactional
        @query(value="INSERT INTO test_users (name) VALUES (:name)")
        def create_user(session: Session, name: str) -> None:
            pass
            
        create_user(session=session, name="Carol")
        
        # Corregir esta línea usando text()
        result = session.execute(text("SELECT * FROM test_users")).fetchall()
        print(f"📦 Usuarios en la base de datos: {result}")
        assert len(result) == 1
        assert result[0][1] == "Carol"
