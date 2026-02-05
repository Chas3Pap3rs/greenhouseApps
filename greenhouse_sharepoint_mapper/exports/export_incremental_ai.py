#!/usr/bin/env python3
"""
Incremental AI Access Export - Export only NEW candidates since last full export

This script exports only candidates added since the last full export,
making it easy to append new records to Zapier Tables or other systems
without re-uploading everything.

Usage:
  python export_incremental_ai.py                    # Export new candidates since last full export
  python export_incremental_ai.py --since 2025-01-01 # Export candidates since specific date
  python export_incremental_ai.py --reset            # Reset tracking (next run will be full export)
"""

import os
import sys
import argparse
import pandas as pd
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Database configuration
PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": "greenhouse_candidates_ai",
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

# Tracking file to store last export info
TRACKING_FILE = os.path.join(os.path.dirname(__file__), "ai_database", "incremental", ".last_incremental_export")

# Target size per segment (in MB)
TARGET_SIZE_MB = 45
TARGET_SIZE_BYTES = TARGET_SIZE_MB * 1024 * 1024

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_last_export_info():
    """Get info about the last export"""
    if not os.path.exists(TRACKING_FILE):
        return None
    
    try:
        with open(TRACKING_FILE, 'r') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                last_candidate_id = int(lines[0].strip())
                last_export_date = lines[1].strip()
                return {
                    'last_candidate_id': last_candidate_id,
                    'last_export_date': last_export_date
                }
    except:
        pass
    
    return None

def save_export_info(max_candidate_id):
    """Save info about this export"""
    os.makedirs(os.path.dirname(TRACKING_FILE), exist_ok=True)
    
    with open(TRACKING_FILE, 'w') as f:
        f.write(f"{max_candidate_id}\n")
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

def reset_tracking():
    """Reset tracking file"""
    if os.path.exists(TRACKING_FILE):
        os.remove(TRACKING_FILE)
        log("✅ Reset tracking file. Next export will include all candidates.")
    else:
        log("⚠️  No tracking file found.")

def estimate_rows_per_segment(sample_df, target_bytes):
    """Estimate how many rows fit in target size based on sample"""
    if len(sample_df) == 0:
        return 100
    
    sample_csv = sample_df.to_csv(index=False)
    sample_bytes = len(sample_csv.encode('utf-8'))
    bytes_per_row = sample_bytes / len(sample_df)
    
    estimated_rows = int(target_bytes / bytes_per_row * 0.9)
    return max(10, estimated_rows)

