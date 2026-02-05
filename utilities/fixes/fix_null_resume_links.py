#!/usr/bin/env python3
"""
Fix NULL resume_links in AI Database

Finds candidates with resume_filenames but NULL resume_links and generates
SharePoint links for them.
"""

import os
import sys
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
AI_ACCESS_DIR = os.path.join(LOCAL_RESUME_DIR, "AI_Access")

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_sharepoint_url_for_file(graph_client, filename):
    """Get SharePoint URL for a file in the AI_Access folder"""
    try:
        relative_path = f"AI_Access/{filename}"
        
        file_info = graph_client.find_file_by_path(relative_path)
        if not file_info:
            return None
        
        # Get the sharing link (direct access link for AI agents)
        file_id = file_info.get("id")
        if file_id:
            sharing_url = graph_client.create_sharing_link(file_id, link_type="view")
            return sharing_url
        
        return None
        
    except Exception as e:
        log(f"  ⚠️  Error getting SharePoint URL: {e}")
        return None

def get_metadata_url(graph_client, candidate_id):
    """Get SharePoint URL for metadata JSON file"""
    try:
        metadata_filename = f"{candidate_id}_metadata.json"
        relative_path = f"AI_Access/{metadata_filename}"
        
        file_info = graph_client.find_file_by_path(relative_path)
        if not file_info:
            return None
        
        file_id = file_info.get("id")
        if file_id:
            sharing_url = graph_client.create_sharing_link(file_id, link_type="view")
            return sharing_url
        
        return None
        
    except Exception as e:
        return None

def fix_null_resume_links():
    """Fix candidates with NULL resume_links"""
    log("="*80)
    log("FIX NULL RESUME_LINKS IN AI DATABASE")
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
    
    conn = psycopg2.connect(**{**PG_CONFIG, "dbname": "greenhouse_candidates_ai"})
    cur = conn.cursor()
    
    try:
        # Find candidates with resume_filenames but NULL resume_links
        log("Finding candidates with NULL resume_links...")
        cur.execute("""
            SELECT candidate_id, full_name, resume_filenames
            FROM gh.candidates
            WHERE resume_filenames IS NOT NULL 
            AND array_length(resume_filenames, 1) > 0
            AND (resume_links IS NULL OR array_length(resume_links, 1) = 0 OR resume_links = '{}')
            ORDER BY candidate_id
        """)
        
        null_link_candidates = cur.fetchall()
        total = len(null_link_candidates)
        
        log(f"Found {total:,} candidates with NULL resume_links")
        log("")
        
        if total == 0:
            log("✅ No candidates need fixing!")
            return True
        
        log("Generating SharePoint links...")
        
        updated = 0
        failed = 0
        file_not_found = 0
        
        for candidate_id, full_name, resume_filenames in null_link_candidates:
            if not resume_filenames or len(resume_filenames) == 0:
                continue
            
            filename = resume_filenames[0]
            
            # Check if file exists locally in AI_Access
            local_file = os.path.join(AI_ACCESS_DIR, filename)
            if not os.path.exists(local_file):
                file_not_found += 1
                if file_not_found <= 5:
                    log(f"  ⚠️  File not found locally: {filename}")
                continue
            
            # Get SharePoint URL
            sharepoint_url = get_sharepoint_url_for_file(graph_client, filename)
            
            if sharepoint_url:
                # Also try to get metadata URL
                metadata_url = get_metadata_url(graph_client, candidate_id)
                
                # Update AI database
                cur.execute("""
                    UPDATE gh.candidates
                    SET resume_links = ARRAY[%s],
                        metadata_url = %s
                    WHERE candidate_id = %s
                """, (sharepoint_url, metadata_url, candidate_id))
                
                updated += 1
                
                if updated % 100 == 0:
                    log(f"  Updated {updated:,}/{total:,} candidates...")
                    conn.commit()
            else:
                failed += 1
                if failed <= 5:
                    log(f"  ❌ Failed to get SharePoint URL for: {filename}")
        
        # Final commit
        conn.commit()
        
        log("")
        log("="*80)
        log("FIX SUMMARY")
        log("="*80)
        log(f"Total candidates processed: {total:,}")
        log(f"Successfully updated: {updated:,}")
        log(f"Failed to get SharePoint URL: {failed:,}")
        log(f"File not found locally: {file_not_found:,}")
        log("="*80)
        
        if file_not_found > 0:
            log("")
            log("⚠️  NOTE: Some files were not found in the AI_Access folder.")
            log("   These files may still be syncing to SharePoint via OneDrive.")
            log("   Wait for OneDrive sync to complete and run this script again.")
        
        return True
        
    except Exception as e:
        log(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    success = fix_null_resume_links()
    if success:
        log("\n✅ NULL resume_links fixed successfully!")
        log("\n📊 Next step: Export updated CSV")
        log("   Run: python export_ai_access_csv.py")
    else:
        log("\n❌ Fix failed!")
