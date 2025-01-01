from typing import Callable, TypeVar, get_type_hints
from functools import wraps
from sqlmodel import Session
from inspect import signature
from src.repository.procedure.procedure_executor import ProcedureExecutor
from src.repository.procedure.database_type import DatabaseType
from src.exception.decorator_exception import StoreProcedureValidationError

T = TypeVar('T')

def store_procedure(
    name: str,
    scalar: bool = False,
    db_type: DatabaseType = DatabaseType.POSTGRESQL
):
    """
    Decorator for executing stored procedures.

    This decorator simplifies the execution of database stored procedures by wrapping
    methods and handling parameter validation and execution.

    Args:
        name (str): Name of the stored procedure to execute
        scalar (bool, optional): Whether the procedure returns a single value. 
            Defaults to False.
        db_type (DatabaseType, optional): Type of database to use. 
            Defaults to PostgreSQL.

    Returns:
        Callable: Decorated function that executes the stored procedure.

    Raises:
        StoreProcedureValidationError: If any of these conditions occur:
            - Invalid procedure name
            - Invalid database type
            - Missing session parameter
            - Invalid session type
        ProcedureError: If procedure execution fails

    Example:
        ```python
        class UserRepository:
            @store_procedure(name="get_users_by_status", db_type=DatabaseType.POSTGRESQL)
            def get_active_users(
                self, 
                session: Session,
                status: str = "active"
            ) -> List[Dict[str, Any]]:
                pass

            @store_procedure(name="get_user_count", scalar=True)
            def count_users(
                self,
                session: Session,
                department: str
            ) -> int:
                pass

        # Usage
        try:
            repo = UserRepository()
            users = repo.get_active_users(session, status="active")
            count = repo.count_users(session, department="IT")
        except StoreProcedureValidationError as e:
            print(f"Validation error: {e}")
        except ProcedureError as e:
            print(f"Procedure error: {e}")
        ```
    """
    if not name or not isinstance(name, str):
        raise StoreProcedureValidationError("Valid procedure name required")
    if not isinstance(db_type, DatabaseType):
        raise StoreProcedureValidationError("Invalid database type")

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        """
        Internal decorator function that wraps the method.

        Args:
            func (Callable[..., T]): Function to decorate

        Returns:
            Callable[..., T]: Wrapped function

        Raises:
            StoreProcedureValidationError: If function signature is invalid
        """
        sig = signature(func)

        if 'session' not in sig.parameters:
            raise StoreProcedureValidationError(
                f"Function '{func.__name__}' must have 'session: Session' parameter"
            )

        procedure_executor = ProcedureExecutor(db_type=db_type)
        func_annotations = get_type_hints(func)
        params_list = set(sig.parameters.keys()) - {'self', 'cls', 'session'}

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            """
            Executes the stored procedure with provided arguments.

            Returns:
                T: Result from the procedure execution

            Raises:
                StoreProcedureValidationError: If arguments are invalid
                ProcedureError: If execution fails
            """
            try:
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                session = bound_args.arguments.get('session')
                if not isinstance(session, Session):
                    raise StoreProcedureValidationError(
                        "session parameter must be a Session instance"
                    )

                params = {
                    k: v for k, v in bound_args.arguments.items()
                    if k in params_list
                }

                if scalar:
                    return procedure_executor.execute_scalar_procedure(
                        session=session,
                        name=name,
                        params=params
                    )
                else:
                    return procedure_executor.execute_procedure(
                        session=session,
                        name=name,
                        params=params
                    )

            except StoreProcedureValidationError:
                raise
            except Exception:
                raise

        return wrapper
    return decorator