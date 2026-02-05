#!/usr/bin/env python3
"""
Check AI Database Status

This script checks the actual data in greenhouse_candidates_ai to verify
what fields are populated for the latest candidates.
"""

import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PG_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", ""),
    "dbname": "greenhouse_candidates_ai"
}

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_ai_database():
    """Check the status of fields in AI database"""
    
    log("="*60)
    log("AI Database Field Status Check")
    log("="*60)
    log("")
    
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    try:
        # Get overall statistics
        log("Overall Statistics:")
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(resume_content) as has_content,
                COUNT(addresses) as has_addresses,
                COUNT(updated_at) as has_updated,
                COUNT(resume_links) as has_resume_links,
                COUNT(resume_filenames) as has_filename,
                COUNT(ai_access_links) as has_ai_links
            FROM gh.candidates
        """)
        
        stats = cur.fetchone()
        log(f"Total candidates: {stats[0]:,}")
        log(f"With resume_content: {stats[1]:,} ({stats[1]/stats[0]*100:.1f}%)")
        log(f"With addresses: {stats[2]:,} ({stats[2]/stats[0]*100:.1f}%)")
        log(f"With updated_at: {stats[3]:,} ({stats[3]/stats[0]*100:.1f}%)")
        log(f"With resume_links: {stats[4]:,} ({stats[4]/stats[0]*100:.1f}%)")
        log(f"With resume_filename: {stats[5]:,} ({stats[5]/stats[0]*100:.1f}%)")
        log(f"With ai_access_links: {stats[6]:,} ({stats[6]/stats[0]*100:.1f}%)")
        log("")
        
        # Check latest 20 candidates
        log("Latest 20 Candidates (by candidate_id):")
        log("-" * 60)
        cur.execute("""
            SELECT 
                candidate_id,
                first_name,
                last_name,
                resume_filenames,
                CASE WHEN resume_content IS NOT NULL THEN 'YES' ELSE 'NULL' END as has_content,
                CASE WHEN addresses IS NOT NULL THEN 'YES' ELSE 'NULL' END as has_addresses,
                CASE WHEN updated_at IS NOT NULL THEN 'YES' ELSE 'NULL' END as has_updated,
                CASE WHEN resume_links IS NOT NULL THEN 'YES' ELSE 'NULL' END as has_resume_links,
                CASE WHEN ai_access_links IS NOT NULL THEN 'YES' ELSE 'NULL' END as has_ai_links
            FROM gh.candidates
            ORDER BY candidate_id DESC
            LIMIT 20
        """)
        
        results = cur.fetchall()
        for row in results:
            log(f"ID: {row[0]} | {row[1]} {row[2]}")
            log(f"  Filename: {row[3]}")
            log(f"  Content: {row[4]} | Addresses: {row[5]} | Updated: {row[6]}")
            log(f"  Resume Links: {row[7]} | AI Links: {row[8]}")
            log("")
        
        # Check candidates with filenames but no content
        log("Candidates with resume_filenames but NULL resume_content:")
        cur.execute("""
            SELECT COUNT(*)
            FROM gh.candidates
            WHERE resume_filenames IS NOT NULL
            AND resume_content IS NULL
        """)
        no_content_count = cur.fetchone()[0]
        log(f"Count: {no_content_count:,}")
        log("")
        
        # Sample 5 of these candidates
        log("Sample 5 candidates with filename but no content:")
        cur.execute("""
            SELECT 
                candidate_id,
                first_name,
                last_name,
                resume_filenames
            FROM gh.candidates
            WHERE resume_filenames IS NOT NULL
            AND resume_content IS NULL
            ORDER BY candidate_id DESC
            LIMIT 5
        """)
        
        samples = cur.fetchall()
        for row in samples:
            log(f"  {row[0]} | {row[1]} {row[2]} | {row[3]}")
        
        log("")
        log("="*60)
        
    except Exception as e:
        log(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_ai_database()
