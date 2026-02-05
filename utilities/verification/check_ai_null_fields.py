#!/usr/bin/env python3
"""
Check AI database for NULL fields in specific columns
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

conn = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates_ai"})
cur = conn.cursor()

print("="*80)
print("AI DATABASE - NULL FIELD ANALYSIS")
print("="*80)

# Total candidates
cur.execute("SELECT COUNT(*) FROM gh.candidates")
total = cur.fetchone()[0]
print(f"\nTotal candidates: {total:,}")

# Check NULL counts for optional fields
fields = ['degrees', 'employment_titles', 'employment_companies', 'jobs_name', 'raw']

print(f"\nNULL counts for optional fields:")
for field in fields:
    cur.execute(f"SELECT COUNT(*) FROM gh.candidates WHERE {field} IS NULL")
    null_count = cur.fetchone()[0]
    print(f"  {field}: {null_count:,} ({null_count/total*100:.1f}%)")

# Check if these are the same candidates with NULL raw field
cur.execute("""
    SELECT COUNT(*)
    FROM gh.candidates
    WHERE raw IS NULL
    AND (degrees IS NULL OR employment_titles IS NULL OR employment_companies IS NULL OR jobs_name IS NULL)
""")
overlap = cur.fetchone()[0]

print(f"\nCandidates with NULL raw AND other NULL fields: {overlap:,}")

# Sample candidates with NULL raw
cur.execute("""
    SELECT candidate_id, first_name, last_name, 
           CASE WHEN degrees IS NULL THEN 'NULL' ELSE 'HAS DATA' END,
           CASE WHEN employment_titles IS NULL THEN 'NULL' ELSE 'HAS DATA' END,
           CASE WHEN jobs_name IS NULL THEN 'NULL' ELSE 'HAS DATA' END
    FROM gh.candidates
    WHERE raw IS NULL
    ORDER BY candidate_id DESC
    LIMIT 10
""")

print(f"\nSample candidates with NULL raw (latest 10):")
for row in cur.fetchall():
    print(f"  {row[0]} | {row[1]} {row[2]} | degrees:{row[3]} titles:{row[4]} jobs:{row[5]}")

# Check if main database has this data
print(f"\n{'='*80}")
print("Checking if main database has this data...")
print(f"{'='*80}")

conn_main = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates"})
cur_main = conn_main.cursor()

cur.execute("SELECT candidate_id FROM gh.candidates WHERE raw IS NULL LIMIT 5")
null_candidates = [row[0] for row in cur.fetchall()]

for candidate_id in null_candidates:
    cur_main.execute("""
        SELECT 
            candidate_id,
            CASE WHEN degrees IS NULL OR array_length(degrees, 1) = 0 THEN 'EMPTY' ELSE 'HAS DATA' END,
            CASE WHEN employment_titles IS NULL OR array_length(employment_titles, 1) = 0 THEN 'EMPTY' ELSE 'HAS DATA' END,
            CASE WHEN jobs_name IS NULL OR array_length(jobs_name, 1) = 0 THEN 'EMPTY' ELSE 'HAS DATA' END,
            CASE WHEN raw IS NULL THEN 'NULL' ELSE 'HAS DATA' END
        FROM gh.candidates
        WHERE candidate_id = %s
    """, (candidate_id,))
    
    row = cur_main.fetchone()
    if row:
        print(f"\nMain DB - Candidate {row[0]}:")
        print(f"  degrees: {row[1]}")
        print(f"  employment_titles: {row[2]}")
        print(f"  jobs_name: {row[3]}")
        print(f"  raw: {row[4]}")

cur.close()
cur_main.close()
conn.close()
conn_main.close()

print(f"\n{'='*80}")
print("ANALYSIS COMPLETE")
print(f"{'='*80}")
