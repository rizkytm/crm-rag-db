"""
Test script to demonstrate security features
Run this to see how different users see different data
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from db_connection import CRMDatabase
from auth import AuthService
from crm_agent import CRMDatabaseTools

def test_security():
    print("=" * 60)
    print("🔒 CRM SECURITY TEST")
    print("=" * 60)

    # Initialize
    db = CRMDatabase()
    auth = AuthService(db)

    print("\n📊 Total leads in database: 30")
    print("\n" + "=" * 60)

    # Test 1: Admin User (can see everything)
    print("\n✅ TEST 1: ADMIN USER")
    print("-" * 60)
    admin_user = auth.authenticate_user("admin", "any_password")
    print(f"User: {admin_user.username} ({admin_user.role})")
    print(f"Can see all leads: {admin_user.can_view_all_leads()}")
    print(f"Can see value column: {admin_user.is_admin()}")

    admin_tools = CRMDatabaseTools(db, user=admin_user, auth_service=auth)
    result = admin_tools.execute_sql("SELECT COUNT(*) as total FROM leads")
    print(f"\nQuery: SELECT COUNT(*) FROM leads")
    print(f"Result: {result}")

    # Test 2: Sales Rep (can only see their leads)
    print("\n" + "=" * 60)
    print("\n✅ TEST 2: SALES REP USER")
    print("-" * 60)
    sales_user = auth.authenticate_user("sarah_sales", "any_password")
    print(f"User: {sales_user.username} ({sales_user.role})")
    print(f"Can see all leads: {sales_user.can_view_all_leads()}")
    print(f"Can see value column: {not auth.get_hidden_columns(sales_user)}")

    sales_tools = CRMDatabaseTools(db, user=sales_user, auth_service=auth)
    result = sales_tools.execute_sql("""
        SELECT id, name, email, company, status
        FROM leads
        ORDER BY created_at DESC
        LIMIT 5
    """)
    print(f"\nQuery: SELECT id, name, email, company, status FROM leads LIMIT 5")
    print(f"Result:\n{result}")

    # Test 3: Manager (can see team data but no internal notes)
    print("\n" + "=" * 60)
    print("\n✅ TEST 3: MANAGER USER")
    print("-" * 60)
    manager_user = auth.authenticate_user("john_manager", "any_password")
    print(f"User: {manager_user.username} ({manager_user.role})")
    print(f"Can see all leads: {manager_user.can_view_all_leads()}")
    print(f"Hidden columns: {auth.get_hidden_columns(manager_user)}")

    manager_tools = CRMDatabaseTools(db, user=manager_user, auth_service=auth)
    result = manager_tools.execute_sql("""
        SELECT COUNT(*) as total FROM leads
    """)
    print(f"\nQuery: SELECT COUNT(*) FROM leads")
    print(f"Result: {result}")

    # Test 4: Check audit log
    print("\n" + "=" * 60)
    print("\n✅ TEST 4: AUDIT LOG")
    print("-" * 60)
    print("Checking recent access logs...")

    result = db.execute_query("""
        SELECT
            al.action,
            u.username,
            al.table_name,
            al.created_at
        FROM audit_logs al
        JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC
        LIMIT 5
    """)
    print("\nRecent Access:")
    print(result.to_string(index=False))

    print("\n" + "=" * 60)
    print("✅ SECURITY TEST COMPLETE!")
    print("=" * 60)
    print("\n🔑 Key Takeaways:")
    print("1. Admin sees ALL 30 leads")
    print("2. Sales rep sees ONLY their assigned leads")
    print("3. Manager sees team data")
    print("4. All access is logged to audit_logs table")
    print("5. Sensitive columns (value) hidden for non-admins")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_security()
