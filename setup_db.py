"""
Setup script for CRM Leads Database
This script helps you initialize the PostgreSQL database
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import pandas as pd

# Load environment variables
load_dotenv()


def setup_database():
    """Setup database with schema and sample data"""
    print("🚀 Setting up CRM Leads Database...")
    print("=" * 50)

    try:
        # Get environment variables
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "crm_db_rag")

        # Connect to database
        print("\n📡 Connecting to PostgreSQL...")
        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

        engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )

        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        print("✅ Connected successfully!")

        # Read schema SQL
        schema_file = os.path.join(os.path.dirname(__file__), "schema.sql")
        if not os.path.exists(schema_file):
            print(f"❌ Error: schema.sql not found at {schema_file}")
            return False

        with open(schema_file, 'r') as f:
            sql_content = f.read()

        print("\n📊 Executing schema.sql...")

        # Execute SQL script using psycopg2 directly
        import psycopg2
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Execute the entire SQL script
        cursor.execute(sql_content)
        cursor.close()
        conn.close()

        print("✅ Schema executed successfully!")

        # Display summary
        print("\n📈 Database Summary:")
        print("-" * 50)

        # Total leads
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as total FROM leads"))
            total = result.fetchone()[0]
            print(f"Total leads: {total}")

            # Leads by status
            print("\nLeads by status:")
            result = conn.execute(text("SELECT status, COUNT(*) as count FROM leads GROUP BY status ORDER BY count DESC"))
            for row in result:
                print(f"  {row[0]}: {row[1]}")

            # Leads by source
            print("\nLeads by source:")
            result = conn.execute(text("SELECT source, COUNT(*) as count FROM leads GROUP BY source ORDER BY count DESC"))
            for row in result:
                print(f"  {row[0]}: {row[1]}")

            # Sample data
            print("\n📋 Sample leads data:")
            print("-" * 50)
            result = conn.execute(text("""
                SELECT id, name, email, company, status, source, created_at
                FROM leads
                ORDER BY created_at DESC
                LIMIT 5
            """))
            print(f"{'ID':<5} {'Name':<20} {'Email':<25} {'Company':<15} {'Status':<12} {'Source':<10}")
            print("-" * 95)
            for row in result:
                print(f"{row[0]:<5} {row[1]:<20} {row[2]:<25} {row[3]:<15} {row[4]:<12} {row[5]:<10}")

        print("\n" + "=" * 50)
        print("✅ Database setup completed successfully!")
        print("\n🎯 You can now run the application:")
        print("   streamlit run app.py")
        print("\n📝 Environment variables configured:")
        print(f"   DB_HOST: {db_host}")
        print(f"   DB_PORT: {db_port}")
        print(f"   DB_NAME: {db_name}")
        print(f"   DB_USER: {db_user}")

        return True

    except Exception as e:
        print(f"\n❌ Error setting up database: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure PostgreSQL is running")
        print("   2. Verify your database credentials in .env file")
        print(f"   3. Ensure the database exists: docker exec crm_postgres psql -U {os.getenv('DB_USER')} -d {os.getenv('DB_NAME')} -c 'SELECT 1'")
        return False


if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
