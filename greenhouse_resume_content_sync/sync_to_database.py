#!/usr/bin/env python3
"""
Sync resume_content from Greenhouse to PostgreSQL database

This script:
1. Adds resume_content column to greenhouse_candidates_ai database (if needed)
2. Fetches all candidates from Greenhouse API
3. Updates the database with resume_content field values
4. Provides progress tracking and summary

Run this after sync_resume_content.py and sync_from_sharepoint.py to populate
the database with resume content for AI agent access.
"""

import os
import sys
import requests
import base64
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Greenhouse API configuration
GREENHOUSE_API_KEY = os.getenv("GREENHOUSE_API_KEY")
GREENHOUSE_BASE_URL = "https://harvest.greenhouse.io/v1"

# Database configuration
DB_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': os.getenv('PGPORT', '5432'),
    'database': 'greenhouse_candidates_ai',
    'user': os.getenv('PGUSER'),
    'password': os.getenv('PGPASSWORD')
}

if not GREENHOUSE_API_KEY:
    print("ERROR: GREENHOUSE_API_KEY not found in .env file")
    sys.exit(1)

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def get_greenhouse_headers():
    """Get headers for Greenhouse API requests"""
    auth_string = f"{GREENHOUSE_API_KEY}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    return {"Authorization": f"Basic {encoded_auth}"}

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        log(f"❌ Database connection error: {e}")
        sys.exit(1)

def add_resume_content_column(conn):
    """Add resume_content column to candidates table if it doesn't exist"""
    try:
        with conn.cursor() as cur:
            # Check if column exists
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'gh' 
                AND table_name = 'candidates' 
                AND column_name = 'resume_content'
            """)
            
            if cur.fetchone():
                log("✅ resume_content column already exists")
                return
            
            # Add column
            log("Adding resume_content column to database...")
            cur.execute("""
                ALTER TABLE gh.candidates 
                ADD COLUMN resume_content TEXT
            """)
            
            # Add index for faster searches
            cur.execute("""
                CREATE INDEX idx_candidates_resume_content 
                ON gh.candidates USING gin(to_tsvector('english', resume_content))
            """)
            
            conn.commit()
            log("✅ Added resume_content column with full-text search index")
            
    except Exception as e:
        log(f"❌ Error adding column: {e}")
        conn.rollback()
        sys.exit(1)

def fetch_all_candidates():
    """Fetch all candidates from Greenhouse API"""
    log("Fetching candidates from Greenhouse API...")
    
    all_candidates = []
    page = 1
    
    while True:
        try:
            response = requests.get(
                f"{GREENHOUSE_BASE_URL}/candidates",
                headers=get_greenhouse_headers(),
                params={"per_page": 500, "page": page},
                timeout=30
            )
            response.raise_for_status()
            candidates = response.json()
            
            if not candidates:
                break
            
            all_candidates.extend(candidates)
            
            if page % 10 == 0:
                log(f"  Fetched page {page}: {len(all_candidates):,} candidates so far...")
            
            page += 1
            
            if len(candidates) < 500:
                break
                
        except Exception as e:
            log(f"❌ Error fetching page {page}: {e}")
            break
    
    log(f"✅ Fetched {len(all_candidates):,} candidates from Greenhouse")
    return all_candidates

def update_database(conn, candidates):
    """Update database with resume_content from candidates"""
    log("")
    log("Updating database with resume_content...")
    log("")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        with conn.cursor() as cur:
            for i, candidate in enumerate(candidates, 1):
                candidate_id = candidate.get('id')
                custom_fields = candidate.get('custom_fields', {})
                resume_content = custom_fields.get('resume_content')
                
                # Progress update every 1000 candidates
                if i % 1000 == 0:
                    log(f"  Progress: {i:,}/{len(candidates):,} ({i/len(candidates)*100:.1f}%)")
                    log(f"    Updated: {updated_count:,} | Skipped: {skipped_count:,} | Errors: {error_count:,}")
                
                # Skip if no resume content
                if not resume_content or not resume_content.strip():
                    skipped_count += 1
                    continue
                
                try:
                    # Update database
                    cur.execute("""
                        UPDATE gh.candidates 
                        SET resume_content = %s 
                        WHERE candidate_id = %s
                    """, (resume_content, candidate_id))
                    
                    if cur.rowcount > 0:
                        updated_count += 1
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:  # Only log first 5 errors
                        log(f"  ⚠️  Error updating {candidate_id}: {e}")
            
            # Commit all updates
            conn.commit()
            
    except Exception as e:
        log(f"❌ Database update error: {e}")
        conn.rollback()
        return updated_count, skipped_count, error_count
    
    return updated_count, skipped_count, error_count

def main():
    """Main function"""
    log("="*70)
    log("SYNC RESUME CONTENT TO DATABASE")
    log("="*70)
    log("")
    
    # Connect to database
    log("Connecting to database...")
    conn = get_db_connection()
    log("✅ Connected to greenhouse_candidates_ai")
    log("")
    
    # Add column if needed
    add_resume_content_column(conn)
    log("")
    
    # Fetch candidates from Greenhouse
    candidates = fetch_all_candidates()
    log("")
    
    # Update database
    updated, skipped, errors = update_database(conn, candidates)
    
    # Close connection
    conn.close()
    
    # Final summary
    log("")
    log("="*70)
    log("SYNC SUMMARY")
    log("="*70)
    log(f"Total candidates processed: {len(candidates):,}")
    log(f"✅ Updated with resume_content: {updated:,}")
    log(f"⏭️  Skipped (no content): {skipped:,}")
    log(f"❌ Errors: {errors:,}")
    log("")
    
    if updated > 0:
        log(f"🎉 Successfully synced {updated:,} candidates to database!")
        log("")
        log("Next step: Run export_ai_access_csv.py to update the CSV file")
    
    log("="*70)

if __name__ == "__main__":
    main()
