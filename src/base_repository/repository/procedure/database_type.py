from enum import Enum

class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql" 
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"