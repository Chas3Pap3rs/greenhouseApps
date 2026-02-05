#!/usr/bin/env python3
"""
Verify what types of links are actually in each database
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

def check_database(dbname):
    """Check what types of links are in a database"""
    print(f"\n{'='*80}")
    print(f"DATABASE: {dbname}")
    print(f"{'='*80}")
    
    conn = psycopg2.connect(**{**PG_CONFIG, "dbname": dbname})
    cur = conn.cursor()
    
    # Count total with links
    cur.execute("""
        SELECT COUNT(*)
        FROM gh.candidates
        WHERE resume_links IS NOT NULL 
        AND array_length(resume_links, 1) > 0
    """)
    total_with_links = cur.fetchone()[0]
    print(f"Total with resume_links: {total_with_links:,}")
    
    # Count AWS S3 links
    cur.execute("""
        SELECT COUNT(*)
        FROM gh.candidates
        WHERE resume_links IS NOT NULL 
        AND array_length(resume_links, 1) > 0
        AND resume_links[1] LIKE '%amazonaws.com%'
    """)
    aws_links = cur.fetchone()[0]
    print(f"AWS S3 links: {aws_links:,} ({aws_links/total_with_links*100:.1f}%)")
    
    # Count SharePoint links
    cur.execute("""
        SELECT COUNT(*)
        FROM gh.candidates
        WHERE resume_links IS NOT NULL 
        AND array_length(resume_links, 1) > 0
        AND resume_links[1] LIKE '%sharepoint.com%'
    """)
    sp_links = cur.fetchone()[0]
    print(f"SharePoint links: {sp_links:,} ({sp_links/total_with_links*100:.1f}%)")
    
    # Sample of each type
    print(f"\nSample AWS S3 link:")
    cur.execute("""
        SELECT candidate_id, first_name, last_name, resume_links[1]
        FROM gh.candidates
        WHERE resume_links IS NOT NULL 
        AND array_length(resume_links, 1) > 0
        AND resume_links[1] LIKE '%amazonaws.com%'
        ORDER BY candidate_id DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        print(f"  {row[0]} | {row[1]} {row[2]}")
        print(f"  {row[3][:120]}...")
    
    print(f"\nSample SharePoint link:")
    cur.execute("""
        SELECT candidate_id, first_name, last_name, resume_links[1]
        FROM gh.candidates
        WHERE resume_links IS NOT NULL 
        AND array_length(resume_links, 1) > 0
        AND resume_links[1] LIKE '%sharepoint.com%'
        ORDER BY candidate_id DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        print(f"  {row[0]} | {row[1]} {row[2]}")
        print(f"  {row[3][:120]}...")
    
    cur.close()
    conn.close()

print("="*80)
print("LINK TYPE VERIFICATION")
print("="*80)

check_database("greenhouse_candidates")
check_database("greenhouse_candidates_sp")
check_database("greenhouse_candidates_ai")

print(f"\n{'='*80}")
print("VERIFICATION COMPLETE")
print(f"{'='*80}")
