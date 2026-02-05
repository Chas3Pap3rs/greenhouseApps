#!/usr/bin/env python3
"""
Greenhouse Candidates ETL Script
(ETL = Extract, Transform, Load)

This script:
1. Pulls candidates from Greenhouse Harvest API (up to 500/page, auto-paginates)
2. Upserts into PostgreSQL (dedupe on candidate_id)
3. Stores multi-value fields as parallel arrays to keep indices aligned
4. Exports CSV with Zapier-compatible column names

Usage:
    python main.py                    # Run incremental sync + export
    python main.py --full-sync        # Force full backfill
    python main.py --export-only      # Only export CSV from existing data
"""

import os
import sys
import time
import json
import argparse
import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values, Json
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables
load_dotenv()

# Database configuration
PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "greenhouse_candidates"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

# API configuration
GH_KEY = os.getenv("GREENHOUSE_API_KEY")
BASE_URL = "https://harvest.greenhouse.io/v1"
PAGE_SIZE = max(1, min(500, int(os.getenv("PAGE_SIZE", "500"))))  # clamp at 500
CSV_PATH = os.getenv("CSV_PATH", "./candidates_export.csv")
INITIAL_SINCE = os.getenv("INITIAL_SINCE", "2020-01-01T00:00:00Z")
RESUME_CONTENT_FIELD_ID = os.getenv("RESUME_CONTENT_FIELD_ID", "11138961008")  # Custom field ID for resume_content

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def gh_get(url, params=None, attempt=1):
    """
    Make HTTP GET request to Greenhouse API with exponential backoff retry logic
    """
    auth = requests.auth.HTTPBasicAuth(GH_KEY, "")
    
    try:
        response = requests.get(url, auth=auth, params=params, timeout=60)
        
        # Handle rate limiting and server errors with exponential backoff
        if response.status_code in (429, 500, 502, 503, 504) and attempt <= 6:
            sleep_time = min(60, (2 ** (attempt - 1)) + (0.1 * attempt))
            log(f"Rate limited or server error (status {response.status_code}), retrying in {sleep_time:.1f}s (attempt {attempt}/6)")
            time.sleep(sleep_time)
            return gh_get(url, params, attempt + 1)
        
        response.raise_for_status()
        data = response.json()
        
        # Parse Link header for pagination
        next_url = None
        link_header = response.headers.get("Link")
        if link_header and 'rel="next"' in link_header:
            for part in link_header.split(","):
                if 'rel="next"' in part:
                    next_url = part.split(";")[0].strip().strip("<>")
                    break
        
        return data, next_url
        
    except requests.exceptions.RequestException as e:
        log(f"Request failed: {e}")
        if attempt <= 3:
            log(f"Retrying in 5 seconds (attempt {attempt}/3)")
            time.sleep(5)
            return gh_get(url, params, attempt + 1)
        raise

def safe_string(value):
    """Convert value to string, handling None values"""
    return "" if value is None else str(value)

def first_value(array, key=None):
    """Get first value from array, optionally extracting a key from dict"""
    if not isinstance(array, list) or not array:
        return ""
    
    first_item = array[0]
    if key and isinstance(first_item, dict):
        value = first_item.get(key)
    else:
        value = first_item
    
    return "" if value is None else str(value)

def normalize_spaces(text):
    """Normalize whitespace in text"""
    return " ".join(safe_string(text).split()).strip()

def flatten_candidate(candidate):
    """
    Transform a Greenhouse candidate object into a flat row for database insertion
    """
    # Basic identity fields
    first_name = safe_string(candidate.get("first_name"))
    last_name = safe_string(candidate.get("last_name"))
    full_name = normalize_spaces(f"{first_name} {last_name}")
    
    # Contact information - take first value from arrays
    email = first_value(candidate.get("email_addresses"), "value")
    phone = first_value(candidate.get("phone_numbers"), "value")
    address = first_value(candidate.get("addresses"), "value")
    
    # Resume attachments - filter for type="resume" and preserve order
    resumes = []
    for attachment in (candidate.get("attachments") or []):
        if attachment and attachment.get("type") == "resume":
            resumes.append(attachment)
    
    resume_links = [safe_string(resume.get("url")) for resume in resumes]
    resume_filenames = [safe_string(resume.get("filename")) for resume in resumes]
    
    # Employment history - parallel arrays to maintain index alignment
    employment_titles = []
    employment_companies = []
    for employment in (candidate.get("employments") or []):
        if not isinstance(employment, dict):
            continue
        
        title = safe_string(employment.get("title")).strip()
        company = safe_string(employment.get("company_name")).strip()
        
        if title:
            employment_titles.append(title)
        if company:
            employment_companies.append(company)
    
    # Education degrees
    degrees = []
    for education in (candidate.get("educations") or []):
        if isinstance(education, dict) and education.get("degree"):
            degree = safe_string(education.get("degree")).strip()
            if degree:
                degrees.append(degree)
    
    # Job applications - extract job names
    jobs_names = []
    for application in (candidate.get("applications") or []):
        for job in (application.get("jobs") or []):
            job_name = safe_string(job.get("name")).strip()
            if job_name:
                jobs_names.append(job_name)
    
    # Extract resume_content from custom fields
    resume_content = ""
    for custom_field in (candidate.get("custom_fields") or {}).values():
        if isinstance(custom_field, dict) and str(custom_field.get("id")) == RESUME_CONTENT_FIELD_ID:
            resume_content = safe_string(custom_field.get("value"))
            break
    
    # Return tuple for database insertion
    return (
        int(candidate["id"]),
        safe_string(candidate.get("first_name")),
        safe_string(candidate.get("last_name")),
        full_name,
        email,
        phone,
        address,
        resume_links,
        resume_filenames,
        employment_titles,
        employment_companies,
        degrees,
        jobs_names,
        resume_content,
        candidate.get("created_at"),
        candidate.get("updated_at"),
        Json(candidate)  # Store raw JSON for traceability
    )

