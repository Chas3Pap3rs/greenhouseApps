#!/usr/bin/env python3
"""
Setup script for SharePoint-enabled candidate database
Creates greenhouse_candidates_sp database with same structure as original
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

def log(message):
    """Simple logging"""
    print(f"[SETUP] {message}")

def setup_sharepoint_database():
    """Create the SharePoint-enabled candidate database"""
    load_dotenv()
    
    # Database configurations
    source_db = os.getenv("SOURCE_PGDATABASE", "greenhouse_candidates")
    target_db = os.getenv("PGDATABASE", "greenhouse_candidates_sp")
    
    pg_config = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": int(os.getenv("PGPORT", "5432")),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD", "")
    }
    
    log(f"Setting up SharePoint database: {target_db}")
    log(f"Source database: {source_db}")
    
    try:
        # Connect to PostgreSQL server (not specific database)
        server_config = pg_config.copy()
        server_config["dbname"] = "postgres"
        
        conn = psycopg2.connect(**server_config)
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                # Create database if it doesn't exist
                cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{target_db}'")
                if not cur.fetchone():
                    cur.execute(f'CREATE DATABASE "{target_db}"')
                    log(f"Created database: {target_db}")
                else:
                    log(f"Database already exists: {target_db}")
        finally:
            conn.close()
        
        # Connect to target database and create schema
        target_config = pg_config.copy()
        target_config["dbname"] = target_db
        
        with psycopg2.connect(**target_config) as conn:
            with conn.cursor() as cur:
                # Create schema
                cur.execute("CREATE SCHEMA IF NOT EXISTS gh")
                
                # Create candidates table (same structure as original)
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS gh.candidates (
                    candidate_id        BIGINT PRIMARY KEY,
                    first_name          TEXT,
                    last_name           TEXT,
                    full_name           TEXT,
                    email               TEXT,
                    phone_numbers       TEXT,
                    addresses           TEXT,
                    created_at          TIMESTAMPTZ,
                    updated_at          TIMESTAMPTZ,
                    
                    -- Resume fields (will contain SharePoint links)
                    resume_links        TEXT[],
                    resume_filenames    TEXT[],
                    
                    -- Education and employment (parallel arrays)
                    degrees             TEXT[],
                    employment_titles   TEXT[],
                    employment_companies TEXT[],
                    
                    -- Job applications
                    jobs_name           TEXT[],
                    
                    -- Raw JSON (updated with SharePoint links)
                    raw                 JSONB
                );
                """
                
                cur.execute(create_table_sql)
                
                # Create indexes for performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_sp_candidates_id ON gh.candidates (candidate_id)",
                    "CREATE INDEX IF NOT EXISTS idx_sp_candidates_email ON gh.candidates (email)",
                    "CREATE INDEX IF NOT EXISTS idx_sp_candidates_updated ON gh.candidates (updated_at)",
                    "CREATE INDEX IF NOT EXISTS idx_sp_candidates_resume_links ON gh.candidates USING GIN (resume_links)",
                ]
                
                for index_sql in indexes:
                    cur.execute(index_sql)
                
                # Create mapping audit table
                audit_table_sql = """
                CREATE TABLE IF NOT EXISTS gh.sharepoint_mapping_audit (
                    candidate_id        BIGINT PRIMARY KEY,
                    original_resume_url TEXT,
                    sharepoint_url      TEXT,
                    sharepoint_filename TEXT,
                    local_file_path     TEXT,
                    mapping_status      TEXT DEFAULT 'pending',  -- 'success', 'failed', 'no_resume'
                    error_message       TEXT,
                    mapped_at           TIMESTAMPTZ DEFAULT NOW(),
                    
                    FOREIGN KEY (candidate_id) REFERENCES gh.candidates(candidate_id) ON DELETE CASCADE
                );
                """
                
                cur.execute(audit_table_sql)
                
                # Create index for audit table
                cur.execute("CREATE INDEX IF NOT EXISTS idx_sp_audit_status ON gh.sharepoint_mapping_audit (mapping_status)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_sp_audit_mapped_at ON gh.sharepoint_mapping_audit (mapped_at)")
                
            conn.commit()
            log("SharePoint database schema created successfully")
        
        return True
        
    except Exception as e:
        log(f"Error setting up SharePoint database: {e}")
        return False

def verify_setup():
    """Verify the SharePoint database was created correctly"""
    load_dotenv()
    
    target_db = os.getenv("PGDATABASE", "greenhouse_candidates_sp")
    pg_config = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": int(os.getenv("PGPORT", "5432")),
        "dbname": target_db,
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD", "")
    }
    
    try:
        with psycopg2.connect(**pg_config) as conn:
            with conn.cursor() as cur:
                # Check if tables exist
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'gh' 
                    AND table_name IN ('candidates', 'sharepoint_mapping_audit')
                    ORDER BY table_name;
                """)
                tables = [row[0] for row in cur.fetchall()]
                
                expected_tables = ['candidates', 'sharepoint_mapping_audit']
                missing_tables = set(expected_tables) - set(tables)
                
                if missing_tables:
                    log(f"ERROR: Missing tables: {', '.join(missing_tables)}")
                    return False
                
                # Check table structure
                cur.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_schema = 'gh' AND table_name = 'candidates'
                    ORDER BY ordinal_position;
                """)
                columns = [row[0] for row in cur.fetchall()]
                
                required_columns = [
                    'candidate_id', 'full_name', 'email', 'resume_links', 
                    'resume_filenames', 'raw'
                ]
                
                missing_columns = set(required_columns) - set(columns)
                if missing_columns:
                    log(f"ERROR: Missing columns: {', '.join(missing_columns)}")
                    return False
                
                log("SharePoint database verification passed")
                log(f"Tables created: {', '.join(tables)}")
                log(f"Columns in candidates table: {len(columns)}")
        
        return True
        
    except Exception as e:
        log(f"Error verifying setup: {e}")
        return False

def main():
    """Main setup function"""
    log("Setting up SharePoint-enabled candidate database...")
    
    if not setup_sharepoint_database():
        sys.exit(1)
    
    if not verify_setup():
        sys.exit(1)
    
    log("Setup completed successfully!")
    log("Next steps:")
    log("1. Update .env with Azure App Registration credentials")
    log("2. Run: python map_sharepoint_links.py")

if __name__ == "__main__":
    main()
