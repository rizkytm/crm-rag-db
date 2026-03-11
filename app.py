import os
import streamlit as st
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from db_connection import CRMDatabase
from crm_agent import CRMDatabaseTools

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="CRM Leads Assistant",
    page_icon="👥",
    layout="wide"
)

# add comment


# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .query-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">👥 CRM Leads Assistant</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    st.subheader("Database Connection")
    db_user = st.text_input("DB User", value=os.getenv("DB_USER", "postgres"))
    db_password = st.text_input("DB Password", value=os.getenv("DB_PASSWORD", "postgres"), type="password")
    db_host = st.text_input("DB Host", value=os.getenv("DB_HOST", "localhost"))
    db_port = st.text_input("DB Port", value=os.getenv("DB_PORT", "5432"))
    db_name = st.text_input("DB Name", value=os.getenv("DB_NAME", "crm_db"))

    st.subheader("OpenAI API")
    openai_key = st.text_input("OpenAI API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")

    if st.button("Save Configuration"):
        os.environ["DB_USER"] = db_user
        os.environ["DB_PASSWORD"] = db_password
        os.environ["DB_HOST"] = db_host
        os.environ["DB_PORT"] = db_port
        os.environ["DB_NAME"] = db_name
        os.environ["OPENAI_API_KEY"] = openai_key
        st.success("✅ Configuration saved!")

    st.markdown("---")
    st.markdown("### Example Queries:")
    st.markdown("""
    - "Show me 10 latest leads"
    - "How many leads by status?"
    - "Leads from company Google"
    - "New leads this week"
    - "Leads by source"
    """)

# Initialize database connection
@st.cache_resource
def init_database():
    """Initialize database connection"""
    try:
        db = CRMDatabase()
        return db
    except Exception as e:
        st.error(f"❌ Failed to connect to database: {e}")
        return None

# Initialize agent
# Note: We use caching to avoid re-initializing the agent on every interaction, which can be expensive.
@st.cache_resource
def init_agent(_db_connection, openai_api_key):
    """Initialize CRM agent"""
    if not openai_api_key:
        return None

    crm_tools = CRMDatabaseTools(_db_connection)

    agent = Agent(
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        tools=[crm_tools],
        system_message="""You are a helpful CRM assistant that helps users query and analyze leads data from a PostgreSQL database.

Database Information:
- Table name: 'leads'
- This is a CRM leads database with customer information

Your capabilities:
- You can execute SQL queries using the execute_sql tool
- You can get table schema information using get_table_schema tool
- You can get column information and sample data using get_column_info tool

Guidelines:
1. When users ask questions about leads, use the execute_sql tool to query the database
2. Always retrieve the latest data first (ORDER BY created_at DESC) when looking for "latest" leads
3. Use LIMIT to restrict results when appropriate (e.g., "show me 10 leads")
4. For counting questions, use COUNT(*) and GROUP BY
5. For filtering, use WHERE clauses with appropriate conditions
6. Format your responses in a clear, friendly manner with the data presented nicely
7. If you're unsure about column names, use get_table_schema first

Example queries you can generate:
- "SELECT * FROM leads ORDER BY created_at DESC LIMIT 10"
- "SELECT status, COUNT(*) as count FROM leads GROUP BY status ORDER BY count DESC"
- "SELECT * FROM leads WHERE company ILIKE '%google%' ORDER BY created_at DESC"
- "SELECT source, COUNT(*) as count FROM leads GROUP BY source ORDER BY count DESC"

Always explain what query you're executing and present results in a user-friendly way.""",
        markdown=True,
    )

    return agent

# Main app
def main():
    # Check for API key
    if not openai_key:
        st.warning("⚠️ Please enter your OpenAI API key in the sidebar to continue.")
        return

    # Initialize database
    db = init_database()
    if not db:
        st.error("❌ Could not connect to database. Please check your configuration in the sidebar.")
        return

    # Initialize agent
    agent = init_agent(db, openai_key)
    if not agent:
        st.error("❌ Could not initialize agent. Please check your OpenAI API key.")
        return

    # Test database connection
    try:
        schema = agent.run("What is the schema of the leads table?")
        st.success("✅ Connected to database successfully!")

        # Show table info in expander
        with st.expander("📊 Database Schema"):
            st.markdown(schema.content if hasattr(schema, 'content') else str(schema))

    except Exception as e:
        st.error(f"❌ Error querying database: {e}")
        return

    st.markdown("---")

    # Query interface
    col1, col2 = st.columns([4, 1])

    with col1:
        user_query = st.text_area(
            "💬 Ask about your CRM leads:",
            placeholder="e.g., Show me 10 latest leads",
            height=100,
            label_visibility="collapsed"
        )

    with col2:
        st.write("")
        st.write("")
        submit_button = st.button("🔍 Search", use_container_width=True, type="primary")

    if submit_button:
        if not user_query.strip():
            st.warning("⚠️ Please enter a query.")
        else:
            try:
                with st.spinner("🔄 Analyzing your query and fetching data..."):
                    # Get response from agent
                    response = agent.run(user_query)

                    # Display response
                    st.markdown("### 📋 Results")
                    st.markdown("---")

                    if hasattr(response, 'content'):
                        st.markdown(response.content)
                    else:
                        st.markdown(str(response))

            except Exception as e:
                st.error(f"❌ Error processing query: {e}")

    # Quick action buttons
    # st.markdown("---")
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📊 Latest 10 Leads", use_container_width=True):
            query = "Show me the 10 latest leads"
            with st.spinner("Fetching..."):
                response = agent.run(query)
                st.markdown(response.content if hasattr(response, 'content') else str(response))

    with col2:
        if st.button("📈 Leads by Status", use_container_width=True):
            query = "Show me a count of leads grouped by status"
            with st.spinner("Fetching..."):
                response = agent.run(query)
                st.markdown(response.content if hasattr(response, 'content') else str(response))

    with col3:
        if st.button("🏢 Leads by Source", use_container_width=True):
            query = "Show me a count of leads grouped by source"
            with st.spinner("Fetching..."):
                response = agent.run(query)
                st.markdown(response.content if hasattr(response, 'content') else str(response))

    with col4:
        if st.button("🆕 New Leads Today", use_container_width=True):
            query = "Show me leads created today"
            with st.spinner("Fetching..."):
                response = agent.run(query)
                st.markdown(response.content if hasattr(response, 'content') else str(response))

if __name__ == "__main__":
    main()