def upsert_candidates_batch(connection, candidate_rows):
    """
    Upsert a batch of candidate rows into the database
    """
    upsert_sql = """
    INSERT INTO gh.candidates (
      candidate_id, first_name, last_name, full_name, email, phone_numbers, addresses,
      resume_links, resume_filenames, employment_titles, employment_companies, degrees, jobs_name,
      resume_content, created_at, updated_at, raw
    )
    VALUES %s
    ON CONFLICT (candidate_id) DO UPDATE SET
      first_name=EXCLUDED.first_name,
      last_name=EXCLUDED.last_name,
      full_name=EXCLUDED.full_name,
      email=EXCLUDED.email,
      phone_numbers=EXCLUDED.phone_numbers,
      addresses=EXCLUDED.addresses,
      resume_links=EXCLUDED.resume_links,
      resume_filenames=EXCLUDED.resume_filenames,
      employment_titles=EXCLUDED.employment_titles,
      employment_companies=EXCLUDED.employment_companies,
      degrees=EXCLUDED.degrees,
      jobs_name=EXCLUDED.jobs_name,
      resume_content=EXCLUDED.resume_content,
      created_at=LEAST(gh.candidates.created_at, EXCLUDED.created_at),
      updated_at=GREATEST(gh.candidates.updated_at, EXCLUDED.updated_at),
      raw=EXCLUDED.raw;
    """
    
    with connection.cursor() as cursor:
        execute_values(cursor, upsert_sql, candidate_rows, page_size=100)
    connection.commit()

