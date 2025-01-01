import re
from typing import Dict, Any, Callable, TypeVar, get_type_hints
from functools import wraps
from sqlmodel import Session
from inspect import signature
from src.repository.query.query_executor import QueryExecutor

# Regular expression to detect placeholders in the format ':param'
placeholder_pattern = r':(\w+)'

T = TypeVar('T')

def query(
    value: str = None,
    scalar: bool = False
) -> Callable[..., T]:
    """
    Decorator to execute native SQL queries, automatically mapping function parameters to SQL query placeholders.

    This decorator simplifies executing native SQL queries by ensuring that the parameters of the function
    are correctly mapped to the placeholders in the SQL query string. Additionally, it validates the 
    presence of required parameters, improves function docstrings, and enhances IDE support for type hints.

    Args:
        value (str): The SQL query string containing placeholders in the form `:placeholder`.
        scalar (bool): Indicates whether the query returns a scalar value (e.g., int, str).

    Returns:
        Callable[..., T]: The decorated function that executes the query and returns the result.

    Raises:
        ValueError: If the function does not include a `session` parameter or if there are discrepancies
                    between the placeholders and function parameters.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        query_executor = QueryExecutor()
        sig = signature(func)

        # Validate that 'session' is present in the function signature
        if 'session' not in sig.parameters:
            raise ValueError(
                f"The function '{func.__name__}' must have a 'session: Session' parameter."
            )

        # Extract function annotations and SQL query placeholders
        func_annotations = get_type_hints(func)
        placeholders = set(re.findall(placeholder_pattern, value or ""))

        # Validate that placeholders match the function parameters
        missing_params = placeholders - set(sig.parameters.keys())
        unused_params = set(sig.parameters.keys()) - placeholders - {'self', 'cls', 'session'}

        if missing_params:
            raise ValueError(
                f"Placeholders without corresponding parameters: "
                f"{', '.join([f':{p}' for p in missing_params])}."
            )

        if unused_params:
            raise ValueError(
                f"Parameters without corresponding placeholders: "
                f"{', '.join(unused_params)}."
            )

        # Enhance the function docstring with information about the query parameters
        func.__doc__ = (func.__doc__ or "") + "\n\n"
        func.__doc__ += "### Query Parameters Detected:\n"
        for placeholder in placeholders:
            param_type = func_annotations.get(placeholder, "Unknown")
            func.__doc__ += f"  - `{placeholder}`: `{param_type}`\n"

        # Add type annotations for query parameters to help IDEs (e.g., Pylance)
        for placeholder in placeholders:
            if placeholder not in func_annotations:
                func_annotations[placeholder] = str  # Default to 'str' for query params
        func.__annotations__ = func_annotations

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            """
            Wrapper function that binds the arguments to the signature, validates the session, and executes 
            the SQL query.

            Args:
                *args: Positional arguments passed to the decorated function.
                **kwargs: Keyword arguments passed to the decorated function.

            Returns:
                T: The result of the SQL query, either a list of results or a scalar value based on 'scalar'.
            """
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Extract the 'session' argument
            session = bound_args.arguments.get('session')
            if not isinstance(session, Session):
                raise ValueError("The 'session' parameter must be an instance of `Session`.")

            # Filter and collect the parameters for the query
            params: Dict[str, Any] = {
                k: v for k, v in bound_args.arguments.items()
                if k in placeholders
            }

            if scalar:
                result = query_executor.execute_scalar_function(
                    session=session,
                    query=value,
                    params=params
                )
            else:
                result = query_executor.execute_native_query(
                    session=session,
                    query=value,
                    params=params
                )

            return result

        return wrapper
    return decorator
