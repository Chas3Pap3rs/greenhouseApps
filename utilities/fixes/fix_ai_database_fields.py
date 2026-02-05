#!/usr/bin/env python3
"""
Fix AI Database Missing Fields

The AI database has 5,991 candidates with NULL fields for:
- degrees, employment_titles, employment_companies, jobs_name, raw

This script copies these missing fields from the main database to the AI database.
"""

import os
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

def fix_ai_database():
    """Fix missing fields in AI database"""
    log("="*80)
    log("FIX AI DATABASE MISSING FIELDS")
    log("="*80)
    log("")
    
    conn_main = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates"})
    conn_ai = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates_ai"})
    
    cur_main = conn_main.cursor()
    cur_ai = conn_ai.cursor()
    
    try:
        # Find candidates with NULL raw field in AI database
        log("Finding candidates with missing fields in AI database...")
        cur_ai.execute("""
            SELECT candidate_id
            FROM gh.candidates
            WHERE raw IS NULL
            ORDER BY candidate_id
        """)
        
        null_candidates = [row[0] for row in cur_ai.fetchall()]
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
                # Update AI database with missing fields
                cur_ai.execute("""
                    UPDATE gh.candidates
                    SET 
                        degrees = %s,
                        employment_titles = %s,
                        employment_companies = %s,
                        jobs_name = %s,
                        raw = %s
                    WHERE candidate_id = %s
                """, (
                    row[0],  # degrees
                    row[1],  # employment_titles
                    row[2],  # employment_companies
                    row[3],  # jobs_name
                    Json(row[4]) if row[4] is not None else None,  # raw (JSONB)
                    candidate_id
                ))
                
                updated += 1
                
                if updated % 100 == 0:
                    log(f"  Updated {updated:,}/{total:,} candidates...")
                    conn_ai.commit()
            else:
                failed += 1
                log(f"  ⚠️  Candidate {candidate_id} not found in main database")
        
        # Final commit
        conn_ai.commit()
        
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
        conn_ai.rollback()
        return False
    finally:
        cur_main.close()
        cur_ai.close()
        conn_main.close()
        conn_ai.close()

if __name__ == "__main__":
    success = fix_ai_database()
    if success:
        log("\n✅ AI database fields fixed successfully!")
    else:
        log("\n❌ Fix failed!")
