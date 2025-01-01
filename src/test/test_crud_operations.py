import pytest
from sqlmodel import SQLModel, Session, create_engine, Field
from typing import Optional
from datetime import datetime
from src.repository.crud.crud_operations import BasicOperations
from src.decorator.transactional import transactional

# Modelo de prueba
class Recipe(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    ingredients: str
    steps: str
    created_at: datetime = Field(default_factory=datetime.now)

# Fixtures
@pytest.fixture(name="engine")
def fixture_engine():
    """Configura el motor de base de datos para MariaDB."""
    DATABASE_URL = "mysql+pymysql://root:oracle@localhost:3306/sqlmodel_db"
    engine = create_engine(DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    print("🛠️ Base de datos MariaDB configurada")
    return engine

@pytest.fixture(name="session")
def fixture_session(engine):
    """Crea una sesión para la base de datos."""
    with Session(engine) as session:
        print("🔗 Sesión creada para MariaDB")
        yield session

@pytest.fixture
def crud():
    """Crea una instancia del CRUDOperations para el modelo Recipe."""
    print("⚙️ CRUDOperations inicializado")
    return BasicOperations(Recipe)

# Funciones transaccionales
@transactional
def create_recipe(session: Session, crud: BasicOperations, recipe: Recipe):
    """Crea una receta."""
    crud.save(session, recipe)
    print(f"➕ Receta creada: {recipe}")

@transactional(read_only=True)
def get_all(session: Session, crud: BasicOperations):
    """Obtiene todas las recetas."""
    recipes = crud.get_all(session)
    print(f"📋 Todas las recetas obtenidas: {recipes}")
    return recipes

@transactional(read_only=True)
def get_all_by(session: Session, crud: BasicOperations, where: Optional[dict]):
    """Obtiene todas las recetas aplicando filtros."""
    recipes = crud.get_all(session, where=where)
    print(f"🔍 Recetas filtradas con {where}: {recipes}")
    return recipes

@transactional(read_only=True)
def get_all_order(session: Session, crud: BasicOperations, order_by: str, sort_order: str = "asc"):
    """Obtiene todas las recetas aplicando ordenamiento."""
    recipes = crud.get_all(session, order_by=order_by, sort_order=sort_order)
    print(f"↕️ Recetas ordenadas por {order_by} ({sort_order}): {recipes}")
    return recipes

@transactional(read_only=True)
def get_all_with_options(
    session: Session,
    crud: BasicOperations,
    where: Optional[dict] = None,
    order_by: Optional[str] = None,
    sort_order: str = "asc"
):
    """Obtiene todas las recetas con filtros y ordenamiento."""
    recipes = crud.get_all(session, where=where, order_by=order_by, sort_order=sort_order)
    print(f"🎯 Recetas con filtros {where} y orden {order_by} ({sort_order}): {recipes}")
    return recipes

@transactional
def update_recipe(session: Session, crud: BasicOperations, recipe_id: int, updated_recipe: Recipe):
    """Actualiza una receta."""
    crud.update(session, recipe_id, updated_recipe)
    print(f"🔄 Receta actualizada ID {recipe_id}: {updated_recipe}")

@transactional
def delete_recipe(session: Session, crud: BasicOperations, recipe_id: int):
    """Elimina una receta."""
    success = crud.delete(session, recipe_id)
    print(f"🗑️ Resultado de eliminación de receta ID {recipe_id}: {'Éxito' if success else 'Fallido'}")
    return success

# Tests
def test_crud_operations(session: Session, crud: BasicOperations):
    """Prueba básica de operaciones CRUD."""
    print("🛠️ Iniciando test_crud_operations")
    recipe1 = Recipe(name="Ensalada César", ingredients="Lechuga, crutones, pollo", steps="Mezclar todo")
    recipe2 = Recipe(name="Sopa de Tomate", ingredients="Tomates, ajo, cebolla", steps="Cocinar y licuar")
    create_recipe(session, crud, recipe1)
    create_recipe(session, crud, recipe2)

    recipes = get_all(session, crud)
    assert len(recipes) == 2

    updated_data = Recipe(name="Ensalada César Actualizada", ingredients="Lechuga, crutones", steps="Mezclar")
    update_recipe(session, crud, recipe_id=recipe1.id, updated_recipe=updated_data)

    updated_recipe = session.get(Recipe, recipe1.id)
    assert updated_recipe.name == "Ensalada César Actualizada"

    delete_success = delete_recipe(session, crud, recipe_id=recipe2.id)
    assert delete_success is True

    recipes_after_deletion = get_all(session, crud)
    assert len(recipes_after_deletion) == 1
    print("✅ test_crud_operations completado")

def test_transaction_rollback_on_error(session: Session, crud: BasicOperations):
    """Prueba de rollback en caso de error."""
    print("🔄 Iniciando test_transaction_rollback_on_error")
    recipe = Recipe(name="Error Recipe", ingredients="Ingredientes", steps="Pasos")
    create_recipe(session, crud, recipe)

    try:
        update_recipe(session, crud, recipe_id=recipe.id, updated_recipe=None)
    except Exception as e:
        print(f"❌ Error esperado: {e}")

    rolled_back_recipe = session.get(Recipe, recipe.id)
    assert rolled_back_recipe.name == "Error Recipe"
    print("✅ test_transaction_rollback_on_error completado")

def test_get_all_with_options(session: Session, crud: BasicOperations):
    """Prueba de obtener recetas combinando filtros y ordenamiento."""
    print("🎯 Iniciando test_get_all_with_options")
    recipe1 = Recipe(name="Ensalada César", ingredients="Lechuga, pollo", steps="Mezclar todo")
    recipe2 = Recipe(name="Sopa de Tomate", ingredients="Tomates, ajo", steps="Cocinar")
    recipe3 = Recipe(name="Ensalada Rusa", ingredients="Papa, zanahoria", steps="Hervir y mezclar")
    create_recipe(session, crud, recipe1)
    create_recipe(session, crud, recipe2)
    create_recipe(session, crud, recipe3)

    filtered_sorted_recipes = get_all_with_options(
        session, crud, where={"ingredients": "Lechuga, pollo"}, order_by="name", sort_order="asc"
    )
    assert len(filtered_sorted_recipes) == 1
    assert filtered_sorted_recipes[0].name == "Ensalada César"
    print("✅ test_get_all_with_options completado")
