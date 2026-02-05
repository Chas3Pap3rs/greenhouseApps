#!/usr/bin/env python3
"""
Map metadata JSON files to SharePoint URLs using batch approach
Gets all files from AI_Access folder at once, then matches by filename
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

def get_all_ai_access_files(graph_client):
    """Get all files from AI_Access folder in one API call"""
    log("Fetching all files from AI_Access folder...")
    
    try:
        import requests
        
        # Use the Graph API to list all files in the AI_Access folder
        ai_access_path = "Greenhouse/Greenhouse_Resumes/AI_Access"
        
        # Build the URL to list folder contents
        url = f"https://graph.microsoft.com/v1.0/sites/{graph_client.site_id}/drive/root:/{ai_access_path}:/children"
        
        all_files = {}
        next_link = url
        page_count = 0
        
        while next_link:
            page_count += 1
            log(f"  Fetching page {page_count}...")
            
            headers = graph_client.get_headers()
            response = requests.get(next_link, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Process files in this page
            for item in data.get('value', []):
                if 'file' in item:  # It's a file, not a folder
                    filename = item.get('name')
                    web_url = item.get('webUrl')
                    
                    if filename and web_url:
                        all_files[filename] = web_url
            
            # Check for next page
            next_link = data.get('@odata.nextLink')
            
            if page_count % 10 == 0:
                log(f"  Processed {len(all_files):,} files so far...")
        
        log(f"✅ Found {len(all_files):,} total files in AI_Access folder")
        return all_files
        
    except Exception as e:
        log(f"❌ Error fetching files: {e}")
        raise

def map_metadata_links_batch():
    """Map metadata JSON files using batch approach"""
    log("="*60)
    log("MAPPING METADATA JSON FILES (BATCH MODE)")
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
    
    # Get all files from AI_Access folder
    try:
        all_files = get_all_ai_access_files(graph_client)
    except Exception as e:
        log(f"❌ Failed to fetch files: {e}")
        return False
    
    # Filter to only metadata files
    metadata_files = {name: url for name, url in all_files.items() if name.endswith('_metadata.json')}
    log(f"Found {len(metadata_files):,} metadata JSON files")
    
    # Get candidates that need metadata URLs
    log("\nFetching candidates from database...")
    
    try:
        with psycopg2.connect(**PG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM gh.candidates 
                    WHERE resume_links IS NOT NULL 
                    AND array_length(resume_links, 1) > 0
                """)
                total = cur.fetchone()[0]
                log(f"Total candidates with resumes: {total:,}")
            
            success_count = 0
            no_metadata_count = 0
            batch_size = 1000
            
            for offset in range(0, total, batch_size):
                with conn.cursor() as cur:
                    # Fetch batch of candidates
                    cur.execute("""
                        SELECT candidate_id, full_name, resume_filenames[1]
                        FROM gh.candidates
                        WHERE resume_links IS NOT NULL 
                        AND array_length(resume_links, 1) > 0
                        ORDER BY candidate_id
                        LIMIT %s OFFSET %s
                    """, (batch_size, offset))
                    
                    candidates = cur.fetchall()
                    
                    if offset % 5000 == 0:
                        log(f"Progress: {offset:,}/{total:,} ({offset/total*100:.1f}%)")
                    
                    for candidate_id, full_name, resume_filename in candidates:
                        if not resume_filename:
                            no_metadata_count += 1
                            continue
                        
                        # Generate expected metadata filename
                        # Remove extension and add _metadata.json
                        base_name = resume_filename.rsplit('.', 1)[0]
                        metadata_filename = f"{base_name}_metadata.json"
                        
                        # Look up in our files dictionary
                        if metadata_filename in metadata_files:
                            metadata_url = metadata_files[metadata_filename]
                            
                            # Update database
                            with conn.cursor() as update_cur:
                                update_cur.execute("""
                                    UPDATE gh.candidates
                                    SET metadata_url = %s
                                    WHERE candidate_id = %s
                                """, (metadata_url, candidate_id))
                                conn.commit()
                            
                            success_count += 1
                            
                            if success_count % 1000 == 0:
                                log(f"  ✅ Mapped {success_count:,} metadata URLs so far")
                        else:
                            no_metadata_count += 1
            
            # Final summary
            log("")
            log("="*60)
            log("METADATA MAPPING SUMMARY")
            log("="*60)
            log(f"Total candidates: {total:,}")
            log(f"Successfully mapped: {success_count:,}")
            log(f"No metadata file: {no_metadata_count:,}")
            
            if success_count > 0:
                success_rate = (success_count / total) * 100
                log(f"Success rate: {success_rate:.1f}%")
            
            log("="*60)
            log("✅ Metadata links mapped successfully!")
            log("")
            log("📊 Next step: Export AI-friendly CSV")
            log("   Run: python export_ai_access_csv.py")
            
            return True
            
    except Exception as e:
        log(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    map_metadata_links_batch()
