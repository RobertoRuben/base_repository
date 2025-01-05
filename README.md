
# Base Repository 🚀

> ⚠️ **Note**: This library is currently in beta. Feedback and contributions are welcome!

A powerful Python library that implements the repository pattern for SQL operations, providing a clean and type-safe way to interact with your database using SQLModel and FastAPI.

## Quick Overview 🎯

```python
from base_repository import BaseRepository

# Define your repository
class UserRepo(BaseRepository[User]):
    def __init__(self, session = Depends(get_session)):
        super().__init__(User, session)

# Use built-in operations with full type support
users = repo.find_by({"status": "active"})
latest = repo.find_latest(order_by="created_at")
page = repo.get_page(page=1, size=10)
```

## Key Features ⭐

- 🔒 **Type-Safe Operations**: Full IDE support with type hints
- 📦 **Built-in CRUD**: Ready-to-use repository pattern implementation
- 🔍 **Advanced Querying**: Native SQL, stored procedures, and complex searches
- 📑 **Smart Pagination**: Built-in support for paginated queries
- 🛡️ **Transaction Management**: Automatic handling with `@transactional`
- 💉 **FastAPI Integration**: Seamless dependency injection support

## Installation 📦

```bash
pip install base-repository
```

## Documentation Structure 📚

1. [Getting Started](#getting-started)
2. [Core Concepts](#core-concepts)
3. [Advanced Features](#advanced-features)
4. [API Reference](#api-reference)
5. [Examples & Use Cases](#examples--use-cases)

## Getting Started 🚀

### 1. Configure Database and Session Management

```python
# config/database.py
from sqlmodel import SQLModel, create_engine, Session
from fastapi import Depends
from .settings import settings

# Database URL configuration
db_url = f"mysql+pymysql://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"

# Create engine
engine = create_engine(db_url, echo=True)

# Create all tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Session dependency for FastAPI
def get_session():
    """
    FastAPI dependency that provides a database session.
    Usage in repositories:
        def __init__(self, session: Session = Depends(get_session)):
            super().__init__(Model, session)
    """
    with Session(engine) as session:
        yield session
```

### 2. Define Your Model

```python
from sqlmodel import SQLModel, Field
from decimal import Decimal
from datetime import datetime

class Product(SQLModel, table=True):
    id: int | None = Field(primary_key=True, index=True)
    name: str
    price: Decimal
    stock: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 3. Create Your Repository

```python
from fastapi import Depends
from sqlmodel import Session
from base_repository import BaseRepository
from .database import get_session

class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: Session = Depends(get_session)):
        super().__init__(Product, session)
    
    @query("SELECT * FROM product WHERE price > :min_price")
    def find_premium_products(self, min_price: Decimal) -> List[Product]:
        pass
```

### 4. Create Your Service

```python
from fastapi import Depends

class ProductService:
    def __init__(self, repo: ProductRepository = Depends()):
        self.repo = repo
    
    @transactional
    async def create_product(self, data: ProductCreate) -> Product:
        return self.repo.save(Product(**data.dict()))
    
    @transactional(read_only=True)
    async def get_product_catalog(self, page: int = 1) -> Page[Product]:
        return self.repo.get_page(
            page=page,
            size=20,
            order_by="name"
        )
```

### 5. Use in FastAPI Controllers

```python
from fastapi import APIRouter, Depends
from .service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductResponse)
async def create_product(
    data: ProductCreate,
    service: ProductService = Depends()
):
    return await service.create_product(data)

@router.get("/", response_model=Page[ProductResponse])
async def get_products(
    page: int = 1,
    service: ProductService = Depends()
):
    return await service.get_product_catalog(page)
```

## Core Concepts 🎓

### Repository Pattern with FastAPI

Base Repository implements the repository pattern with proper FastAPI dependency injection:

```python
from fastapi import Depends
from sqlmodel import Session
from base_repository import BaseRepository
from .database import get_session

class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session = Depends(get_session)):
        super().__init__(User, session)
        
    # Custom methods with automatic session management
    def find_active_users(self) -> List[User]:
        return self.find_by({"status": "active"})
```

### Built-in Operations

Every repository automatically includes:

1. **Basic CRUD**:
```python
class UserService:
    def __init__(self, repo: UserRepository = Depends()):
        self.repo = repo

    # Create
    @transactional
    async def create_user(self, data: UserCreate) -> User:
        return self.repo.save(User(**data.dict()))

    # Read
    @transactional(read_only=True)
    async def get_user(self, id: int) -> User:
        return self.repo.get_by_id(id)

    # Update
    @transactional
    async def update_user(self, id: int, data: UserUpdate) -> User:
        return self.repo.update(id, User(**data.dict()))

    # Delete
    @transactional
    async def delete_user(self, id: int) -> bool:
        return self.repo.delete(id)
```

2. **Advanced Find Operations**:
```python
class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session = Depends(get_session)):
        super().__init__(User, session)

    # Find with conditions
    @query("""
        SELECT u.* FROM users u
        WHERE u.status = :status 
        AND u.created_at >= :since_date
    """)
    def find_recent_active_users(
        self, 
        status: str = "active",
        since_date: datetime
    ) -> List[User]:
        pass

    # Complex date range queries
    def find_users_registered_between(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[User]:
        return self.find_by_date_between(
            "created_at",
            start_date=start_date,
            end_date=end_date
        )

    # Pattern matching with automatic session management
    def find_users_by_name_pattern(self, pattern: str) -> List[User]:
        return self.find_by_like("name", pattern)
```

3. **Smart Pagination with FastAPI**

```python
from fastapi import Query

class UserController:
    @router.get("/users", response_model=Page[UserResponse])
    async def get_users(
        self,
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100),
        order_by: str = Query("created_at"),
        service: UserService = Depends()
    ):
        return await service.get_users_page(
            page=page,
            size=size,
            order_by=order_by
        )

class UserService:
    def __init__(self, repo: UserRepository = Depends()):
        self.repo = repo

    @transactional(read_only=True)
    async def get_users_page(
        self,
        page: int,
        size: int,
        order_by: str
    ) -> Page[User]:
        return self.repo.get_page(
            page=page,
            size=size,
            order_by=order_by,
            sort_order="desc"
        )
```

## Advanced Features 🔥

### 1. Transaction Management with FastAPI

```python
from fastapi import Depends, HTTPException
from base_repository import transactional

class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository = Depends(),
        product_repo: ProductRepository = Depends(),
        user_repo: UserRepository = Depends()
    ):
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.user_repo = user_repo

    @transactional  # Automatic transaction management
    async def create_order(self, order_data: OrderCreate) -> Order:
        # All operations are wrapped in a transaction
        user = self.user_repo.get_by_id(order_data.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        product = self.product_repo.get_by_id(order_data.product_id)
        if not product or product.stock < order_data.quantity:
            raise HTTPException(status_code=400, detail="Product unavailable")

        # Update product stock
        product.stock -= order_data.quantity
        self.product_repo.save(product)

        # Create order
        order = Order(**order_data.dict())
        return self.order_repo.save(order)

    @transactional(read_only=True)  # Optimized for reads
    async def get_order_details(self, order_id: int) -> OrderDetails:
        return self.order_repo.get_details(order_id)

    @transactional(auto_concurrent=True)  # Handles concurrent access
    async def update_order_status(
        self,
        order_id: int,
        status: str
    ) -> Order:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order.status = status
        return self.order_repo.save(order)
```

### 2. Complex Queries with FastAPI Integration

```python
from fastapi import Depends
from sqlmodel import Session
from base_repository import query

class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: Session = Depends(get_session)):
        super().__init__(Product, session)

    @query("""
        WITH RankedProducts AS (
            SELECT 
                p.*,
                AVG(r.rating) as avg_rating,
                COUNT(r.id) as review_count,
                ROW_NUMBER() OVER (
                    PARTITION BY p.category_id 
                    ORDER BY AVG(r.rating) DESC
                ) as rank
            FROM products p
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.price BETWEEN :min_price AND :max_price
            GROUP BY p.id
            HAVING COUNT(r.id) >= :min_reviews
        )
        SELECT * FROM RankedProducts
        WHERE rank <= :top_n
    """)
    def find_top_rated_by_category(
        self,
        min_price: Decimal,
        max_price: Decimal,
        min_reviews: int = 5,
        top_n: int = 3
    ) -> List[Product]:
        pass

    @query("""
        SELECT 
            p.*,
            SUM(o.quantity) as total_sold
        FROM products p
        JOIN orders o ON p.id = o.product_id
        WHERE o.created_at >= :since_date
        GROUP BY p.id
        HAVING total_sold >= :min_sales
    """, scalar=False)
    def find_best_sellers(
        self,
        since_date: datetime,
        min_sales: int = 100
    ) -> List[Product]:
        pass
