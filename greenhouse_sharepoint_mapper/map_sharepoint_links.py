#!/usr/bin/env python3
"""
SharePoint Link Mapper

Maps original candidate database to SharePoint-enabled version.
Replaces Greenhouse S3 URLs with SharePoint sharing links.
"""

import os
import sys
import json
import time
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from graph_client import GraphClient

# Load environment variables
load_dotenv()

# Database configurations
SOURCE_PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("SOURCE_PGDATABASE", "greenhouse_candidates"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

TARGET_PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "greenhouse_candidates_sp"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

LOCAL_RESUME_DIR = os.getenv("LOCAL_RESUME_DIR")
SKIP_IF_ALREADY_MAPPED = os.getenv("SKIP_IF_ALREADY_MAPPED", "true").lower() == "true"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def find_local_resume_file(candidate_id):
    """Find the local resume file for a candidate"""
    if not os.path.exists(LOCAL_RESUME_DIR):
        return None
    
    # Search through organized directory structure
    for root, dirs, files in os.walk(LOCAL_RESUME_DIR):
        for file in files:
            # Check if filename starts with candidate_id
            if file.startswith(f"{candidate_id}_") and not file.startswith("FAILED_"):
                return os.path.join(root, file)
    
    return None

def update_raw_json_attachments(raw_json, sharepoint_url, sharepoint_filename):
    """Update the raw JSON with SharePoint attachment info"""
    if not raw_json or not isinstance(raw_json, dict):
        return raw_json
    
    updated_json = raw_json.copy()
    
    # Update attachments array if it exists
    if "attachments" in updated_json and isinstance(updated_json["attachments"], list):
        for attachment in updated_json["attachments"]:
            if attachment.get("type") == "resume":
                # Update with SharePoint info
                attachment["url"] = sharepoint_url
                attachment["filename"] = sharepoint_filename
                attachment["source"] = "sharepoint"
                attachment["mapped_at"] = datetime.now().isoformat()
                break
    
    return updated_json

def map_candidate_to_sharepoint(candidate_data, graph_client):
    """Map a single candidate to SharePoint version"""
    candidate_id = candidate_data["candidate_id"]
    
    # Find local resume file
    local_file_path = find_local_resume_file(candidate_id)
    
    if not local_file_path:
        # No local resume file found
        mapped_candidate = candidate_data.copy()
        mapped_candidate["resume_links"] = []
        mapped_candidate["resume_filenames"] = []
        mapped_candidate["raw"] = candidate_data.get("raw", {})
        
        return mapped_candidate, "no_resume", None, None
    
    # Get SharePoint URL for the file
    sharepoint_url, sharepoint_filename = graph_client.get_sharepoint_url_for_local_file(local_file_path)
    
    if not sharepoint_url:
        # Failed to get SharePoint URL
        mapped_candidate = candidate_data.copy()
        mapped_candidate["resume_links"] = []
        mapped_candidate["resume_filenames"] = []
        mapped_candidate["raw"] = candidate_data.get("raw", {})
        
        return mapped_candidate, "failed", local_file_path, "Could not generate SharePoint URL"
    
    # Successfully mapped to SharePoint
    mapped_candidate = candidate_data.copy()
    mapped_candidate["resume_links"] = [sharepoint_url]
    mapped_candidate["resume_filenames"] = [sharepoint_filename]
    
    # Update raw JSON
    updated_raw = update_raw_json_attachments(
        candidate_data.get("raw", {}),
        sharepoint_url,
        sharepoint_filename
    )
    mapped_candidate["raw"] = updated_raw
    
    return mapped_candidate, "success", local_file_path, None

def record_mapping_attempt(conn, candidate_id, original_url, sharepoint_url, sharepoint_filename, 
                          local_path, status, error_msg=None):
    """Record mapping attempt in audit table"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO gh.sharepoint_mapping_audit (
                candidate_id, original_resume_url, sharepoint_url, 
                sharepoint_filename, local_file_path, mapping_status, error_message
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (candidate_id) DO UPDATE SET
                original_resume_url = EXCLUDED.original_resume_url,
                sharepoint_url = EXCLUDED.sharepoint_url,
                sharepoint_filename = EXCLUDED.sharepoint_filename,
                local_file_path = EXCLUDED.local_file_path,
                mapping_status = EXCLUDED.mapping_status,
                error_message = EXCLUDED.error_message,
                mapped_at = NOW()
        """, (
            candidate_id, original_url, sharepoint_url, 
            sharepoint_filename, local_path, status, error_msg
        ))
    conn.commit()

