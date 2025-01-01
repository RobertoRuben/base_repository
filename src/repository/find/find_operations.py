from typing import Generic, TypeVar, Optional, List, Iterable, Dict, Any
from sqlmodel import SQLModel, Session, select
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from src.exception.base_repository_exception import ValidationError

T = TypeVar("T", bound=SQLModel)

class FindOperations(Generic[T]):
    def __init__(self, model_class: type[T]):
        """
        Initialize the find operations.

        Args:
            model_class (type[T]): The SQLModel class type
        """
        if not issubclass(model_class, SQLModel):
            raise ValidationError("model_class must be a SQLModel type")
        self.model_class = model_class


    def find_by_id(self, session: Session, id_value: Any) -> Optional[T]:
        """
        Find an entity by its ID.

        Args:
            session (Session): Database session
            id_value (Any): ID value to search for

        Returns:
            Optional[T]: Found entity or None if not found

        Raises:
            ValidationError: If session is invalid
            SQLAlchemyError: For any database-related errors
            
        Example:
            ```python
            try:
                user = repo.find_by_id(session, 1)
                if user:
                    print(f"Found user: {user.name}")
            except ValidationError as e:
                print(f"Validation error: {e}")
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid session required")
        try:
            return session.get(self.model_class, id_value)
        except SQLAlchemyError:
            raise


    def find_all(self, session: Session) -> List[T]:
        """
        Retrieve all entities from the database.

        This method returns all entities of the specified type without any filtering.
        Implements basic validation and error handling.

        Args:
            session (Session): Active database session for the query.

        Returns:
            List[T]: List of all entities found. Empty list if no entities exist.

        Raises:
            ValidationError: If the provided session is invalid.
            SQLAlchemyError: For any database-related errors.

        Examples:
            ```python
            try:
                # Get all users
                all_users = repo.find_all(session)
                print(f"Found {len(all_users)} users")

                # Handle empty results
                if not all_users:
                    print("No users found in database")
                    
            except ValidationError as e:
                print(f"Invalid session: {e}")
            except SQLAlchemyError as e:
                print(f"Database error occurred")
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid database session required")

        try:
            statement = select(self.model_class)
            return session.exec(statement).all()
        except SQLAlchemyError:
            raise


    def find_all_by_id(self, session: Session, ids: Iterable[Any]) -> List[T]:
        """
        Find multiple entities by their IDs.

        This method retrieves multiple entities in a single query using an IN clause.
        Handles validation and error scenarios appropriately.

        Args:
            session (Session): Active database session for the query
            ids (Iterable[Any]): Collection of IDs to search for. Must not be empty.

        Returns:
            List[T]: List of found entities matching the provided IDs.
                    Empty list if no matches found.

        Raises:
            ValidationError: If any of these conditions occur:
                - Invalid session provided
                - Empty IDs collection
                - Invalid ID types
            SQLAlchemyError: For any database-related errors

        Examples:
            ```python
            try:
                # Find multiple users
                users = repo.find_all_by_id(session, [1, 2, 3])
                print(f"Found {len(users)} users")

                # Handle missing entities
                if len(users) < len(ids):
                    print("Some users were not found")

            except ValidationError as e:
                print(f"Validation error: {e}")
            except SQLAlchemyError as e:
                print(f"Database error occurred")
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid database session required")
        
        if not ids:
            raise ValidationError("IDs collection cannot be empty")

        try:
            statement = select(self.model_class).where(self.model_class.id.in_(ids))
            return session.exec(statement).all()
        except SQLAlchemyError:
            raise


    def exists_by(self, session: Session, **kwargs) -> bool:
        """
        Check if at least one entity exists with the specified criteria.

        This method verifies the existence of entities matching the given field conditions
        without retrieving the full entities.

        Args:
            session (Session): Active database session for the query.
            **kwargs: Field-value pairs for filtering. Each key must be a valid field name.

        Returns:
            bool: True if at least one entity matches the criteria, False otherwise.

        Raises:
            ValidationError: If any of these conditions occur:
                - Invalid session provided
                - No valid filter fields provided
            SQLAlchemyError: For any database-related errors

        Examples:
            ```python
            try:
                # Check if user exists by email
                exists = repo.exists_by(session, email="user@example.com")
                
                # Check multiple conditions
                admin_exists = repo.exists_by(
                    session, 
                    role="admin",
                    is_active=True
                )

                # Handle validation errors
                try:
                    exists = repo.exists_by(session, invalid_field="value")
                except ValidationError as e:
                    print(f"Invalid field: {e}")

            except SQLAlchemyError as e:
                print("Database error occurred")
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid database session required")

        if not kwargs:
            raise ValidationError("At least one filter condition required")

        try:
            statement = select(self.model_class)
            conditions = []
            
            for field, value in kwargs.items():
                if not hasattr(self.model_class, field):
                    raise ValidationError(f"Invalid field: {field}")
                column = getattr(self.model_class, field)
                conditions.append(column == value)
                    
            if conditions:
                statement = statement.where(*conditions)
            
            return session.exec(statement).first() is not None
        except SQLAlchemyError:
            raise


    def find_by(self, session: Session, filters: Dict[str, Any] = None) -> List[T]:
        """
        Find entities by optional filter conditions.

        This method allows filtering entities based on field-value pairs and handles
        validation of filters and session.

        Args:
            session (Session): Active database session for the query.
            filters (Optional[Dict[str, Any]]): Dictionary of field-value pairs 
                to filter entities. Defaults to None.

        Returns:
            List[T]: List of entities matching the filter conditions, 
                    or all entities if no filters.

        Raises:
            ValidationError: If any of these conditions occur:
                - Invalid session provided
                - Invalid field name in filters
            SQLAlchemyError: For any database-related errors

        Examples:
            ```python
            try:
                # Find active admin users
                users = repo.find_by(session, {
                    "role": "admin",
                    "is_active": True
                })

                # Find all users (no filters)
                all_users = repo.find_by(session)

                # Handle empty results
                if not users:
                    print("No matching users found")

            except ValidationError as e:
                print(f"Invalid filters: {e}")
            except SQLAlchemyError as e:
                print("Database error occurred")
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid database session required")

        try:
            statement = select(self.model_class)
            if filters:
                conditions = []
                for field, value in filters.items():
                    if not hasattr(self.model_class, field):
                        raise ValidationError(f"Invalid field: {field}")
                    column = getattr(self.model_class, field)
                    conditions.append(column == value)
                if conditions:
                    statement = statement.where(*conditions)
            return session.exec(statement).all()
        except SQLAlchemyError:
            raise


    def find_one(self, session: Session, id_or_filters: Any) -> Optional[T]:
        """
        Find a single entity by ID or filter conditions.

        This method provides flexibility to search for an entity either by its primary key
        or by a set of filter conditions. Only returns the first matching entity if multiple
        matches exist.

        Args:
            session (Session): Active database session for the query.
            id_or_filters (Union[Any, Dict[str, Any]]): Search criteria, either:
                - A single ID value to find by primary key
                - A dictionary of field-value pairs for filtering

        Returns:
            Optional[T]: The found entity instance or None if not found.

        Raises:
            ValidationError: If any of these conditions occur:
                - Invalid session provided
                - Invalid fields in filter dictionary
            SQLAlchemyError: For any database-related errors

        Examples:
            ```python
            try:
                # Find by ID
                user = repo.find_one(session, 1)
                if user:
                    print(f"Found user: {user.name}")

                # Find by multiple criteria
                filters = {
                    "email": "user@example.com",
                    "is_active": True
                }
                active_user = repo.find_one(session, filters)
                
                # Handle not found case
                if not active_user:
                    print("No matching user found")

            except ValidationError as e:
                print(f"Invalid search criteria: {e}")
            except SQLAlchemyError as e:
                print("Database error occurred")
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid database session required")

        try:
            if isinstance(id_or_filters, dict):
                statement = select(self.model_class)
                conditions = []
                for field, value in id_or_filters.items():
                    if not hasattr(self.model_class, field):
                        raise ValidationError(f"Invalid field: {field}")
                    column = getattr(self.model_class, field)
                    conditions.append(column == value)
                if conditions:
                    statement = statement.where(*conditions)
                return session.exec(statement).first()
            return session.get(self.model_class, id_or_filters)
        except SQLAlchemyError:
            raise
    
    
    def find_by_date_between(
        self, 
        session: Session, 
        date_field: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[T]:
        """
        Find entities where a date field falls between two dates.

        This method searches for entities where the specified date field value
        is between the start and end dates (inclusive).

        Args:
            session (Session): Active database session for the query.
            date_field (str): Name of the date field to search on.
            start_date (datetime): Start date for the range (inclusive).
            end_date (datetime): End date for the range (inclusive).

        Returns:
            List[T]: List of entities matching the date range criteria.

        Raises:
            ValidationError: If any of these conditions occur:
                - Invalid session provided
                - Invalid date field name
                - Start date is after end date
            SQLAlchemyError: For any database-related errors

        Examples:
            ```python
            try:
                # Find orders in 2024
                orders = repo.find_by_date_between(
                    session,
                    "created_at",
                    datetime(2024, 1, 1),
                    datetime(2024, 12, 31)
                )
                
                # Handle results
                if orders:
                    print(f"Found {len(orders)} orders")
                else:
                    print("No orders found in date range")

            except ValidationError as e:
                print(f"Invalid parameters: {e}")
            except SQLAlchemyError as e:
                print("Database error occurred")
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid database session required")
            
        if not hasattr(self.model_class, date_field):
            raise ValidationError(f"Invalid date field: {date_field}")
            
        if start_date > end_date:
            raise ValidationError("Start date must be before or equal to end date")

        try:
            date_column = getattr(self.model_class, date_field)
            statement = select(self.model_class).where(
                date_column.between(start_date, end_date)
            )
            return session.exec(statement).all()
        except SQLAlchemyError:
            raise
        
    
    def find_first(self, session: Session, order_by: str = "id") -> Optional[T]:
        """
        Find the first entity ordered by a specific field.

        This method retrieves the first entity when ordered by the specified field.
        Useful for getting the oldest/newest record based on a field.

        Args:
            session (Session): Active database session for the query.
            order_by (str): Field name to order by. Defaults to "id".

        Returns:
            Optional[T]: First entity found or None if no entities exist.

        Raises:
            ValidationError: If any of these conditions occur:
                - Invalid session provided
                - Invalid order_by field name
            SQLAlchemyError: For any database-related errors

        Examples:
            ```python
            try:
                # Get oldest user by creation date
                oldest_user = repo.find_first(session, order_by="created_at")
                if oldest_user:
                    print(f"Oldest user: {oldest_user.name}")
                
                # Get first user by ID
                first_user = repo.find_first(session)
                if not first_user:
                    print("No users found")
                    
            except ValidationError as e:
                print(f"Invalid parameters: {e}")
            except SQLAlchemyError as e:
                print("Database error occurred")
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid database session required")
        
        if not hasattr(self.model_class, order_by):
            raise ValidationError(f"Invalid order_by field: {order_by}")

        try:
            column = getattr(self.model_class, order_by)
            statement = select(self.model_class).order_by(column)
            return session.exec(statement).first()
        except SQLAlchemyError:
            raise
        
        
    def find_latest(self, session: Session, order_by: str = "created_at") -> Optional[T]:
        """
        Find the most recent entity ordered by a specific field.

        This method retrieves the most recent entity when ordered by the specified field
        in descending order. Commonly used with timestamp fields.

        Args:
            session (Session): Active database session for the query.
            order_by (str): Field name to order by. Defaults to "created_at".

        Returns:
            Optional[T]: Most recent entity found or None if no entities exist.

        Raises:
            ValidationError: If any of these conditions occur:
                - Invalid session provided
                - Invalid order_by field name
            SQLAlchemyError: For any database-related errors

        Examples:
            ```python
            try:
                # Get most recent user
                latest_user = repo.find_latest(session)
                if latest_user:
                    print(f"Latest user: {latest_user.name}")

                # Get latest by specific field
                latest_order = repo.find_latest(session, order_by="order_date")
                if not latest_order:
                    print("No orders found")

            except ValidationError as e:
                print(f"Invalid parameters: {e}")
            except SQLAlchemyError as e:
                print("Database error occurred")
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid database session required")
        
        if not hasattr(self.model_class, order_by):
            raise ValidationError(f"Invalid order_by field: {order_by}")

        try:
            column = getattr(self.model_class, order_by)
            statement = select(self.model_class).order_by(column.desc())
            return session.exec(statement).first()
        except SQLAlchemyError:
            raise


    def find_by_like(
        self, 
        session: Session, 
        field: str, 
        value: str
    ) -> List[T]:
        """
        Find entities using partial string matching (LIKE).

        This method performs a case-insensitive search using SQL LIKE operator with
        wildcards before and after the search term.

        Args:
            session (Session): Active database session for the query.
            field (str): Name of the field to search in.
            value (str): Search term to match against the field.

        Returns:
            List[T]: List of entities matching the search criteria.

        Raises:
            ValidationError: If any of these conditions occur:
                - Invalid session provided
                - Invalid field name
                - Empty search value
            SQLAlchemyError: For any database-related errors

        Examples:
            ```python
            try:
                # Find users with gmail addresses
                gmail_users = repo.find_by_like(session, "email", "@gmail.com")
                print(f"Found {len(gmail_users)} Gmail users")

                # Find users by name pattern
                johns = repo.find_by_like(session, "name", "john")
                if not johns:
                    print("No users found matching pattern")

            except ValidationError as e:
                print(f"Invalid search parameters: {e}")
            except SQLAlchemyError as e:
                print("Database error occurred")
            ```
        """
        if not isinstance(session, Session):
            raise ValidationError("Valid database session required")
        
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Valid search value required")
        
        if not hasattr(self.model_class, field):
            raise ValidationError(f"Invalid field: {field}")

        try:
            column = getattr(self.model_class, field)
            statement = select(self.model_class).where(column.like(f"%{value}%"))
            return session.exec(statement).all()
        except SQLAlchemyError:
            raise
    
    
    