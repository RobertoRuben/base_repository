from abc import ABC, abstractmethod
from typing import Dict, Any
from src.exception.base_repository_exception import ProcedureValidationError

class ProcedureDialect(ABC):
    @abstractmethod
    def build_call(self, name: str, params: Dict[str, Any]) -> str:
        """
        Build a procedure call query string.

        Args:
            name (str): Procedure name
            params (Dict[str, Any]): Procedure parameters

        Returns:
            str: Formatted procedure call

        Raises:
            ProcedureValidationError: If name or params are invalid
        """
        if not name or not isinstance(name, str):
            raise ProcedureValidationError("Valid procedure name required")
        if params is not None and not isinstance(params, dict):
            raise ProcedureValidationError("Parameters must be a dictionary")
        

class PostgreSQLDialect(ProcedureDialect):
    def build_call(self, name: str, params: Dict[str, Any]) -> str:
        param_list = [f":{param}" for param in params.keys()]
        return f"CALL {name}({','.join(param_list)})"

class MySQLDialect(ProcedureDialect):
    def build_call(self, name: str, params: Dict[str, Any]) -> str:
        param_list = [f":{param}" for param in params.keys()]
        return f"CALL {name}({','.join(param_list)})"

class SQLServerDialect(ProcedureDialect):
    def build_call(self, name: str, params: Dict[str, Any]) -> str:
        param_list = [f"@{param}=:{param}" for param in params.keys()]
        return f"EXEC {name} {', '.join(param_list)}"

class OracleDialect(ProcedureDialect):
    def build_call(self, name: str, params: Dict[str, Any]) -> str:
        param_list = [f":{param}" for param in params.keys()]
        return f"BEGIN {name}({','.join(param_list)}); END;"