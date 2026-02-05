#!/usr/bin/env python3
"""
Setup script for Greenhouse Candidates ETL

This script helps set up the database schema and verify the environment.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

def log(message):
    """Simple logging"""
    print(f"[SETUP] {message}")

def check_environment():
    """Check if all required environment variables are set"""
    load_dotenv()
    
    required_vars = [
        "PGHOST", "PGPORT", "PGDATABASE", "PGUSER", 
        "GREENHOUSE_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        log(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        log("Please check your .env file")
        return False
    
    log("Environment variables check passed")
    return True

def test_database_connection():
    """Test PostgreSQL connection"""
    load_dotenv()
    
    pg_config = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": int(os.getenv("PGPORT", "5432")),
        "dbname": os.getenv("PGDATABASE", "greenhouse_candidates"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD", "")
    }
    
    try:
        with psycopg2.connect(**pg_config) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                log(f"Database connection successful: {version}")
        return True
    except Exception as e:
        log(f"Database connection failed: {e}")
        return False

def setup_database_schema():
    """Create the database schema"""
    load_dotenv()
    
    pg_config = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": int(os.getenv("PGPORT", "5432")),
        "dbname": os.getenv("PGDATABASE", "greenhouse_candidates"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD", "")
    }
    
    schema_file = "schema.sql"
    if not os.path.exists(schema_file):
        log(f"ERROR: Schema file {schema_file} not found")
        return False
    
    try:
        with psycopg2.connect(**pg_config) as conn:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            
            conn.commit()
            log("Database schema created successfully")
        return True
    except Exception as e:
        log(f"Schema creation failed: {e}")
        return False

def verify_schema():
    """Verify that the schema was created correctly"""
    load_dotenv()
    
    pg_config = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": int(os.getenv("PGPORT", "5432")),
        "dbname": os.getenv("PGDATABASE", "greenhouse_candidates"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD", "")
    }
    
    try:
        with psycopg2.connect(**pg_config) as conn:
            with conn.cursor() as cur:
                # Check if schema exists
                cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'gh';")
                if not cur.fetchone():
                    log("ERROR: Schema 'gh' not found")
                    return False
                
                # Check if table exists
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'gh' AND table_name = 'candidates';
                """)
                if not cur.fetchone():
                    log("ERROR: Table 'gh.candidates' not found")
                    return False
                
                # Check table structure
                cur.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_schema = 'gh' AND table_name = 'candidates'
                    ORDER BY ordinal_position;
                """)
                columns = [row[0] for row in cur.fetchall()]
                
                expected_columns = [
                    'candidate_id', 'first_name', 'last_name', 'full_name', 'email',
                    'phone_numbers', 'addresses', 'resume_links', 'resume_filenames',
                    'employment_titles', 'employment_companies', 'degrees', 'jobs_name',
                    'created_at', 'updated_at', 'raw'
                ]
                
                missing_columns = set(expected_columns) - set(columns)
                if missing_columns:
                    log(f"ERROR: Missing columns: {', '.join(missing_columns)}")
                    return False
                
                log("Schema verification passed")
        return True
    except Exception as e:
        log(f"Schema verification failed: {e}")
        return False

def main():
    """Main setup function"""
    log("Starting Greenhouse Candidates ETL setup...")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Test database connection
    if not test_database_connection():
        sys.exit(1)
    
    # Setup schema
    if not setup_database_schema():
        sys.exit(1)
    
    # Verify schema
    if not verify_schema():
        sys.exit(1)
    
    log("Setup completed successfully!")
    log("You can now run: python main.py")

if __name__ == "__main__":
    main()
