#!/usr/bin/env python3
"""
Map metadata JSON files to SharePoint URLs and add to database
"""

import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from graph_client import GraphClient

# Load environment variables
load_dotenv()

# Database configuration
PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", 5432)),
    "database": os.getenv("PGDATABASE_AI", "greenhouse_candidates_ai"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD")
}

# Local AI_Access directory
LOCAL_RESUME_DIR = os.getenv("LOCAL_RESUME_DIR")
LOCAL_AI_ACCESS_DIR = os.path.join(LOCAL_RESUME_DIR, "AI_Access")

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_sharepoint_url_for_metadata(graph_client, local_file_path):
    """Get SharePoint URL for a metadata JSON file"""
    try:
        # Get file info from SharePoint - returns (url, filename) tuple
        url, filename = graph_client.get_sharepoint_url_for_local_file(local_file_path)
        return url
        
    except Exception as e:
        return None

def find_metadata_file(candidate_id):
    """Find metadata JSON file for a candidate"""
    # Look for metadata file in AI_Access folder
    for file in os.listdir(LOCAL_AI_ACCESS_DIR):
        if file.startswith(f"{candidate_id}_") and file.endswith("_metadata.json"):
            return os.path.join(LOCAL_AI_ACCESS_DIR, file)
    return None

def add_metadata_column():
    """Add metadata_url column to database if it doesn't exist"""
    try:
        with psycopg2.connect(**PG) as conn:
            with conn.cursor() as cur:
                # Check if column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'gh' 
                    AND table_name = 'candidates' 
                    AND column_name = 'metadata_url'
                """)
                
                if not cur.fetchone():
                    log("Adding metadata_url column to database...")
                    cur.execute("""
                        ALTER TABLE gh.candidates 
                        ADD COLUMN metadata_url TEXT
                    """)
                    conn.commit()
                    log("✅ Column added successfully")
                else:
                    log("✅ metadata_url column already exists")
                    
    except Exception as e:
        log(f"❌ Error adding column: {e}")
        raise

def map_metadata_links():
    """Map metadata JSON files to SharePoint URLs"""
    log("="*60)
    log("MAPPING METADATA JSON FILES")
    log("="*60)
    
    # Add metadata_url column if needed
    add_metadata_column()
    
    # Connect to SharePoint
    log("\nConnecting to SharePoint...")
    try:
        graph_client = GraphClient()
        site_info = graph_client.get_site_info()
        log(f"✅ Connected to SharePoint: {site_info.get('displayName')}")
    except Exception as e:
        log(f"❌ Failed to connect to SharePoint: {e}")
        return False
    
    # Get candidates that have resume links but no metadata URL
    log("\nFetching candidates from database...")
    
    try:
        with psycopg2.connect(**PG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM gh.candidates 
                    WHERE resume_links IS NOT NULL 
                    AND array_length(resume_links, 1) > 0
                    AND (metadata_url IS NULL OR metadata_url = '')
                """)
                total = cur.fetchone()[0]
                log(f"Candidates needing metadata URLs: {total:,}")
            
            success_count = 0
            failed_count = 0
            no_metadata_count = 0
            batch_size = 100
            
            for offset in range(0, total, batch_size):
                with conn.cursor() as cur:
                    # Fetch batch of candidates
                    cur.execute("""
                        SELECT candidate_id, full_name
                        FROM gh.candidates
                        WHERE resume_links IS NOT NULL 
                        AND array_length(resume_links, 1) > 0
                        AND (metadata_url IS NULL OR metadata_url = '')
                        ORDER BY candidate_id
                        LIMIT %s OFFSET %s
                    """, (batch_size, offset))
                    
                    candidates = cur.fetchall()
                    
                    if offset % 1000 == 0:
                        log(f"Progress: {offset:,}/{total:,} ({offset/total*100:.1f}%)")
                        log(f"Processing batch {offset//batch_size + 1}: candidates {offset+1} to {min(offset+batch_size, total)}")
                    
                    for candidate_id, full_name in candidates:
                        try:
                            # Find metadata file
                            metadata_file = find_metadata_file(candidate_id)
                            
                            if not metadata_file:
                                no_metadata_count += 1
                                if no_metadata_count % 100 == 0:
                                    log(f"  ⚠️  No metadata file found for {no_metadata_count} candidates so far")
                                continue
                            
                            # Get SharePoint URL
                            metadata_url = get_sharepoint_url_for_metadata(graph_client, metadata_file)
                            
                            if metadata_url:
                                # Update database
                                with conn.cursor() as update_cur:
                                    update_cur.execute("""
                                        UPDATE gh.candidates
                                        SET metadata_url = %s
                                        WHERE candidate_id = %s
                                    """, (metadata_url, candidate_id))
                                    conn.commit()
                                
                                success_count += 1
                                log(f"  ✅ Mapped candidate {candidate_id}: {full_name}")
                            else:
                                failed_count += 1
                                
                        except Exception as e:
                            failed_count += 1
                            log(f"  ❌ Error mapping {candidate_id}: {e}")
                            continue
            
            # Final summary
            log("")
            log("="*60)
            log("METADATA MAPPING SUMMARY")
            log("="*60)
            log(f"Total candidates: {total:,}")
            log(f"Successfully mapped: {success_count:,}")
            log(f"Failed to map: {failed_count:,}")
            log(f"No metadata file: {no_metadata_count:,}")
            
            if success_count > 0:
                success_rate = (success_count / (success_count + failed_count)) * 100
                log(f"Success rate: {success_rate:.1f}%")
            
            log("="*60)
            log("✅ Metadata links mapped successfully!")
            log("")
            log("📊 Next step: Export AI-friendly CSV")
            log("   Run: python export_ai_access_csv.py")
            
            return True
            
    except Exception as e:
        log(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    map_metadata_links()
