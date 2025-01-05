from functools import wraps, partial
from sqlmodel import Session, text
from typing import Callable, TypeVar, Union
from contextlib import contextmanager
import time
from sqlalchemy.exc import SQLAlchemyError
from base_repository.exception.decorator_exception import (
    TransactionError,
    TransactionConfigError,
    TransactionValidationError,
)

T = TypeVar("T")

MAX_RETRIES = 5
RETRY_DELAY = 0.1


@contextmanager
def transaction_context(
    session: Session, auto_concurrent: bool = False, read_only: bool = False
):
    """Context manager for transaction handling"""
    if not isinstance(session, Session):
        raise TransactionConfigError("Valid database session required")

    try:
        if read_only:
            if not session.in_transaction():
                session.execute(text("SET TRANSACTION READ ONLY"))
        elif auto_concurrent and not session.in_transaction():
            session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))

        yield session

        if not read_only:
            session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise TransactionError(f"Transaction failed: {str(e)}")


def transactional(
    func: Union[Callable, None] = None,
    *,
    auto_concurrent: bool = True,
    read_only: bool = False,
):
    """Transaction management decorator with full IDE support.

    IDE Features:
        * Parameter type hints (Ctrl+Space inside parentheses)
        * Return type inference from decorated function
        * Auto-completion for transaction parameters
        * Documentation on hover
        * Go to definition support (F12)

    Args:
        func (Callable, optional): Function to decorate
        auto_concurrent (bool): Enables REPEATABLE READ isolation
        read_only (bool): Marks transaction as read-only

    Returns:
        Callable[..., T]: Decorated function with transaction management

    Example:
        ```python
        class UserService:
            @transactional  # Basic usage
            def create_user(self, user: User) -> User:
                return self.repository.save(user)

            @transactional(read_only=True)  # Read-only transaction
            def get_users(self) -> List[User]:
                return self.repository.find_all()

            @transactional(auto_concurrent=True)  # Concurrent access
            def update_user(self, user: User) -> User:
                return self.repository.update(user)

            # IDE Support:
            service.create_user(  # Shows User parameter hint
            users = service.get_users()  # Shows List[User] return type
        ```

    Features:
        * Automatic session detection
        * Retry mechanism for failed transactions
        * Transaction isolation level control
        * Read-only optimization
        * Exception handling with rollback
    """
    if func is None:
        return partial(
            transactional, auto_concurrent=auto_concurrent, read_only=read_only
        )

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        if args and hasattr(args[0], "session"):
            session = args[0].session

        elif (
            args
            and hasattr(args[0], "repository")
            and hasattr(args[0].repository, "session")
        ):
            session = args[0].repository.session

        else:
            session = next(
                (arg for arg in args if isinstance(arg, Session)), kwargs.get("session")
            )

        if not isinstance(session, Session):
            raise TransactionValidationError("Valid database session required")

        retries = 0
        last_error = None

        while retries < MAX_RETRIES:
            try:
                with transaction_context(
                    session, auto_concurrent=auto_concurrent, read_only=read_only
                ):
                    return func(*args, **kwargs)
            except SQLAlchemyError as e:
                last_error = e
                if retries < MAX_RETRIES - 1 and not read_only:
                    retries += 1
                    time.sleep(RETRY_DELAY)
                    continue
                raise

        if last_error:
            raise last_error

    return wrapper
