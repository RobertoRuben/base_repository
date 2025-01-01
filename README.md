  
#  Base Repository 🚀

> ⚠️ **Note**: This library is currently in beta. Some features may not
> be fully stable.

A Python library implementing the repository pattern for SQL operations using SQLModel.

##  Installation 📦
You can install **Base Repository** by running the following command in your terminal:
```bash
pip install  base-repository
```

## Basic Usage 🛠️
Learn how to quickly set up and use **Base Repository** for seamless CRUD operations, pagination, advanced searches, and transaction management in your projects.

### Define Model 📝
---
```python
from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel,  table=True):
    id: int | None  =  Field(default=None,  primary_key=True)
    name:  str
    email:  str
```


### Create Repository 🏗️
---
```python
from base_repository.core.base_repository import BaseRepository
from base_repository.decorator.repository import repository

@repository
class UserRepository(BaseRepository[User]):
	pass
```

### Use Repository ⚙️
---
```python
from sqlmodel import create_engine, Session

engine =  create_engine("sqlite:///database.db")
session =  Session(engine)
repo =  UserRepository()
```

# Decorators 🎨
Decorators in this library are used to simplify and manage various aspects of database operations. They provide a clean and consistent way to handle transactions, stored procedures, and native SQL queries.

The library provides the following four decorators:

1.  `@transactional`

2.  `@store_procedure`

3.  `@query`

4.  `@repository`


## Transactional 🔄

The  `@transactional`  decorator is used to manage database transactions. It ensures that the operations within the decorated function are executed within a transaction context. If an error occurs, the transaction is rolled back.

By default, the  `@transactional`  decorator uses  auto_concurrent=True  and  read_only=False.

#### Usage

```python
from base_repository.decorator.transactional import transactional

@transactional
def create_user(session: Session,  user: User)  -> User:
	return repo.save(session, user)
```

#### Configuration

-   **auto_concurrent**: Enables REPEATABLE READ isolation level for concurrent transactions.
-   **read_only:** Enables read-only mode for the transaction.

#### Example with Configuration

```python
@transactional(auto_concurrent=True,  read_only=False)
def update_user(session: Session,  user_id:  int,  new_name:  str)  -> User:
	user = repo.get_by_id(session, user_id)
	user.name = new_name
	return repo.save(session, user)
```

#### Read-Only Operations

To perform read-only operations, set the  read_only  parameter to  `True`.

```python
@transactional(read_only=True)
def get_user_by_id(session: Session, user_id: int) -> User:
    return repo.get_by_id(session, user_id)
```
#### Error Handling

The  `@transactional`  decorator handles various exceptions:

-   TransactionConfigError: Raised for configuration errors.
-   TransactionValidationError: Raised for validation errors.
-   TransactionError: Raised for general transaction errors.
-   SQLAlchemyError: Raised for database errors.

#### Example with Error Handling
```python
from base_repository.exception.decorator_exception import TransactionError

@transactional
def delete_user(session: Session,  user_id:  int):
	try:
		repo.delete(session, user_id)
	except TransactionError as e:
		print(f"Transaction failed: {str(e)}")
```


## Store Procedure 🗃️
The `@store_procedure` decorator simplifies the execution of database stored procedures by wrapping methods and handling parameter validation and execution.

#### Supported Databases
The `@store_procedure` decorator supports the following databases:
- PostgreSQL
- MySQL
- SQLServer
- Oracle

⚠️ **Note**: Ensure you have the necessary database connector installed for your database. For example:
- PostgreSQL: `pip install psycopg2`
- MySQL: `pip install mysql-connector-python`
- SQLServer: `pip install pyodbc`
- Oracle: `pip install cx_Oracle`

#### Usage
```python
from base_repository.decorator.store_procedure import store_procedure
from base_repository.repository.procedure.database_type import DatabaseType

class UserRepository:
    @store_procedure(name="get_users_by_status", db_type=DatabaseType.POSTGRESQL)
    def get_active_users(self, session: Session, status: str = "active"):
        pass

    @store_procedure(name="get_user_count", scalar=True, db_type=DatabaseType.MYSQL)
    def count_users(self, session: Session, department: str) -> int:
        pass
```

