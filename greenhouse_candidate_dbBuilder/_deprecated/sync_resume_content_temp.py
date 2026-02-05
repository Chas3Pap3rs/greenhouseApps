#!/usr/bin/env python3
"""
TEMPORARY: Sync resume_content from greenhouse_candidates_ai to greenhouse_candidates

This is a one-time script to copy resume_content from the AI database to the dbBuilder database.
After this, we can export from dbBuilder with Greenhouse links + resume_content.

Future: Modify dbBuilder to fetch resume_content directly from Greenhouse API.

Usage:
    python sync_resume_content_temp.py
"""

import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Database configurations
PG_SOURCE = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": "greenhouse_candidates_ai",  # Source: has resume_content
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

PG_TARGET = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": "greenhouse_candidates",  # Target: dbBuilder database
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def add_resume_content_column():
    """Add resume_content column to greenhouse_candidates if it doesn't exist"""
    log("Checking if resume_content column exists in greenhouse_candidates...")
    
    with psycopg2.connect(**PG_TARGET) as conn:
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'gh' 
            AND table_name = 'candidates' 
            AND column_name = 'resume_content';
        """)
        
        if cursor.fetchone():
            log("✅ resume_content column already exists")
        else:
            log("Adding resume_content column...")
            cursor.execute("""
                ALTER TABLE gh.candidates 
                ADD COLUMN resume_content TEXT;
            """)
            conn.commit()
            log("✅ resume_content column added")
        
        cursor.close()

def sync_resume_content():
    """Copy resume_content from AI database to dbBuilder database"""
    log("="*70)
    log("TEMPORARY SYNC: Copying resume_content to dbBuilder database")
    log("="*70)
    log("")
    
    # First, add the column if needed
    add_resume_content_column()
    
    log("")
    log("Starting resume_content sync...")
    
    # Connect to both databases
    source_conn = psycopg2.connect(**PG_SOURCE)
    target_conn = psycopg2.connect(**PG_TARGET)
    
    try:
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        # Get count of candidates with resume_content in source
        source_cursor.execute("""
            SELECT COUNT(*) 
            FROM gh.candidates 
            WHERE resume_content IS NOT NULL AND resume_content != '';
        """)
        total_with_content = source_cursor.fetchone()[0]
        log(f"Source database has {total_with_content:,} candidates with resume_content")
        
        # Get all resume_content from source
        log("Fetching resume_content from AI database...")
        source_cursor.execute("""
            SELECT candidate_id, resume_content
            FROM gh.candidates
            WHERE resume_content IS NOT NULL AND resume_content != ''
            ORDER BY candidate_id;
        """)
        
        # Update target database in batches
        log("Updating dbBuilder database...")
        batch_size = 1000
        updated_count = 0
        batch = []
        
        for row in source_cursor:
            candidate_id, resume_content = row
            batch.append((resume_content, candidate_id))
            
            if len(batch) >= batch_size:
                target_cursor.executemany("""
                    UPDATE gh.candidates 
                    SET resume_content = %s 
                    WHERE candidate_id = %s;
                """, batch)
                target_conn.commit()
                updated_count += len(batch)
                log(f"  Updated {updated_count:,} / {total_with_content:,} candidates...")
                batch = []
        
        # Update remaining batch
        if batch:
            target_cursor.executemany("""
                UPDATE gh.candidates 
                SET resume_content = %s 
                WHERE candidate_id = %s;
            """, batch)
            target_conn.commit()
            updated_count += len(batch)
        
        log(f"✅ Updated {updated_count:,} candidates with resume_content")
        
        # Verify
        target_cursor.execute("""
            SELECT COUNT(*) 
            FROM gh.candidates 
            WHERE resume_content IS NOT NULL AND resume_content != '';
        """)
        final_count = target_cursor.fetchone()[0]
        
        log("")
        log("="*70)
        log("SYNC COMPLETE!")
        log("="*70)
        log(f"✅ dbBuilder database now has {final_count:,} candidates with resume_content")
        log("")
        log("🎯 Next steps:")
        log("   1. Run: python export_segmented.py")
        log("   2. This will export with Greenhouse links + resume_content")
        log("   3. Upload segments to Zapier Tables")
        log("")
        log("⚠️  NOTE: This is a temporary solution.")
        log("   Future: Modify dbBuilder to fetch resume_content from Greenhouse API")
        log("="*70)
        
        source_cursor.close()
        target_cursor.close()
        
    finally:
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    try:
        sync_resume_content()
    except Exception as e:
        log(f"❌ Error: {e}")
        raise
