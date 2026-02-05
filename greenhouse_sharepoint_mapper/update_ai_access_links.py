#!/usr/bin/env python3
"""
Incremental AI Access Links Updater (AI-Friendly DB)

Updates only NEW candidates added since last run.
Much faster than full scan - use this for regular updates.
Use map_ai_access_links.py only for full rebuilds.
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
    "dbname": "greenhouse_candidates_ai",
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
AI_ACCESS_DIR = os.path.join(LOCAL_RESUME_DIR, "AI_Access")

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_last_sync_time(conn):
    """Get the last time we synced AI Access links"""
    with conn.cursor() as cur:
        # Check if we have a sync tracking table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gh.ai_sync_log (
                sync_id SERIAL PRIMARY KEY,
                sync_type TEXT,
                last_synced_candidate_id BIGINT,
                sync_completed_at TIMESTAMPTZ
            )
        """)
        
        cur.execute("""
            SELECT MAX(last_synced_candidate_id)
            FROM gh.ai_sync_log
            WHERE sync_type = 'ai_friendly'
        """)
        
        result = cur.fetchone()
        return result[0] if result and result[0] else 0

def record_sync_completion(conn, last_candidate_id):
    """Record successful sync completion"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO gh.ai_sync_log (sync_type, last_synced_candidate_id, sync_completed_at)
            VALUES ('ai_friendly', %s, NOW())
        """, (last_candidate_id,))
    conn.commit()

def find_local_resume_file(candidate_id):
    """Find resume file in AI_Access folder"""
    try:
        for file in os.listdir(AI_ACCESS_DIR):
            if file.startswith(f"{candidate_id}_") and not file.endswith("_metadata.json") and not file.startswith("_"):
                return os.path.join(AI_ACCESS_DIR, file)
    except:
        pass
    return None

def get_sharepoint_url_for_ai_file(graph_client, filename):
    """Get SharePoint URL for a file in the AI_Access folder"""
    try:
        relative_path = f"AI_Access/{filename}"
        
        file_info = graph_client.find_file_by_path(relative_path)
        if not file_info:
            return None
        
        web_url = file_info.get("webUrl")
        return web_url
        
    except Exception as e:
        return None

def update_new_candidates():
    """Update AI Access links for new candidates only"""
    log("="*60)
    log("INCREMENTAL AI ACCESS LINKS UPDATE (AI-Friendly)")
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
                # Find local file in AI_Access
                local_file = find_local_resume_file(candidate_id)
                
                if not local_file:
                    no_resume_count += 1
                    last_processed_id = candidate_id
                    continue
                
                # Get SharePoint URL
                filename = os.path.basename(local_file)
                ai_url = get_sharepoint_url_for_ai_file(graph_client, filename)
                
                if ai_url:
                    # Update or insert candidate
                    with conn.cursor() as cur:
                        # First, copy full candidate data from source if not exists
                        cur.execute("""
                            SELECT candidate_id FROM gh.candidates WHERE candidate_id = %s
                        """, (candidate_id,))
                        
                        if not cur.fetchone():
                            # Copy from source database
                            with psycopg2.connect(**SOURCE_PG) as source_conn:
                                with source_conn.cursor() as source_cur:
                                    source_cur.execute("""
                                        SELECT * FROM gh.candidates WHERE candidate_id = %s
                                    """, (candidate_id,))
                                    candidate_data = source_cur.fetchone()
                                    
                                    if candidate_data:
                                        # Insert into AI database
                                        cur.execute("""
                                            INSERT INTO gh.candidates 
                                            SELECT * FROM unnest(%s::gh.candidates[])
                                        """, ([candidate_data],))
                        
                        # Update with AI_Access URL
                        cur.execute("""
                            UPDATE gh.candidates
                            SET resume_links = ARRAY[%s],
                                resume_filenames = ARRAY[%s]
                            WHERE candidate_id = %s
                        """, (ai_url, filename, candidate_id))
                    
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
    log("INCREMENTAL AI ACCESS UPDATE")
    log("="*60)
    
    success = update_new_candidates()
    
    if success:
        log("\n✅ Incremental update complete!")
        log("\n📊 Next step: Export updated CSV")
        log("   Run: python export_ai_access_csv.py")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
