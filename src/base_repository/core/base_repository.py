from typing import TypeVar, Type
from sqlmodel import SQLModel, Session
from base_repository.repository.crud.crud_operations import BasicOperations 
from base_repository.repository.pageable.pageable_operations import PageableOperations
from base_repository.repository.find.find_operations import FindOperations

T = TypeVar("T", bound=SQLModel)

class BaseRepository(BasicOperations[T], PageableOperations[T], FindOperations[T]):
    """Generic repository for database operations.

    IDE Features:
        * Auto-completion for all methods (type '.')
        * Parameter type hints (Ctrl+Space inside parentheses)
        * Method documentation on hover
        * Go to definition support (F12)
        * Type checking for models

    Available Methods:
        CRUD Operations:
            * create(model: T) -> T
            * update(model: T) -> T
            * delete(model: T) -> None
            * save(model: T) -> T
        
        Find Operations:
            * find_all() -> List[T]
            * find_by_id(id: Any) -> Optional[T]
            * find_by(**kwargs) -> List[T]
        
        Pagination:
            * page_by(page: int, size: int) -> Page[T]
            * count() -> int

    Type Support:
        T = Your model type (must inherit from SQLModel)
        All methods will enforce correct types for your model

    Example:
        ```python
        # IDE will provide completion for User properties
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: Session):
                super().__init__(User, session)

        repo = UserRepository(session)
        # Type '.' after repo to see all available methods
        user = repo.find_by_id(1)  # IDE shows User as return type
        users = repo.find_all()    # IDE shows List[User] as return type
        ```
    """

    def __init__(self, model_class: Type[T], session: Session = None):
        """Initialize repository with automatic type inference.

        The IDE will provide:
            * Method completion when typing 'self.'
            * Parameter hints inside method calls
            * Type checking for model_class
            * Session validation

        Args:
            model_class: Your SQLModel class (automatically sets generic type T)
            session: Database session for operations
        """
        BasicOperations.__init__(self, model_class, session)
        PageableOperations.__init__(self, model_class, session)
        FindOperations.__init__(self, model_class, session)