def already_mapped(conn, candidate_id):
    """Check if candidate is already mapped"""
    if not SKIP_IF_ALREADY_MAPPED:
        return False
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT mapping_status FROM gh.sharepoint_mapping_audit 
            WHERE candidate_id = %s AND mapping_status IN ('success', 'no_resume')
        """, (candidate_id,))
        return cur.fetchone() is not None

def insert_mapped_candidate(conn, candidate_data):
    """Insert mapped candidate into SharePoint database"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO gh.candidates (
                candidate_id, first_name, last_name, full_name, email,
                phone_numbers, addresses, created_at, updated_at,
                resume_links, resume_filenames, degrees, employment_titles,
                employment_companies, jobs_name, raw
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (candidate_id) DO UPDATE SET
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                full_name = EXCLUDED.full_name,
                email = EXCLUDED.email,
                phone_numbers = EXCLUDED.phone_numbers,
                addresses = EXCLUDED.addresses,
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at,
                resume_links = EXCLUDED.resume_links,
                resume_filenames = EXCLUDED.resume_filenames,
                degrees = EXCLUDED.degrees,
                employment_titles = EXCLUDED.employment_titles,
                employment_companies = EXCLUDED.employment_companies,
                jobs_name = EXCLUDED.jobs_name,
                raw = EXCLUDED.raw
        """, (
            candidate_data["candidate_id"],
            candidate_data.get("first_name"),
            candidate_data.get("last_name"),
            candidate_data.get("full_name"),
            candidate_data.get("email"),
            candidate_data.get("phone_numbers"),
            candidate_data.get("addresses"),
            candidate_data.get("created_at"),
            candidate_data.get("updated_at"),
            candidate_data.get("resume_links", []),
            candidate_data.get("resume_filenames", []),
            candidate_data.get("degrees", []),
            candidate_data.get("employment_titles", []),
            candidate_data.get("employment_companies", []),
            candidate_data.get("jobs_name", []),
            json.dumps(candidate_data.get("raw", {}))
        ))

def main():
    """Main mapping process"""
    log("Starting SharePoint link mapping process...")
    
    # Initialize Graph client
    try:
        graph_client = GraphClient()
        connection_test = graph_client.test_connection()
        
        if not connection_test["success"]:
            log(f"❌ Graph API connection failed: {connection_test['error']}")
            sys.exit(1)
        
        log(f"✅ Connected to SharePoint site: {connection_test['site_name']}")
        
    except Exception as e:
        log(f"❌ Failed to initialize Graph client: {e}")
        log("Make sure Azure credentials are configured in .env file")
        sys.exit(1)
    
    # Counters
    total_candidates = 0
    successful_mappings = 0
    failed_mappings = 0
    no_resume_count = 0
    skipped_count = 0
    
    try:
        with psycopg2.connect(**SOURCE_PG) as source_conn:
            with psycopg2.connect(**TARGET_PG) as target_conn:
                log("Connected to databases")
                
                # Get total count
                with source_conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM gh.candidates")
                    total_count = cur.fetchone()[0]
                    log(f"Total candidates to process: {total_count:,}")
                
                # Process candidates in batches
                offset = 0
                
                while True:
                    with source_conn.cursor() as cur:
                        cur.execute("""
                            SELECT 
                                candidate_id, first_name, last_name, full_name, email,
                                phone_numbers, addresses, created_at, updated_at,
                                resume_links, resume_filenames, degrees, employment_titles,
                                employment_companies, jobs_name, raw
                            FROM gh.candidates
                            ORDER BY candidate_id
                            LIMIT %s OFFSET %s
                        """, (BATCH_SIZE, offset))
                        
                        candidates = cur.fetchall()
                        
                        if not candidates:
                            break  # No more candidates
                        
                        log(f"Processing batch {offset//BATCH_SIZE + 1}: candidates {offset + 1} to {offset + len(candidates)}")
                        
                        for candidate_row in candidates:
                            total_candidates += 1
                            
                            # Convert row to dict
                            candidate_data = {
                                "candidate_id": candidate_row[0],
                                "first_name": candidate_row[1],
                                "last_name": candidate_row[2],
                                "full_name": candidate_row[3],
                                "email": candidate_row[4],
                                "phone_numbers": candidate_row[5],
                                "addresses": candidate_row[6],
                                "created_at": candidate_row[7],
                                "updated_at": candidate_row[8],
                                "resume_links": candidate_row[9] or [],
                                "resume_filenames": candidate_row[10] or [],
                                "degrees": candidate_row[11] or [],
                                "employment_titles": candidate_row[12] or [],
                                "employment_companies": candidate_row[13] or [],
                                "jobs_name": candidate_row[14] or [],
                                "raw": candidate_row[15] or {}
                            }
                            
                            candidate_id = candidate_data["candidate_id"]
                            
                            # Skip if already mapped
                            if already_mapped(target_conn, candidate_id):
                                skipped_count += 1
                                continue
                            
                            # Get original resume URL for audit
                            original_url = None
                            if candidate_data["resume_links"]:
                                original_url = candidate_data["resume_links"][0]
                            
                            # Map to SharePoint
                            mapped_candidate, status, local_path, error_msg = map_candidate_to_sharepoint(
                                candidate_data, graph_client
                            )
                            
                            # Insert mapped candidate
                            insert_mapped_candidate(target_conn, mapped_candidate)
                            
                            # Record mapping attempt
                            sharepoint_url = mapped_candidate["resume_links"][0] if mapped_candidate["resume_links"] else None
                            sharepoint_filename = mapped_candidate["resume_filenames"][0] if mapped_candidate["resume_filenames"] else None
                            
                            record_mapping_attempt(
                                target_conn, candidate_id, original_url, sharepoint_url,
                                sharepoint_filename, local_path, status, error_msg
                            )
                            
                            # Update counters
                            if status == "success":
                                successful_mappings += 1
                                if total_candidates % 50 == 0:  # Log every 50 successful mappings
                                    log(f"  ✅ Mapped candidate {candidate_id}: {mapped_candidate.get('full_name', 'Unknown')}")
                            elif status == "failed":
                                failed_mappings += 1
                                log(f"  ❌ Failed to map candidate {candidate_id}: {error_msg}")
                            elif status == "no_resume":
                                no_resume_count += 1
                            
                            # Be gentle on the API
                            time.sleep(0.1)
                        
                        target_conn.commit()
                        offset += BATCH_SIZE
                        
                        # Progress update
                        progress = (offset / total_count) * 100
                        log(f"Progress: {progress:.1f}% ({offset:,}/{total_count:,})")
    
    except Exception as e:
        log(f"❌ Error during mapping process: {e}")
        sys.exit(1)
    
    # Final summary
    log("\n" + "="*60)
    log("SHAREPOINT MAPPING SUMMARY")
    log("="*60)
    log(f"Total candidates processed: {total_candidates:,}")
    log(f"Successful mappings: {successful_mappings:,}")
    log(f"Failed mappings: {failed_mappings:,}")
    log(f"No resume found: {no_resume_count:,}")
    log(f"Skipped (already mapped): {skipped_count:,}")
    
    success_rate = (successful_mappings / total_candidates * 100) if total_candidates > 0 else 0
    log(f"Success rate: {success_rate:.1f}%")
    
    log(f"\nSharePoint database ready: {TARGET_PG['dbname']}")
    log("Next step: Run 'python export_sharepoint_csv.py' to generate CSV with SharePoint links")

if __name__ == "__main__":
    main()
