#!/usr/bin/env python3
"""
Export lightweight CSV with only essential fields for Zapier Tables

This script exports a minimal CSV with only:
- candidate_id
- full_name
- email
- resume_content

Optimized to stay under Zapier's 50MB upload limit.
"""

import os
import sys
import psycopg2
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': os.getenv('PGPORT', '5432'),
    'database': 'greenhouse_candidates_ai',
    'user': os.getenv('PGUSER'),
    'password': os.getenv('PGPASSWORD')
}

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def get_database_stats(cursor):
    """Get statistics about the database"""
    # Total candidates
    cursor.execute("SELECT COUNT(*) FROM gh.candidates")
    total = cursor.fetchone()[0]
    
    # With resume_content
    cursor.execute("""
        SELECT COUNT(*) 
        FROM gh.candidates 
        WHERE resume_content IS NOT NULL AND resume_content != ''
    """)
    with_resume_content = cursor.fetchone()[0]
    
    return {
        "total": total,
        "with_resume_content": with_resume_content
    }

def export_lightweight_csv():
    """Export lightweight CSV with only essential fields"""
    log("Lightweight CSV Export Tool")
    log("=" * 70)
    
    try:
        # Connect to database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Get stats
        stats = get_database_stats(cursor)
        log(f"Database: {DB_CONFIG['database']}")
        log(f"Total candidates: {stats['total']:,}")
        log(f"With resume_content: {stats['with_resume_content']:,} ({stats['with_resume_content']/stats['total']*100:.1f}%)")
        log("")
        
        # Export query - only essential fields
        log("Starting lightweight CSV export...")
        export_query = """
            SELECT 
                candidate_id,
                full_name,
                email,
                resume_content
            FROM gh.candidates
            WHERE resume_content IS NOT NULL AND resume_content != ''
            ORDER BY candidate_id
        """
        
        dataframe = pd.read_sql_query(export_query, connection)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%m.%d.%Y_%H.%M.%S")
        filename = f"gh_candidates_lightweight_{timestamp}.csv"
        export_dir = os.path.join(os.path.dirname(__file__), "ai_database", "full")
        filepath = os.path.join(export_dir, filename)
        
        # Ensure exports directory exists
        os.makedirs(export_dir, exist_ok=True)
        
        # Export to CSV
        dataframe.to_csv(filepath, index=False)
        
        # Create/update symlink to latest export (in parent exports/ directory)
        latest_link = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports", "latest_lightweight_export.csv")
        if os.path.exists(latest_link) or os.path.islink(latest_link):
            os.remove(latest_link)
        os.symlink(f"ai_database/full/{filename}", latest_link)
        
        # Get file size
        file_size_bytes = os.path.getsize(filepath)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        log(f"Lightweight CSV export completed! {len(dataframe):,} rows exported to {filename}")
        log(f"File saved as: {filepath}")
        log(f"File size: {file_size_mb:.1f} MB")
        log(f"Latest export symlink updated: {latest_link}")
        log("")
        
        # Close database connection
        cursor.close()
        connection.close()
        
        # Final summary
        log("=" * 70)
        log("✅ Export completed successfully!")
        log("=" * 70)
        log(f"📄 File: {filename}")
        log(f"📊 Rows: {len(dataframe):,}")
        log(f"💾 Size: {file_size_mb:.1f} MB")
        log(f"📁 Location: {filepath}")
        
        if file_size_mb > 50:
            log("")
            log("⚠️  WARNING: File is larger than 50MB Zapier limit!")
            log(f"   Current size: {file_size_mb:.1f} MB")
            log(f"   Need to reduce by: {file_size_mb - 50:.1f} MB")
            log("")
            log("💡 Suggestions:")
            log("   - Consider splitting into multiple files")
            log("   - Or truncate resume_content to first N characters")
        else:
            log("")
            log(f"✅ File is under 50MB limit! ({file_size_mb:.1f} MB)")
        
        log("")
        log("🎯 This CSV contains only:")
        log("   - candidate_id")
        log("   - full_name")
        log("   - email")
        log("   - resume_content")
        log("   - Ready to upload to Zapier Tables!")
        log("=" * 70)
        
    except Exception as e:
        log(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    export_lightweight_csv()
