import pytest
from sqlmodel import SQLModel, Session, create_engine, Field
from typing import Optional
from datetime import datetime
from src.repository.crud.crud_operations import BasicOperations
from src.decorator.transactional import transactional

# Test Model
class Recipe(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    ingredients: str
    steps: str
    created_at: datetime = Field(default_factory=datetime.now)

# Fixtures
@pytest.fixture(name="engine")
def fixture_engine():
    """Sets up the MariaDB database engine."""
    DATABASE_URL = "mysql+pymysql://root:oracle@localhost:3306/sqlmodel_db"
    engine = create_engine(DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    print("🛠️ MariaDB database configured")
    return engine

@pytest.fixture(name="session")
def fixture_session(engine):
    """Creates a session for the database."""
    with Session(engine) as session:
        print("🔗 Session created for MariaDB")
        yield session

@pytest.fixture
def crud():
    """Creates an instance of CRUDOperations for the Recipe model."""
    print("⚙️ CRUDOperations initialized")
    return BasicOperations(Recipe)

# Transactional Functions
@transactional
def create_recipe(session: Session, crud: BasicOperations, recipe: Recipe):
    """Creates a recipe."""
    crud.save(session, recipe)
    print(f"➕ Recipe created: {recipe}")

@transactional(read_only=True)
def get_all(session: Session, crud: BasicOperations):
    """Gets all recipes."""
    recipes = crud.get_all(session)
    print(f"📋 All recipes fetched: {recipes}")
    return recipes

@transactional(read_only=True)
def get_all_by(session: Session, crud: BasicOperations, where: Optional[dict]):
    """Gets all recipes with filters."""
    recipes = crud.get_all(session, where=where)
    print(f"🔍 Filtered recipes with {where}: {recipes}")
    return recipes

@transactional(read_only=True)
def get_all_order(session: Session, crud: BasicOperations, order_by: str, sort_order: str = "asc"):
    """Gets all recipes with sorting."""
    recipes = crud.get_all(session, order_by=order_by, sort_order=sort_order)
    print(f"↕️ Recipes sorted by {order_by} ({sort_order}): {recipes}")
    return recipes

@transactional(read_only=True)
def get_all_with_options(
    session: Session,
    crud: BasicOperations,
    where: Optional[dict] = None,
    order_by: Optional[str] = None,
    sort_order: str = "asc"
):
    """Gets all recipes with filters and sorting."""
    recipes = crud.get_all(session, where=where, order_by=order_by, sort_order=sort_order)
    print(f"🎯 Recipes with filters {where} and order {order_by} ({sort_order}): {recipes}")
    return recipes

@transactional
def update_recipe(session: Session, crud: BasicOperations, recipe_id: int, updated_recipe: Recipe):
    """Updates a recipe."""
    crud.update(session, recipe_id, updated_recipe)
    print(f"🔄 Recipe updated ID {recipe_id}: {updated_recipe}")

@transactional
def delete_recipe(session: Session, crud: BasicOperations, recipe_id: int):
    """Deletes a recipe."""
    success = crud.delete(session, recipe_id)
    print(f"🗑️ Recipe deletion result ID {recipe_id}: {'Success' if success else 'Failed'}")
    return success

# Tests
def test_crud_operations(session: Session, crud: BasicOperations):
    """Basic CRUD operations test."""
    print("🛠️ Starting test_crud_operations")
    recipe1 = Recipe(name="Caesar Salad", ingredients="Lettuce, croutons, chicken", steps="Mix everything")
    recipe2 = Recipe(name="Tomato Soup", ingredients="Tomatoes, garlic, onion", steps="Cook and blend")
    create_recipe(session, crud, recipe1)
    create_recipe(session, crud, recipe2)

    recipes = get_all(session, crud)
    assert len(recipes) == 2

    updated_data = Recipe(name="Updated Caesar Salad", ingredients="Lettuce, croutons", steps="Mix")
    update_recipe(session, crud, recipe_id=recipe1.id, updated_recipe=updated_data)

    updated_recipe = session.get(Recipe, recipe1.id)
    assert updated_recipe.name == "Updated Caesar Salad"

    delete_success = delete_recipe(session, crud, recipe_id=recipe2.id)
    assert delete_success is True

    recipes_after_deletion = get_all(session, crud)
    assert len(recipes_after_deletion) == 1
    print("✅ test_crud_operations completed")

def test_transaction_rollback_on_error(session: Session, crud: BasicOperations):
    """Test rollback in case of error."""
    print("🔄 Starting test_transaction_rollback_on_error")
    recipe = Recipe(name="Error Recipe", ingredients="Ingredients", steps="Steps")
    create_recipe(session, crud, recipe)

    try:
        update_recipe(session, crud, recipe_id=recipe.id, updated_recipe=None)
    except Exception as e:
        print(f"❌ Expected error: {e}")

    rolled_back_recipe = session.get(Recipe, recipe.id)
    assert rolled_back_recipe.name == "Error Recipe"
    print("✅ test_transaction_rollback_on_error completed")

def test_get_all_with_options(session: Session, crud: BasicOperations):
    """Test getting recipes combining filters and sorting."""
    print("🎯 Starting test_get_all_with_options")
    recipe1 = Recipe(name="Caesar Salad", ingredients="Lettuce, chicken", steps="Mix everything")
    recipe2 = Recipe(name="Tomato Soup", ingredients="Tomatoes, garlic", steps="Cook")
    recipe3 = Recipe(name="Russian Salad", ingredients="Potato, carrot", steps="Boil and mix")
    create_recipe(session, crud, recipe1)
    create_recipe(session, crud, recipe2)
    create_recipe(session, crud, recipe3)

    filtered_sorted_recipes = get_all_with_options(
        session, crud, where={"ingredients": "Lettuce, chicken"}, order_by="name", sort_order="asc"
    )
    assert len(filtered_sorted_recipes) == 1
    assert filtered_sorted_recipes[0].name == "Caesar Salad"
    print("✅ test_get_all_with_options completed")
