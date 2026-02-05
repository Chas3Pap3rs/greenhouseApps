#!/usr/bin/env python3
"""
Resume Download Status Checker

Shows current status of resume downloads and provides insights.
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

SAVE_DIR = os.path.expanduser(os.getenv("RESUME_SAVE_DIR", "./downloads/resumes"))

def get_database_stats():
    """Get resume download statistics from database"""
    try:
        with psycopg2.connect(**PG) as conn:
            with conn.cursor() as cur:
                # Total candidates
                cur.execute("SELECT COUNT(*) FROM gh.candidates;")
                total_candidates = cur.fetchone()[0]
                
                # Candidates with attachments
                cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE raw ? 'attachments';")
                candidates_with_attachments = cur.fetchone()[0]
                
                # Download audit stats
                cur.execute("""
                    SELECT 
                        download_status,
                        COUNT(*) as count,
                        SUM(file_size_bytes) as total_bytes
                    FROM gh.resume_download_audit 
                    GROUP BY download_status
                """)
                download_stats = {row[0]: {'count': row[1], 'bytes': row[2] or 0} for row in cur.fetchall()}
                
                # Recent downloads (last 24 hours)
                cur.execute("""
                    SELECT COUNT(*) FROM gh.resume_download_audit 
                    WHERE downloaded_at > NOW() - INTERVAL '24 hours'
                """)
                recent_downloads = cur.fetchone()[0]
                
                # Most recent download
                cur.execute("""
                    SELECT downloaded_at FROM gh.resume_download_audit 
                    ORDER BY downloaded_at DESC LIMIT 1
                """)
                latest_download = cur.fetchone()
                latest_download = latest_download[0] if latest_download else None
                
                return {
                    'total_candidates': total_candidates,
                    'candidates_with_attachments': candidates_with_attachments,
                    'download_stats': download_stats,
                    'recent_downloads': recent_downloads,
                    'latest_download': latest_download
                }
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def get_local_file_stats():
    """Get statistics about local downloaded files"""
    if not os.path.exists(SAVE_DIR):
        return {'exists': False}
    
    try:
        total_files = 0
        total_size = 0
        year_folders = []
        failed_files = 0
        
        # Walk through organized directory structure
        for root, dirs, files in os.walk(SAVE_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
                total_files += 1
                
                # Count failed downloads
                if "Failed_Downloads" in root:
                    failed_files += 1
            
            # Track year folders for organization info
            if root != SAVE_DIR:
                rel_path = os.path.relpath(root, SAVE_DIR)
                if "/" not in rel_path and rel_path.isdigit():  # Year folder
                    year_folders.append(rel_path)
        
        return {
            'exists': True,
            'total_files': total_files,
            'total_size_bytes': total_size,
            'directory': SAVE_DIR,
            'year_folders': sorted(set(year_folders)),
            'failed_files': failed_files,
            'successful_files': total_files - failed_files
        }
        
    except Exception as e:
        return {'exists': True, 'error': str(e)}

def format_bytes(bytes_count):
    """Format bytes into human readable format"""
    if bytes_count == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f} TB"

def main():
    """Main status check"""
    print("📊 Greenhouse Resume Download Status\n")
    
    # Database stats
    print("🗄️  Database Status:")
    stats = get_database_stats()
    
    if stats:
        print(f"   Total candidates: {stats['total_candidates']:,}")
        print(f"   With attachments: {stats['candidates_with_attachments']:,}")
        
        if stats['candidates_with_attachments'] > 0:
            attachment_pct = (stats['candidates_with_attachments'] / stats['total_candidates']) * 100
            print(f"   Attachment coverage: {attachment_pct:.1f}%")
        
        print(f"   Recent downloads (24h): {stats['recent_downloads']:,}")
        print(f"   Latest download: {stats['latest_download'] or 'None'}")
        
        # Download status breakdown
        download_stats = stats['download_stats']
        if download_stats:
            print("\n📥 Download Status:")
            
            success_count = download_stats.get('success', {}).get('count', 0)
            failed_count = download_stats.get('failed', {}).get('count', 0)
            total_attempts = success_count + failed_count
            
            if total_attempts > 0:
                success_rate = (success_count / total_attempts) * 100
                print(f"   Success rate: {success_rate:.1f}% ({success_count:,}/{total_attempts:,})")
            
            for status, data in download_stats.items():
                count = data['count']
                size = data['bytes']
                print(f"   {status.title()}: {count:,} files ({format_bytes(size)})")
        
    else:
        print("   ❌ Unable to connect to database")
    
    # Local file stats
    print("\n📁 Local Files Status:")
    file_stats = get_local_file_stats()
    
    if not file_stats['exists']:
        print("   Directory: ❌ Does not exist")
        print(f"   Expected location: {SAVE_DIR}")
    elif 'error' in file_stats:
        print(f"   Error: {file_stats['error']}")
    else:
        print(f"   Directory: ✅ {file_stats['directory']}")
        print(f"   Total files: {file_stats['total_files']:,}")
        print(f"   Successful: {file_stats['successful_files']:,}")
        print(f"   Failed: {file_stats['failed_files']:,}")
        print(f"   Total size: {format_bytes(file_stats['total_size_bytes'])}")
        
        # Show organization structure
        if file_stats['year_folders']:
            print(f"   Organized by years: {', '.join(file_stats['year_folders'])}")
        
        # Check for discrepancies
        if stats and 'success' in stats['download_stats']:
            db_success_count = stats['download_stats']['success']['count']
            file_success_count = file_stats['successful_files']
            
            if db_success_count != file_success_count:
                print(f"   ⚠️  Mismatch: DB shows {db_success_count:,} successful downloads, but {file_success_count:,} successful files found")
    
    # Next steps
    print("\n🚀 Next Steps:")
    
    if not stats:
        print("   1. Check database connection and run setup_audit_table.py")
    elif not stats['download_stats']:
        print("   1. Run 'python download_resumes.py' to start downloading")
    else:
        success_count = stats['download_stats'].get('success', {}).get('count', 0)
        failed_count = stats['download_stats'].get('failed', {}).get('count', 0)
        
        if failed_count > 0:
            print(f"   1. Review failed downloads: SELECT * FROM gh.resume_download_audit WHERE download_status='failed';")
        
        if success_count > 0:
            print(f"   2. Update RESUME_SAVE_DIR to SharePoint path when OneDrive is ready")
            print(f"   3. Re-run download_resumes.py to sync to SharePoint")
        else:
            print("   1. Run 'python download_resumes.py' to start downloading")

if __name__ == "__main__":
    main()
