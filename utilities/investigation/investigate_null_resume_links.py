#!/usr/bin/env python3
"""
Investigate NULL resume_links in AI database for candidates with resume_filenames
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

def investigate_null_links():
    """Check candidates with resume_filenames but NULL resume_links"""
    
    print("="*80)
    print("AI DATABASE - NULL RESUME_LINKS INVESTIGATION")
    print("="*80)
    
    conn_ai = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates_ai"})
    conn_sp = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates_sp"})
    conn_main = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates"})
    
    cur_ai = conn_ai.cursor()
    cur_sp = conn_sp.cursor()
    cur_main = conn_main.cursor()
    
    # Find candidates with resume_filenames but NULL resume_links in AI database
    cur_ai.execute("""
        SELECT COUNT(*)
        FROM gh.candidates
        WHERE resume_filenames IS NOT NULL 
        AND array_length(resume_filenames, 1) > 0
        AND (resume_links IS NULL OR array_length(resume_links, 1) = 0 OR resume_links = '{}')
    """)
    
    null_links_count = cur_ai.fetchone()[0]
    
    # Total candidates
    cur_ai.execute("SELECT COUNT(*) FROM gh.candidates")
    total = cur_ai.fetchone()[0]
    
    print(f"\nTotal candidates in AI database: {total:,}")
    print(f"Candidates with resume_filenames but NULL/empty resume_links: {null_links_count:,}")
    
    if null_links_count > 0:
        print(f"\n{'='*80}")
        print(f"SAMPLE CANDIDATES (Latest 10):")
        print(f"{'='*80}")
        
        cur_ai.execute("""
            SELECT 
                candidate_id,
                full_name,
                resume_filenames,
                resume_links,
                metadata_url
            FROM gh.candidates
            WHERE resume_filenames IS NOT NULL 
            AND array_length(resume_filenames, 1) > 0
            AND (resume_links IS NULL OR array_length(resume_links, 1) = 0 OR resume_links = '{}')
            ORDER BY candidate_id DESC
            LIMIT 10
        """)
        
        null_link_candidates = cur_ai.fetchall()
        
        for candidate_id, full_name, filenames, links, metadata in null_link_candidates:
            print(f"\nCandidate ID: {candidate_id}")
            print(f"  Name: {full_name}")
            print(f"  Filenames: {filenames}")
            print(f"  Links: {links}")
            print(f"  Metadata URL: {metadata if metadata else 'NULL'}")
            
            # Check if this candidate exists in SP database with links
            cur_sp.execute("""
                SELECT resume_links, resume_filenames
                FROM gh.candidates
                WHERE candidate_id = %s
            """, (candidate_id,))
            
            sp_row = cur_sp.fetchone()
            if sp_row and sp_row[0]:
                print(f"  ✅ SP Database HAS links: {sp_row[0]}")
            else:
                print(f"  ❌ SP Database: No links or not found")
            
            # Check main database
            cur_main.execute("""
                SELECT resume_links, resume_filenames
                FROM gh.candidates
                WHERE candidate_id = %s
            """, (candidate_id,))
            
            main_row = cur_main.fetchone()
            if main_row and main_row[0]:
                print(f"  Main Database links: {main_row[0][:100]}...")
            else:
                print(f"  Main Database: No links")
        
        # Check if SP database has SharePoint links for these candidates
        print(f"\n{'='*80}")
        print(f"CHECKING IF SP DATABASE HAS SHAREPOINT LINKS:")
        print(f"{'='*80}")
        
        cur_ai.execute("""
            SELECT candidate_id
            FROM gh.candidates
            WHERE resume_filenames IS NOT NULL 
            AND array_length(resume_filenames, 1) > 0
            AND (resume_links IS NULL OR array_length(resume_links, 1) = 0 OR resume_links = '{}')
            LIMIT 100
        """)
        
        candidate_ids = [row[0] for row in cur_ai.fetchall()]
        
        has_sp_links = 0
        no_sp_links = 0
        
        for candidate_id in candidate_ids:
            cur_sp.execute("""
                SELECT resume_links
                FROM gh.candidates
                WHERE candidate_id = %s
                AND resume_links IS NOT NULL
                AND array_length(resume_links, 1) > 0
            """, (candidate_id,))
            
            if cur_sp.fetchone():
                has_sp_links += 1
            else:
                no_sp_links += 1
        
        print(f"\nOut of {len(candidate_ids)} candidates with NULL links in AI database:")
        print(f"  ✅ {has_sp_links} have SharePoint links in SP database")
        print(f"  ❌ {no_sp_links} do NOT have SharePoint links in SP database")
        
        if has_sp_links > 0:
            print(f"\n💡 SOLUTION: Copy SharePoint links from SP database to AI database")
        if no_sp_links > 0:
            print(f"\n⚠️  WARNING: {no_sp_links} candidates need SharePoint links generated")
    
    cur_ai.close()
    cur_sp.close()
    cur_main.close()
    conn_ai.close()
    conn_sp.close()
    conn_main.close()
    
    print(f"\n{'='*80}")
    print("INVESTIGATION COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    investigate_null_links()
