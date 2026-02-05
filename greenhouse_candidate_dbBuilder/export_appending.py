#!/usr/bin/env python3
"""
Appending Export - Export only NEW candidates since last export

This script exports only candidates that were added since the last export run.
It tracks the last exported candidate_id and only exports newer candidates.

Use this for incremental Zapier uploads to append new rows without re-uploading everything.
"""

import os
import sys
import pandas as pd
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Database configuration
PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "greenhouse_candidates"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

# Tracking file to store last exported candidate_id
TRACKING_FILE = "exports/.last_appending_export"

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_last_exported_id():
    """Get the last exported candidate_id from tracking file"""
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, 'r') as f:
            return int(f.read().strip())
    return 0

def save_last_exported_id(candidate_id):
    """Save the last exported candidate_id to tracking file"""
    os.makedirs(os.path.dirname(TRACKING_FILE), exist_ok=True)
    with open(TRACKING_FILE, 'w') as f:
        f.write(str(candidate_id))

def export_new_candidates():
    """Export only new candidates since last export"""
    log("Starting appending export (new candidates only)...")
    
    try:
        # Get last exported ID
        last_id = get_last_exported_id()
        log(f"Last exported candidate_id: {last_id}")
        
        # Create exports directory
        exports_dir = "exports"
        os.makedirs(exports_dir, exist_ok=True)
        
        # Generate timestamped filename
        now = datetime.now()
        date_str = now.strftime("%m.%d.%Y")
        time_str = now.strftime("%H.%M.%S")
        csv_filename = f"gh_candidates_appending_{date_str}_{time_str}.csv"
        csv_path = os.path.join(exports_dir, csv_filename)
        
        with psycopg2.connect(**PG) as connection:
            # Query only candidates with ID greater than last exported
            # Keep employment arrays indexed (paired)
            export_query = f"""
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
              WHERE candidate_id > {last_id}
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
            ORDER BY candidate_id ASC;
            """
            
            dataframe = pd.read_sql_query(export_query, connection)
            
            if len(dataframe) == 0:
                log("No new candidates to export!")
                return 0, None
            
            # Export to CSV
            dataframe.to_csv(csv_path, index=False)
            
            # Update tracking file with highest candidate_id
            max_id = dataframe['candidate_id'].max()
            save_last_exported_id(max_id)
            
        log(f"Appending export completed! {len(dataframe)} new candidates exported")
        log(f"File saved as: {csv_path}")
        log(f"Candidate ID range: {dataframe['candidate_id'].min()} to {max_id}")
        log(f"Updated tracking file with last ID: {max_id}")
        
        # Create/update symlink
        latest_path = os.path.join(exports_dir, "latest_appending_export.csv")
        if os.path.exists(latest_path) or os.path.islink(latest_path):
            os.remove(latest_path)
        os.symlink(csv_filename, latest_path)
        log(f"Latest appending export symlink updated: {latest_path}")
        
        return len(dataframe), csv_path
        
    except Exception as e:
        log(f"Error during appending export: {e}")
        raise

def reset_tracking():
    """Reset tracking file (use with caution!)"""
    if os.path.exists(TRACKING_FILE):
        os.remove(TRACKING_FILE)
        log("Tracking file reset. Next export will include all candidates.")
    else:
        log("No tracking file to reset.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Export new candidates only (appending)")
    parser.add_argument("--reset", action="store_true", help="Reset tracking (next export will include all)")
    args = parser.parse_args()
    
    if args.reset:
        reset_tracking()
    else:
        count, path = export_new_candidates()
        if count > 0:
            log(f"✅ Successfully exported {count} new candidates!")
            log(f"📁 Upload this file to Zapier to append new rows: {path}")
        else:
            log("✅ Already up to date - no new candidates to export")
