#!/usr/bin/env python3
"""
SharePoint CSV Exporter

Exports candidates from SharePoint-enabled database to CSV file with SharePoint links.
Uses same format as original exporter but with SharePoint URLs instead of S3 URLs.
"""

import os
import pandas as pd
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "greenhouse_candidates_sp"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def export_to_csv(sync_type="sync"):
    """
    Export candidates from SharePoint database to CSV file with Zapier-compatible format
    Creates timestamped files in exports/ directory with SharePoint links
    
    Args:
        sync_type: "full" for full sync, "sync" for incremental sync
    """
    log("Starting SharePoint CSV export...")
    
    try:
        # Create exports directory if it doesn't exist - SharePoint Database
        exports_dir = os.path.join(os.path.dirname(__file__), "sharepoint_database", "full")
        os.makedirs(exports_dir, exist_ok=True)
        
        # Generate timestamped filename - single format that's both readable and filesystem-safe
        now = datetime.now()
        date_str = now.strftime("%m.%d.%Y")  # Use dots instead of slashes
        time_str = now.strftime("%H.%M.%S")  # Use dots instead of colons
        csv_filename = f"gh_spCandidates_export_{sync_type}_{date_str}_{time_str}.csv"
        csv_path = os.path.join(exports_dir, csv_filename)
        
        with psycopg2.connect(**PG) as connection:
            # Query with array-to-string conversion to match Zapier format
            # Same query as original but from SharePoint database
            export_query = """
            SELECT
              candidate_id,
              full_name,
              email,
              phone_numbers,
              addresses,
              created_at,
              updated_at,
              -- Convert arrays to strings to match Zapier Table format
              array_to_string(resume_links, E'\\n') AS resume_links,
              array_to_string(resume_filenames, ', ') AS resume_filenames,
              array_to_string(degrees, ', ') AS degrees,
              array_to_string(employment_titles, ', ') AS employment_titles,
              array_to_string(employment_companies, ', ') AS employment_companies,
              array_to_string(jobs_name, ', ') AS jobs_name
            FROM gh.candidates
            ORDER BY updated_at DESC NULLS LAST;
            """
            
            dataframe = pd.read_sql_query(export_query, connection)
            dataframe.to_csv(csv_path, index=False)
            
        log(f"SharePoint CSV export completed! {len(dataframe)} rows exported to {csv_filename}")
        log(f"File saved as: exports/sharepoint_database/full/{csv_filename}")
        
        # Also create/update a "latest" symlink for convenience
        latest_path = os.path.join(exports_dir, "latest_export.csv")
        if os.path.exists(latest_path) or os.path.islink(latest_path):
            os.remove(latest_path)
        os.symlink(csv_filename, latest_path)
        log(f"Latest export symlink updated: {latest_path}")
        
        return len(dataframe), csv_path
        
    except Exception as e:
        log(f"Error during SharePoint CSV export: {e}")
        raise

def get_export_stats():
    """Get statistics about the SharePoint database for export"""
    try:
        with psycopg2.connect(**PG) as connection:
            with connection.cursor() as cur:
                # Total candidates
                cur.execute("SELECT COUNT(*) FROM gh.candidates")
                total_candidates = cur.fetchone()[0]
                
                # Candidates with SharePoint links
                cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE array_length(resume_links, 1) > 0")
                with_sharepoint_links = cur.fetchone()[0]
                
                # Mapping statistics
                cur.execute("""
                    SELECT 
                        mapping_status,
                        COUNT(*) as count
                    FROM gh.sharepoint_mapping_audit 
                    GROUP BY mapping_status
                """)
                mapping_stats = {row[0]: row[1] for row in cur.fetchall()}
                
                return {
                    "total_candidates": total_candidates,
                    "with_sharepoint_links": with_sharepoint_links,
                    "mapping_stats": mapping_stats
                }
                
    except Exception as e:
        log(f"Error getting export stats: {e}")
        return None

def main():
    """Main export function"""
    log("SharePoint CSV Export Tool")
    log("="*50)
    
    # Get and display statistics
    stats = get_export_stats()
    if stats:
        log(f"Database: {PG['dbname']}")
        log(f"Total candidates: {stats['total_candidates']:,}")
        log(f"With SharePoint links: {stats['with_sharepoint_links']:,}")
        
        if stats['mapping_stats']:
            log("Mapping status breakdown:")
            for status, count in stats['mapping_stats'].items():
                log(f"  {status}: {count:,}")
        
        coverage = (stats['with_sharepoint_links'] / stats['total_candidates'] * 100) if stats['total_candidates'] > 0 else 0
        log(f"SharePoint coverage: {coverage:.1f}%")
        log("")
    
    # Export CSV
    try:
        exported_count, csv_path = export_to_csv("sync")
        log(f"✅ Export completed successfully!")
        log(f"📄 File: {os.path.basename(csv_path)}")
        log(f"📊 Rows: {exported_count:,}")
        log(f"📁 Location: {csv_path}")
        
        if stats and stats['with_sharepoint_links'] > 0:
            log(f"🔗 SharePoint links: {stats['with_sharepoint_links']:,} candidates have accessible resume links")
        
    except Exception as e:
        log(f"❌ Export failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
