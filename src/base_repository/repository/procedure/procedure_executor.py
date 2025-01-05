from typing import Dict, Any, List
from sqlmodel import Session, text
from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError
import time
from base_repository.repository.procedure.database_type import DatabaseType
from base_repository.repository.procedure.procedure_dialect import PostgreSQLDialect, MySQLDialect, SQLServerDialect, OracleDialect
from base_repository.exception.base_repository_exception import ProcedureValidationError

class ProcedureExecutor:
    """
    Executes database stored procedures with retry logic.

    Handles different database dialects and provides retry mechanism for transient failures.

    Attributes:
        MAX_RETRIES (int): Maximum number of retry attempts
        RETRY_DELAY (float): Delay between retries in seconds

    Example:
        ```python
        executor = ProcedureExecutor(DatabaseType.POSTGRESQL)
        result = executor.execute_procedure(session, "get_users", {"active": True})
        ```
    """

    def __init__(self, db_type: DatabaseType = DatabaseType.POSTGRESQL):
        """
        Initialize the procedure executor.

        Args:
            db_type (DatabaseType): Database type to use. Defaults to PostgreSQL.

        Raises:
            ProcedureValidationError: If database type is invalid
        """
        if not isinstance(db_type, DatabaseType):
            raise ProcedureValidationError("Invalid database type")

        self.MAX_RETRIES = 5
        self.RETRY_DELAY = 0.1
        self._dialects = {
            DatabaseType.POSTGRESQL: PostgreSQLDialect(),
            DatabaseType.MYSQL: MySQLDialect(),
            DatabaseType.SQLSERVER: SQLServerDialect(),
            DatabaseType.ORACLE: OracleDialect()
        }
        
        try:
            self.dialect = self._dialects[db_type]
        except KeyError:
            raise ProcedureValidationError(f"Unsupported database type: {db_type}")

    def execute_procedure(
        self,
        session: Session,
        name: str,
        params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a stored procedure that returns multiple rows.

        Args:
            session (Session): Active database session
            name (str): Name of the procedure to execute
            params (Dict[str, Any], optional): Parameters for the procedure

        Returns:
            List[Dict[str, Any]]: Results if procedure returns rows, empty list otherwise

        Raises:
            ProcedureValidationError: For invalid inputs
            SQLAlchemyError: For database-related errors

        Example:
            ```python
            try:
                results = executor.execute_procedure(
                    session, 
                    "get_active_users",
                    {"department": "IT"}
                )
            except ProcedureValidationError as e:
                print(f"Invalid parameters: {e}")
            except SQLAlchemyError as e:
                print("Database error occurred")
            ```
        """
        if not isinstance(session, Session):
            raise ProcedureValidationError("Valid database session required")
        if not name or not isinstance(name, str):
            raise ProcedureValidationError("Valid procedure name required")

        params = params or {}
        retries = 0

        try:
            call_query = self.dialect.build_call(name, params)
        except ProcedureValidationError:
            raise

        while retries < self.MAX_RETRIES:
            try:
                result = session.execute(text(call_query), params)
                if result.returns_rows:
                    return [dict(zip(result.keys(), row)) for row in result.fetchall()]
                return []
            except (OperationalError, IntegrityError):
                if retries < self.MAX_RETRIES - 1:
                    retries += 1
                    time.sleep(self.RETRY_DELAY)
                    continue
                raise
            except SQLAlchemyError:
                raise

    def execute_scalar_procedure(
        self,
        session: Session,
        name: str,
        params: Dict[str, Any] = None
    ) -> Any:
        """
        Execute a stored procedure that returns a single value.

        Args:
            session (Session): Active database session
            name (str): Name of the procedure to execute
            params (Dict[str, Any], optional): Parameters for the procedure

        Returns:
            Any: Single value returned by the procedure

        Raises:
            ProcedureValidationError: For invalid inputs
            SQLAlchemyError: For database-related errors

        Example:
            ```python
            try:
                count = executor.execute_scalar_procedure(
                    session,
                    "get_user_count",
                    {"status": "active"}
                )
            except ProcedureValidationError as e:
                print(f"Invalid parameters: {e}")
            except SQLAlchemyError as e:
                print("Database error occurred")
            ```
        """
        if not isinstance(session, Session):
            raise ProcedureValidationError("Valid database session required")
        if not name or not isinstance(name, str):
            raise ProcedureValidationError("Valid procedure name required")

        params = params or {}
        retries = 0

        try:
            call_query = self.dialect.build_call(name, params)
        except ProcedureValidationError:
            raise

        while retries < self.MAX_RETRIES:
            try:
                result = session.execute(text(call_query), params)
                return result.scalar()
            except (OperationalError, IntegrityError):
                if retries < self.MAX_RETRIES - 1:
                    retries += 1
                    time.sleep(self.RETRY_DELAY)
                    continue
                raise
            except SQLAlchemyError:
                raise