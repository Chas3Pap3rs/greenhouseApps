#!/usr/bin/env python3
"""
Segmented AI Access Export (Lightweight) - Split into ~50MB chunks for Zapier

This script exports all candidates from greenhouse_candidates_ai database
with AI-friendly SharePoint links (NO resume_content), split into segments
under 50MB each for Zapier Tables compatibility.

For full version with resume_content, use export_segmented_ai_full.py
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
    "dbname": "greenhouse_candidates_ai",
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

# Target size per segment (in MB) - aim for 45MB to stay safely under 50MB
TARGET_SIZE_MB = 45
TARGET_SIZE_BYTES = TARGET_SIZE_MB * 1024 * 1024

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def estimate_rows_per_segment(sample_df, target_bytes):
    """Estimate how many rows fit in target size based on sample"""
    if len(sample_df) == 0:
        return 1000  # Default fallback
    
    # Get size of sample
    sample_csv = sample_df.to_csv(index=False)
    sample_bytes = len(sample_csv.encode('utf-8'))
    bytes_per_row = sample_bytes / len(sample_df)
    
    # Calculate rows per segment with safety margin
    rows_per_segment = int((target_bytes * 0.95) / bytes_per_row)  # 95% to be safe
    
    return max(rows_per_segment, 100)  # Minimum 100 rows per segment

def export_segmented():
    """Export AI Access candidates (lightweight) in segments under 50MB"""
    log("="*70)
    log("SEGMENTED AI ACCESS EXPORT (LIGHTWEIGHT) - Zapier Compatible")
    log("="*70)
    log("✅ No resume_content - fetch via Greenhouse API when needed")
    log("="*70)
    log("")
    
    try:
        # Create timestamped export folder in new structure
        now = datetime.now()
        folder_name = now.strftime("%Y.%m.%d_%H.%M.%S")
        export_base = os.path.join(os.path.dirname(__file__), "ai_database", "segmented")
        export_dir = os.path.join(export_base, folder_name)
        os.makedirs(export_dir, exist_ok=True)
        
        log(f"Export directory: {export_dir}")
        log("")
        
        with psycopg2.connect(**PG) as connection:
            # First, get total count
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM gh.candidates")
            total_count = cursor.fetchone()[0]
            log(f"Total candidates to export: {total_count:,}")
            
            # Get a sample to estimate segment size
            log("Analyzing data to determine segment size...")
            sample_query = """
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
              ORDER BY candidate_id
              LIMIT 1000
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
            
            log(f"Estimated rows per segment: {rows_per_segment:,}")
            estimated_segments = (total_count + rows_per_segment - 1) // rows_per_segment
            log(f"Estimated number of segments: {estimated_segments}")
            log("")
            
            # Export in segments
            segment_num = 1
            offset = 0
            segment_files = []
            
            while offset < total_count:
                log(f"Exporting segment {segment_num}/{estimated_segments}...")
                
                # Query for this segment (NO resume_content)
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
                
                # Generate filename
                segment_filename = f"segment_{segment_num:03d}_of_{estimated_segments:03d}.csv"
                segment_path = os.path.join(export_dir, segment_filename)
                
                # Export segment
                segment_df.to_csv(segment_path, index=False)
                
                # Check file size
                file_size_mb = os.path.getsize(segment_path) / (1024 * 1024)
                
                log(f"  ✅ {segment_filename}: {len(segment_df):,} rows, {file_size_mb:.1f} MB")
                
                if file_size_mb > 50:
                    log(f"  ⚠️  WARNING: Segment exceeds 50MB! Consider reducing rows_per_segment.")
                
                segment_files.append({
                    'filename': segment_filename,
                    'rows': len(segment_df),
                    'size_mb': file_size_mb,
                    'id_range': f"{segment_df['candidate_id'].min()} to {segment_df['candidate_id'].max()}"
                })
                
                offset += rows_per_segment
                segment_num += 1
            
            cursor.close()
        
        # Create manifest file
        manifest_path = os.path.join(export_dir, "_manifest.txt")
        with open(manifest_path, 'w') as f:
            f.write(f"Segmented AI Access Export Manifest (LIGHTWEIGHT)\n")
            f.write(f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Candidates: {total_count:,}\n")
            f.write(f"Total Segments: {len(segment_files)}\n")
            f.write(f"\n")
            f.write(f"Segments:\n")
            f.write(f"-" * 80 + "\n")
            for seg in segment_files:
                f.write(f"{seg['filename']:<40} {seg['rows']:>6,} rows  {seg['size_mb']:>6.1f} MB  IDs: {seg['id_range']}\n")
            f.write(f"-" * 80 + "\n")
            f.write(f"\nNOTE: This export does NOT include resume_content to keep files under 50MB.\n")
            f.write(f"AI agents should fetch resume_content via Greenhouse API when needed:\n")
            f.write(f"  GET https://harvest.greenhouse.io/v1/candidates/{{candidate_id}}\n")
            f.write(f"  Custom Field: resume_content (ID: 11138961008)\n")
            f.write(f"\nUpload Order: Upload segments to Zapier in numerical order (001, 002, 003, ...)\n")
            f.write(f"Each segment can be uploaded separately to append rows.\n")
        
        log("")
        log("="*70)
        log("EXPORT COMPLETE!")
        log("="*70)
        log(f"📁 Export directory: {export_dir}")
        log(f"📊 Total segments: {len(segment_files)}")
        log(f"📝 Total rows: {total_count:,}")
        log(f"📄 Manifest file: {manifest_path}")
        log("")
        log("🎯 Next steps:")
        log("   1. Navigate to the export directory")
        log("   2. Upload segments to Zapier Tables in order (001, 002, 003, ...)")
        log("   3. Each segment is under 50MB and Zapier-compatible")
        log("   4. AI agents fetch resume_content via Greenhouse API when needed")
        log("="*70)
        
        return len(segment_files), export_dir
        
    except Exception as e:
        log(f"❌ Error during segmented export: {e}")
        raise

if __name__ == "__main__":
    segment_count, export_dir = export_segmented()
    print(f"\n✅ Successfully created {segment_count} Zapier-compatible segments in: {export_dir}")
