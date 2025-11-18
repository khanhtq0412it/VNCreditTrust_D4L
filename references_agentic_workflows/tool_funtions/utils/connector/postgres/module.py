from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker


class PostgresConnector:
    """
    A connector class for interacting with a PostgreSQL database using SQLAlchemy.
    """

    def __init__(self, host: str, port: int, user: str, password: str, db: str):
        """
        Initializes the PostgresConnector with connection parameters.

        Args:
            host (str): Hostname or IP address of the PostgreSQL server.
            port (int): Port number of the PostgreSQL server.
            user (str): Username for authentication.
            password (str): Password for authentication.
            db (str): Database name.
        """
        self.__host = host
        self.__port = port
        self.__user = user
        self.__password = password
        self.__db = db
        self.__engine: Engine = None
        self.__session_factory = None

    def __variable__(self) -> str:
        """
        Returns the connection details as a string.

        Returns:
            str: A formatted string representing the connection details.
        """
        return (
            f"PostgresConnection("
            f"host={self.__host}, port={self.__port}, "
            f"user={self.__user}, db={self.__db})"
        )

    def connect_engine(self) -> Engine:
        """
        Creates and returns a SQLAlchemy engine for PostgreSQL.

        Returns:
            Engine: A SQLAlchemy engine instance.

        Raises:
            SQLAlchemyError: If the connection fails.
        """
        try:
            if not self.__engine:
                conn_str = (
                    f"postgresql+psycopg2://{self.__user}:{self.__password}"
                    f"@{self.__host}:{self.__port}/{self.__db}"
                )
                self.__engine = create_engine(conn_str)
                self.__session_factory = sessionmaker(bind=self.__engine)
            return self.__engine
        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to connect to PostgreSQL: {e}") from e

    def test_connection(self) -> bool:
        """
        Tests the PostgreSQL connection by executing a simple query.

        Returns:
            bool: True if connection is successful, False otherwise.
        """
        try:
            engine = self.connect_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"PostgreSQL connection test failed: {e}")
            return False

    def get_session(self):
        """
        Returns a new SQLAlchemy session.

        Returns:
            Session: A SQLAlchemy session instance.
        """
        if not self.__session_factory:
            self.connect_engine()
        return self.__session_factory()

    def close(self):
        """
        Disposes of the SQLAlchemy engine and closes all connections.
        """
        if self.__engine:
            try:
                self.__engine.dispose()
                print("PostgreSQL engine connection closed successfully.")
            except Exception as e:
                print(f"Failed to close PostgreSQL connection: {e}")
            finally:
                self.__engine = None
                self.__session_factory = None