#### Example
```python
repo = UserRepository()
users = repo.get_active_users(session, status="active")
count = repo.count_users(session, department="IT")
```

#### Detailed Explanation

The `@store_procedure` decorator handles the following:
- **Parameter Validation**: Ensures that the procedure name and parameters are valid.
- **Execution**: Executes the stored procedure with the provided parameters.
- **Database Dialects**: Supports different SQL dialects for various databases.

#### Configuration

- **name**: The name of the stored procedure to execute.
- **scalar**: Whether the procedure returns a single value. Defaults to `False`.
- **db_type**: The type of database to use. Defaults to DatabaseType.POSTGRESQL


#### Example with Configuration

```python
@store_procedure(name="get_users_by_status", db_type=DatabaseType.POSTGRESQL)
def get_active_users(self, session: Session, status: str = "active"):
    pass

@store_procedure(name="get_user_count", scalar=True, db_type=DatabaseType.MYSQL)
def count_users(self, session: Session, department: str) -> int:
    pass
```

#### Error Handling

The `@store_procedure` decorator handles various exceptions:
 

- `StoreProcedureValidationError` : Raised for validation errors.
- `ProcedureError`: Raised for general procedure execution errors.

#### Example with Error Handling

```python
from base_repository.exception.decorator_exception import StoreProcedureValidationError, ProcedureError

try:
    repo = UserRepository()
    users = repo.get_active_users(session, status="active")
    count = repo.count_users(session, department="IT")
except StoreProcedureValidationError as e:
    print(f"Validation error: {e}")
except ProcedureError as e:
    print(f"Procedure error: {e}")
```


## Query 🔍
The `@query` decorator is used to execute native SQL queries, automatically mapping function parameters to SQL query placeholders.

#### Usage
```python
from base_repository.decorator.query import query

class  UserRepository:
	@query("SELECT * FROM users WHERE status = :status")
	def get_users_by_status(self,  session: Session,  status:  str):
		pass

	@query("SELECT COUNT(*) FROM users WHERE department = :department",  scalar=True)
	def count_users(self,  session: Session,  department:  str)  ->  int:
		pass
```

#### Usage
```python
repo =  UserRepository()
users = repo.get_users_by_status(session,  status="active")
count = repo.count_users(session,  department="IT")
```

## Repository 🏗️
The `@repository` decorator configures a repository with its model class, extracting the model class from the first generic base class and configuring the repository instance with it.

### Usage
```python
from base_repository.core.base_repository import BaseRepository
from base_repository.decorator.repository import repository

@repository
class UserRepository(BaseRepository[User]):
    pass
```



# CRUD Operations 🗂️
The  BasicOperations class provides fundamental CRUD operations for managing database entities. This class supports SQLModel and Pydantic models.

## Save a New User
For write operations, use the `@transactional` decorator to ensure the operation is executed within a transaction context.

#### Without `@transactional`
```python
def save_user(session: Session, user: User) -> User:
    session.add(user)
    session.commit()  # Manual commit
    return user

user = User(name="John", email="john@example.com")
saved_user = save_user(session, user)
```

#### With `@transactional`
```python
from base_repository.decorator.transactional import transactional

@transactional
def save_user(session: Session, user: User) -> User:
    session.add(user)
    return user

user = User(name="John", email="john@example.com")
saved_user = save_user(session, user)
```

## Get All Users
For read operations, use the `@transactional` decorator with `read_only=True` to ensure the operation is executed in read-only mode.

#### Without `@transactional`
```python
def get_all_users(session: Session) -> List[User]:
    return session.exec(select(User)).all()

users = get_all_users(session)
```

#### With `@transactional`
```python
@transactional(read_only=True)
def get_all_users(session: Session) -> List[User]:
    return session.exec(select(User)).all()

users = get_all_users(session)
```

