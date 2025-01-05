from typing import Callable, TypeVar, get_type_hints
from functools import wraps
from sqlmodel import Session
from inspect import signature
from base_repository.repository.procedure.procedure_executor import ProcedureExecutor
from base_repository.repository.procedure.database_type import DatabaseType
from base_repository.exception.decorator_exception import StoreProcedureValidationError
from base_repository.core.base_repository import BaseRepository

T = TypeVar("T")

def store_procedure(
    name: str, scalar: bool = False, db_type: DatabaseType = DatabaseType.POSTGRESQL
):
    """Stored procedure decorator with IDE support and type checking.

    IDE Features:
        * Parameter type hints (Ctrl+Space inside parentheses)
        * Return type inference based on function annotation
        * Auto-completion for procedure parameters
        * Documentation on hover
        * Go to definition support (F12)

    Args:
        name (str): Name of the stored procedure
        scalar (bool): If True, returns single value instead of result set
        db_type (DatabaseType): Database type (POSTGRESQL, MYSQL, etc)

    Returns:
        Callable[..., T]: Decorated function with proper type hints

    Example:
        ```python
        class UserRepository(BaseRepository[User]):
            @store_procedure("get_users_by_age")
            def get_users(self, min_age: int) -> List[User]:
                pass  # IDE shows parameter hints and return type

            @store_procedure("count_active_users", scalar=True)
            def count_users(self) -> int:
                pass  # IDE shows int as return type

            # Usage with IDE support:
            repo = UserRepository(session)
            users = repo.get_users(  # Shows min_age parameter hint
            count = repo.count_users()  # Shows int return type
        ```

    Type Support:
        * Parameters are validated against procedure signature
        * Return types are inferred from function annotation
        * IDE provides completion for result objects
        * Type checking for procedure parameters

    Database Support:
        * PostgreSQL (default)
        * MySQL
        * SQL Server
        * Oracle
    """
    if not name or not isinstance(name, str):
        raise StoreProcedureValidationError("Valid procedure name required")
    if not isinstance(db_type, DatabaseType):
        raise StoreProcedureValidationError("Invalid database type")

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        sig = signature(func)
        procedure_executor = ProcedureExecutor(db_type=db_type)
        func_annotations = get_type_hints(func)
        params_list = set(sig.parameters.keys()) - {"self", "cls", "session"}

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                self = bound_args.arguments.get("self")
                session = bound_args.arguments.get("session")

                if session is None and isinstance(self, BaseRepository):
                    session = getattr(self, "session", None)

                if not isinstance(session, Session):
                    raise StoreProcedureValidationError(
                        "Valid database session required. Either pass it as parameter or ensure class inherits from BaseRepository"
                    )

                params = {
                    k: v for k, v in bound_args.arguments.items() if k in params_list
                }

                if scalar:
                    return procedure_executor.execute_scalar_procedure(
                        session=session, name=name, params=params
                    )
                else:
                    return procedure_executor.execute_procedure(
                        session=session, name=name, params=params
                    )

            except StoreProcedureValidationError:
                raise
            except Exception:
                raise

        return wrapper

    return decorator
