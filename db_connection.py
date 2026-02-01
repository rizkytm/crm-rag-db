import os
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import pandas as pd


class CRMDatabase:
    """PostgreSQL database connection for CRM leads"""

    def __init__(self):
        """Initialize database connection from environment variables"""
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "postgres")
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "crm_db_rag")

        self.engine = None
        self.connect()

    def connect(self):
        """Establish database connection"""
        try:
            connection_string = f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

            self.engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Verify connections before using
            )

            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            print("✅ Successfully connected to PostgreSQL database")
            return True

        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            raise

    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as DataFrame

        Args:
            query: SQL query string

        Returns:
            DataFrame with query results
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df

        except Exception as e:
            raise Exception(f"Error executing query: {e}")

    def get_table_info(self, table_name: str = "leads") -> dict:
        """
        Get information about table structure

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with column information
        """
        try:
            query = """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """

            with self.engine.connect() as conn:
                result = conn.execute(text(query), {"table_name": table_name})
                columns = result.fetchall()

            return {
                "table_name": table_name,
                "columns": [
                    {
                        "name": col[0],
                        "type": col[1],
                        "nullable": col[2],
                        "default": col[3]
                    }
                    for col in columns
                ]
            }

        except Exception as e:
            raise Exception(f"Error getting table info: {e}")

    def get_sample_data(self, table_name: str = "leads", limit: int = 5) -> pd.DataFrame:
        """
        Get sample data from table

        Args:
            table_name: Name of the table
            limit: Number of rows to return

        Returns:
            DataFrame with sample data
        """
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.execute_query(query)

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            self.get_sample_data()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