## Get User by ID
The get_by_id method retrieves an entity by its ID from the database. It performs a direct lookup by primary key and returns the entity if found.
#### Without `@transactional`
```python
def get_user_by_id(session: Session, user_id: int) -> User:
    return session.get(User, user_id)

user = get_user_by_id(session, 1)
```

#### With `@transactional`
```python
@transactional(read_only=True)
def get_user_by_id(session: Session, user_id: int) -> User:
    return session.get(User, user_id)

user = get_user_by_id(session, 1)
```

## Update User
The update method updates an existing entity in the database by its ID with new data. It ensures all fields being updated are valid for the entity type.

#### Without `@transactional`
```python
def update_user(session: Session, user_id: int, new_name: str) -> User:
    user = session.get(User, user_id)
    user.name = new_name
    session.commit()  # Manual commit
    return user

updated_user = update_user(session, 1, "John Doe")
```

#### With `@transactional`
```python
@transactional
def update_user(session: Session, user_id: int, new_name: str) -> User:
    user = session.get(User, user_id)
    user.name = new_name
    return user

updated_user = update_user(session, 1, "John Doe")
```

## Delete User
The delete method deletes an entity from the database by its ID. It ensures the entity exists before deletion.
#### Without `@transactional`
```python
def delete_user(session: Session, user_id: int) -> bool:
    user = session.get(User, user_id)
    session.delete(user)
    session.commit()  # Manual commit
    return True

delete_success = delete_user(session, 1)
```

#### With `@transactional`
```python
@transactional
def delete_user(session: Session, user_id: int) -> bool:
    user = session.get(User, user_id)
    session.delete(user)
    return True

delete_success = delete_user(session, 1)
```

### Detailed Explanation

The BasicOperations class includes the following methods:

- **save**: Persists a new entity to the database.
- **get_all**: Retrieves all entities from the database.
- **get_by_id**: Retrieves an entity by its ID.
- **update**: Updates an existing entity.
- **delete**: Deletes an entity by its ID.

#### Example with Detailed CRUD Operations

```python
from sqlmodel import SQLModel, Field, Session, create_engine
from base_repository.core.base_repository import BaseRepository
from base_repository.decorator.repository import repository
from base_repository.decorator.transactional import transactional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str

@repository
class UserRepository(BaseRepository[User]):
    pass

# Setup database
engine = create_engine("sqlite:///database.db")
session = Session(engine)

repo = UserRepository()

# Save a new user
@transactional
def save_user(session: Session, user: User) -> User:
    return repo.save(session, user)

user = User(name="John", email="john@example.com")
saved_user = save_user(session, user)

# Get all users
@transactional(read_only=True)
def get_all_users(session: Session) -> List[User]:
    return repo.get_all(session)

users = get_all_users(session)

# Get user by ID
@transactional(read_only=True)
def get_user_by_id(session: Session, user_id: int) -> User:
    return repo.get_by_id(session, user_id)

user = get_user_by_id(session, 1)

# Update user
@transactional
def update_user(session: Session, user_id: int, new_name: str) -> User:
    user = repo.get_by_id(session, user_id)
    user.name = new_name
    return repo.update(session, user_id, user)

updated_user = update_user(session, 1, "John Doe")

# Delete user
@transactional
def delete_user(session: Session, user_id: int) -> bool:
    return repo.delete(session, user_id)

delete_success = delete_user(session, 1)
```

### Error Handling

The BasicOperations class handles various exceptions:

- `ValidationError`: Raised for validation errors.
- `EntityNotFoundError`: Raised when an entity is not found.
- `SQLAlchemyError`: Raised for general database errors.

#### Example with Error Handling

```python
from base_repository.exception.base_repository_exception import EntityNotFoundError, ValidationError

try:
    user = get_user_by_id(session, 1)
except EntityNotFoundError:
    print("User not found")
except ValidationError as e:
    print(f"Validation error: {e}")
except SQLAlchemyError as e:
    print(f"Database error: {e}")
```

