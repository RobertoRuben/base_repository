from typing import Literal, TypeVar, Generic, Type, Optional, List, Union
from base_repository.exception.base_repository_exception import (
    ValidationError,
    EntityNotFoundError,
)
from sqlmodel import Session, select
from sqlmodel import SQLModel
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

T = TypeVar("T", bound=Union[SQLModel, BaseModel])


class BasicOperations(Generic[T]):
    """Base CRUD operations.

    IDE Features:
        * Method autocompletion (type '.')
        * Parameter type hints (Ctrl+Space)
        * Return type inference
        * Go to definition (F12)
        * Documentation on hover

    Available Operations:
        * save(entity: T) -> T
        * get_all(where?: dict, order_by?: str) -> List[T]
        * get_by_id_store_procedure(id: int) -> Optional[T]
        * update(id: int, entity: T) -> T
        * delete(id: int) -> bool

    Example:
        ```python
        class UserRepo(BasicOperations[User]):
            def __init__(self, session: Session):
                super().__init__(User, session)

        # IDE Support:
        repo = UserRepo(session)
        repo.  # Shows all available methods
        user = repo.save(  # Shows User type hint
        users = repo.get_all(  # Shows dict parameter hints
        found = repo.get_by_id_store_procedure(  # Shows int parameter
        ```

    Type Support:
        * T = Your model type (SQLModel/BaseModel)
        * Full type checking for parameters
        * Return type inference
        * Generic type validation
    """

    def __init__(self, model_class: Type[T], session: Session = None):
        """Initialize CRUD operations with model type checking.

        IDE Support:
            * Type hints for parameters
            * Validation checking
            * Session initialization

        Args:
            model_class: Your model class (User, Product, etc)
            session: Database session
        """
        if not issubclass(model_class, (SQLModel, BaseModel)):
            raise ValidationError("model_class must be SQLModel or BaseModel")
        self.model_class = model_class
        self.session = session

    def save(self, entity: T) -> T:
        """Save entity to database.

        Args:
            entity (T): Entity to save (e.g. User, Product)
                    Type hints show available fields

        Returns:
            T: Saved entity with updated ID

        Example:
            ```python
            repo = UserRepository(session)
            user = User(name="John")
            saved = repo.save(user)
            print(saved.id)
            ```

        Raises:
            ValidationError: If session not initialized or invalid entity type
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
        if not isinstance(entity, self.model_class):
            raise ValidationError(f"Entity must be of type {self.model_class.__name__}")
        try:
            self.session.add(entity)
            self.session.flush()
            return entity
        except SQLAlchemyError:
            raise

    def get_all(
        self,
        where: Optional[dict] = None,
        order_by: Optional[str] = None,
        sort_order: Literal["asc", "desc"] = "asc",
    ) -> List[T]:
        """Retrieve all entities with filtering and sorting support.

        Args:
            where: Filter conditions {field: value}
            order_by: Field name for sorting
            sort_order: Sort direction ('asc' or 'desc')

        Returns:
            List[T]: List of entities matching criteria

        Example:
            ```python
            repo = UserRepository(session)
            # IDE shows field suggestions:
            users = repo.get_all(
                where={"status": "active"},
                order_by="created_at",
                sort_order="desc"
            )
            ```

        Raises:
            ValidationError: If invalid fields or sort order
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
        if sort_order not in ["asc", "desc"]:
            raise ValidationError("sort_order must be either 'asc' or 'desc'")

        try:
            statement = select(self.model_class)

            if where:
                filters = []
                for field, value in where.items():
                    if not hasattr(self.model_class, field):
                        raise ValidationError(f"Invalid field name: {field}")
                    column = getattr(self.model_class, field)
                    filters.append(column == value)
                if filters:
                    statement = statement.where(*filters)

            if order_by:
                if not hasattr(self.model_class, order_by):
                    raise ValidationError(f"Invalid order_by field: {order_by}")
                order_column = getattr(self.model_class, order_by)
                statement = statement.order_by(
                    order_column.desc() if sort_order == "desc" else order_column.asc()
                )

            return self.session.exec(statement).all()
        except SQLAlchemyError:
            raise

    def get_by_id(self, id: int) -> Optional[T]:
        """Retrieve entity by ID.

        Args:
            id (int): Primary key of entity to retrieve

        Returns:
            Optional[T]: Found entity or None

        Example:
            ```python
            repo = UserRepository(session)
            user = repo.get_by_id(1)
            if user:
                print(user.name)

        Raises:
            ValidationError: If invalid ID type or session not initialized
            EntityNotFoundError: If no entity found with given ID
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
        if not isinstance(id, int):
            raise ValidationError("ID must be an integer")

        try:
            entity = self.session.get(self.model_class, id)
            if not entity:
                raise EntityNotFoundError(f"Entity not found with ID: {id}")
            return entity
        except SQLAlchemyError:
            raise

    def update(self, id: int, entity: T) -> T:
        """Update entity by ID.

        Args:
            id (int): Primary key of entity to update
            entity (T): Entity with updated values

        Returns:
            T: Updated entity with all changes

        Example:
            ```python
            repo = UserRepository(session)
            user = User(name="Updated")
            updated = repo.update(1, user)
            print(updated.name)
            ```
        Raises:
            ValidationError: If invalid ID/entity or session not initialized
            EntityNotFoundError: If no entity found with given ID
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
        if not isinstance(id, int):
            raise ValidationError("ID must be an integer")
        if not isinstance(entity, self.model_class):
            raise ValidationError(f"Entity must be of type {self.model_class.__name__}")

        try:
            db_entity = self.session.get(self.model_class, id)
            if not db_entity:
                raise EntityNotFoundError(f"Entity not found with ID: {id}")

            for key, value in entity.model_dump(exclude_unset=True).items():
                if not hasattr(db_entity, key):
                    raise ValidationError(f"Invalid field: {key}")
                setattr(db_entity, key, value)

            self.session.add(db_entity)
            self.session.flush()
            return db_entity
        except SQLAlchemyError:
            raise

    def delete(self, id: int) -> bool:
        """Delete entity by ID with IDE support.

        Args:
            id (int): Primary key of entity to delete

        Returns:
            bool: True if entity was deleted successfully

        Example:
            ```python
            repo = UserRepository(session)
            success = repo.delete(1)
            if success:
                print("User deleted")
            ```

        Raises:
            ValidationError: If invalid ID type or session not initialized
            EntityNotFoundError: If no entity found with given ID
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
        if not isinstance(id, int):
            raise ValidationError("ID must be an integer")

        try:
            entity = self.session.get(self.model_class, id)
            if not entity:
                raise EntityNotFoundError(f"Entity not found with ID: {id}")

            self.session.delete(entity)
            return True
        except SQLAlchemyError:
            raise
