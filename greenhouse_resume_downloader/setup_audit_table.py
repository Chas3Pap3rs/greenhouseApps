#!/usr/bin/env python3
"""
Setup script for resume download audit table
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

def log(message):
    """Simple logging"""
    print(f"[SETUP] {message}")

def setup_audit_table():
    """Create the resume download audit table"""
    load_dotenv()
    
    pg_config = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": int(os.getenv("PGPORT", "5432")),
        "dbname": os.getenv("PGDATABASE", "greenhouse_candidates"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD", "")
    }
    
    audit_table_sql = """
    CREATE TABLE IF NOT EXISTS gh.resume_download_audit (
      candidate_id        BIGINT PRIMARY KEY,
      attachment_url      TEXT,
      attachment_filename TEXT,
      attachment_created  TIMESTAMPTZ,
      saved_path          TEXT,
      download_status     TEXT DEFAULT 'success',  -- 'success', 'failed', 'skipped'
      error_message       TEXT,
      downloaded_at       TIMESTAMPTZ DEFAULT NOW(),
      file_size_bytes     BIGINT,
      
      -- Foreign key to candidates table
      FOREIGN KEY (candidate_id) REFERENCES gh.candidates(candidate_id) ON DELETE CASCADE
    );
    
    -- Index for quick lookups
    CREATE INDEX IF NOT EXISTS idx_resume_audit_status ON gh.resume_download_audit (download_status);
    CREATE INDEX IF NOT EXISTS idx_resume_audit_downloaded_at ON gh.resume_download_audit (downloaded_at);
    """
    
    try:
        with psycopg2.connect(**pg_config) as conn:
            with conn.cursor() as cur:
                cur.execute(audit_table_sql)
            conn.commit()
            log("Resume download audit table created successfully")
        return True
    except Exception as e:
        log(f"Error creating audit table: {e}")
        return False

def verify_setup():
    """Verify the audit table was created correctly"""
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
                # Check if table exists
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'gh' AND table_name = 'resume_download_audit';
                """)
                if not cur.fetchone():
                    log("ERROR: Audit table not found")
                    return False
                
                # Check table structure
                cur.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_schema = 'gh' AND table_name = 'resume_download_audit'
                    ORDER BY ordinal_position;
                """)
                columns = [row[0] for row in cur.fetchall()]
                
                expected_columns = [
                    'candidate_id', 'attachment_url', 'attachment_filename', 
                    'attachment_created', 'saved_path', 'download_status',
                    'error_message', 'downloaded_at', 'file_size_bytes'
                ]
                
                missing_columns = set(expected_columns) - set(columns)
                if missing_columns:
                    log(f"ERROR: Missing columns: {', '.join(missing_columns)}")
                    return False
                
                log("Audit table verification passed")
        return True
    except Exception as e:
        log(f"Error verifying setup: {e}")
        return False

def main():
    """Main setup function"""
    log("Setting up resume download audit table...")
    
    if not setup_audit_table():
        sys.exit(1)
    
    if not verify_setup():
        sys.exit(1)
    
    log("Setup completed successfully!")
    log("You can now run: python download_resumes.py")

if __name__ == "__main__":
    main()
