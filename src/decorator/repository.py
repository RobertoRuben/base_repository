from functools import wraps
from typing import Type, TypeVar, Any

T = TypeVar('T')

def repository(cls: Type[T]) -> Type[T]:
    """Class decorator that configures a repository with its model class.
    
    This decorator extracts the model class from the first generic base class
    and configures the repository instance with it. It's designed to work with
    repository classes that inherit from a generic base repository.

    Args:
        cls (Type[T]): The repository class being decorated

    Returns:
        Type[T]: The configured repository class

    Raises:
        TypeError: If the class doesn't have the expected generic base class structure

    Example:
        ```python
        @repository
        class UserRepository(BaseRepository[User]):
            pass
        ```
    """
    try:
        # Extract model class from first generic base
        base = cls.__orig_bases__[0]
        model_class = base.__args__[0]

        # Store original init
        original_init = cls.__init__

        @wraps(original_init)
        def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
            """Initialize repository with model class."""
            super(cls, self).__init__(model_class, *args, **kwargs)

        # Replace init with new version
        cls.__init__ = __init__
        return cls
        
    except (AttributeError, IndexError) as e:
        raise TypeError(
            f"Repository decorator requires a class with generic base. Error: {str(e)}"
        ) from e