# Find Operations 🔎
The FindOperations class provides methods to retrieve entities from the database based on various criteria. This class supports SQLModel models.

## Find User by ID
The find_by_id method retrieves an entity by its ID from the database. It performs a direct lookup by primary key and returns the entity if found.

#### Without `@transactional`
```python
def find_user_by_id(session: Session, user_id: int) -> User:
    return repo.find_by_id(session, user_id)

user = find_user_by_id(session, 1)
```

#### With `@transactional`
```python
from base_repository.decorator.transactional import transactional

@transactional(read_only=True)
def find_user_by_id(session: Session, user_id: int) -> User:
    return repo.find_by_id(session, user_id)

user = find_user_by_id(session, 1)
```

## Find All Users
The find_all method retrieves all entities from the database.

#### Without `@transactional`
```python
def find_all_users(session: Session) -> List[User]:
    return repo.find_all(session)

users = find_all_users(session)
```

#### With `@transactional`
```python
@transactional(read_only=True)
def find_all_users(session: Session) -> List[User]:
    return repo.find_all(session)

users = find_all_users(session)
```

## Find Users by Criteria
The find_by method retrieves entities based on specified criteria.

#### Without `@transactional`
```python
def find_users_by_criteria(session: Session, criteria: dict) -> List[User]:
    return repo.find_by(session, criteria)

users = find_users_by_criteria(session, {"name": "John"})
```

#### With `@transactional`
```python
@transactional(read_only=True)
def find_users_by_criteria(session: Session, criteria: dict) -> List[User]:
    return repo.find_by(session, criteria)

users = find_users_by_criteria(session, {"name": "John"})
```

## Check if User Exists
The exists_by method checks if at least one entity exists with the specified criteria.

#### Without `@transactional`
```python
def check_user_exists(session: Session, email: str) -> bool:
    return repo.exists_by(session, email=email)

exists = check_user_exists(session, "john@example.com")
```

#### With `@transactional`
```python
@transactional(read_only=True)
def check_user_exists(session: Session, email: str) -> bool:
    return repo.exists_by(session, email=email)

exists = check_user_exists(session, "john@example.com")
```

## Find First User
The  find_first method retrieves the first entity ordered by a specific field.

#### Without `@transactional`
```python
def find_first_user(session: Session) -> User:
    return repo.find_first(session)

first_user = find_first_user(session)
```

#### With `@transactional`
```python
@transactional(read_only=True)
def find_first_user(session: Session) -> User:
    return repo.find_first(session)

first_user = find_first_user(session)
```

## Find Latest User
The find_latest method retrieves the most recent entity ordered by a specific field.

#### Without `@transactional`
```python
def find_latest_user(session: Session) -> User:
    return repo.find_latest(session)

latest_user = find_latest_user(session)
```

#### With `@transactional`
```python
@transactional(read_only=True)
def find_latest_user(session: Session) -> User:
    return repo.find_latest(session)

latest_user = find_latest_user(session)
```

### Detailed Explanation

The FindOperations class includes the following methods:

- **find_by_id**: Retrieves an entity by its ID.
- **find_all**: Retrieves all entities from the database.
- **find_by**: Retrieves entities based on specified criteria.
- **exists_by**: Checks if at least one entity exists with the specified criteria.
- **find_first**: Retrieves the first entity ordered by a specific field.
- **find_latest**: Retrieves the most recent entity ordered by a specific field.

#### Example with Detailed Find Operations

