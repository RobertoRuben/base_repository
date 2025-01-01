import pytest
from sqlmodel import SQLModel, Session, create_engine, select, Field
from src.core.base_repository import BaseRepository
from src.decorator.repository import repository
from typing import Optional
from datetime import datetime
from src.exception.base_repository_exception import EntityNotFoundError

# Definición del modelo de entidad
class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    price: float
    description: Optional[str] = None
    stock: int = Field(default=0)

# Repositorio con decorador @repository
@repository
class ProductRepository(BaseRepository[Product]):
    """Repositorio para operaciones CRUD de productos."""

    def find_by_price_range(self, session: Session, min_price: float, max_price: float):
        """Método personalizado para buscar productos por rango de precio."""
        statement = select(self.model_class).where(
            self.model_class.price >= min_price,
            self.model_class.price <= max_price
        )
        return session.exec(statement).all()

# Fixtures para la base de datos y sesiones
@pytest.fixture(name="engine")
def fixture_engine():
    """Configura el motor de base de datos SQLite en memoria para pruebas."""
    engine = create_engine("sqlite:///:memory:", echo=True)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)  # Limpia la base de datos después de las pruebas

@pytest.fixture(name="session")
def fixture_session(engine):
    """Crea una sesión para la base de datos en memoria."""
    with Session(engine) as session:
        yield session

@pytest.fixture
def product_repo():
    """Crea una instancia del repositorio ProductRepository."""
    return ProductRepository()

# Test para crear un producto
def test_create_product(session: Session, product_repo: ProductRepository):
    """🛠️ Prueba la creación de un producto en la base de datos."""
    new_product = Product(name="Laptop", price=999.99, description="Potente laptop", stock=10)
    product_repo.save(session, new_product)
    session.commit()
    
    # Verificar que el producto ha sido creado
    product = product_repo.get_by_id(session, new_product.id)
    print("📦 Producto creado:", product.name)
    assert product is not None, "El producto no debería ser nulo"
    assert product.name == "Laptop"
    assert product.price == 999.99
    assert product.stock == 10
    print("✅ Producto validado con éxito.")

# Test para obtener todos los productos
def test_get_all_products(session: Session, product_repo: ProductRepository):
    """🗃️ Prueba la obtención de todos los productos."""
    product1 = Product(name="Laptop", price=999.99, description="Potente laptop", stock=10)
    product2 = Product(name="Phone", price=499.99, description="Teléfono inteligente", stock=5)
    
    product_repo.save(session, product1)
    product_repo.save(session, product2)
    session.commit()
    
    products = product_repo.get_all(session)
    print("📱 Productos obtenidos:", [p.name for p in products])
    assert len(products) == 2, "Deberían existir 2 productos"
    assert products[0].name == "Laptop"
    assert products[1].name == "Phone"
    print("✅ Todos los productos obtenidos correctamente.")

# Test para obtener producto por ID
def test_get_product_by_id(session: Session, product_repo: ProductRepository):
    """🔍 Prueba la obtención de un producto por su ID."""
    new_product = Product(name="Tablet", price=299.99, description="Tablet económica", stock=7)
    product_repo.save(session, new_product)
    session.commit()
    
    product = product_repo.get_by_id(session, new_product.id)
    print("🔍 Producto obtenido por ID:", product.name)
    assert product is not None, "El producto no debería ser nulo"
    assert product.id == new_product.id
    assert product.name == "Tablet"
    print("✅ Producto por ID validado correctamente.")

# Test para actualizar un producto
def test_update_product(session: Session, product_repo: ProductRepository):
    """✏️ Prueba la actualización de un producto."""
    product = Product(name="Smartwatch", price=199.99, description="Reloj inteligente", stock=15)
    product_repo.save(session, product)
    session.commit()
    
    # Actualizar el producto
    product.price = 179.99
    updated_product = product_repo.update(session, product.id, product)
    session.commit()
    
    # Verificar que el precio ha sido actualizado
    product_in_db = product_repo.get_by_id(session, product.id)
    print("✏️ Producto actualizado:", product_in_db.name, "Nuevo precio:", product_in_db.price)
    assert product_in_db.price == 179.99, "El precio no coincide con el valor actualizado"
    print("✅ Producto actualizado correctamente.")

# Test para eliminar un producto
def test_delete_product(session: Session, product_repo: ProductRepository):
    """❌ Prueba la eliminación de un producto."""
    product = Product(name="Headphones", price=89.99, description="Auriculares Bluetooth", stock=20)
    product_repo.save(session, product)
    session.commit()
    
    # Eliminar el producto
    product_repo.delete(session, product.id)
    session.commit()
    
    # Verificar que intentar obtener el producto lanza la excepción esperada
    with pytest.raises(EntityNotFoundError) as exc_info:
        product_repo.get_by_id(session, product.id)
    
    # Verificar detalles de la excepción
    assert str(exc_info.value) == f"Entity not found with ID: {product.id}"
    print("❌ Producto eliminado correctamente y no encontrado:", product.name)

# Test para el método personalizado de búsqueda por rango de precio
def test_find_by_price_range(session: Session, product_repo: ProductRepository):
    """🔍 Prueba la búsqueda de productos por rango de precio."""
    product1 = Product(name="Smartphone", price=799.99, description="Smartphone de gama alta", stock=10)
    product2 = Product(name="Smartwatch", price=199.99, description="Smartwatch económico", stock=15)
    product3 = Product(name="Laptop", price=999.99, description="Laptop potente", stock=5)
    product_repo.save(session, product1)
    product_repo.save(session, product2)
    product_repo.save(session, product3)
    session.commit()
    
    # Buscar productos entre 199 y 800 (inclusive)
    products_in_range = product_repo.find_by_price_range(session, 199, 800)
    print("🔍 Productos en rango de precio:", [p.name for p in products_in_range])
    assert len(products_in_range) == 2, "Deberían encontrarse 2 productos en el rango"
    assert products_in_range[0].name == "Smartphone"
    assert products_in_range[1].name == "Smartwatch"
    print("✅ Búsqueda por rango de precio completada.")
