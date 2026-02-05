#!/usr/bin/env python3
"""
Fix Recent Candidates with AWS Links

Targets only candidates that have AWS S3 links instead of SharePoint links
in the SP and AI databases. This is much faster than scanning all 50K+ candidates.
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
        
        relative_path = os.path.relpath(local_file_path, LOCAL_RESUME_DIR)
        filename = os.path.basename(local_file_path)
        
        file_info = graph_client.find_file_by_path(relative_path)
        if not file_info:
            return None, None
        
        web_url = file_info.get("webUrl")
        return web_url, filename
        
    except Exception as e:
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

def fix_aws_links():
    """Fix candidates that have AWS links instead of SharePoint links"""
    log("="*80)
    log("FIX RECENT CANDIDATES WITH AWS LINKS")
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
    
    conn_sp = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates_sp"})
    conn_ai = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates_ai"})
    
    cur_sp = conn_sp.cursor()
    cur_ai = conn_ai.cursor()
    
    try:
        # Find candidates with AWS links in SP database
        log("\nFinding candidates with AWS links in SharePoint database...")
        cur_sp.execute("""
            SELECT candidate_id, first_name, last_name
            FROM gh.candidates
            WHERE resume_links IS NOT NULL 
            AND array_length(resume_links, 1) > 0
            AND resume_links[1] LIKE '%amazonaws.com%'
            ORDER BY candidate_id
        """)
        
        sp_aws_candidates = cur_sp.fetchall()
        log(f"Found {len(sp_aws_candidates):,} candidates with AWS links in SP database")
        
        # Find candidates with AWS links in AI database
        log("Finding candidates with AWS links in AI database...")
        cur_ai.execute("""
            SELECT candidate_id, first_name, last_name
            FROM gh.candidates
            WHERE resume_links IS NOT NULL 
            AND array_length(resume_links, 1) > 0
            AND resume_links[1] LIKE '%amazonaws.com%'
            ORDER BY candidate_id
        """)
        
        ai_aws_candidates = cur_ai.fetchall()
        log(f"Found {len(ai_aws_candidates):,} candidates with AWS links in AI database")
        log("")
        
        # Fix SP database
        sp_fixed = 0
        sp_failed = 0
        
        if sp_aws_candidates:
            log(f"Fixing SharePoint database ({len(sp_aws_candidates):,} candidates)...")
            for candidate_id, first_name, last_name in sp_aws_candidates:
                organized_file = find_resume_in_organized_folders(candidate_id)
                
                if organized_file:
                    sp_url, sp_filename = get_sharepoint_url_for_file(graph_client, organized_file)
                    
                    if sp_url:
                        cur_sp.execute("""
                            UPDATE gh.candidates
                            SET resume_links = ARRAY[%s],
                                resume_filenames = ARRAY[%s]
                            WHERE candidate_id = %s
                        """, (sp_url, sp_filename, candidate_id))
                        sp_fixed += 1
                        
                        if sp_fixed % 10 == 0:
                            log(f"  Fixed {sp_fixed}/{len(sp_aws_candidates)} candidates...")
                    else:
                        sp_failed += 1
                else:
                    sp_failed += 1
            
            conn_sp.commit()
            log(f"✅ SP Database: Fixed {sp_fixed:,} | Failed {sp_failed:,}")
        
        # Fix AI database
        ai_fixed = 0
        ai_failed = 0
        
        if ai_aws_candidates:
            log(f"\nFixing AI Access database ({len(ai_aws_candidates):,} candidates)...")
            for candidate_id, first_name, last_name in ai_aws_candidates:
                ai_file = find_resume_in_ai_access(candidate_id)
                
                if ai_file:
                    ai_url, ai_filename = get_sharepoint_url_for_file(graph_client, ai_file)
                    metadata_url = get_metadata_url(graph_client, candidate_id)
                    
                    if ai_url:
                        cur_ai.execute("""
                            UPDATE gh.candidates
                            SET resume_links = ARRAY[%s],
                                resume_filenames = ARRAY[%s],
                                metadata_url = %s
                            WHERE candidate_id = %s
                        """, (ai_url, ai_filename, metadata_url, candidate_id))
                        ai_fixed += 1
                        
                        if ai_fixed % 10 == 0:
                            log(f"  Fixed {ai_fixed}/{len(ai_aws_candidates)} candidates...")
                    else:
                        ai_failed += 1
                else:
                    ai_failed += 1
            
            conn_ai.commit()
            log(f"✅ AI Database: Fixed {ai_fixed:,} | Failed {ai_failed:,}")
        
        log("")
        log("="*80)
        log("FIX SUMMARY")
        log("="*80)
        log(f"SharePoint DB: {sp_fixed:,} fixed, {sp_failed:,} failed")
        log(f"AI Access DB: {ai_fixed:,} fixed, {ai_failed:,} failed")
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
        cur_sp.close()
        cur_ai.close()
        conn_sp.close()
        conn_ai.close()

if __name__ == "__main__":
    success = fix_aws_links()
    if success:
        log("\n✅ Fix complete! All databases now have correct SharePoint links.")
    else:
        log("\n❌ Fix failed!")