```

### 3. Stored Procedures with Different Databases

```python
class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: Session = Depends(get_session)):
        super().__init__(Order, session)

    @store_procedure(
        name="sp_process_payment",
        db_type=DatabaseType.POSTGRESQL
    )
    def process_payment(
        self,
        order_id: int,
        amount: Decimal,
        payment_method: str
    ) -> PaymentResult:
        pass

    @store_procedure(
        name="sp_calculate_shipping",
        db_type=DatabaseType.MYSQL,
        scalar=True
    )
    def calculate_shipping_cost(
        self,
        order_id: int,
        destination: str
    ) -> Decimal:
        pass

    @store_procedure(
        name="sp_update_inventory",
        db_type=DatabaseType.SQLSERVER
    )
    def update_inventory(
        self,
        product_id: int,
        quantity: int,
        operation: Literal["add", "subtract"]
    ) -> InventoryResult:
        pass
```

## API Reference 📖


Here is the updated documentation with the complete table for Basic Operations:

### Basic Operations
| Method             | Description                  | Example                                                              |
|--------------------|------------------------------|----------------------------------------------------------------------|
| `save`             | Create or update entity      | `repo.save(entity)`                                                  |
| `get_all`          | List all entities            | `repo.get_all(where={"status": "active"}, order_by="created_at")`     |
| `get_by_id`        | Find by primary key          | `repo.get_by_id(1)`                                                  |
| `update`           | Update entity by ID          | `repo.update(1, updated_entity)`                                      |
| `delete`           | Remove entity                | `repo.delete(1)`                                                     |

### Detailed Examples of Basic Operations:
The `BasicOperations` class provides essential CRUD (Create, Read, Update, Delete) operations for managing entities in your database. These operations include saving entities, retrieving all entities with optional filtering and sorting, finding entities by their primary key, updating entities, and deleting entities. Below is a table summarizing these operations, followed by detailed examples.

**Save Operation**
```python
# Create or update entity
repo = UserRepository(session)
new_user = User(name="John Doe", email="john.doe@example.com")
saved_user = repo.save(new_user)
print(saved_user.id)  # Outputs the ID of the saved user
```

**Get All Operation**
```python
# List all entities with optional filters and sorting
repo = UserRepository(session)
users = repo.get_all(
    where={"status": "active"},
    order_by="created_at",
    sort_order="desc"
)
for user in users:
    print(user.name)
