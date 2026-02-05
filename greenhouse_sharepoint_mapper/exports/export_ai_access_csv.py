#!/usr/bin/env python3
"""
Export AI Access CSV (Lightweight)

Exports candidates from greenhouse_candidates_ai database with AI-friendly
flat folder SharePoint links for agent consumption.

This version does NOT include resume_content to keep file size under 50MB.
For AI agents: Use this CSV for candidate metadata, then fetch resume_content
via Greenhouse API when needed for specific candidates.

For full version with resume_content, use export_ai_access_csv_full.py
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

# Export directory - AI Database (Full exports without resume_content)
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "ai_database", "full")

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_database_stats(connection):
    """Get statistics about the database"""
    with connection.cursor() as cursor:
        # Total candidates
        cursor.execute("SELECT COUNT(*) FROM gh.candidates")
        total = cursor.fetchone()[0]
        
        # With AI Access links (stored in resume_links column)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM gh.candidates 
            WHERE resume_links IS NOT NULL AND array_length(resume_links, 1) > 0
        """)
        with_ai_links = cursor.fetchone()[0]
        
        # With resume_content
        cursor.execute("""
            SELECT COUNT(*) 
            FROM gh.candidates 
            WHERE resume_content IS NOT NULL AND resume_content != ''
        """)
        with_resume_content = cursor.fetchone()[0]
        
        # No mapping audit table in AI database
        status_breakdown = []
        
        return {
            "total": total,
            "with_ai_links": with_ai_links,
            "with_resume_content": with_resume_content,
            "status_breakdown": status_breakdown
        }

def export_ai_csv():
    """Export AI-friendly CSV with flat folder links"""
    log("AI Access CSV Export Tool")
    log("="*60)
    
    # Create export directory
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    try:
        # Connect to database
        connection = psycopg2.connect(**PG)
        
        # Get stats
        stats = get_database_stats(connection)
        log(f"Database: greenhouse_candidates_ai")
        log(f"Total candidates: {stats['total']:,}")
        log(f"With AI Access links: {stats['with_ai_links']:,}")
        
        if stats['status_breakdown']:
            log("Mapping status breakdown:")
            for status, count in stats['status_breakdown']:
                log(f"  {status}: {count:,}")
        
        if stats['with_ai_links'] > 0:
            coverage = (stats['with_ai_links'] / stats['total']) * 100
            log(f"AI Access coverage: {coverage:.1f}%")
        
        log("")
        log("Starting AI Access CSV export...")
        
        # Export query - optimized for AI agent consumption (lightweight)
        # Extract first element from arrays for CSV compatibility
        # Use actual metadata_url from database (mapped via map_metadata_links.py)
        # Does NOT include resume_content to keep file size small
        export_query = """
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
            FROM indexed_data
            ORDER BY candidate_id
        """
        
        # Read into DataFrame
        dataframe = pd.read_sql_query(export_query, connection)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%m.%d.%Y_%H.%M.%S")
        filename = f"gh_aiCandidates_export_sync_{timestamp}.csv"
        filepath = os.path.join(EXPORT_DIR, filename)
        
        # Export to CSV
        dataframe.to_csv(filepath, index=False)
        
        # Create symlink to latest export (in parent exports/ directory)
        latest_link = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports", "latest_ai_export.csv")
        if os.path.exists(latest_link) or os.path.islink(latest_link):
            os.remove(latest_link)
        os.symlink(f"ai_database/full/{filename}", latest_link)
        
        log(f"AI Access CSV export completed! {len(dataframe)} rows exported to {filename}")
        log(f"File saved as: exports/ai_database/full/{filename}")
        log(f"Latest export symlink updated: exports/latest_ai_export.csv")
        
        log("")
        log("="*60)
        log("✅ Export completed successfully!")
        log("="*60)
        log(f"📄 File: {filename}")
        log(f"📊 Rows: {len(dataframe):,}")
        log(f"📁 Location: exports/{filename}")
        log(f"🔗 AI Access links: {stats['with_ai_links']:,} candidates")
        log(f"📝 Metadata links: {stats['with_ai_links']:,} JSON files")
        log(f"📝 Resume content: {stats['with_resume_content']:,} candidates in database ({stats['with_resume_content']/stats['total']*100:.1f}%)")
        log(f"⚠️  Note: resume_content NOT included in this export (use export_ai_access_csv_full.py for full version)")
        log("")
        log("🎯 This CSV is optimized for AI agents:")
        log("   - Flat folder structure (no nested paths)")
        log("   - Direct resume URLs for file access")
        log("   - Metadata JSON URLs for text extraction")
        log("   - Lightweight (no resume_content) - under 50MB for Zapier Tables")
        log("   - Fetch resume_content via Greenhouse API when needed")
        log("")
        log("💡 For full version with resume_content, run: python export_ai_access_csv_full.py")
        log("="*60)
        
        connection.close()
        return True
        
    except Exception as e:
        log(f"❌ Export failed: {e}")
        return False

def main():
    """Main execution"""
    success = export_ai_csv()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
