#!/usr/bin/env python3
"""
Map AI Access Links to Database

Maps all resumes in the flat AI_Access folder to SharePoint URLs
and updates the greenhouse_candidates_ai database.
"""

import os
import sys
import json
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from graph_client import GraphClient

load_dotenv()

# Configuration
LOCAL_RESUME_DIR = os.getenv("LOCAL_RESUME_DIR")
AI_ACCESS_FOLDER = "AI_Access"
LOCAL_AI_ACCESS_DIR = os.path.join(LOCAL_RESUME_DIR, AI_ACCESS_FOLDER)

PG = {
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

def load_master_index():
    """Load the master index file"""
    index_path = os.path.join(LOCAL_AI_ACCESS_DIR, "_master_index.json")
    
    if not os.path.exists(index_path):
        log(f"❌ Master index not found: {index_path}")
        return None
    
    with open(index_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_sharepoint_url_for_ai_file(graph_client, filename):
    """Get SharePoint URL for a file in the AI_Access folder"""
    try:
        # The path in SharePoint is: Greenhouse/Greenhouse_Resumes/AI_Access/{filename}
        relative_path = f"AI_Access/{filename}"
        
        file_info = graph_client.find_file_by_path(relative_path)
        if not file_info:
            return None
        
        # Use direct web URL
        web_url = file_info.get("webUrl")
        return web_url
        
    except Exception as e:
        return None

def find_local_resume_file(candidate_id):
    """Find resume file in AI_Access folder"""
    # Look for file starting with candidate_id in AI_Access folder
    for file in os.listdir(LOCAL_AI_ACCESS_DIR):
        if file.startswith(f"{candidate_id}_") and not file.endswith("_metadata.json") and not file.startswith("_"):
            return os.path.join(LOCAL_AI_ACCESS_DIR, file)
    return None

def map_ai_access_links():
    """Map AI Access links and update database - same logic as original mapper"""
    log("="*60)
    log("MAPPING AI ACCESS LINKS")
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
    
    # Get all candidates from database
    log("\nFetching candidates from database...")
    
    try:
        with psycopg2.connect(**PG) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM gh.candidates")
                total = cur.fetchone()[0]
                log(f"Total candidates to process: {total:,}")
            
            success_count = 0
            failed_count = 0
            no_resume_count = 0
            batch_size = 100
            
            for offset in range(0, total, batch_size):
                batch_num = (offset // batch_size) + 1
                log(f"Processing batch {batch_num}: candidates {offset+1} to {min(offset+batch_size, total)}")
                
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT candidate_id, full_name, resume_filenames
                        FROM gh.candidates
                        ORDER BY candidate_id
                        LIMIT %s OFFSET %s
                    """, (batch_size, offset))
                    
                    candidates = cur.fetchall()
                
                for candidate_id, full_name, resume_filenames in candidates:
                    # Find local file in AI_Access
                    local_file = find_local_resume_file(candidate_id)
                    
                    if not local_file:
                        no_resume_count += 1
                        continue
                    
                    # Get SharePoint URL
                    filename = os.path.basename(local_file)
                    ai_url = get_sharepoint_url_for_ai_file(graph_client, filename)
                    
                    if ai_url:
                        # Update resume_links to point to AI_Access
                        with conn.cursor() as cur:
                            cur.execute("""
                                UPDATE gh.candidates
                                SET resume_links = ARRAY[%s],
                                    resume_filenames = ARRAY[%s]
                                WHERE candidate_id = %s
                            """, (ai_url, filename, candidate_id))
                        
                        success_count += 1
                        if success_count % 10 == 0:
                            log(f"  ✅ Mapped candidate {candidate_id}: {full_name}")
                    else:
                        failed_count += 1
                
                conn.commit()
                log(f"Progress: {min(offset+batch_size, total):,}/{total:,} ({(min(offset+batch_size, total)/total*100):.1f}%)")
            
            log("\n" + "="*60)
            log("AI ACCESS MAPPING SUMMARY")
            log("="*60)
            log(f"Total candidates: {total:,}")
            log(f"Successfully mapped: {success_count:,}")
            log(f"Failed to map: {failed_count:,}")
            log(f"No resume: {no_resume_count:,}")
            log(f"Success rate: {(success_count/(total-no_resume_count)*100):.1f}%")
            log("="*60)
            
            return True
            
    except Exception as e:
        log(f"❌ Database error: {e}")
        return False

def main():
    """Main execution"""
    log("="*60)
    log("AI ACCESS LINKS MAPPER")
    log("="*60)
    
    # Check if AI_Access folder exists
    if not os.path.exists(LOCAL_AI_ACCESS_DIR):
        log(f"❌ AI_Access folder not found: {LOCAL_AI_ACCESS_DIR}")
        log("   Run 'python create_ai_access_folder.py' first")
        return
    
    # Map links
    success = map_ai_access_links()
    
    if success:
        log("\n✅ AI Access links mapped successfully!")
        log("\n📊 Next step: Export AI-friendly CSV")
        log("   Run: python export_ai_access_csv.py")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