```
**Get by ID Operation**
```python
# Find entity by primary key
repo = UserRepository(session)
user = repo.get_by_id(1)
if user:
    print(user.name)
else:
    print("User not found")
```

**Update Operation**
```python
# Update entity by ID
repo = UserRepository(session)
updated_user = User(name="Jane Doe")
updated_entity = repo.update(1, updated_user)
print(updated_entity.name)  # Outputs "Jane Doe"
```

**Delete Operation**
```python
# Remove entity by ID
repo = UserRepository(session)
success = repo.delete(1)
if success:
    print("User deleted")
else:
    print("User not found or delete failed")
```
This should provide a clear understanding of the basic CRUD operations available in the `BasicOperations` class.


### Find Operations
The `FindOperations` class provides various methods to retrieve entities from the database based on different criteria. These operations include finding entities by their primary key, querying with filters, checking for the existence of entities, retrieving entities within a date range, and more. Below is a table summarizing these operations, followed by detailed examples.

| Method                  | Description                   | Example                                                       |
|-------------------------|-------------------------------|---------------------------------------------------------------|
| `find_by`               | Query with filters            | `repo.find_by({"status": "active"})`                          |
| `find_one`              | Get single result             | `repo.find_one({"email": "user@example.com"})`                |
| `exists_by`             | Check existence               | `repo.exists_by(name="John")`                                 |
| `find_by_date_between`  | Date range query              | `repo.find_by_date_between("created_at", start, end)`         |
| `find_by_id`            | Find entity by ID             | `repo.find_by_id(1)`                                          |
| `find_all`              | Retrieve all entities         | `repo.find_all()`                                             |
| `find_all_by_id`        | Retrieve entities by IDs      | `repo.find_all_by_id([1, 2, 3])`                              |
| `find_first`            | Find the first entity         | `repo.find_first(order_by="name")`                            |
| `find_latest`           | Find the latest entity        | `repo.find_latest(order_by="created_at")`                     |
| `find_by_like`          | Search using LIKE operator    | `repo.find_by_like(field="name", value="john")`               |
| `search`                | Search across multiple fields | `repo.search(value="john", fields=["name", "email"])`         |

### Detailed Examples of Find Operations:

**Find by Filters**
```python
# Query with filters
repo = UserRepository(session)
users = repo.find_by({"status": "active", "age": 25})
for user in users:
    print(user.name)
```

**Find One by Filters**
```python
# Get single result by filters
repo = UserRepository(session)
user = repo.find_one({"email": "user@example.com"})
if user:
    print(user.name)
else:
    print("User not found")
```

**Exists by Filters**
```python
# Check if entity exists by field conditions
repo = UserRepository(session)
exists = repo.exists_by(email="user@example.com", status="active")
if exists:
    print("User exists")
else:
    print("User does not exist")
