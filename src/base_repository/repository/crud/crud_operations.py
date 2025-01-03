from typing import Literal, TypeVar, Generic, Type, Optional, List, Union
from base_repository.exception.base_repository_exception import ValidationError, EntityNotFoundError
from sqlmodel import Session, select
from sqlmodel import SQLModel
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

T = TypeVar("T", bound=Union[SQLModel, BaseModel])

class BasicOperations(Generic[T]):
    """
    Provides basic CRUD operations for database entities.
    
    This class implements common database operations like create, read, update, and delete
    for SQLModel or Pydantic models.

    Attributes:
        model_class (Type[T]): The model class type for the entity being managed.

    Example:
        ```python
        class User(SQLModel):
            id: int
            name: str

        user_ops = BasicOperations[User](User)
        user = User(name="John")
        saved_user = user_ops.save(session, user)
        ```

    Raises:
        ValidationError: If model_class is not a valid SQLModel or BaseModel type.
    """

    def __init__(self, model_class: Type[T]):
        """
        Initialize BasicOperations with a model class.

        Args:
            model_class (Type[T]): The model class to operate on. Must be SQLModel or BaseModel.

        Raises:
            ValidationError: If model_class is not a valid model type.
        """
        if not issubclass(model_class, (SQLModel, BaseModel)):
            raise ValidationError("model_class must be SQLModel or BaseModel")
        self.model_class = model_class

    def save(self, session: Session, entity: T) -> T:
        """
        Save a new entity to the database.

        Args:
            session (Session): Active database session.
            entity (T): Entity instance to save.

        Returns:
            T: The saved entity.

        Raises:
            ValidationError: If session or entity is invalid.
            SQLAlchemyError: If database operation fails.
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid session required")
        if not isinstance(entity, self.model_class):
            raise ValidationError(f"Entity must be of type {self.model_class.__name__}")
        try:
            session.add(entity)
            session.flush()
            return entity
        except SQLAlchemyError:
            raise

    def get_all(
        self, 
        session: Session, 
        where: Optional[dict] = None,
        order_by: Optional[str] = None,
        sort_order: Literal["asc", "desc"] = "asc"
    ) -> List[T]:
        """
        Retrieve all entities with optional filtering and ordering.

        This method allows querying entities with complex filtering and ordering options.
        Filters are applied as exact matches on entity fields.

        Args:
            session (Session): Active database session for the query.
            where (Optional[dict]): Dictionary of filter conditions where keys are field 
                names and values are the matching values. Example: {"status": "active"}.
            order_by (Optional[str]): Name of the field to order results by.
                Must be a valid field name of the entity.
            sort_order (Literal["asc", "desc"]): Sort direction, either ascending ("asc") 
                or descending ("desc"). Defaults to "asc".

        Returns:
            List[T]: List of entities matching the specified criteria.

        Raises:
            ValidationError: If any of these conditions occur:
                - Invalid session provided
                - Invalid sort_order value
                - Invalid field name in where dictionary
                - Invalid order_by field name
            SQLAlchemyError: For any database-related errors

        Examples:
            ```python
            # Get all active users sorted by name
            users = crud.get_all(
                session,
                where={"status": "active"},
                order_by="name",
                sort_order="asc"
            )

            # Get all records without filtering
            all_records = crud.get_all(session)
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid database session required")
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
                    order_column.desc() if sort_order == "desc" 
                    else order_column.asc()
                )
                    
            return session.exec(statement).all()
        except SQLAlchemyError:
            raise
    
    
    def get_by_id(self, session: Session, id: int) -> Optional[T]:
        """
        Retrieve an entity by its ID from the database.

        This method performs a direct lookup by primary key and returns the entity
        if found. It includes validation for session and ID parameters.

        Args:
            session (Session): Active database session for the query.
            id (int): Primary key ID of the entity to retrieve.

        Returns:
            Optional[T]: The found entity instance or None if not found.

        Raises:
            ValidationError: If any of these conditions occur:
                - Invalid session provided
                - ID is not an integer
            EntityNotFoundError: If no entity exists with the given ID
            SQLAlchemyError: For any database-related errors

        Examples:
            ```python
            # Get user by ID
            try:
                user = crud.get_by_id(session, 123)
                print(f"Found user: {user.name}")
            except EntityNotFoundError:
                print("User not found")
            
            # Handle validation error
            try:
                user = crud.get_by_id(session, "invalid_id")  # Will raise ValidationError
            except ValidationError as e:
                print(f"Invalid input: {e}")
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid database session required")
        if not isinstance(id, int):
            raise ValidationError("ID must be an integer")
            
        try:
            entity = session.get(self.model_class, id)
            if not entity:
                raise EntityNotFoundError(f"Entity not found with ID: {id}")
            return entity
        except SQLAlchemyError:
            raise


    def update(self, session: Session, id: int, entity: T) -> T:
        """
        Update an existing entity in the database.

        This method updates an entity by its ID with new data. It performs validations
        and ensures all fields being updated are valid for the entity type.

        Args:
            session (Session): Active database session for the operation.
            id (int): Primary key ID of the entity to update.
            entity (T): Entity instance with updated data.

        Returns:
            T: The updated entity instance.

        Raises:
            ValidationError: If any of these conditions occur:
                - Invalid session provided
                - Invalid entity type
                - Invalid field in update data
            EntityNotFoundError: If no entity exists with the given ID
            SQLAlchemyError: For any database-related errors

        Examples:
            ```python
            # Update user name
            try:
                updated_user = User(name="New Name")
                result = crud.update(session, 123, updated_user)
                print(f"Updated user: {result.name}")
            except EntityNotFoundError:
                print("User not found")
            except ValidationError as e:
                print(f"Invalid update data: {e}")
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid database session required")
        if not isinstance(id, int):
            raise ValidationError("ID must be an integer")
        if not isinstance(entity, self.model_class):
            raise ValidationError(f"Entity must be of type {self.model_class.__name__}")
            
        try:
            db_entity = session.get(self.model_class, id)
            if not db_entity:
                raise EntityNotFoundError(f"Entity not found with ID: {id}")
            
            for key, value in entity.model_dump(exclude_unset=True).items():
                if not hasattr(db_entity, key):
                    raise ValidationError(f"Invalid field: {key}")
                setattr(db_entity, key, value)
            
            session.add(db_entity)
            session.flush()
            return db_entity
        except SQLAlchemyError:
            raise


    def delete(self, session: Session, id: int) -> bool:
        """
        Delete an entity from the database by its ID.

        This method attempts to delete an entity with the specified ID from the database.
        It performs validation checks on the input parameters and ensures the entity exists
        before deletion.

        Args:
            session (Session): Active database session for the deletion operation.
            id (int): Primary key ID of the entity to delete.

        Returns:
            bool: True if the entity was successfully deleted.

        Raises:
            ValidationError: If any of these conditions occur:
                - Invalid session provided
                - ID is not an integer
            EntityNotFoundError: If no entity exists with the given ID
            SQLAlchemyError: For any database-related errors

        Examples:
            ```python
            # Delete a user
            try:
                was_deleted = crud.delete(session, 123)
                print("User deleted successfully")
            except EntityNotFoundError:
                print("User not found")
            except ValidationError as e:
                print(f"Invalid input: {e}")
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid database session required")
        if not isinstance(id, int):
            raise ValidationError("ID must be an integer")
            
        try:
            entity = session.get(self.model_class, id)
            if not entity:
                raise EntityNotFoundError(f"Entity not found with ID: {id}")
            
            session.delete(entity)
            return True
        except SQLAlchemyError:
            raise