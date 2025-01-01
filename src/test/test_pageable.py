from datetime import datetime
import pytest
from sqlmodel import SQLModel, Session, create_engine, Field, Relationship
from src.repository.pageable.pageable_operations import PageableOperations
from src.decorator.transactional import transactional

# Modelos de prueba
class Author(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    books: list["Book"] = Relationship(back_populates="author")


class Book(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    published_date: datetime
    author_id: int | None = Field(default=None, foreign_key="author.id")
    author: Author | None = Relationship(back_populates="books")


# Fixtures
@pytest.fixture(name="engine")
def fixture_engine():
    """Configura el motor de base de datos para PostgreSQL."""
    DATABASE_URL = "postgresql+psycopg2://postgres:oracle@localhost:5432/sqlmodel_db"
    engine = create_engine(DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(name="session")
def fixture_session(engine):
    """Crea una sesión para la base de datos."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def pageable():
    """Crea una instancia de PageableOperations para el modelo Book."""
    return PageableOperations(Book)


# Tests
@transactional(read_only=True)
def test_get_page_with_joins(session: Session, pageable: PageableOperations):
    """Prueba paginación con joins (INNER JOIN)."""
    # Paginación con INNER JOIN para un autor específico
    page_result = pageable.get_page(
        session=session,
        page=1,
        size=2,
        join_relations=[Book.author],  # Relación explícita
        join_type="inner",
        select_fields=[Author.name, Book.title],
        where=(Book.title == "Book 1"),  # Filtrar por el título del libro
        order_by=Book.title
    )

    print("\n🔍 Resultado completo de get_page (INNER JOIN):")
    print(page_result)

    # Validaciones
    assert page_result.pagination.total_items == 1, f"Expected 1 item, got {page_result.pagination.total_items}"
    assert len(page_result.data) == 1, f"Expected 1 item in data, got {len(page_result.data)}"
    assert page_result.data[0]["title"] == "Book 1", f"Expected 'Book 1', got {page_result.data[0]['Book.title']}"


@transactional(read_only=True)
def test_get_page_with_left_join(session: Session, pageable: PageableOperations):
    """Prueba de paginación con LEFT JOIN."""
    # Paginación con LEFT JOIN para incluir libros huérfanos
    page_result = pageable.get_page(
        session=session,
        page=5,
        size=5,
        join_relations=[Book.author],  # Relación explícita
        join_type="left",
        select_fields=[Author.name, Book.title],
        where=(Book.title.like("Book%") | (Book.title == "Orphan Book")),  # Incluir "Orphan Book"
        order_by=Book.title
    )

    print("\n🔍 Resultado completo de get_page (LEFT JOIN):")
    print(page_result)

    # Validaciones
    assert page_result.pagination.total_items == 21, f"Expected 21 items, got {page_result.pagination.total_items}"
    assert len(page_result.data) == 1, f"Expected 1 item in data, got {len(page_result.data)}"
    assert page_result.data[0]["title"] == "Orphan Book", f"Expected 'Orphan Book', got {page_result.data[0]['title']}"
    assert page_result.data[0]["name"] is None, f"Expected 'name' to be None, got {page_result.data[0]['name']}"


@transactional(read_only=True)
def test_pagination_and_sorting(session: Session, pageable: PageableOperations):
    """Prueba paginación y ordenamiento."""
    # Paginación en una página específica con orden descendente
    page_result = pageable.get_page(
        session=session,
        page=2,
        size=5,
        join_relations=[Book.author],  # Relación explícita
        join_type="inner",
        select_fields=[Author.name, Book.title],
        order_by=Book.title,
        sort_order="desc"
    )

    print("\n🔍 Resultado completo de get_page (Página 2, Orden Descendente):")
    print(page_result)

    # Validaciones
    assert len(page_result.data) == 5, f"Expected 5 items in data, got {len(page_result.data)}"
    assert page_result.pagination.current_page == 2, f"Expected current_page=2, got {page_result.pagination.current_page}"
    assert page_result.pagination.page_size == 5, f"Expected page_size=5, got {page_result.pagination.page_size}"
    assert page_result.pagination.total_items == 20, f"Expected total_items=20, got {page_result.pagination.total_items}"
    assert page_result.pagination.total_pages == 4, f"Expected total_pages=4, got {page_result.pagination.total_pages}"

    # Verificar los datos específicos de la página 2
    expected_data = [
        {"name": "Alice Johnson", "title": "Book 6"},
        {"name": "Bob Williams", "title": "Book 7"},
        {"name": "Bob Williams", "title": "Book 8"},
        {"name": "Eve Brown", "title": "Book 9"},
        {"name": "Eve Brown", "title": "Book 10"},
    ]
    actual_data = page_result.data

    assert actual_data == expected_data, f"Expected data {expected_data}, got {actual_data}"
