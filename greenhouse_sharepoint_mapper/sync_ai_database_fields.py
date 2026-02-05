#!/usr/bin/env python3
"""
Sync Missing Fields to AI Access Database

This script syncs missing fields from greenhouse_candidates to greenhouse_candidates_ai:
- resume_content (from Greenhouse custom field)
- addresses (from candidate data)
- updated_at (timestamp)
- resume_links (human-friendly SharePoint links from greenhouse_candidates_sp)
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

def sync_missing_fields():
    """Sync missing fields from greenhouse_candidates to greenhouse_candidates_ai"""
    
    log("="*60)
    log("Sync Missing Fields to AI Access Database")
    log("="*60)
    log("")
    
    # Connect to both databases
    conn_main = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates"})
    conn_ai = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates_ai"})
    conn_sp = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates_sp"})
    
    cur_main = conn_main.cursor()
    cur_ai = conn_ai.cursor()
    cur_sp = conn_sp.cursor()
    
    try:
        # Get count of candidates with NULL fields in AI database
        log("Checking for candidates with missing data...")
        cur_ai.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE resume_content IS NULL) as null_content,
                COUNT(*) FILTER (WHERE addresses IS NULL) as null_addresses,
                COUNT(*) FILTER (WHERE updated_at IS NULL) as null_updated,
                COUNT(*) FILTER (WHERE resume_links IS NULL) as null_resume_links
            FROM gh.candidates
        """)
        
        stats = cur_ai.fetchone()
        log(f"Total candidates: {stats[0]:,}")
        log(f"Missing resume_content: {stats[1]:,}")
        log(f"Missing addresses: {stats[2]:,}")
        log(f"Missing updated_at: {stats[3]:,}")
        log(f"Missing resume_links: {stats[4]:,}")
        log("")
        
        # Sync resume_content from main database
        log("Syncing resume_content from greenhouse_candidates...")
        cur_main.execute("""
            SELECT candidate_id, resume_content
            FROM gh.candidates
            WHERE resume_content IS NOT NULL
        """)
        main_content = cur_main.fetchall()
        log(f"Found {len(main_content):,} candidates with resume_content in main database")
        
        if main_content:
            content_updated = 0
            for candidate_id, resume_content in main_content:
                cur_ai.execute("""
                    UPDATE gh.candidates
                    SET resume_content = %s
                    WHERE candidate_id = %s
                    AND (resume_content IS NULL OR resume_content = '')
                """, (resume_content, candidate_id))
                if cur_ai.rowcount > 0:
                    content_updated += 1
            conn_ai.commit()
            log(f"✅ Updated resume_content for {content_updated:,} candidates")
        else:
            content_updated = 0
            log(f"⚠️  No resume_content found in main database")
        
        # Sync addresses from main database
        log("Syncing addresses from greenhouse_candidates...")
        cur_main.execute("""
            SELECT candidate_id, addresses
            FROM gh.candidates
            WHERE addresses IS NOT NULL
        """)
        main_addresses = cur_main.fetchall()
        log(f"Found {len(main_addresses):,} candidates with addresses in main database")
        
        if main_addresses:
            addresses_updated = 0
            for candidate_id, addresses in main_addresses:
                cur_ai.execute("""
                    UPDATE gh.candidates
                    SET addresses = %s
                    WHERE candidate_id = %s
                    AND addresses IS NULL
                """, (addresses, candidate_id))
                if cur_ai.rowcount > 0:
                    addresses_updated += 1
            conn_ai.commit()
            log(f"✅ Updated addresses for {addresses_updated:,} candidates")
        else:
            log(f"⚠️  No addresses found in main database")
        
        # Sync updated_at from main database
        log("Syncing updated_at from greenhouse_candidates...")
        cur_main.execute("""
            SELECT candidate_id, updated_at
            FROM gh.candidates
            WHERE updated_at IS NOT NULL
        """)
        main_updated = cur_main.fetchall()
        log(f"Found {len(main_updated):,} candidates with updated_at in main database")
        
        if main_updated:
            updated_at_updated = 0
            for candidate_id, updated_at in main_updated:
                cur_ai.execute("""
                    UPDATE gh.candidates
                    SET updated_at = %s
                    WHERE candidate_id = %s
                    AND updated_at IS NULL
                """, (updated_at, candidate_id))
                if cur_ai.rowcount > 0:
                    updated_at_updated += 1
            conn_ai.commit()
            log(f"✅ Updated updated_at for {updated_at_updated:,} candidates")
        else:
            log(f"⚠️  No updated_at found in main database")
        
        # Sync resume_links from greenhouse_candidates_sp
        log("Syncing resume_links from greenhouse_candidates_sp...")
        cur_sp.execute("""
            SELECT candidate_id, resume_links
            FROM gh.candidates
            WHERE resume_links IS NOT NULL
        """)
        sp_links = cur_sp.fetchall()
        log(f"Found {len(sp_links):,} candidates with resume_links in SharePoint database")
        
        if sp_links:
            resume_links_updated = 0
            for candidate_id, resume_links in sp_links:
                cur_ai.execute("""
                    UPDATE gh.candidates
                    SET resume_links = %s
                    WHERE candidate_id = %s
                    AND resume_links IS NULL
                """, (resume_links, candidate_id))
                if cur_ai.rowcount > 0:
                    resume_links_updated += 1
            conn_ai.commit()
            log(f"✅ Updated resume_links for {resume_links_updated:,} candidates")
        else:
            log(f"⚠️  No resume_links found in SharePoint database")
        
        log("")
        log("="*60)
        log("✅ Sync completed successfully!")
        log("="*60)
        log(f"resume_content: {content_updated:,} updated")
        log(f"addresses: {addresses_updated:,} updated")
        log(f"updated_at: {updated_at_updated:,} updated")
        log(f"resume_links: {resume_links_updated:,} updated")
        log("="*60)
        
    except Exception as e:
        log(f"❌ Error: {e}")
        conn_ai.rollback()
        raise
    finally:
        cur_main.close()
        cur_ai.close()
        cur_sp.close()
        conn_main.close()
        conn_ai.close()
        conn_sp.close()

if __name__ == "__main__":
    sync_missing_fields()
