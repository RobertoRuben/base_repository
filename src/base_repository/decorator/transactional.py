from functools import wraps, partial
from sqlmodel import Session, text
from typing import Callable, TypeVar, Union
from contextlib import contextmanager
import time
from sqlalchemy.exc import SQLAlchemyError
from base_repository.exception.decorator_exception import TransactionError, TransactionConfigError, TransactionValidationError

T = TypeVar("T")

MAX_RETRIES = 5
RETRY_DELAY = 0.1

@contextmanager
def transaction_context(session: Session, auto_concurrent: bool = False, read_only: bool = False):
    """
    Context manager for transaction handling.

    Args:
        session (Session): Database session
        auto_concurrent (bool): Enable REPEATABLE READ isolation
        read_only (bool): Enable read-only mode

    Raises:
        TransactionConfigError: For configuration errors
        SQLAlchemyError: For database errors
    """
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
    func: Union[Callable, bool] = None, 
    *, 
    auto_concurrent: bool = True, 
    read_only: bool = False
):
    """
    Transaction management decorator.

    Args:
        func (Callable): Function to decorate
        auto_concurrent (bool): Enable REPEATABLE READ isolation
        read_only (bool): Enable read-only mode

    Raises:
        TransactionValidationError: For validation errors
        SQLAlchemyError: For database errors
    """
    if callable(func):
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            session = next(
                (arg for arg in args if isinstance(arg, Session)), 
                kwargs.get("session")
            )
            
            if not isinstance(session, Session):
                raise TransactionValidationError("Valid database session required")

            retries = 0
            last_error = None

            while retries < MAX_RETRIES:
                try:
                    with transaction_context(
                        session, 
                        auto_concurrent=auto_concurrent, 
                        read_only=read_only
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
    
    return partial(transactional, auto_concurrent=auto_concurrent, read_only=read_only)