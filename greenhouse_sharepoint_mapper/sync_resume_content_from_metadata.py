#!/usr/bin/env python3
"""
Sync resume_content from metadata JSON files to AI database

This script reads the resume_text from metadata JSON files and populates
the resume_content field in the database for candidates missing it.
"""

import os
import json
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Configuration
LOCAL_RESUME_DIR = os.getenv("LOCAL_RESUME_DIR")
AI_ACCESS_DIR = os.path.join(LOCAL_RESUME_DIR, "AI_Access")

PG_AI = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": "greenhouse_candidates_ai",
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def sync_resume_content():
    """Sync resume_content from metadata JSON files"""
    log("="*70)
    log("SYNC RESUME_CONTENT FROM METADATA JSON FILES")
    log("="*70)
    log("")
    
    conn = psycopg2.connect(**PG_AI)
    cur = conn.cursor()
    
    # Get candidates with metadata_url but no resume_content
    log("Fetching candidates needing resume_content...")
    cur.execute("""
        SELECT candidate_id, full_name
        FROM gh.candidates
        WHERE metadata_url IS NOT NULL AND metadata_url != ''
        AND (resume_content IS NULL OR resume_content = '')
        ORDER BY candidate_id
    """)
    
    candidates = cur.fetchall()
    log(f"Found {len(candidates):,} candidates needing resume_content")
    log("")
    
    if not candidates:
        log("✅ All candidates with metadata_url already have resume_content!")
        cur.close()
        conn.close()
        return
    
    log("Processing metadata files...")
    updated = 0
    failed = 0
    no_file = 0
    no_text = 0
    
    for i, (cid, name) in enumerate(candidates, 1):
        if i % 100 == 0:
            log(f"  Progress: {i:,} / {len(candidates):,} ({i/len(candidates)*100:.1f}%)")
        
        # Find metadata file
        metadata_file = None
        try:
            for file in os.listdir(AI_ACCESS_DIR):
                if file.startswith(f"{cid}_") and file.endswith("_metadata.json"):
                    metadata_file = os.path.join(AI_ACCESS_DIR, file)
                    break
        except Exception as e:
            failed += 1
            continue
        
        if not metadata_file or not os.path.exists(metadata_file):
            no_file += 1
            continue
        
        # Read metadata JSON and extract text_content
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                # Try both 'text_content' and 'resume_text' fields
                resume_text = metadata.get('text_content', '') or metadata.get('resume_text', '')
                
                if resume_text:
                    # Update database
                    cur.execute("""
                        UPDATE gh.candidates
                        SET resume_content = %s
                        WHERE candidate_id = %s
                    """, (resume_text, cid))
                    updated += 1
                    
                    if updated % 100 == 0:
                        conn.commit()
                else:
                    no_text += 1
        except Exception as e:
            failed += 1
            continue
    
    # Final commit
    conn.commit()
    
    log("")
    log("="*70)
    log("SYNC COMPLETE!")
    log("="*70)
    log(f"Total candidates processed: {len(candidates):,}")
    log(f"Successfully updated: {updated:,}")
    log(f"No metadata file: {no_file:,}")
    log(f"No text in metadata: {no_text:,}")
    log(f"Failed: {failed:,}")
    log("")
    
    # Verify final coverage
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN resume_content IS NOT NULL AND resume_content != '' THEN 1 END) as with_content
        FROM gh.candidates
        WHERE resume_links IS NOT NULL AND array_length(resume_links, 1) > 0
    """)
    
    result = cur.fetchone()
    log(f"✅ AI Database now has {result[1]:,} / {result[0]:,} candidates with resume_content ({result[1]/result[0]*100:.1f}%)")
    log("="*70)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    try:
        sync_resume_content()
    except Exception as e:
        log(f"❌ Error: {e}")
        raise
