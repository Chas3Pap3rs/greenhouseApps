#!/usr/bin/env python3
"""
Incremental SharePoint Links Updater (Human-Friendly DB)

Updates only NEW candidates added since last run.
Much faster than full scan - use this for regular updates.
Use map_sharepoint_links.py only for full rebuilds.
"""

import os
import sys
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from graph_client import GraphClient

load_dotenv()

PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": "greenhouse_candidates_sp",
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

SOURCE_PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": "greenhouse_candidates",
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

LOCAL_RESUME_DIR = os.getenv("LOCAL_RESUME_DIR")

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_last_sync_time(conn):
    """Get the last time we synced SharePoint links"""
    with conn.cursor() as cur:
        # Check if we have a sync tracking table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gh.sharepoint_sync_log (
                sync_id SERIAL PRIMARY KEY,
                sync_type TEXT,
                last_synced_candidate_id BIGINT,
                sync_completed_at TIMESTAMPTZ
            )
        """)
        
        cur.execute("""
            SELECT MAX(last_synced_candidate_id)
            FROM gh.sharepoint_sync_log
            WHERE sync_type = 'human_friendly'
        """)
        
        result = cur.fetchone()
        return result[0] if result and result[0] else 0

def record_sync_completion(conn, last_candidate_id):
    """Record successful sync completion"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO gh.sharepoint_sync_log (sync_type, last_synced_candidate_id, sync_completed_at)
            VALUES ('human_friendly', %s, NOW())
        """, (last_candidate_id,))
    conn.commit()

def find_local_resume_file(candidate_id):
    """Find resume file in organized folder structure"""
    for root, dirs, files in os.walk(LOCAL_RESUME_DIR):
        # Skip AI_Access folder
        if 'AI_Access' in root:
            continue
        
        for file in files:
            if file.startswith(f"{candidate_id}_") and not file.startswith("FAILED_"):
                return os.path.join(root, file)
    return None

def get_sharepoint_url_for_local_file(graph_client, local_file_path):
    """Get SharePoint URL for a local file"""
    try:
        # Extract relative path from local path
        if not local_file_path.startswith(LOCAL_RESUME_DIR):
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
        return None, None

def update_new_candidates():
    """Update SharePoint links for new candidates only"""
    log("="*60)
    log("INCREMENTAL SHAREPOINT LINKS UPDATE (Human-Friendly)")
    log("="*60)
    
    # Connect to SharePoint
    log("Connecting to SharePoint...")
    try:
        graph_client = GraphClient()
        site_info = graph_client.get_site_info()
        log(f"✅ Connected to SharePoint: {site_info.get('displayName')}")
    except Exception as e:
        log(f"❌ Failed to connect to SharePoint: {e}")
        return False
    
    try:
        with psycopg2.connect(**PG) as conn:
            # Get last sync point
            last_synced_id = get_last_sync_time(conn)
            log(f"Last synced candidate ID: {last_synced_id}")
            
            # Get new candidates from source database
            with psycopg2.connect(**SOURCE_PG) as source_conn:
                with source_conn.cursor() as cur:
                    cur.execute("""
                        SELECT candidate_id, full_name, resume_filenames
                        FROM gh.candidates
                        WHERE candidate_id > %s
                        ORDER BY candidate_id
                    """, (last_synced_id,))
                    
                    new_candidates = cur.fetchall()
            
            if not new_candidates:
                log("✅ No new candidates to process!")
                return True
            
            log(f"Found {len(new_candidates):,} new candidates to process")
            
            success_count = 0
            failed_count = 0
            no_resume_count = 0
            last_processed_id = last_synced_id
            
            for candidate_id, full_name, resume_filenames in new_candidates:
                # Find local file
                local_file = find_local_resume_file(candidate_id)
                
                if not local_file:
                    no_resume_count += 1
                    last_processed_id = candidate_id
                    continue
                
                # Get SharePoint URL
                sp_url, sp_filename = get_sharepoint_url_for_local_file(graph_client, local_file)
                
                if sp_url:
                    # Update or insert candidate
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO gh.candidates (
                                candidate_id, full_name, resume_links, resume_filenames
                            )
                            SELECT candidate_id, full_name, resume_links, resume_filenames
                            FROM dblink(
                                'dbname=greenhouse_candidates',
                                'SELECT candidate_id, full_name, resume_links, resume_filenames FROM gh.candidates WHERE candidate_id = ' || %s
                            ) AS t(candidate_id BIGINT, full_name TEXT, resume_links TEXT[], resume_filenames TEXT[])
                            ON CONFLICT (candidate_id) DO UPDATE SET
                                resume_links = ARRAY[%s],
                                resume_filenames = ARRAY[%s]
                        """, (candidate_id, sp_url, sp_filename))
                    
                    success_count += 1
                    if success_count % 10 == 0:
                        log(f"  ✅ Mapped {success_count} new candidates...")
                else:
                    failed_count += 1
                
                last_processed_id = candidate_id
                
                # Commit every 100 candidates
                if (success_count + failed_count + no_resume_count) % 100 == 0:
                    conn.commit()
            
            # Final commit
            conn.commit()
            
            # Record sync completion
            record_sync_completion(conn, last_processed_id)
            
            log("\n" + "="*60)
            log("UPDATE SUMMARY")
            log("="*60)
            log(f"New candidates processed: {len(new_candidates):,}")
            log(f"Successfully mapped: {success_count:,}")
            log(f"Failed to map: {failed_count:,}")
            log(f"No resume: {no_resume_count:,}")
            if success_count > 0:
                log(f"Success rate: {(success_count/(success_count+failed_count)*100):.1f}%")
            log(f"Last processed ID: {last_processed_id}")
            log("="*60)
            
            return True
            
    except Exception as e:
        log(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main execution"""
    log("="*60)
    log("INCREMENTAL SHAREPOINT UPDATE")
    log("="*60)
    
    success = update_new_candidates()
    
    if success:
        log("\n✅ Incremental update complete!")
        log("\n📊 Next step: Export updated CSV")
        log("   Run: python export_sharepoint_csv.py")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
