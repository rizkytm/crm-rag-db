"""
Authentication and Authorization Module for CRM
"""
import os
import hashlib
from typing import Optional, List, Dict
from db_connection import CRMDatabase
from sqlalchemy import text


class User:
    """User model"""

    def __init__(self, id: int, username: str, email: str, full_name: str, role: str):
        self.id = id
        self.username = username
        self.email = email
        self.full_name = full_name
        self.role = role

    def can_view_all_leads(self) -> bool:
        """Check if user can view all leads (admin or manager)"""
        return self.role in ['admin', 'manager']

    def can_export_data(self) -> bool:
        """Check if user can export data"""
        return self.role in ['admin', 'manager']

    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == 'admin'


class AuthService:
    """Authentication and authorization service"""

    def __init__(self, db: CRMDatabase):
        self.db = db

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password

        Note: This is a simple implementation. In production:
        - Use proper password hashing (bcrypt, argon2)
        - Implement JWT tokens
        - Add rate limiting
        - Use HTTPS
        """
        query = """
            SELECT u.id, u.username, u.email, u.full_name, r.name as role
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.username = :username
            AND u.is_active = true
        """

        try:
            with self.db.engine.connect() as conn:
                result = conn.execute(text(query), {"username": username})
                user_data = result.fetchone()

                if not user_data:
                    return None

                # TODO: Verify password hash
                # For now, accept any password for demo purposes
                # In production: verify_password(password, user_data.password_hash)

                user = User(
                    id=user_data[0],
                    username=user_data[1],
                    email=user_data[2],
                    full_name=user_data[3],
                    role=user_data[4]
                )

                return user

        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    def get_accessible_leads_query(self, user: User) -> str:
        """
        Get SQL WHERE clause for leads user can access

        Returns:
            SQL WHERE clause string
        """
        if user.can_view_all_leads():
            # Admins and managers can see all leads
            return "1=1"
        else:
            # Sales reps can only see their assigned leads
            # Wrap in parentheses for proper SQL syntax
            return f"""(id IN (SELECT lead_id FROM lead_assignments WHERE user_id = {user.id}) OR owner_id = {user.id})"""

    def get_hidden_columns(self, user: User) -> List[str]:
        """
        Get list of columns to hide based on user role

        Returns:
            List of column names to hide
        """
        if user.is_admin():
            return []  # Admins see everything

        # Hide sensitive columns for non-admins
        sensitive_columns = ['value', 'internal_notes', 'admin_notes']

        # Viewers and sales reps can't see value
        if user.role in ['viewer', 'sales_rep']:
            return sensitive_columns

        # Managers can see value but not internal notes
        if user.role == 'manager':
            return ['internal_notes', 'admin_notes']

        return []

    def log_access(self, user: User, action: str, table_name: str,
                   record_ids: List[int] = None, query: str = None):
        """
        Log user access to audit table

        Args:
            user: The user performing the action
            action: Action performed (view, query, export, etc.)
            table_name: Table accessed
            record_ids: List of record IDs accessed
            query: SQL query executed
        """
        import json

        query = """
            INSERT INTO audit_logs (user_id, action, table_name, record_ids, query_text)
            VALUES (:user_id, :action, :table_name, :record_ids, :query)
        """

        try:
            with self.db.engine.connect() as conn:
                conn.execute(text(query), {
                    "user_id": user.id,
                    "action": action,
                    "table_name": table_name,
                    "record_ids": json.dumps(record_ids) if record_ids else None,
                    "query": query
                })
                conn.commit()
        except Exception as e:
            print(f"Failed to log access: {e}")

    def sanitize_query(self, user: User, original_query: str) -> str:
        """
        Modify query to respect user permissions

        Args:
            user: The user executing the query
            original_query: Original SQL query

        Returns:
            Modified query with permission filters
        """
        # Get columns to hide
        hidden_columns = self.get_hidden_columns(user)

        if not hidden_columns and user.can_view_all_leads():
            # No restrictions
            return original_query

        # Remove hidden columns from SELECT
        import re

        # Extract SELECT columns
        if "SELECT *" in original_query.upper():
            # Replace * with specific columns (excluding hidden ones)
            all_columns = [
                "id", "name", "email", "phone", "company", "title",
                "status", "source", "value", "notes",
                "created_at", "updated_at", "last_contacted_at"
            ]

            visible_columns = [col for col in all_columns if col not in hidden_columns]
            columns_str = ", ".join(visible_columns)

            modified_query = re.sub(
                r"SELECT \*",
                f"SELECT {columns_str}",
                original_query,
                flags=re.IGNORECASE
            )
        else:
            modified_query = original_query

        # Add WHERE clause for row-level security
        if not user.can_view_all_leads():
            # Add permission filter to WHERE clause
            access_filter = self.get_accessible_leads_query(user)

            if "WHERE" in modified_query.upper():
                # Query already has WHERE, append with AND
                modified_query = f"{modified_query} AND {access_filter}"
            else:
                # No WHERE, add it after FROM leads
                # Find the table reference (FROM leads)
                modified_query = re.sub(
                    r"(FROM leads)(\s|$)",
                    rf"\1 WHERE {access_filter}\2",
                    modified_query,
                    flags=re.IGNORECASE
                )

        return modified_query


def create_demo_users(db: CRMDatabase):
    """Create demo users for testing"""
    query = """
        INSERT INTO users (username, email, full_name, role_id)
        VALUES
            ('admin', 'admin@company.com', 'Admin User', 1),
            ('manager', 'manager@company.com', 'Manager User', 2),
            ('sales', 'sales@company.com', 'Sales Rep', 3),
            ('viewer', 'viewer@company.com', 'Viewer User', 4)
        ON CONFLICT (username) DO NOTHING
    """

    try:
        with db.engine.connect() as conn:
            conn.execute(text(query))
            conn.commit()
        print("Demo users created successfully!")
    except Exception as e:
        print(f"Error creating demo users: {e}")
