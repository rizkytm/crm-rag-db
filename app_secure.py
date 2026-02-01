import os
import streamlit as st
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from db_connection import CRMDatabase
from auth import AuthService
from crm_agent import CRMDatabaseTools

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="CRM Leads Assistant - Secure",
    page_icon="🔐",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .user-info {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .security-notice {
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for user
if 'user' not in st.session_state:
    st.session_state.user = None
if 'auth_service' not in st.session_state:
    st.session_state.auth_service = None
if 'db' not in st.session_state:
    st.session_state.db = None

# =============== LOGIN PAGE ===============
def show_login_page():
    """Display login page"""
    st.markdown('<div class="main-header">🔐 CRM Leads Assistant</div>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Login")
        st.markdown("Enter your credentials to access the CRM system")

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g., admin, manager, sales, viewer")
            password = st.text_input("Password", type="password", help="For demo, any password works")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")

            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    # Initialize database and auth service
                    try:
                        db = CRMDatabase()
                        auth_service = AuthService(db)

                        # Authenticate user
                        user = auth_service.authenticate_user(username, password)

                        if user:
                            # Store in session state
                            st.session_state.user = user
                            st.session_state.auth_service = auth_service
                            st.session_state.db = db
                            st.success(f"✅ Welcome, {user.full_name}!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")

                    except Exception as e:
                        st.error(f"❌ Error connecting to database: {e}")

        st.markdown("---")
        st.markdown("### Demo Accounts")
        st.markdown("""
        | Username | Role | Access |
        |----------|------|--------|
        | `admin` | Administrator | All data |
        | `manager` | Manager | Team data |
        | `sales` | Sales Rep | Own leads only |
        | `viewer` | Viewer | Read-only own leads |
        """)

        st.info("💡 **Note**: For this demo, any password will work!")

# =============== MAIN APP ===============
def show_main_app():
    """Display main application after login"""
    user = st.session_state.user
    auth_service = st.session_state.auth_service
    db = st.session_state.db

    # Header with user info
    st.markdown('<div class="main-header">🔐 CRM Leads Assistant</div>', unsafe_allow_html=True)

    # User info bar
    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])

    with col1:
        st.markdown(f"👤 **{user.full_name}**")
    with col2:
        st.markdown(f"🏷️ `{user.role}`")
    with col3:
        if user.can_view_all_leads():
            st.markdown("🌐 **Team Access**")
        else:
            st.markdown("🔒 **Personal Access**")
    with col4:
        if user.is_admin():
            st.markdown("👑 **Administrator**")
    with col5:
        if st.button("🚪 Logout", use_container_width=True):
            # Clear session state
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

    st.markdown("---")

    # Security notice for non-admins
    if not user.can_view_all_leads():
        st.markdown('<div class="security-notice">🔒 <strong>Security Notice:</strong> You can only view your assigned leads. Your queries are automatically filtered.</div>', unsafe_allow_html=True)
        st.markdown("")

    # Sidebar
    with st.sidebar:
        st.header(f"👤 {user.full_name}")
        st.markdown(f"**Role:** {user.role}")

        st.markdown("---")

        # Show permissions
        st.subheader("🔑 Your Permissions")
        if user.is_admin():
            st.success("✅ View all leads")
            st.success("✅ See all fields")
            st.success("✅ Export data")
        elif user.role == 'manager':
            st.success("✅ View team leads")
            st.warning("⚠️ Internal notes hidden")
            st.success("✅ Export data")
        elif user.role == 'sales_rep':
            st.error("❌ Only assigned leads")
            st.error("❌ Deal value hidden")
            st.error("❌ Cannot export")
        else:  # viewer
            st.error("❌ Only assigned leads")
            st.error("❌ Read-only")
            st.error("❌ Cannot export")

        st.markdown("---")

        # Quick stats
        st.subheader("📊 Quick Stats")
        try:
            # Get user's lead count
            if user.can_view_all_leads():
                total_result = db.execute_query("SELECT COUNT(*) as count FROM leads")
            else:
                total_result = db.execute_query(f"""
                    SELECT COUNT(*) as count
                    FROM leads
                    WHERE id IN (SELECT lead_id FROM lead_assignments WHERE user_id = {user.id})
                    OR owner_id = {user.id}
                """)

            st.metric("Your Leads", total_result['count'][0])
        except:
            st.metric("Your Leads", "N/A")

        st.markdown("---")

        # Example queries
        st.subheader("💬 Example Queries")
        st.markdown("""
        - "Show me my latest leads"
        - "How many leads by status?"
        - "Leads from website source"
        - "My leads this week"
        """)

        # Admin: Audit log viewer
        if user.is_admin():
            st.markdown("---")
            st.subheader("📋 Audit Log")

            if st.button("Show Recent Activity"):
                try:
                    audit_data = db.execute_query("""
                        SELECT
                            al.action,
                            u.username,
                            al.table_name,
                            al.created_at
                        FROM audit_logs al
                        JOIN users u ON al.user_id = u.id
                        ORDER BY al.created_at DESC
                        LIMIT 20
                    """)

                    st.dataframe(audit_data, use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading audit log: {e}")

    # Initialize agent with security
    @st.cache_resource
    def init_secure_agent(_db_connection, _user, _auth_service, openai_api_key):
        """Initialize CRM agent with security"""
        if not openai_api_key:
            return None

        # Create tools WITH security
        crm_tools = CRMDatabaseTools(
            db_connection=_db_connection,
            user=_user,
            auth_service=_auth_service
        )

        # Update system message based on user role
        if _user.can_view_all_leads():
            system_msg = f"""You are a helpful CRM assistant helping {_user.full_name} (role: {_user.role}) query and analyze leads data.

The user has access to ALL leads in the database.

Available tools:
- execute_sql: ⭐ PRIMARY TOOL - Run SQL queries on the leads table (use for 90% of queries)
- my_leads: Quick way to see latest 20 leads (good for "show me my leads" requests)
- team_leads: Show team leads (managers and admins)
- get_table_schema: Get table structure
- get_column_info: Get column details

Guidelines:
1. ⭐ PRIORITY: Use execute_sql for most queries including:
   - Searching for specific leads ("show me lead named Diana Baker")
   - Filtering ("leads from company Cloudify")
   - Analytics ("leads by status")
   - Any query with WHERE, GROUP BY, etc.
2. Use my_leads ONLY for generic "show me leads" or "show me my latest leads" requests
3. Be helpful and efficient
4. Explain what queries you're running
5. Present results in a clear, friendly manner
6. Use markdown for formatting

Examples:
- "Show me lead named Diana Baker" → execute_sql with "SELECT * FROM leads WHERE name LIKE '%Diana%'"
- "Show me my leads" → my_leads tool
- "Leads from Cloudify" → execute_sql with "SELECT * FROM leads WHERE company = 'Cloudify'"
- "Leads by status" → execute_sql with "SELECT status, COUNT(*) FROM leads GROUP BY status"
"""
        else:
            system_msg = f"""You are a helpful CRM assistant helping {_user.full_name} (role: {_user.role}) query and analyze leads data.

IMPORTANT SECURITY NOTICE:
The user can ONLY see leads assigned to them or that they own.
All queries are automatically filtered for security.

Available tools:
- my_leads: ⭐ BEST CHOICE for simple queries like "show me my leads" - automatically shows your assigned leads
- execute_sql: Run SQL queries (automatically filtered to show only your leads) - use for complex queries only
- get_table_schema: Get table structure
- get_column_info: Get column details

Guidelines:
1. ⭐ PRIORITY: For "show me my leads" or simple listing queries, ALWAYS use the my_leads tool first
2. Only use execute_sql for complex queries with specific filters (WHERE, GROUP BY, etc.)
3. Be helpful and efficient
4. Mention that results are filtered to show only their leads
5. Present results in a clear, friendly manner
6. Use markdown for formatting

Examples:
- "show me my leads" → Use my_leads tool
- "my leads by status" → Use execute_sql with "SELECT status, COUNT(*) FROM leads GROUP BY status"
- "leads from website" → Use execute_sql with "SELECT * FROM leads WHERE source = 'website'"
"""

        agent = Agent(
            model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
            tools=[crm_tools],
            system_message=system_msg,
            markdown=True,
        )

        return agent

    # Get OpenAI key
    openai_key = os.getenv("OPENAI_API_KEY", "")

    if not openai_key:
        st.error("⚠️ OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.")
        return

    # Initialize agent
    agent = init_secure_agent(db, user, auth_service, openai_key)

    if not agent:
        st.error("❌ Could not initialize agent. Please check your OpenAI API key.")
        return

    # Test connection
    try:
        schema = agent.run("What is the schema of the leads table?")
        st.success("✅ Connected to database successfully!")

        # Show table info in expander
        with st.expander("📊 Database Schema"):
            st.markdown(schema.content if hasattr(schema, 'content') else str(schema))

    except Exception as e:
        st.error(f"❌ Error: {e}")
        return

    st.markdown("---")

    # Query interface - using form for better button behavior
    with st.form("query_form", clear_on_submit=False):
        user_query = st.text_area(
            "💬 Ask about your CRM leads:",
            placeholder="e.g., Show me my latest leads",
            height=100,
            label_visibility="collapsed",
            help="Press the Search button or click outside and click Search"
        )
        submit_button = st.form_submit_button("🔍 Search", use_container_width=True, type="primary")

    if submit_button and user_query and user_query.strip():
        try:
            with st.spinner("🔄 Analyzing your query and fetching data..."):
                response = agent.run(user_query)

            st.markdown("### 📋 Results")
            st.markdown("---")

            if hasattr(response, 'content'):
                st.markdown(response.content)
            else:
                st.markdown(str(response))

        except Exception as e:
            st.error(f"❌ Error processing query: {e}")
    elif submit_button:
        st.warning("⚠️ Please enter a query.")

    # Quick action buttons
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📊 My Latest Leads", use_container_width=True):
            query = "Show me my 10 latest leads with name, company, and status"
            with st.spinner("Fetching..."):
                response = agent.run(query)
                st.markdown(response.content if hasattr(response, 'content') else str(response))

    with col2:
        if st.button("📈 My Leads by Status", use_container_width=True):
            query = "Show me a count of my leads grouped by status"
            with st.spinner("Fetching..."):
                response = agent.run(query)
                st.markdown(response.content if hasattr(response, 'content') else str(response))

    with col3:
        if st.button("🏢 My Leads by Source", use_container_width=True):
            query = "Show me a count of my leads grouped by source"
            with st.spinner("Fetching..."):
                response = agent.run(query)
                st.markdown(response.content if hasattr(response, 'content') else str(response))

    with col4:
        if user.can_view_all_leads():
            if st.button("👥 Team Overview", use_container_width=True):
                query = "Show me total leads, leads by status, and leads by source for the entire team"
                with st.spinner("Fetching..."):
                    response = agent.run(query)
                    st.markdown(response.content if hasattr(response, 'content') else str(response))
        else:
            if st.button("🆕 My New Leads", use_container_width=True):
                query = "Show me my leads with status 'new'"
                with st.spinner("Fetching..."):
                    response = agent.run(query)
                    st.markdown(response.content if hasattr(response, 'content') else str(response))


# =============== MAIN LOGIC ===============
def main():
    # Check if user is logged in
    if st.session_state.user is None:
        show_login_page()
    else:
        show_main_app()


if __name__ == "__main__":
    main()
