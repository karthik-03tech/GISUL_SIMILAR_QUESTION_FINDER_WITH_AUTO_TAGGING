import os
import sys
import psycopg2
from psycopg2 import sql

# The connection string template provided
CONNECTION_TEMPLATE = "postgresql://postgres.ansfukdcmakkayoztrux:{}@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"

def main():
    print("=" * 60)
    print("Supabase PostgreSQL Database Setup Script")
    print("=" * 60)

    # 1. Get the password
    password = os.environ.get("SUPABASE_DB_PASSWORD")
    if not password:
        if len(sys.argv) > 1:
            password = sys.argv[1]
        else:
            print("Please enter your Supabase database password:")
            try:
                # Use input() to get the password
                password = input("> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nSetup cancelled.")
                sys.exit(1)
    
    if not password:
        print("Error: Password cannot be empty.")
        sys.exit(1)

    # 2. Build the final connection string
    connection_string = CONNECTION_TEMPLATE.format(password)

    print("\nConnecting to Supabase PostgreSQL database...")
    try:
        conn = psycopg2.connect(connection_string)
        # Enable autocommit so that CREATE DATABASE / CREATE EXTENSION operations run correctly
        conn.autocommit = True
        cursor = conn.cursor()
        print("Successfully connected to the database!")
    except Exception as e:
        print(f"\nConnection failed! Error: {e}")
        print("\nPlease verify:")
        print("1. Your password is correct.")
        print("2. Your internet connection is active.")
        print("3. Supabase project is active and not paused.")
        sys.exit(1)

    # 3. Read and execute the schema file
    schema_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    if not os.path.exists(schema_file_path):
        print(f"\nError: Schema file not found at {schema_file_path}")
        sys.exit(1)

    print(f"\nReading database schema from '{schema_file_path}'...")
    with open(schema_file_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    print("Executing schema SQL queries...")
    try:
        # Split statements by semicolon to run them or execute all at once
        # psycopg2 allows executing multiple statements separated by semicolons in one execute() call
        cursor.execute(schema_sql)
        print("\nDatabase tables and extensions created successfully! 🎉")
        
        # Verify tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = cursor.fetchall()
        print("\nCreated tables in public schema:")
        for table in tables:
            print(f" - {table[0]}")
            
    except Exception as e:
        print(f"\nError executing SQL schema: {e}")
    finally:
        cursor.close()
        conn.close()
        print("\nDatabase connection closed.")
        print("=" * 60)

if __name__ == "__main__":
    main()
