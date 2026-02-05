#!/usr/bin/env python3
"""
Comprehensive Database Analysis

Analyzes all three databases to understand:
1. Schema structure
2. Data populations
3. What links should be where
4. Data inconsistencies
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
    "password": os.getenv("PGPASSWORD", "")
}

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def analyze_database(dbname, description):
    """Analyze a single database"""
    log("")
    log("="*80)
    log(f"DATABASE: {dbname} ({description})")
    log("="*80)
    
    conn = psycopg2.connect(**{**PG_CONFIG, "dbname": dbname})
    cur = conn.cursor()
    
    # Get schema
    log("\n📋 SCHEMA:")
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'gh' 
        AND table_name = 'candidates'
        ORDER BY ordinal_position
    """)
    
    for row in cur.fetchall():
        nullable = "NULL" if row[2] == "YES" else "NOT NULL"
        log(f"  {row[0]:30} {row[1]:20} {nullable}")
    
    # Get statistics
    log("\n📊 STATISTICS:")
    cur.execute("SELECT COUNT(*) FROM gh.candidates")
    total = cur.fetchone()[0]
    log(f"  Total candidates: {total:,}")
    
    # Check resume_links
    cur.execute("""
        SELECT COUNT(*) 
        FROM gh.candidates 
        WHERE resume_links IS NOT NULL 
        AND array_length(resume_links, 1) > 0
    """)
    with_resume_links = cur.fetchone()[0]
    log(f"  With resume_links: {with_resume_links:,} ({with_resume_links/total*100:.1f}%)")
    
    # Sample resume_links to see what they contain
    log("\n🔗 SAMPLE resume_links (first 3 with links):")
    cur.execute("""
        SELECT candidate_id, first_name, last_name, resume_links[1] as first_link
        FROM gh.candidates
        WHERE resume_links IS NOT NULL 
        AND array_length(resume_links, 1) > 0
        ORDER BY candidate_id DESC
        LIMIT 3
    """)
    
    for row in cur.fetchall():
        link = row[3]
        if link:
            if 'sharepoint.com' in link:
                link_type = "SharePoint"
            elif 'amazonaws.com' in link:
                link_type = "AWS S3"
            else:
                link_type = "Unknown"
            log(f"  {row[0]} | {row[1]} {row[2]}")
            log(f"    Type: {link_type}")
            log(f"    Link: {link[:100]}...")
    
    # Check resume_content
    cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE resume_content IS NOT NULL")
    with_content = cur.fetchone()[0]
    log(f"\n📄 With resume_content: {with_content:,} ({with_content/total*100:.1f}%)")
    
    # Check for metadata_url if it exists
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'gh' 
        AND table_name = 'candidates'
        AND column_name = 'metadata_url'
    """)
    
    if cur.fetchone():
        cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE metadata_url IS NOT NULL")
        with_metadata = cur.fetchone()[0]
        log(f"🔗 With metadata_url: {with_metadata:,} ({with_metadata/total*100:.1f}%)")
        
        # Sample metadata URLs
        log("\n📝 SAMPLE metadata_url (first 3):")
        cur.execute("""
            SELECT candidate_id, first_name, last_name, metadata_url
            FROM gh.candidates
            WHERE metadata_url IS NOT NULL
            ORDER BY candidate_id DESC
            LIMIT 3
        """)
        
        for row in cur.fetchall():
            log(f"  {row[0]} | {row[1]} {row[2]}")
            log(f"    {row[3][:100]}...")
    
    # Check addresses
    cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE addresses IS NOT NULL")
    with_addresses = cur.fetchone()[0]
    log(f"\n📍 With addresses: {with_addresses:,} ({with_addresses/total*100:.1f}%)")
    
    # Check updated_at
    cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE updated_at IS NOT NULL")
    with_updated = cur.fetchone()[0]
    log(f"⏰ With updated_at: {with_updated:,} ({with_updated/total*100:.1f}%)")
    
    cur.close()
    conn.close()

def main():
    log("="*80)
    log("COMPREHENSIVE DATABASE STRUCTURE ANALYSIS")
    log("="*80)
    
    analyze_database("greenhouse_candidates", "Main DB - dbBuilder output")
    analyze_database("greenhouse_candidates_sp", "SharePoint DB - Human-friendly links")
    analyze_database("greenhouse_candidates_ai", "AI Access DB - Flat structure for AI")
    
    log("")
    log("="*80)
    log("ANALYSIS COMPLETE")
    log("="*80)

if __name__ == "__main__":
    main()