```

**Find by Date Range**
```python
# Find entities between date range
repo = UserRepository(session)
users = repo.find_by_date_between(
    date_field="created_at",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
for user in users:
    print(user.name)
```

**Find by ID**
```python
# Find entity by primary key
repo = UserRepository(session)
user = repo.find_by_id(1)
if user:
    print(user.name)
else:
    print("User not found")
```

**Find All**
```python
# Retrieve all entities
repo = UserRepository(session)
users = repo.find_all()
for user in users:
    print(user.name)
```

**Find All by IDs**
```python
# Retrieve entities by a list of IDs
repo = UserRepository(session)
users = repo.find_all_by_id([1, 2, 3])
for user in users:
    print(user.name)
```

**Find First**
```python
# Find the first entity ordered by a specified field
repo = UserRepository(session)
first_user = repo.find_first(order_by="created_at")
if first_user:
    print(first_user.name)
else:
    print("No users found")
```

**Find Latest**
```python
# Find the latest entity ordered by a specified field
repo = UserRepository(session)
latest_user = repo.find_latest(order_by="created_at")
if latest_user:
    print(latest_user.name)
else:
    print("No users found")
```

**Find by LIKE Operator**
```python
# Search entities by field using LIKE operator
repo = UserRepository(session)
users = repo.find_by_like(field="name", value="john")
for user in users:
    print(user.email)
```

**Search Across Multiple Fields**
```python
# Search across multiple fields
repo = UserRepository(session)
users = repo.search(value="john", fields=["name", "email"])
for user in users:
    print(user.name)
```

This should provide a clear understanding of the various find operations available in the `FindOperations` class.


### Pagination
The `PageableOperations` class provides methods for paginating and searching entities with full IDE support and type checking. These operations include getting paginated results and searching with pagination. Below is a table summarizing these operations, followed by detailed examples.

| Method       | Description            | Example                                          |
|--------------|------------------------|--------------------------------------------------|
| `get_page`   | Get paginated results  | `repo.get_page(page=1, size=10)`                 |
| `find_page`  | Search with pagination | `repo.find_page("john", ["name", "email"])`      |

### Detailed Examples of Pagination Operations:

**Get Paginated Results**
```python
# Get paginated results
repo = UserRepository(session)
page = repo.get_page(
    page=1,
    size=10,
    order_by="created_at",
    sort_order="desc"
)

for item in page.data:
    print(item["name"])

print(page.pagination.total_pages)  # Outputs the total number of pages
```

**Search with Pagination**
```python
# Search with pagination
repo = UserRepository(session)
results = repo.find_page(
    search_term="john",
    search_fields=["name", "email"],
    page=1,
    size=10,
    order_by="created_at",
    sort_order="desc"
)

for item in results.data:
    print(item["name"])

print(results.pagination.total_items)  # Outputs the total number of items found
```

This should provide a clear understanding of the pagination operations available in the `PageableOperations` class.

## Examples & Use Cases 📚

### 1. E-Commerce Product Catalog

```python
class ProductRepo(BaseRepository[Product]):
    def __init__(self, session: Session = Depends(get_session)):
        super().__init__(Product, session)

    @query("""
        SELECT p.*, avg(r.rating) as avg_rating
        FROM product p
        LEFT JOIN review r ON p.id = r.product_id
        GROUP BY p.id
        HAVING avg(r.rating) >= :min_rating
    """)
    def find_top_rated_products(self, min_rating: float) -> List[Product]:
        pass

    @transactional(read_only=True)
    def get_product_catalog(
        self,
        category: str = None,
        min_price: Decimal = None,
        max_price: Decimal = None,
        page: int = 1,
        size: int = 20
    ) -> Page[Product]:
        filters = {}
        if category:
            filters["category"] = category
        if min_price:
            filters["price_gte"] = min_price
        if max_price:
            filters["price_lte"] = max_price
            
        return self.get_page(
            page=page,
            size=size,
            where=filters,
            order_by="name",
            sort_order="asc"
        )
```

### 2. User Management System

```python
class UserRepo(BaseRepository[User]):
    def __init__(self, session: Session = Depends(get_session)):
        super().__init__(User, session)

    @store_procedure(
        name="sp_authenticate_user",
        db_type=DatabaseType.POSTGRESQL
    )
    def authenticate(self, email: str, password_hash: str) -> Optional[User]:
        pass

    @query("""
        SELECT u.*, count(p.id) as post_count
        FROM user u
        LEFT JOIN post p ON u.id = p.user_id
        GROUP BY u.id
        HAVING count(p.id) > :min_posts
    """)
    def find_active_creators(self, min_posts: int) -> List[User]:
        pass

    def find_users_by_role(
        self,
        role: str,
        page: int = 1,
        size: int = 20
    ) -> Page[User]:
        return self.get_page(
            page=page,
            size=size,
            where={"role": role},
            join_relations=[User.profile],
            join_type="left",
            order_by="created_at",
            sort_order="desc"
        )
```


## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

> "Clean code always looks like it was written by someone who cares." - Michael Feathers

---
Made with ❤️ by the Base Repository Team