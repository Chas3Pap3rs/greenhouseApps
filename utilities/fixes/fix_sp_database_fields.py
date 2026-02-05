#!/usr/bin/env python3
"""
Fix SharePoint Database Missing Fields

The SP database has 1,492 candidates with NULL fields because update_sharepoint_links.py
only inserted candidate_id, full_name, resume_links, and resume_filenames.

This script copies all missing fields from the main database to the SP database.
"""

import os
import json
import psycopg2
from psycopg2.extras import Json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PG_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def fix_sp_database():
    """Fix missing fields in SP database"""
    log("="*80)
    log("FIX SHAREPOINT DATABASE MISSING FIELDS")
    log("="*80)
    log("")
    
    conn_main = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates"})
    conn_sp = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates_sp"})
    
    cur_main = conn_main.cursor()
    cur_sp = conn_sp.cursor()
    
    try:
        # Find candidates with NULL first_name in SP database
        log("Finding candidates with missing fields in SP database...")
        cur_sp.execute("""
            SELECT candidate_id
            FROM gh.candidates
            WHERE first_name IS NULL
            ORDER BY candidate_id
        """)
        
        null_candidates = [row[0] for row in cur_sp.fetchall()]
        total = len(null_candidates)
        
        log(f"Found {total:,} candidates with missing fields")
        log("")
        
        if total == 0:
            log("✅ No candidates need fixing!")
            return True
        
        log("Copying missing fields from main database...")
        
        updated = 0
        failed = 0
        
        for idx, candidate_id in enumerate(null_candidates, 1):
            # Get full data from main database
            cur_main.execute("""
                SELECT 
                    first_name,
                    last_name,
                    email,
                    phone_numbers,
                    addresses,
                    created_at,
                    updated_at,
                    degrees,
                    employment_titles,
                    employment_companies,
                    jobs_name,
                    raw
                FROM gh.candidates
                WHERE candidate_id = %s
            """, (candidate_id,))
            
            row = cur_main.fetchone()
            
            if row:
                # Update SP database with all fields
                cur_sp.execute("""
                    UPDATE gh.candidates
                    SET 
                        first_name = %s,
                        last_name = %s,
                        email = %s,
                        phone_numbers = %s,
                        addresses = %s,
                        created_at = %s,
                        updated_at = %s,
                        degrees = %s,
                        employment_titles = %s,
                        employment_companies = %s,
                        jobs_name = %s,
                        raw = %s
                    WHERE candidate_id = %s
                """, (
                    row[0],  # first_name
                    row[1],  # last_name
                    row[2],  # email
                    row[3],  # phone_numbers
                    row[4],  # addresses
                    row[5],  # created_at
                    row[6],  # updated_at
                    row[7],  # degrees
                    row[8],  # employment_titles
                    row[9],  # employment_companies
                    row[10], # jobs_name
                    Json(row[11]) if row[11] is not None else None, # raw (JSONB)
                    candidate_id
                ))
                
                updated += 1
                
                if updated % 100 == 0:
                    log(f"  Updated {updated:,}/{total:,} candidates...")
                    conn_sp.commit()
            else:
                failed += 1
                log(f"  ⚠️  Candidate {candidate_id} not found in main database")
        
        # Final commit
        conn_sp.commit()
        
        log("")
        log("="*80)
        log("FIX SUMMARY")
        log("="*80)
        log(f"Total candidates processed: {total:,}")
        log(f"Successfully updated: {updated:,}")
        log(f"Failed: {failed:,}")
        log("="*80)
        
        return True
        
    except Exception as e:
        log(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn_sp.rollback()
        return False
    finally:
        cur_main.close()
        cur_sp.close()
        conn_main.close()
        conn_sp.close()

if __name__ == "__main__":
    success = fix_sp_database()
    if success:
        log("\n✅ SharePoint database fields fixed successfully!")
    else:
        log("\n❌ Fix failed!")