```python
from sqlmodel import SQLModel, Field, Session, create_engine
from base_repository.core.base_repository import BaseRepository
from base_repository.decorator.repository import repository
from base_repository.decorator.transactional import transactional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str

@repository
class UserRepository(BaseRepository[User]):
    pass

# Setup database
engine = create_engine("sqlite:///database.db")
session = Session(engine)

repo = UserRepository()

# Find user by ID without @transactional
def find_user_by_id(session: Session, user_id: int) -> User:
    return repo.find_by_id(session, user_id)

user = find_user_by_id(session, 1)

# Find user by ID with @transactional
@transactional(read_only=True)
def find_user_by_id(session: Session, user_id: int) -> User:
    return repo.find_by_id(session, user_id)

user = find_user_by_id(session, 1)

# Find all users without @transactional
def find_all_users(session: Session) -> List[User]:
    return repo.find_all(session)

users = find_all_users(session)

# Find all users with @transactional
@transactional(read_only=True)
def find_all_users(session: Session) -> List[User]:
    return repo.find_all(session)

users = find_all_users(session)

# Find users by criteria without @transactional
def find_users_by_criteria(session: Session, criteria: dict) -> List[User]:
    return repo.find_by(session, criteria)

users = find_users_by_criteria(session, {"name": "John"})

# Find users by criteria with @transactional
@transactional(read_only=True)
def find_users_by_criteria(session: Session, criteria: dict) -> List[User]:
    return repo.find_by(session, criteria)

users = find_users_by_criteria(session, {"name": "John"})

# Check if user exists without @transactional
def check_user_exists(session: Session, email: str) -> bool:
    return repo.exists_by(session, email=email)

exists = check_user_exists(session, "john@example.com")

# Check if user exists with @transactional
@transactional(read_only=True)
def check_user_exists(session: Session, email: str) -> bool:
    return repo.exists_by(session, email=email)

exists = check_user_exists(session, "john@example.com")

# Find first user without @transactional
def find_first_user(session: Session) -> User:
    return repo.find_first(session)

first_user = find_first_user(session)

# Find first user with @transactional
@transactional(read_only=True)
def find_first_user(session: Session) -> User:
    return repo.find_first(session)

first_user = find_first_user(session)

# Find latest user without @transactional
def find_latest_user(session: Session) -> User:
    return repo.find_latest(session)

latest_user = find_latest_user(session)

# Find latest user with @transactional
@transactional(read_only=True)
def find_latest_user(session: Session) -> User:
    return repo.find_latest(session)

latest_user = find_latest_user(session)
```


# Pageable Operations 📄
The PageableOperations class provides methods to retrieve entities from the database with pagination, sorting, and filtering support. This class supports SQLModel models.

## Get Paginated Users
The get_page method retrieves a paginated list of entities from the database.

#### Without `@transactional`
```python
from base_repository.repository.pageable.page import Page, PageInfo

def get_paginated_users(session: Session, page: int = 1, size: int = 10) -> Page[dict]:
    return repo.get_page(session, page=page, size=size, order_by="name", sort_order="asc")

page = get_paginated_users(session, page=1, size=10)
```

#### With `@transactional`
```python
from base_repository.decorator.transactional import transactional

@transactional(read_only=True)
def get_paginated_users(session: Session, page: int = 1, size: int = 10) -> Page[dict]:
    return repo.get_page(session, page=page, size=size, order_by="name", sort_order="asc")

page = get_paginated_users(session, page=1, size=10)
```

## Find Paginated Users by Search Term

The find_page method retrieves a paginated list of entities from the database based on a search term.

#### Without `@transactional`
```python
def find_paginated_users(session: Session, search_term: str, search_fields: List[str], page: int = 1, size: int = 10) -> Page[dict]:
    return repo.find_page(session, search_term=search_term, search_fields=search_fields, page=page, size=size)

page = find_paginated_users(session, search_term="john", search_fields=["name", "email"], page=1, size=10)
```

#### With `@transactional`
```python
@transactional(read_only=True)
def find_paginated_users(session: Session, search_term: str, search_fields: List[str], page: int = 1, size: int = 10) -> Page[dict]:
    return repo.find_page(session, search_term=search_term, search_fields=search_fields, page=page, size=size)

page = find_paginated_users(session, search_term="john", search_fields=["name", "email"], page=1, size=10)
```

### Exception Handling 🚨
The PageableOperations class handles various exceptions:

