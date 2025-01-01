class BaseRepositoryException(Exception):
    """Base exception class for all repository operations."""
    def __init__(self, message: str = "Repository operation error"):
        self.message = message
        super().__init__(self.message)

class RepositoryError(BaseRepositoryException):
    """Base exception for repository operations."""
    def __init__(self, message: str = "Repository error occurred"):
        super().__init__(message)

class ValidationError(RepositoryError):
    """Validation error for repository operations."""
    def __init__(self, message: str = "Repository validation failed"):
        super().__init__(message)

class EntityNotFoundError(RepositoryError):
    """Error when entity is not found."""
    def __init__(self, message: str = "Entity not found"):
        super().__init__(message)

class InvalidOperationError(RepositoryError):
    """Error for invalid operations."""
    def __init__(self, message: str = "Invalid repository operation"):
        super().__init__(message)

class ProcedureError(RepositoryError):
    """Base error for stored procedures."""
    def __init__(self, message: str = "Stored procedure error occurred"):
        super().__init__(message)

class ProcedureValidationError(ProcedureError):
    """Validation error for procedures."""
    def __init__(self, message: str = "Procedure validation failed"):
        super().__init__(message)

class ProcedureDialectError(ProcedureError):
    """Error for procedure dialect operations."""
    def __init__(self, message: str = "Procedure dialect error"):
        super().__init__(message)