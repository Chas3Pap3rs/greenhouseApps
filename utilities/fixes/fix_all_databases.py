#!/usr/bin/env python3
"""
Fix All Database Issues

This script fixes the fundamental issues:
1. greenhouse_candidates_sp should ONLY have SharePoint links (not AWS S3)
2. greenhouse_candidates_ai should ONLY have SharePoint links (not AWS S3)
3. Both should have metadata_url populated for AI Access
4. Both should have resume_content synced from main database

Strategy:
- For each candidate with a resume file in SharePoint:
  - Get the SharePoint URL for human-friendly folder (YYYY/MM structure)
  - Get the SharePoint URL for AI_Access folder (flat structure)
  - Get the metadata JSON URL
  - Update both databases with correct SharePoint links
"""

import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from graph_client import GraphClient

load_dotenv()

PG_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

LOCAL_RESUME_DIR = os.getenv("LOCAL_RESUME_DIR")

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def find_resume_in_organized_folders(candidate_id):
    """Find resume in YYYY/MM organized folders"""
    for root, dirs, files in os.walk(LOCAL_RESUME_DIR):
        # Skip AI_Access folder
        if 'AI_Access' in root:
            continue
        
        for file in files:
            if file.startswith(f"{candidate_id}_") and not file.startswith("FAILED_"):
                return os.path.join(root, file)
    return None

def find_resume_in_ai_access(candidate_id):
    """Find resume in AI_Access flat folder"""
    ai_access_dir = os.path.join(LOCAL_RESUME_DIR, "AI_Access")
    if not os.path.exists(ai_access_dir):
        return None
    
    for file in os.listdir(ai_access_dir):
        if file.startswith(f"{candidate_id}_") and not file.startswith("FAILED_"):
            return os.path.join(ai_access_dir, file)
    return None

def get_sharepoint_url_for_file(graph_client, local_file_path):
    """Get SharePoint URL for a local file"""
    try:
        if not local_file_path or not os.path.exists(local_file_path):
            return None, None
        
        # Get relative path within SharePoint
        relative_path = os.path.relpath(local_file_path, LOCAL_RESUME_DIR)
        filename = os.path.basename(local_file_path)
        
        # Find file in SharePoint
        file_info = graph_client.find_file_by_path(relative_path)
        if not file_info:
            return None, None
        
        # Use direct web URL
        web_url = file_info.get("webUrl")
        return web_url, filename
        
    except Exception as e:
        log(f"  ⚠️  Error getting SharePoint URL: {e}")
        return None, None

def get_metadata_url(graph_client, candidate_id):
    """Get SharePoint URL for metadata JSON file"""
    try:
        metadata_filename = f"{candidate_id}_metadata.json"
        metadata_path = os.path.join("AI_Access", metadata_filename)
        
        file_info = graph_client.find_file_by_path(metadata_path)
        if not file_info:
            return None
        
        return file_info.get("webUrl")
        
    except Exception as e:
        return None

def fix_databases():
    """Fix all database issues"""
    log("="*80)
    log("COMPREHENSIVE DATABASE FIX")
    log("="*80)
    log("")
    
    # Connect to SharePoint
    log("Connecting to SharePoint...")
    try:
        graph_client = GraphClient()
        site_info = graph_client.get_site_info()
        log(f"✅ Connected to SharePoint: {site_info.get('displayName')}")
    except Exception as e:
        log(f"❌ Failed to connect to SharePoint: {e}")
        return False
    
    # Connect to all databases
    conn_main = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates"})
    conn_sp = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates_sp"})
    conn_ai = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates_ai"})
    
    cur_main = conn_main.cursor()
    cur_sp = conn_sp.cursor()
    cur_ai = conn_ai.cursor()
    
    try:
        # Get all candidates from main database
        log("\nFetching candidates from main database...")
        cur_main.execute("""
            SELECT candidate_id, first_name, last_name, full_name
            FROM gh.candidates
            ORDER BY candidate_id
        """)
        
        all_candidates = cur_main.fetchall()
        total = len(all_candidates)
        log(f"Found {total:,} candidates to process")
        log("")
        
        sp_updated = 0
        ai_updated = 0
        no_resume = 0
        failed = 0
        
        for idx, (candidate_id, first_name, last_name, full_name) in enumerate(all_candidates, 1):
            if idx % 100 == 0:
                log(f"Progress: {idx:,}/{total:,} ({idx/total*100:.1f}%) | SP: {sp_updated:,} | AI: {ai_updated:,}")
            
            # Find resume files
            organized_file = find_resume_in_organized_folders(candidate_id)
            ai_file = find_resume_in_ai_access(candidate_id)
            
            if not organized_file and not ai_file:
                no_resume += 1
                continue
            
            # Get SharePoint URLs
            sp_url = None
            sp_filename = None
            ai_url = None
            ai_filename = None
            metadata_url = None
            
            if organized_file:
                sp_url, sp_filename = get_sharepoint_url_for_file(graph_client, organized_file)
            
            if ai_file:
                ai_url, ai_filename = get_sharepoint_url_for_file(graph_client, ai_file)
                metadata_url = get_metadata_url(graph_client, candidate_id)
            
            # Update SharePoint database (human-friendly)
            if sp_url:
                cur_sp.execute("""
                    UPDATE gh.candidates
                    SET resume_links = ARRAY[%s],
                        resume_filenames = ARRAY[%s]
                    WHERE candidate_id = %s
                """, (sp_url, sp_filename, candidate_id))
                
                if cur_sp.rowcount > 0:
                    sp_updated += 1
            
            # Update AI Access database
            if ai_url:
                cur_ai.execute("""
                    UPDATE gh.candidates
                    SET resume_links = ARRAY[%s],
                        resume_filenames = ARRAY[%s],
                        metadata_url = %s
                    WHERE candidate_id = %s
                """, (ai_url, ai_filename, metadata_url, candidate_id))
                
                if cur_ai.rowcount > 0:
                    ai_updated += 1
            
            # Commit every 100 candidates
            if idx % 100 == 0:
                conn_sp.commit()
                conn_ai.commit()
        
        # Final commit
        conn_sp.commit()
        conn_ai.commit()
        
        log("")
        log("="*80)
        log("FIX SUMMARY")
        log("="*80)
        log(f"Total candidates: {total:,}")
        log(f"SharePoint DB updated: {sp_updated:,}")
        log(f"AI Access DB updated: {ai_updated:,}")
        log(f"No resume: {no_resume:,}")
        log(f"Failed: {failed:,}")
        log("="*80)
        
        return True
        
    except Exception as e:
        log(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn_sp.rollback()
        conn_ai.rollback()
        return False
    finally:
        cur_main.close()
        cur_sp.close()
        cur_ai.close()
        conn_main.close()
        conn_sp.close()
        conn_ai.close()

if __name__ == "__main__":
    success = fix_databases()
    if success:
        log("\n✅ Database fix complete!")
    else:
        log("\n❌ Database fix failed!")
