"""
Custom SQL tools for CRM database operations with PostgreSQL
"""
from typing import List, Dict, Any
import pandas as pd
from agno.tools import Toolkit


class CRMDatabaseTools(Toolkit):
    """Tools for querying CRM PostgreSQL database with security controls"""

    def __init__(self, db_connection, user=None, auth_service=None):
        """
        Initialize CRM tools with security

        Args:
            db_connection: Database connection
            user: Current user object (from auth module)
            auth_service: AuthService instance for permission checks
        """
        super().__init__(name="crm_database_tools")
        self.db = db_connection
        self.user = user
        self.auth_service = auth_service
        self.register(self.execute_sql)
        self.register(self.get_table_schema)
        self.register(self.get_column_info)
        self.register(self.my_leads)
        self.register(self.team_leads)

    def execute_sql(self, query: str) -> str:
        # This method allows executing SQL queries with security controls in place.
        """
        Execute a SQL query on the CRM database and return results.

        Security: Query is automatically sanitized based on user permissions.
        - Row-level security: Users only see their assigned leads
        - Column-level security: Sensitive fields are hidden for non-admins

        Args:
            query: SQL query to execute (use PostgreSQL syntax)

        Returns:
            Query results as formatted table string

        Examples:
            - "SELECT * FROM leads ORDER BY created_at DESC LIMIT 10"
            - "SELECT status, COUNT(*) as count FROM leads GROUP BY status"
            - "SELECT * FROM leads WHERE status = 'new'"
        """
        try:
            # Sanitize query based on user permissions
            if self.auth_service and self.user:
                query = self.auth_service.sanitize_query(self.user, query)

            df = self.db.execute_query(query)

            # Log the access
            if self.auth_service and self.user:
                record_ids = df['id'].tolist() if 'id' in df.columns else []
                self.auth_service.log_access(
                    user=self.user,
                    action='query',
                    table_name='leads',
                    record_ids=record_ids,
                    query=query[:1000]  # Truncate long queries
                )

            if df.empty:
                return "No results found."

            # Format results nicely as a table
            result = f"Query returned {len(df)} row(s):\n\n"

            # Add security notice if data was filtered
            if self.user and not self.user.can_view_all_leads():
                result += "🔒 Showing only your assigned leads.\n\n"

            # Create a simple table format
            # Add header
            headers = "| " + " | ".join(str(col) for col in df.columns) + " |"
            separator = "|" + "|".join([" --- " for _ in df.columns]) + "|"
            result += headers + "\n" + separator + "\n"

            # Add data rows (limit to first 20 rows for readability)
            for idx, row in df.head(20).iterrows():
                row_str = "| " + " | ".join(str(val) if pd.notna(val) else "" for val in row) + " |"
                result += row_str + "\n"

            if len(df) > 20:
                result += f"\n... and {len(df) - 20} more rows\n"

            return result

        except Exception as e:
            return f"Error executing query: {str(e)}\n\nPlease check your SQL syntax and try again."

    def my_leads(self) -> str:
        """
        Show leads for the current user.

        For admin/managers: Shows all leads
        For sales/viewer: Shows only assigned leads
        """
        if not self.user:
            return "Error: User not authenticated. Please login."

        # For admin and managers, show ALL leads
        if self.user.can_view_all_leads():
            query = """
                SELECT id, name, email, company, status, source, value, created_at
                FROM leads
                ORDER BY created_at DESC
                LIMIT 20
            """
        else:
            # For sales/viewers, show only assigned leads
            query = f"""
                SELECT id, name, email, company, status, source, created_at
                FROM leads
                WHERE owner_id = {self.user.id}
                OR id IN (SELECT lead_id FROM lead_assignments WHERE user_id = {self.user.id})
                ORDER BY created_at DESC
                LIMIT 20
            """

        # Execute directly without additional sanitization
        try:
            df = self.db.execute_query(query)

            # Log the access
            if self.auth_service and self.user:
                record_ids = df['id'].tolist() if 'id' in df.columns else []
                self.auth_service.log_access(
                    user=self.user,
                    action='view_my_leads',
                    table_name='leads',
                    record_ids=record_ids,
                    query='my_leads'
                )

            if df.empty:
                return "No leads found."

            # Format results nicely as a table
            result = f"Query returned {len(df)} row(s):\n\n"

            # Add notice based on user role
            if self.user and not self.user.can_view_all_leads():
                result += "🔒 Showing only your assigned leads.\n\n"
            else:
                result += "🌐 Showing all leads in the database.\n\n"

            # Create a simple table format
            headers = "| " + " | ".join(str(col) for col in df.columns) + " |"
            separator = "|" + "|".join([" --- " for _ in df.columns]) + "|"
            result += headers + "\n" + separator + "\n"

            # Add data rows
            for idx, row in df.iterrows():
                row_str = "| " + " | ".join(str(val) if pd.notna(val) else "" for val in row) + " |"
                result += row_str + "\n"

            return result

        except Exception as e:
            return f"Error executing query: {str(e)}"

    def team_leads(self) -> str:
        """
        Show leads for your team (managers and above only).

        This shows all leads that your team members can access.
        Already includes security filtering.
        """
        if not self.user:
            return "Error: User not authenticated. Please login."

        if not self.user.can_view_all_leads():
            return "Access denied: You don't have permission to view team leads."

        query = """
            SELECT id, name, email, company, status, owner_id, created_at
            FROM leads
            ORDER BY created_at DESC
            LIMIT 50
        """

        # Execute directly without sanitization (user has permission to see all)
        try:
            df = self.db.execute_query(query)

            # Log the access
            if self.auth_service and self.user:
                record_ids = df['id'].tolist() if 'id' in df.columns else []
                self.auth_service.log_access(
                    user=self.user,
                    action='view_team_leads',
                    table_name='leads',
                    record_ids=record_ids,
                    query='team_leads'
                )

            if df.empty:
                return "No leads found."

            # Format results nicely as a table
            result = f"Query returned {len(df)} row(s):\n\n"

            # Create a simple table format
            headers = "| " + " | ".join(str(col) for col in df.columns) + " |"
            separator = "|" + "|".join([" --- " for _ in df.columns]) + "|"
            result += headers + "\n" + separator + "\n"

            # Add data rows
            for idx, row in df.iterrows():
                row_str = "| " + " | ".join(str(val) if pd.notna(val) else "" for val in row) + " |"
                result += row_str + "\n"

            return result

        except Exception as e:
            return f"Error executing query: {str(e)}"

    def get_table_schema(self, table_name: str = "leads") -> str:
        """
        Get the schema/structure of a CRM database table.

        Use this to understand what columns are available before writing queries.

        Args:
            table_name: Name of the table (default: "leads")

        Returns:
            Table schema information
        """
        try:
            info = self.db.get_table_info(table_name)

            result = f"Table: {info['table_name']}\n\n"
            result += "Columns:\n"
            for col in info['columns']:
                result += f"  - {col['name']}: {col['type']} (nullable: {col['nullable']})\n"

            return result

        except Exception as e:
            return f"Error getting table schema: {str(e)}"

    def get_column_info(self, table_name: str = "leads") -> str:
        """
        Get detailed column information including sample data.

        Use this to understand the data in each column.

        Args:
            table_name: Name of the table (default: "leads")

        Returns:
            Column information with sample data
        """
        try:
            df = self.db.get_sample_data(table_name, limit=3)

            result = f"Sample data from '{table_name}' table:\n\n"

            # Get column types
            info = self.db.get_table_info(table_name)
            column_types = {col['name']: col['type'] for col in info['columns']}

            for col in df.columns:
                dtype = column_types.get(col, "unknown")
                sample_values = df[col].dropna().head(3).tolist()
                result += f"  - {col} ({dtype}): {sample_values}\n"

            return result

        except Exception as e:
            return f"Error getting column info: {str(e)}"