def get_max_updated_at(connection):
    """Get the maximum updated_at timestamp from existing candidates"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT MAX(updated_at) FROM gh.candidates;")
        result = cursor.fetchone()
        return result[0] if result else None

def determine_sync_start_time(force_full=False):
    """
    Determine the start time for incremental sync
    Uses MAX(updated_at) from database with 2-minute safety overlap, or INITIAL_SINCE for full sync
    """
    if force_full:
        log("Forcing full sync from INITIAL_SINCE")
        return INITIAL_SINCE
    
    try:
        with psycopg2.connect(**PG) as connection:
            max_updated = get_max_updated_at(connection)
        
        if max_updated is None:
            log("No existing data found, starting full sync")
            return INITIAL_SINCE
        
        # Use 2-minute overlap to avoid missing updates
        start_time = (max_updated - timedelta(minutes=2)).astimezone(timezone.utc).isoformat()
        log(f"Starting incremental sync from {start_time}")
        return start_time
        
    except Exception as e:
        log(f"Error determining sync start time: {e}")
        log("Falling back to INITIAL_SINCE")
        return INITIAL_SINCE

def sync_candidates(force_full=False):
    """
    Main sync function - pulls candidates from Greenhouse and upserts to database
    """
    if not GH_KEY:
        raise SystemExit("ERROR: Missing GREENHOUSE_API_KEY in .env file")
    
    log("Starting candidate sync...")
    
    since_timestamp = determine_sync_start_time(force_full)
    params = {"per_page": PAGE_SIZE, "updated_after": since_timestamp}
    url = f"{BASE_URL}/candidates"
    
    total_processed = 0
    page_count = 0
    
    try:
        with psycopg2.connect(**PG) as connection:
            while url:
                page_count += 1
                log(f"Fetching page {page_count}...")
                
                # Fetch data from API
                candidates_data, next_url = gh_get(url, params=params)
                
                # Only first request needs params; subsequent requests use next_url with embedded params
                params = None
                
                if candidates_data:
                    # Transform candidates to database rows
                    candidate_rows = [flatten_candidate(candidate) for candidate in candidates_data]
                    
                    # Upsert to database
                    upsert_candidates_batch(connection, candidate_rows)
                    
                    total_processed += len(candidate_rows)
                    log(f"Processed {len(candidate_rows)} candidates (total: {total_processed})")
                
                url = next_url
                
                # Be gentle on the API
                time.sleep(0.2)
                
    except Exception as e:
        log(f"Error during sync: {e}")
        raise
    
    log(f"Sync completed! Total candidates processed: {total_processed}")
    return total_processed

def export_to_csv(sync_type="sync"):
    """
    Export candidates from database to CSV file with Zapier-compatible format
    Creates timestamped files in exports/ directory
    
    Args:
        sync_type: "full" for full sync, "sync" for incremental sync
    """
    log("Starting CSV export...")
    
    try:
        # Create exports directory if it doesn't exist
        exports_dir = "exports"
        os.makedirs(exports_dir, exist_ok=True)
        
        # Generate timestamped filename - single format that's both readable and filesystem-safe
        now = datetime.now()
        date_str = now.strftime("%m.%d.%Y")  # Use dots instead of slashes
        time_str = now.strftime("%H.%M.%S")  # Use dots instead of colons
        csv_filename = f"gh_candidates_export_{sync_type}_{date_str}_{time_str}.csv"
        csv_path = os.path.join(exports_dir, csv_filename)
        
        with psycopg2.connect(**PG) as connection:
            # Query with array-to-string conversion to match Zapier format
            export_query = """
            WITH indexed_data AS (
              SELECT
                candidate_id,
                full_name,
                email,
                phone_numbers,
                addresses,
                created_at,
                updated_at,
                resume_links,
                resume_filenames,
                degrees,
                jobs_name,
                -- Add index numbers to employment arrays
                ARRAY(
                  SELECT title || '[' || (idx - 1)::text || ']'
                  FROM unnest(employment_titles) WITH ORDINALITY AS t(title, idx)
                ) AS employment_titles_indexed,
                ARRAY(
                  SELECT company || '[' || (idx - 1)::text || ']'
                  FROM unnest(employment_companies) WITH ORDINALITY AS c(company, idx)
                ) AS employment_companies_indexed
              FROM gh.candidates
            )
            SELECT
              candidate_id,
              full_name,
              email,
              phone_numbers,
              addresses,
              created_at,
              updated_at,
              -- Convert arrays to strings
              array_to_string(resume_links, E'\\n') AS resume_links,
              array_to_string(resume_filenames, ', ') AS resume_filenames,
              array_to_string(degrees, ', ') AS degrees,
              array_to_string(employment_titles_indexed, ', ') AS employment_titles,
              array_to_string(employment_companies_indexed, ', ') AS employment_companies,
              array_to_string(jobs_name, ', ') AS jobs_name
            FROM indexed_data
            ORDER BY updated_at DESC NULLS LAST;
            """
            
            dataframe = pd.read_sql_query(export_query, connection)
            dataframe.to_csv(csv_path, index=False)
            
        log(f"CSV export completed! {len(dataframe)} rows exported to {csv_filename}")
        log(f"File saved as: {csv_path}")
        
        # Also create/update a "latest" symlink for convenience
        latest_path = os.path.join(exports_dir, "latest_export.csv")
        if os.path.exists(latest_path) or os.path.islink(latest_path):
            os.remove(latest_path)
        os.symlink(csv_filename, latest_path)
        log(f"Latest export symlink updated: {latest_path}")
        
        return len(dataframe), csv_path
        
    except Exception as e:
        log(f"Error during CSV export: {e}")
        raise

def main():
    """Main entry point with command line argument parsing"""
    parser = argparse.ArgumentParser(description="Greenhouse Candidates ETL")
    parser.add_argument("--full-sync", action="store_true", 
                       help="Force full sync from INITIAL_SINCE instead of incremental")
    parser.add_argument("--export-only", action="store_true",
                       help="Only export CSV from existing database data")
    
    args = parser.parse_args()
    
    try:
        if args.export_only:
            # Only export CSV - use "sync" as default type for export-only
            exported_count, csv_path = export_to_csv("sync")
            log(f"Export completed: {exported_count} rows exported to {csv_path}")
        else:
            # Run sync and then export
            synced_count = sync_candidates(force_full=args.full_sync)
            # Use appropriate sync type based on whether it was a full sync
            sync_type = "full" if args.full_sync else "sync"
            exported_count, csv_path = export_to_csv(sync_type)
            log(f"Pipeline completed: {synced_count} candidates synced, {exported_count} rows exported to {csv_path}")
            
    except KeyboardInterrupt:
        log("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        log(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
