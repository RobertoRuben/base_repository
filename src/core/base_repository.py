from typing import TypeVar, Type
from sqlmodel import SQLModel
from src.repository.crud.crud_operations import BasicOperations 
from src.repository.pageable.pageable_operations import PageableOperations
from src.repository.find.find_operations import FindOperations

T = TypeVar("T", bound=SQLModel)

class BaseRepository(BasicOperations[T], PageableOperations[T], FindOperations[T]):
    """Base repository that combines CRUD and pagination operations
    
    This repository provides a base implementation combining basic CRUD operations
    pagination and find functionality for SQLModel entities.
    
    Type Parameters:
        T: A SQLModel subclass that represents the database entity
    
    Example:
        ```python
        class UserRepository(BaseRepository[User]):
            def __init__(self):
                super().__init__(User)
        
        # Usage
        repo = UserRepository()
        users = repo.find_all()  # From BasicOperations
        page = repo.find_page()  # From PageableOperations
        find = repo.find_by_id(1)  # From FindOperations
        ```
    """

    def __init__(self, model_class: Type[T]):
        """Initialize the base repository
        
        Args:
            model_class: The SQLModel class that this repository manages
        """
        BasicOperations.__init__(self, model_class)
        PageableOperations.__init__(self, model_class)
        FindOperations.__init__(self, model_class)
