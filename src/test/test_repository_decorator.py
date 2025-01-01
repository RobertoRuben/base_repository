import pytest
from sqlmodel import SQLModel, Session, create_engine, select, Field
from src.core.base_repository import BaseRepository
from src.decorator.repository import repository
from typing import Optional
from datetime import datetime
from src.exception.base_repository_exception import EntityNotFoundError

# Entity model definition
class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    price: float
    description: Optional[str] = None
    stock: int = Field(default=0)

# Repository with @repository decorator
@repository
class ProductRepository(BaseRepository[Product]):
    """Repository for CRUD operations on products."""

    def find_by_price_range(self, session: Session, min_price: float, max_price: float):
        """Custom method to find products within a price range."""
        statement = select(self.model_class).where(
            self.model_class.price >= min_price,
            self.model_class.price <= max_price
        )
        return session.exec(statement).all()

# Fixtures for database and sessions
@pytest.fixture(name="engine")
def fixture_engine():
    """Configures an in-memory SQLite database engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=True)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)  # Cleans up the database after tests

@pytest.fixture(name="session")
def fixture_session(engine):
    """Creates a session for the in-memory database."""
    with Session(engine) as session:
        yield session

@pytest.fixture
def product_repo():
    """Creates an instance of the ProductRepository."""
    return ProductRepository()

# Test to create a product
def test_create_product(session: Session, product_repo: ProductRepository):
    """🛠️ Test product creation in the database."""
    new_product = Product(name="Laptop", price=999.99, description="Powerful laptop", stock=10)
    product_repo.save(session, new_product)
    session.commit()
    
    # Verify the product has been created
    product = product_repo.get_by_id(session, new_product.id)
    print("📦 Product created:", product.name)
    assert product is not None, "The product should not be null"
    assert product.name == "Laptop"
    assert product.price == 999.99
    assert product.stock == 10
    print("✅ Product validated successfully.")

# Test to get all products
def test_get_all_products(session: Session, product_repo: ProductRepository):
    """🗃️ Test retrieving all products."""
    product1 = Product(name="Laptop", price=999.99, description="Powerful laptop", stock=10)
    product2 = Product(name="Phone", price=499.99, description="Smartphone", stock=5)
    
    product_repo.save(session, product1)
    product_repo.save(session, product2)
    session.commit()
    
    products = product_repo.get_all(session)
    print("📱 Products retrieved:", [p.name for p in products])
    assert len(products) == 2, "There should be 2 products"
    assert products[0].name == "Laptop"
    assert products[1].name == "Phone"
    print("✅ All products retrieved successfully.")

# Test to get product by ID
def test_get_product_by_id(session: Session, product_repo: ProductRepository):
    """🔍 Test retrieving a product by its ID."""
    new_product = Product(name="Tablet", price=299.99, description="Budget tablet", stock=7)
    product_repo.save(session, new_product)
    session.commit()
    
    product = product_repo.get_by_id(session, new_product.id)
    print("🔍 Product retrieved by ID:", product.name)
    assert product is not None, "The product should not be null"
    assert product.id == new_product.id
    assert product.name == "Tablet"
    print("✅ Product by ID validated successfully.")

# Test to update a product
def test_update_product(session: Session, product_repo: ProductRepository):
    """✏️ Test updating a product."""
    product = Product(name="Smartwatch", price=199.99, description="Smartwatch", stock=15)
    product_repo.save(session, product)
    session.commit()
    
    # Update the product
    product.price = 179.99
    updated_product = product_repo.update(session, product.id, product)
    session.commit()
    
    # Verify the price has been updated
    product_in_db = product_repo.get_by_id(session, product.id)
    print("✏️ Product updated:", product_in_db.name, "New price:", product_in_db.price)
    assert product_in_db.price == 179.99, "The price doesn't match the updated value"
    print("✅ Product updated successfully.")

# Test to delete a product
def test_delete_product(session: Session, product_repo: ProductRepository):
    """❌ Test deleting a product."""
    product = Product(name="Headphones", price=89.99, description="Bluetooth headphones", stock=20)
    product_repo.save(session, product)
    session.commit()
    
    # Delete the product
    product_repo.delete(session, product.id)
    session.commit()
    
    # Verify that trying to retrieve the product throws the expected exception
    with pytest.raises(EntityNotFoundError) as exc_info:
        product_repo.get_by_id(session, product.id)
    
    # Verify exception details
    assert str(exc_info.value) == f"Entity not found with ID: {product.id}"
    print("❌ Product deleted successfully and not found:", product.name)

# Test for the custom method to find products by price range
def test_find_by_price_range(session: Session, product_repo: ProductRepository):
    """🔍 Test finding products by price range."""
    product1 = Product(name="Smartphone", price=799.99, description="High-end smartphone", stock=10)
    product2 = Product(name="Smartwatch", price=199.99, description="Budget smartwatch", stock=15)
    product3 = Product(name="Laptop", price=999.99, description="Powerful laptop", stock=5)
    product_repo.save(session, product1)
    product_repo.save(session, product2)
    product_repo.save(session, product3)
    session.commit()
    
    # Find products between 199 and 800 (inclusive)
    products_in_range = product_repo.find_by_price_range(session, 199, 800)
    print("🔍 Products in price range:", [p.name for p in products_in_range])
    assert len(products_in_range) == 2, "There should be 2 products in the range"
    assert products_in_range[0].name == "Smartphone"
    assert products_in_range[1].name == "Smartwatch"
    print("✅ Price range search completed.")