- `EntityNotFoundError`: Raised when an entity is not found.
- `SQLAlchemyError`: Raised for general database errors.

#### Example with Error Handling

```python
from base_repository.exception.base_repository_exception import EntityNotFoundError

try:
    user = repo.get_by_id(session, 1)
except EntityNotFoundError:
    print("User not found")
except SQLAlchemyError as e:
    print(f"Database error: {e}")
```

### Detailed Explanation

The PageableOperations class includes the following methods:

- **get_page**: Retrieves a paginated list of entities from the database.
- **find_page**: Retrieves a paginated list of entities from the database based on a search term.

#### Example with Detailed Pageable Operations

```python
from sqlmodel import SQLModel, Field, Session, create_engine
from base_repository.core.base_repository import BaseRepository
from base_repository.decorator.repository import repository
from base_repository.decorator.transactional import transactional
from base_repository.repository.pageable.page import Page, PageInfo

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str

@repository
class UserRepository(BaseRepository[User]):
    pass

# Setup database
engine = create_engine("sqlite:///database.db")
session = Session(engine)

repo = UserRepository()

# Get paginated users without @transactional
def get_paginated_users(session: Session, page: int = 1, size: int = 10) -> Page[dict]:
    return repo.get_page(session, page=page, size=size, order_by="name", sort_order="asc")

page = get_paginated_users(session, page=1, size=10)

# Get paginated users with @transactional
@transactional(read_only=True)
def get_paginated_users(session: Session, page: int = 1, size: int = 10) -> Page[dict]:
    return repo.get_page(session, page=page, size=size, order_by="name", sort_order="asc")

page = get_paginated_users(session, page=1, size=10)

# Find paginated users by search term without @transactional
def find_paginated_users(session: Session, search_term: str, search_fields: List[str], page: int = 1, size: int = 10) -> Page[dict]:
    return repo.find_page(session, search_term=search_term, search_fields=search_fields, page=page, size=size)

page = find_paginated_users(session, search_term="john", search_fields=["name", "email"], page=1, size=10)

# Find paginated users by search term with @transactional
@transactional(read_only=True)
def find_paginated_users(session: Session, search_term: str, search_fields: List[str], page: int = 1, size: int = 10) -> Page[dict]:
    return repo.find_page(session, search_term=search_term, search_fields=search_fields, page=page, size=size)

page = find_paginated_users(session, search_term="john", search_fields=["name", "email"], page=1, size=10)
```

### Error Handling

The PageableOperationsclass handles various exceptions:

- `EntityNotFoundError`: Raised when an entity is not found.
- `SQLAlchemyError`: Raised for general database errors.

#### Example with Error Handling

```python
from base_repository.exception.base_repository_exception import EntityNotFoundError

try:
    user = repo.get_by_id(session, 1)
except EntityNotFoundError:
    print("User not found")
except SQLAlchemyError as e:
    print(f"Database error: {e}")
```
# Note 📝
The  `@transactional`  decorator is used for write operations to ensure they are executed within a transaction context. For read operations, it is not always necessary to use the  `@transactional`  decorator, especially if the operations are simple and do not require transaction management. However, using  `@transactional(read_only=True)`  can still be beneficial for consistency and to ensure read-only transactions, which can help prevent accidental modifications.

# Acknowledgements 🙏

We would like to thank the following for their contributions and support:

- **SQLModel**: For providing a powerful and flexible ORM for SQL databases.
- **Pydantic**: For enabling data validation and settings management using Python type annotations.
- **SQLAlchemy**: For being the core SQL toolkit and ORM that powers SQLModel.
- **FastAPI**: For inspiring the creation of modern, fast (high-performance), web frameworks for building APIs with Python 3.6+ based on standard Python type hints.

### License 📜

This project is licensed under the MIT License. See the LICENSE file for more details.

---

Thank you for using **Base Repository**! If you have any questions or feedback, please feel free to open an issue on GitHub or contact us directly. Happy coding! 🚀