def export_incremental(since_date=None, since_candidate_id=None):
    """Export candidates added since last export or specified date"""
    
    log("="*70)
    log("INCREMENTAL AI ACCESS EXPORT")
    log("="*70)
    
    # Determine what to export
    if since_date:
        filter_type = "date"
        filter_value = since_date
        log(f"Exporting candidates created since: {since_date}")
    elif since_candidate_id:
        filter_type = "candidate_id"
        filter_value = since_candidate_id
        log(f"Exporting candidates with ID > {since_candidate_id}")
    else:
        # Check for last export
        last_export = get_last_export_info()
        if last_export:
            filter_type = "candidate_id"
            filter_value = last_export['last_candidate_id']
            log(f"Last export: {last_export['last_export_date']}")
            log(f"Exporting candidates with ID > {filter_value}")
        else:
            log("⚠️  No previous export found. This will be a FULL export.")
            log("   (Use export_segmented_ai_full.py for full exports)")
            filter_type = None
            filter_value = None
    
    # Connect to database
    log("\nConnecting to database...")
    connection = psycopg2.connect(**PG)
    cursor = connection.cursor()
    
    # Build WHERE clause (no table alias needed in CTE)
    if filter_type == "date":
        where_clause = f"WHERE created_at >= '{filter_value}'"
    elif filter_type == "candidate_id":
        where_clause = f"WHERE candidate_id > {filter_value}"
    else:
        where_clause = ""
    
    # Count new candidates
    count_query = f"""
        SELECT COUNT(*) 
        FROM gh.candidates
        {where_clause}
    """
    
    cursor.execute(count_query)
    total_count = cursor.fetchone()[0]
    
    if total_count == 0:
        log("\n✅ No new candidates to export!")
        connection.close()
        return
    
    log(f"Found {total_count:,} new candidates to export")
    
    # Get sample for size estimation
    log("\nEstimating segment size...")
    sample_query = f"""
        WITH indexed_data AS (
          SELECT
            candidate_id,
            first_name,
            last_name,
            full_name,
            email,
            phone_numbers,
            addresses,
            resume_links[1] as resume_url,
            metadata_url,
            resume_filenames[1] as resume_filename,
            degrees,
            jobs_name,
            created_at,
            updated_at,
            ARRAY(
              SELECT title || '[' || (idx - 1)::text || ']'
              FROM unnest(employment_titles) WITH ORDINALITY AS t(title, idx)
            ) AS employment_titles_indexed,
            ARRAY(
              SELECT company || '[' || (idx - 1)::text || ']'
              FROM unnest(employment_companies) WITH ORDINALITY AS c(company, idx)
            ) AS employment_companies_indexed
          FROM gh.candidates
          {where_clause}
          ORDER BY candidate_id
          LIMIT 100
        )
        SELECT
          candidate_id,
          first_name,
          last_name,
          full_name,
          email,
          phone_numbers,
          addresses,
          resume_url,
          metadata_url,
          resume_filename,
          array_to_string(employment_titles_indexed, ', ') as employment_titles,
          array_to_string(employment_companies_indexed, ', ') as employment_companies,
          array_to_string(degrees, ', ') as degrees,
          array_to_string(jobs_name, ', ') as jobs_name,
          created_at,
          updated_at
        FROM indexed_data;
    """
    
    sample_df = pd.read_sql_query(sample_query, connection)
    rows_per_segment = estimate_rows_per_segment(sample_df, TARGET_SIZE_BYTES)
    num_segments = (total_count + rows_per_segment - 1) // rows_per_segment
    
    log(f"Estimated rows per segment: {rows_per_segment:,}")
    log(f"Estimated segments needed: {num_segments}")
    
    # Create export directory in new structure
    timestamp = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
    export_base = os.path.join(os.path.dirname(__file__), "ai_database", "incremental")
    export_dir = os.path.join(export_base, f"{timestamp}_incremental")
    os.makedirs(export_dir, exist_ok=True)
    
    log(f"\n📁 Export directory: {export_dir}")
    log(f"\nExporting {num_segments} segments...")
    
    # Export segments
    total_rows_exported = 0
    max_candidate_id = 0
    
    for segment_num in range(1, num_segments + 1):
        offset = (segment_num - 1) * rows_per_segment
        
        log(f"Exporting segment {segment_num}/{num_segments}...")
        
        segment_query = f"""
            WITH indexed_data AS (
              SELECT
                candidate_id,
                first_name,
                last_name,
                full_name,
                email,
                phone_numbers,
                addresses,
                resume_links[1] as resume_url,
                metadata_url,
                resume_filenames[1] as resume_filename,
                degrees,
                jobs_name,
                created_at,
                updated_at,
                ARRAY(
                  SELECT title || '[' || (idx - 1)::text || ']'
                  FROM unnest(employment_titles) WITH ORDINALITY AS t(title, idx)
                ) AS employment_titles_indexed,
                ARRAY(
                  SELECT company || '[' || (idx - 1)::text || ']'
                  FROM unnest(employment_companies) WITH ORDINALITY AS c(company, idx)
                ) AS employment_companies_indexed
              FROM gh.candidates
              {where_clause}
              ORDER BY candidate_id
              LIMIT {rows_per_segment} OFFSET {offset}
            )
            SELECT
              candidate_id,
              first_name,
              last_name,
              full_name,
              email,
              phone_numbers,
              addresses,
              resume_url,
              metadata_url,
              resume_filename,
              array_to_string(employment_titles_indexed, ', ') as employment_titles,
              array_to_string(employment_companies_indexed, ', ') as employment_companies,
              array_to_string(degrees, ', ') as degrees,
              array_to_string(jobs_name, ', ') as jobs_name,
              created_at,
              updated_at
            FROM indexed_data;
        """
        
        segment_df = pd.read_sql_query(segment_query, connection)
        
        if len(segment_df) == 0:
            break
        
        # Track max candidate_id
        segment_max_id = segment_df['candidate_id'].max()
        if segment_max_id > max_candidate_id:
            max_candidate_id = segment_max_id
        
        # Save segment
        segment_filename = f"segment_{segment_num:03d}_of_{num_segments:03d}_incremental.csv"
        segment_path = os.path.join(export_dir, segment_filename)
        segment_df.to_csv(segment_path, index=False)
        
        # Get file size
        file_size_mb = os.path.getsize(segment_path) / (1024 * 1024)
        total_rows_exported += len(segment_df)
        
        log(f"  ✅ {segment_filename}: {len(segment_df):,} rows, {file_size_mb:.1f} MB")
    
    # Create manifest
    manifest_path = os.path.join(export_dir, "_manifest.txt")
    with open(manifest_path, 'w') as f:
        f.write(f"Incremental Export Manifest\n")
        f.write(f"="*70 + "\n")
        f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Export Type: Incremental\n")
        if filter_type == "date":
            f.write(f"Filter: Candidates created since {filter_value}\n")
        elif filter_type == "candidate_id":
            f.write(f"Filter: Candidates with ID > {filter_value}\n")
        else:
            f.write(f"Filter: All candidates (full export)\n")
        f.write(f"Total Segments: {num_segments}\n")
        f.write(f"Total Rows: {total_rows_exported:,}\n")
        f.write(f"Max Candidate ID: {max_candidate_id}\n")
        f.write(f"\nSegment Files:\n")
        for i in range(1, num_segments + 1):
            f.write(f"  - segment_{i:03d}_of_{num_segments:03d}_incremental.csv\n")
    
    # Save tracking info
    if max_candidate_id > 0:
        save_export_info(max_candidate_id)
    
    # Summary
    log("\n" + "="*70)
    log("EXPORT COMPLETE!")
    log("="*70)
    log(f"📁 Export directory: {export_dir}")
    log(f"📊 Total segments: {num_segments}")
    log(f"📝 Total rows: {total_rows_exported:,}")
    log(f"📄 Manifest file: {manifest_path}")
    log("")
    log("🎯 Next steps:")
    log("   1. Upload these segments to Zapier Tables (append mode)")
    log("   2. Next incremental export will only include candidates added after this")
    log("="*70)
    
    connection.close()

def main():
    parser = argparse.ArgumentParser(description='Export new candidates incrementally')
    parser.add_argument('--since', help='Export candidates since this date (YYYY-MM-DD)')
    parser.add_argument('--since-id', type=int, help='Export candidates with ID greater than this')
    parser.add_argument('--reset', action='store_true', help='Reset tracking (next export will be full)')
    
    args = parser.parse_args()
    
    if args.reset:
        reset_tracking()
        return
    
    export_incremental(since_date=args.since, since_candidate_id=args.since_id)

if __name__ == "__main__":
    main()
