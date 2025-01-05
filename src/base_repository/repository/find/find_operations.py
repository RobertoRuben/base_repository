from typing import Generic, TypeVar, Optional, List, Iterable, Dict, Any, Union
from sqlmodel import SQLModel, Session, or_, select
from datetime import date, datetime
from sqlalchemy.exc import SQLAlchemyError
from base_repository.exception.base_repository_exception import ValidationError

T = TypeVar("T", bound=SQLModel)

class FindOperations(Generic[T]):
    """Find operations.

    IDE Features:
        * Method autocompletion (type '.')
        * Parameter type hints (Ctrl+Space)
        * Return type inference
        * Go to definition (F12)
        * Documentation on hover

    Available Methods:
        * find_by_id(id_value: Any) -> Optional[T]
        * find_all() -> List[T]
        * find_all_by_id(ids: Iterable[Any]) -> List[T]
        * exists_by(**kwargs) -> bool
        * find_by(filters: Dict[str, Any]) -> List[T]
        * find_one(id_or_filters: Any) -> Optional[T]
        * find_by_date_between(date_field: str, start_date: datetime, end_date: datetime) -> List[T]
        * find_first(order_by: str = "id") -> Optional[T]
        * find_latest(order_by: str = "created_at") -> Optional[T]
        * find_by_like(field: str, value: str) -> List[T]

    Example:
        ```python
        class UserRepo(FindOperations[User]):
            def __init__(self, session: Session):
                super().__init__(User, session)

        # IDE Support Features:
        repo = UserRepo(session)
        repo.  # Shows all available methods
        user = repo.find_by_id(1)  # Shows return type
        users = repo.find_by(  # Shows dict parameter hint
            filters={"status": "active"}  # Field completion
        )
        ```
    """
    def __init__(self, model_class: type[T], session: Session = None):
        """Initialize find operations with model type checking.
        
        IDE Tips:
            * Type hints for model_class
            * Session validation
            * Exception documentation
        
        Args:
            model_class: Your model class (User, Product, etc)
            session: Database session for queries
        """
        if not issubclass(model_class, SQLModel):
            raise ValidationError("model_class must be a SQLModel type")
        self.model_class = model_class
        self.session = session

    def find_by_id(self, id_value: Any) -> Optional[T]:
        """Find entity by ID with full IDE support.

        Args:
            id_value (Any): Primary key of entity to find

        Returns:
            Optional[T]: Found entity or None

        Example:
            ```python
            repo = UserRepository(session)
            user = repo.find_by_id(1)
            if user:  # Type checking
                print(user.name)  
            ```

        Raises:
            ValidationError: If session not initialized
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
        try:
            return self.session.get(self.model_class, id_value)
        except SQLAlchemyError:
            raise

    def find_all(self) -> List[T]:
        """Retrieve all entities.

        Returns:
            List[T]: List of all entities in database

        Example:
            ```python
            repo = UserRepository(session)
            # IDE shows return type List[User]:
            users = repo.find_all()  
            for user in users: 
                print(user.name)  
            ```

        Raises:
            ValidationError: If session not initialized
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
        try:
            statement = select(self.model_class)
            return self.session.exec(statement).all()
        except SQLAlchemyError:
            raise

    def find_all_by_id(self, ids: Iterable[Any]) -> List[T]:
        """Retrieve all entities.

        Returns:
            List[T]: List of all entities in database

        Example:
            ```python
            repo = UserRepository(session)
            # IDE shows return type List[User]:
            users = repo.find_all()  
            for user in users:  
                print(user.name)  
            ```

        Raises:
            ValidationError: If session not initialized
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
        if not ids:
            raise ValidationError("IDs collection cannot be empty")
        try:
            statement = select(self.model_class).where(self.model_class.id.in_(ids))
            return self.session.exec(statement).all()
        except SQLAlchemyError:
            raise

    def exists_by(self, **kwargs) -> bool:
        """Check if entity exists by field conditions.
        
        Args:
            **kwargs: Field-value pairs for filtering

        Returns:
            bool: True if entity exists, False otherwise

        Example:
            ```python
            repo = UserRepository(session)
            # IDE shows field suggestions:
            exists = repo.exists_by(
                email="user@example.com",  
                status="active"            
            )
            if exists:  # IDE suggests boolean check
                print("User exists")
            ```

        Raises:
            ValidationError: If session not initialized or invalid fields
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
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
            return self.session.exec(statement).first() is not None
        except SQLAlchemyError:
            raise

    def find_by(self, filters: Dict[str, Any] = None) -> List[T]:
        """Find entities by filter conditions.

        Args:
            filters: Dictionary of field-value pairs

        Returns:
            List[T]: List of entities matching filters

        Example:
            ```python
            repo = UserRepository(session)
            # IDE shows field suggestions:
            users = repo.find_by({
                "status": "active",     
                "age": 25             
            })
            for user in users:  # IDE suggests iteration
                print(user.name)  # IDE shows properties
            ```

        Raises:
            ValidationError: If session not initialized or invalid fields
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
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
            return self.session.exec(statement).all()
        except SQLAlchemyError:
            raise

    def find_one(self, id_or_filters: Any) -> Optional[T]:
        """Find single entity by ID or filter conditions.

        Args:
            id_or_filters: Entity ID or filter dictionary

        Returns:
            Optional[T]: Found entity or None

        Example:
            ```python
            repo = UserRepository(session)
            user1 = repo.find_one(1)

            user2 = repo.find_one({
                "email": "user@example.com"  
            })
            if user2:  # Type checking
                print(user2.name)  
            ```

        Raises:
            ValidationError: If session not initialized or invalid fields
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
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
                return self.session.exec(statement).first()
            return self.session.get(self.model_class, id_or_filters)
        except SQLAlchemyError:
            raise

    def find_by_date_between(
        self, 
        date_field: str, 
        start_date: Union[str, datetime, date], 
        end_date: Union[str, datetime, date]
    ) -> List[T]:
        """Find entities between date range.

        Args:
            date_field: Date field name in model
            start_date: Start date (format: yyyy-mm-dd)
            end_date: End date (format: yyyy-mm-dd)

        Returns:
            List[T]: Entities in date range

        Example:
            ```python
            repo = UserRepository(session)
            users = repo.find_by_date_between(
                date_field="created_at",
                start_date="2024-01-01",  # String format
                end_date="2024-12-31"     # String format
            )
            ```
        """
        if not self.session:
            raise ValidationError("Session not initialized")
        
        if not hasattr(self.model_class, date_field):
            raise ValidationError(f"Invalid date field: {date_field}")
        
        if isinstance(start_date, str):
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise ValidationError("Start date must be in format yyyy-mm-dd")

        if isinstance(end_date, str):
            try:
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise ValidationError("End date must be in format yyyy-mm-dd")

        if start_date > end_date:
            raise ValidationError("Start date must be before or equal to end date")

        try:
            date_column = getattr(self.model_class, date_field)
            statement = select(self.model_class).where(
                date_column.between(start_date, end_date)
            )
            return self.session.exec(statement).all()
        except SQLAlchemyError:
            raise

    def find_latest(self, order_by: str = "created_at") -> Optional[T]:
        """Find latest entity ordered by specified field.

        Args:
            order_by: Field name for ordering
                    IDE shows available model fields

        Returns:
            Optional[T]: Latest entity or None
                        IDE shows available properties

        Example:
            ```python
            repo = UserRepository(session)
            # IDE shows field suggestions:
            latest = repo.find_latest(
                order_by="created_at" 
            )
            if latest:  # Type checking
                print(latest.name)  
            ```

        Raises:
            ValidationError: If session not initialized or invalid field
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
        if not hasattr(self.model_class, order_by):
            raise ValidationError(f"Invalid order_by field: {order_by}")
        try:
            column = getattr(self.model_class, order_by)
            statement = select(self.model_class).order_by(column.desc())
            return self.session.exec(statement).first()
        except SQLAlchemyError:
            raise

    def find_by_like(self, fields: Union[str, List[str]], value: str) -> List[T]:
        """Search entities by multiple fields using LIKE operator.

        Args:
            fields: Single field name or list of field names to search
                IDE shows available text fields
            value: Search text (case insensitive)
                Wildcards % are auto-added

        Returns:
            List[T]: Matching entities

        Example:
            ```python
            repo = UserRepository(session)
            
            # Search in single field
            users = repo.find_by_like("name", "john")
            
            # Search in multiple fields
            users = repo.find_by_like(
                fields=["name", "email", "city"],  # Field completion
                value="john"      # Will match %john% in any field
            )
            ```

        Raises:
            ValidationError: If session not initialized or invalid fields
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Valid search value required")

        if isinstance(fields, str):
            fields = [fields]

        for field in fields:
            if not hasattr(self.model_class, field):
                raise ValidationError(f"Invalid field: {field}")

        try:
            conditions = [
                getattr(self.model_class, field).like(f"%{value}%")
                for field in fields
            ]
            
            statement = select(self.model_class).where(or_(*conditions))
            return self.session.exec(statement).all()
        except SQLAlchemyError:
            raise
        
        
    def search(self, value: str, fields: List[str] = None) -> List[T]:
        """Search entities across multiple text fields.

        Args:
            value: Text to search (case insensitive)
            fields: List of fields to search in. If None, searches all string fields

        Returns:
            List[T]: Matching entities

        Example:
            ```python
            repo = UserRepository(session)
            
            # Search in specific fields
            users = repo.search(
                value="john", 
                fields=["name", "email"]
            )
            
            # Search in all string fields
            users = repo.search("john")
            ```

        Raises:
            ValidationError: If session not initialized or invalid fields
            SQLAlchemyError: If database operation fails
        """
        if not self.session:
            raise ValidationError("Session not initialized")
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Valid search value required")

        try:
            if not fields:
                fields = [
                    field.name for field in self.model_class.__fields__.values()
                    if field.type_ == str
                ]
            else:
                for field in fields:
                    if not hasattr(self.model_class, field):
                        raise ValidationError(f"Invalid field: {field}")

            conditions = [
                getattr(self.model_class, field).like(f"%{value}%")
                for field in fields
            ]
            
            statement = select(self.model_class).where(or_(*conditions))
            return self.session.exec(statement).all()
        except SQLAlchemyError:
            raise
