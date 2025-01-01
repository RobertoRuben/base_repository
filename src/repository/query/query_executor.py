from typing import Dict, Any, List
from sqlmodel import Session, text
from sqlalchemy.exc import OperationalError, IntegrityError
import time

class QueryExecutor:
    """A class for executing SQL queries with retry logic and error handling.

    This class provides methods to execute raw SQL queries and scalar functions
    with built-in retry mechanism for handling transient database errors.

    Attributes:
        MAX_RETRIES (int): Maximum number of retry attempts (default: 5)
        RETRY_DELAY (float): Delay between retries in seconds (default: 0.1)
    """
    
    def __init__(self):
        self.MAX_RETRIES = 5
        self.RETRY_DELAY = 0.1

    def execute_native_query(
        self, 
        session: Session,
        query: str, 
        params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results as a list of dictionaries.

        Args:
            session (Session): SQLAlchemy session object
            query (str): SQL query string to execute
            params (Dict[str, Any], optional): Query parameters. Defaults to None.
            readonly (bool, optional): Whether the query is read-only. Defaults to True.

        Returns:
            List[Dict[str, Any]]: List of dictionaries where each dictionary
            represents a row with column names as keys.

        Raises:
            RuntimeError: If query execution fails after maximum retries or
            encounters unexpected errors.
        """
        params = params or {}
        retries = 0

        while retries < self.MAX_RETRIES:
            try:
                result = session.execute(text(query), params)
                
                if result.returns_rows:
                    rows = [dict(zip(result.keys(), row)) for row in result.fetchall()]
                    return rows
                
                return []
            
            except (OperationalError, IntegrityError) as e:
                if retries < self.MAX_RETRIES - 1:
                    retries += 1
                    time.sleep(self.RETRY_DELAY)
                    continue
                raise RuntimeError(f"Error executing query: {str(e)}") from e
            except Exception as e:
                raise RuntimeError(f"Unexpected error: {str(e)}") from e

    def execute_scalar_function(
        self,
        session: Session,
        query: str,
        params: Dict[str, Any] = None
    ) -> Any:
        """Execute a SQL query and return a single scalar result.

        Args:
            session (Session): SQLAlchemy session object
            query (str): SQL query string to execute
            params (Dict[str, Any], optional): Query parameters. Defaults to None.
            readonly (bool, optional): Whether the query is read-only. Defaults to True.

        Returns:
            Any: Single scalar value from the query result.

        Raises:
            RuntimeError: If query execution fails after maximum retries or
            encounters unexpected errors.
        """
        params = params or {}
        retries = 0

        while retries < self.MAX_RETRIES:
            try:
                result = session.execute(text(query), params)
                return result.scalar()
            
            except (OperationalError, IntegrityError) as e:
                if retries < self.MAX_RETRIES - 1:
                    retries += 1
                    time.sleep(self.RETRY_DELAY)
                    continue
                raise RuntimeError(f"Error executing query: {str(e)}") from e
            except Exception as e:
                raise RuntimeError(f"Unexpected error: {str(e)}") from e
            
            
    