#!/usr/bin/env python3
"""
Check AI Database Schema
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

PG_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", ""),
    "dbname": "greenhouse_candidates_ai"
}

conn = psycopg2.connect(**PG_CONFIG)
cur = conn.cursor()

# Get column names
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'gh' 
    AND table_name = 'candidates'
    ORDER BY ordinal_position
""")

print("Columns in gh.candidates:")
for row in cur.fetchall():
    print(f"  {row[0]} ({row[1]})")

cur.close()
conn.close()
