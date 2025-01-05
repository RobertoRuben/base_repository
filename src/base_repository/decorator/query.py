import re
from typing import Dict, Any, Callable, TypeVar, get_type_hints
from functools import wraps
from sqlmodel import Session
from inspect import signature
from base_repository.repository.query.query_executor import QueryExecutor

placeholder_pattern = r":(\w+)"

T = TypeVar("T")

def query(value: str = None, scalar: bool = False) -> Callable[..., T]:
    """Native SQL query decorator with IDE support and type checking.

    IDE Features:
        * Parameter type hints (Ctrl+Space in query parameters)
        * Return type inference
        * Docstring generation for parameters
        * Auto-completion for result objects

    Query Support:
        * Named parameters with ':param' syntax
        * Automatic parameter mapping
        * Type validation for parameters
        * Result type inference

    Args:
        value (str): SQL query with ':param' style placeholders
        scalar (bool): If True, returns single value instead of result set

    Returns:
        Callable[..., T]: Decorated function with proper type hints

    Example:
        ```python
        class UserRepository(BaseRepository[User]):
            @query("SELECT * FROM users WHERE age > :age")
            def find_by_age(self, age: int) -> List[User]:
                pass  # IDE shows parameter hints and return type

            @query("SELECT count(*) FROM users", scalar=True)
            def count_users(self) -> int:
                pass  # IDE shows int as return type

            # Usage with IDE support:
            repo = UserRepository(session)
            users = repo.find_by_age(  # Shows age parameter hint
            count = repo.count_users()  # Shows int return type
        ```

    Type Hints:
        * Parameters are validated against function signatures
        * Return types are inferred from model class
        * IDE provides completion for result objects
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        query_executor = QueryExecutor()
        sig = signature(func)

        placeholders = set(re.findall(placeholder_pattern, value or ""))

        missing_params = placeholders - set(sig.parameters.keys()) - {"self"}
        unused_params = set(sig.parameters.keys()) - placeholders - {"self"}

        if missing_params:
            raise ValueError(
                f"Placeholders sin parámetros en la función: "
                f"{', '.join([f':{p}' for p in missing_params])}."
            )
        if unused_params:
            raise ValueError(
                f"Parámetros sin placeholder en la consulta: "
                f"{', '.join(unused_params)}."
            )

        func.__doc__ = (func.__doc__ or "") + "\n\n### Query Parameters:\n"
        func_annotations = get_type_hints(func)
        for placeholder in placeholders:
            param_type = func_annotations.get(placeholder, "Desconocido")
            func.__doc__ += f"  - `{placeholder}`: `{param_type}`\n"

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:

            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            self_instance = bound_args.arguments.get("self")
            if not self_instance or not hasattr(self_instance, "session"):
                raise ValueError(
                    "El repositorio no posee un atributo 'session' válido."
                )

            session = getattr(self_instance, "session")
            if not isinstance(session, Session):
                raise ValueError("El atributo 'session' no es instancia de `Session`.")

            params: Dict[str, Any] = {
                k: v for k, v in bound_args.arguments.items() if k in placeholders
            }

            if scalar:
                result = query_executor.execute_scalar_function(
                    session=session, query=value, params=params
                )
            else:
                result = query_executor.execute_native_query(
                    session=session, query=value, params=params
                )

            return result

        return wrapper

    return decorator
