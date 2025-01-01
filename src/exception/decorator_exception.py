from src.exception.base_repository_exception import RepositoryError

class StoreProcedureError(RepositoryError):
    """Base error for store procedure decorator."""
    def __init__(self, message: str = "Store procedure error occurred"):
        self.message = message
        super().__init__(self.message)

class StoreProcedureValidationError(StoreProcedureError):
    """Validation error in store procedure decorator."""
    def __init__(self, message: str = "Store procedure validation failed"):
        super().__init__(message)

class TransactionError(RepositoryError):
    """Base error for transaction operations."""
    def __init__(self, message: str = "Transaction error occurred"):
        self.message = message
        super().__init__(self.message)

class TransactionConfigError(TransactionError):
    """Configuration error in transactions."""
    def __init__(self, message: str = "Transaction configuration invalid"):
        super().__init__(message)

class TransactionValidationError(TransactionError):
    """Validation error in transactions."""
    def __init__(self, message: str = "Transaction validation failed"):
        super().__init__(message)

class TransactionRollbackError(TransactionError):
    """Error when transaction rollback occurs."""
    def __init__(self, message: str = "Transaction rolled back", cause: Exception = None):
        self.cause = cause
        message = f"{message} - Cause: {str(cause)}" if cause else message
        super().__init__(message)