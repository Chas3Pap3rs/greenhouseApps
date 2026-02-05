#!/usr/bin/env python3
"""
Status check script for Greenhouse Candidates ETL
Shows current database state and sync status
"""

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "greenhouse_candidates"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

def get_database_stats():
    """Get current database statistics"""
    try:
        with psycopg2.connect(**PG) as conn:
            with conn.cursor() as cur:
                # Total candidates
                cur.execute("SELECT COUNT(*) FROM gh.candidates;")
                total_candidates = cur.fetchone()[0]
                
                # Latest update timestamp
                cur.execute("SELECT MAX(updated_at) FROM gh.candidates;")
                latest_update = cur.fetchone()[0]
                
                # Candidates with resumes
                cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE array_length(resume_links, 1) > 0;")
                candidates_with_resumes = cur.fetchone()[0]
                
                # Candidates with employment history
                cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE array_length(employment_titles, 1) > 0;")
                candidates_with_employment = cur.fetchone()[0]
                
                # Recent candidates (last 7 days)
                cur.execute("""
                    SELECT COUNT(*) FROM gh.candidates 
                    WHERE updated_at > NOW() - INTERVAL '7 days';
                """)
                recent_candidates = cur.fetchone()[0]
                
                return {
                    'total_candidates': total_candidates,
                    'latest_update': latest_update,
                    'candidates_with_resumes': candidates_with_resumes,
                    'candidates_with_employment': candidates_with_employment,
                    'recent_candidates': recent_candidates
                }
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def check_csv_export():
    """Check if CSV exports exist and get info about the latest one"""
    exports_dir = "exports"
    latest_path = os.path.join(exports_dir, "latest_export.csv")
    
    # Check if exports directory exists
    if not os.path.exists(exports_dir):
        return {'exists': False, 'exports_dir_exists': False}
    
    # Check for latest export symlink
    if os.path.exists(latest_path):
        stat = os.stat(latest_path)
        size_mb = stat.st_size / (1024 * 1024)
        modified = datetime.fromtimestamp(stat.st_mtime)
        
        # Count lines in CSV
        try:
            with open(latest_path, 'r') as f:
                line_count = sum(1 for _ in f) - 1  # Subtract header
        except:
            line_count = "Unknown"
        
        # Count total export files
        try:
            export_files = [f for f in os.listdir(exports_dir) if f.startswith('gh_candidates_export_') and f.endswith('.csv')]
            total_exports = len(export_files)
        except:
            total_exports = "Unknown"
            
        return {
            'exists': True,
            'exports_dir_exists': True,
            'size_mb': size_mb,
            'modified': modified,
            'rows': line_count,
            'total_exports': total_exports,
            'latest_file': os.readlink(latest_path) if os.path.islink(latest_path) else "latest_export.csv"
        }
    else:
        return {'exists': False, 'exports_dir_exists': True}

def main():
    """Main status check"""
    print("📊 Greenhouse Candidates ETL Status\n")
    
    # Database stats
    print("🗄️  Database Status:")
    stats = get_database_stats()
    
    if stats:
        print(f"   Total candidates: {stats['total_candidates']:,}")
        print(f"   Latest update: {stats['latest_update'] or 'None'}")
        print(f"   With resumes: {stats['candidates_with_resumes']:,}")
        print(f"   With employment: {stats['candidates_with_employment']:,}")
        print(f"   Updated last 7 days: {stats['recent_candidates']:,}")
        
        if stats['total_candidates'] > 0:
            resume_pct = (stats['candidates_with_resumes'] / stats['total_candidates']) * 100
            employment_pct = (stats['candidates_with_employment'] / stats['total_candidates']) * 100
            print(f"   Resume coverage: {resume_pct:.1f}%")
            print(f"   Employment coverage: {employment_pct:.1f}%")
    else:
        print("   ❌ Unable to connect to database")
    
    # CSV export status
    print("\n📄 CSV Export Status:")
    csv_info = check_csv_export()
    
    if csv_info.get('exports_dir_exists', False):
        if csv_info['exists']:
            print(f"   Latest export: ✅")
            print(f"   File: {csv_info['latest_file']}")
            print(f"   Size: {csv_info['size_mb']:.2f} MB")
            print(f"   Rows: {csv_info['rows']:,}" if isinstance(csv_info['rows'], int) else f"   Rows: {csv_info['rows']}")
            print(f"   Last modified: {csv_info['modified']}")
            print(f"   Total exports: {csv_info['total_exports']}")
        else:
            print("   Latest export: ❌")
            print("   Exports directory exists but no files found")
    else:
        print("   Exports directory: ❌")
        print("   Run 'python main.py' to generate first export")
    
    # Next steps
    print("\n🚀 Next Steps:")
    if not stats or stats['total_candidates'] == 0:
        print("   1. Run 'python main.py --full-sync' for initial data load")
    else:
        print("   1. Run 'python main.py' for incremental sync")
        
    if not csv_info['exists']:
        print("   2. CSV will be generated automatically after sync")
    else:
        print("   2. Upload CSV to Zapier Table")
        
    print("   3. Set up scheduled runs (cron/launchd) for automation")

if __name__ == "__main__":
    main()
