#!/usr/bin/env python3
"""
Investigate NULL fields in databases for recent candidates
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

PG_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

def check_candidate(dbname, candidate_id):
    """Check a specific candidate's data"""
    print(f"\n{'='*80}")
    print(f"DATABASE: {dbname} | Candidate ID: {candidate_id}")
    print(f"{'='*80}")
    
    conn = psycopg2.connect(**{**PG_CONFIG, "dbname": dbname})
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            candidate_id,
            first_name,
            last_name,
            full_name,
            email,
            phone_numbers,
            addresses,
            created_at,
            updated_at,
            resume_links,
            resume_filenames,
            degrees,
            employment_titles,
            employment_companies,
            jobs_name,
            CASE WHEN raw IS NULL THEN 'NULL' ELSE 'HAS DATA' END as raw_status
        FROM gh.candidates
        WHERE candidate_id = %s
    """, (candidate_id,))
    
    row = cur.fetchone()
    
    if row:
        print(f"candidate_id: {row[0]}")
        print(f"first_name: {row[1]}")
        print(f"last_name: {row[2]}")
        print(f"full_name: {row[3]}")
        print(f"email: {row[4]}")
        print(f"phone_numbers: {row[5]}")
        print(f"addresses: {row[6]}")
        print(f"created_at: {row[7]}")
        print(f"updated_at: {row[8]}")
        print(f"resume_links: {row[9]}")
        print(f"resume_filenames: {row[10]}")
        print(f"degrees: {row[11]}")
        print(f"employment_titles: {row[12]}")
        print(f"employment_companies: {row[13]}")
        print(f"jobs_name: {row[14]}")
        print(f"raw: {row[15]}")
    else:
        print(f"❌ Candidate {candidate_id} NOT FOUND in {dbname}")
    
    cur.close()
    conn.close()

def check_recent_null_candidates(dbname):
    """Check how many recent candidates have NULL fields"""
    print(f"\n{'='*80}")
    print(f"DATABASE: {dbname} - Recent candidates with NULL fields")
    print(f"{'='*80}")
    
    conn = psycopg2.connect(**{**PG_CONFIG, "dbname": dbname})
    cur = conn.cursor()
    
    # Count candidates with NULL first_name (indicator of missing data)
    cur.execute("""
        SELECT COUNT(*)
        FROM gh.candidates
        WHERE first_name IS NULL
    """)
    null_count = cur.fetchone()[0]
    
    # Get total count
    cur.execute("SELECT COUNT(*) FROM gh.candidates")
    total = cur.fetchone()[0]
    
    print(f"Total candidates: {total:,}")
    print(f"Candidates with NULL first_name: {null_count:,}")
    
    # Get sample of candidates with NULL first_name
    cur.execute("""
        SELECT candidate_id, full_name, resume_links
        FROM gh.candidates
        WHERE first_name IS NULL
        ORDER BY candidate_id DESC
        LIMIT 10
    """)
    
    print(f"\nSample of candidates with NULL first_name (latest 10):")
    for row in cur.fetchall():
        has_links = "YES" if row[2] else "NO"
        print(f"  {row[0]} | {row[1]} | Links: {has_links}")
    
    cur.close()
    conn.close()

# Check the specific candidate mentioned
check_candidate("greenhouse_candidates", 47365303008)
check_candidate("greenhouse_candidates_sp", 47365303008)
check_candidate("greenhouse_candidates_ai", 47365303008)

# Check how widespread the issue is
check_recent_null_candidates("greenhouse_candidates_sp")
check_recent_null_candidates("greenhouse_candidates_ai")

print(f"\n{'='*80}")
print("INVESTIGATION COMPLETE")
print(f"{'='*80}")
