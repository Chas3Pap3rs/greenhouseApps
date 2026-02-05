#!/usr/bin/env python3
"""
SharePoint Mapper Status Checker

Shows current status of SharePoint mapping and provides insights.
"""

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
from graph_client import GraphClient

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

def get_source_database_stats():
    """Get statistics from source database"""
    try:
        with psycopg2.connect(**SOURCE_PG) as conn:
            with conn.cursor() as cur:
                # Total candidates
                cur.execute("SELECT COUNT(*) FROM gh.candidates")
                total_candidates = cur.fetchone()[0]
                
                # Candidates with attachments
                cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE raw ? 'attachments'")
                with_attachments = cur.fetchone()[0]
                
                return {
                    'total_candidates': total_candidates,
                    'with_attachments': with_attachments
                }
                
    except Exception as e:
        print(f"❌ Source database error: {e}")
        return None

def get_target_database_stats():
    """Get statistics from SharePoint database"""
    try:
        with psycopg2.connect(**TARGET_PG) as conn:
            with conn.cursor() as cur:
                # Total candidates in SharePoint DB
                cur.execute("SELECT COUNT(*) FROM gh.candidates")
                total_sp_candidates = cur.fetchone()[0]
                
                # Candidates with SharePoint links
                cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE array_length(resume_links, 1) > 0")
                with_sp_links = cur.fetchone()[0]
                
                # Mapping audit stats
                cur.execute("""
                    SELECT 
                        mapping_status,
                        COUNT(*) as count
                    FROM gh.sharepoint_mapping_audit 
                    GROUP BY mapping_status
                """)
                mapping_stats = {row[0]: row[1] for row in cur.fetchall()}
                
                # Recent mappings (last 24 hours)
                cur.execute("""
                    SELECT COUNT(*) FROM gh.sharepoint_mapping_audit 
                    WHERE mapped_at > NOW() - INTERVAL '24 hours'
                """)
                recent_mappings = cur.fetchone()[0]
                
                # Most recent mapping
                cur.execute("""
                    SELECT mapped_at FROM gh.sharepoint_mapping_audit 
                    ORDER BY mapped_at DESC LIMIT 1
                """)
                latest_mapping = cur.fetchone()
                latest_mapping = latest_mapping[0] if latest_mapping else None
                
                return {
                    'total_sp_candidates': total_sp_candidates,
                    'with_sp_links': with_sp_links,
                    'mapping_stats': mapping_stats,
                    'recent_mappings': recent_mappings,
                    'latest_mapping': latest_mapping
                }
                
    except Exception as e:
        print(f"❌ SharePoint database error: {e}")
        return None

def get_export_file_stats():
    """Get statistics about exported CSV files"""
    exports_dir = "exports"
    
    if not os.path.exists(exports_dir):
        return {'exists': False}
    
    try:
        files = [f for f in os.listdir(exports_dir) 
                if f.startswith('gh_spCandidates_export_') and f.endswith('.csv')]
        
        if not files:
            return {'exists': True, 'files': []}
        
        # Get info about latest file
        latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(exports_dir, f)))
        latest_path = os.path.join(exports_dir, latest_file)
        
        stat = os.stat(latest_path)
        size_mb = stat.st_size / (1024 * 1024)
        modified = datetime.fromtimestamp(stat.st_mtime)
        
        # Count lines in CSV
        try:
            with open(latest_path, 'r') as f:
                line_count = sum(1 for _ in f) - 1  # Subtract header
        except:
            line_count = "Unknown"
        
        return {
            'exists': True,
            'files': files,
            'total_exports': len(files),
            'latest_file': latest_file,
            'latest_size_mb': size_mb,
            'latest_modified': modified,
            'latest_rows': line_count
        }
        
    except Exception as e:
        return {'exists': True, 'error': str(e)}

def test_graph_connection():
    """Test Microsoft Graph API connection"""
    try:
        client = GraphClient()
        return client.test_connection()
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

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
    print("📊 Greenhouse SharePoint Mapper Status\n")
    
    # Source database stats
    print("🗄️  Source Database Status:")
    source_stats = get_source_database_stats()
    
    if source_stats:
        print(f"   Database: {SOURCE_PG['dbname']}")
        print(f"   Total candidates: {source_stats['total_candidates']:,}")
        print(f"   With attachments: {source_stats['with_attachments']:,}")
        
        if source_stats['total_candidates'] > 0:
            attachment_pct = (source_stats['with_attachments'] / source_stats['total_candidates']) * 100
            print(f"   Attachment coverage: {attachment_pct:.1f}%")
    else:
        print("   ❌ Unable to connect to source database")
    
    # SharePoint database stats
    print("\n🔗 SharePoint Database Status:")
    target_stats = get_target_database_stats()
    
    if target_stats:
        print(f"   Database: {TARGET_PG['dbname']}")
        print(f"   Total candidates: {target_stats['total_sp_candidates']:,}")
        print(f"   With SharePoint links: {target_stats['with_sp_links']:,}")
        print(f"   Recent mappings (24h): {target_stats['recent_mappings']:,}")
        print(f"   Latest mapping: {target_stats['latest_mapping'] or 'None'}")
        
        if target_stats['total_sp_candidates'] > 0:
            sp_coverage = (target_stats['with_sp_links'] / target_stats['total_sp_candidates']) * 100
            print(f"   SharePoint coverage: {sp_coverage:.1f}%")
        
        # Mapping status breakdown
        mapping_stats = target_stats['mapping_stats']
        if mapping_stats:
            print("\n📈 Mapping Status:")
            total_mapped = sum(mapping_stats.values())
            
            for status, count in mapping_stats.items():
                percentage = (count / total_mapped * 100) if total_mapped > 0 else 0
                status_emoji = {
                    'success': '✅',
                    'failed': '❌', 
                    'no_resume': '📄',
                    'pending': '⏳'
                }.get(status, '❓')
                
                print(f"   {status_emoji} {status.title()}: {count:,} ({percentage:.1f}%)")
    else:
        print("   ❌ Unable to connect to SharePoint database")
    
    # Graph API connection test
    print("\n🌐 Microsoft Graph API Status:")
    graph_test = test_graph_connection()
    
    if graph_test["success"]:
        print("   Connection: ✅ Connected")
        print(f"   Site: {graph_test.get('site_name', 'Unknown')}")
        print(f"   URL: {graph_test.get('web_url', 'Unknown')}")
    else:
        print("   Connection: ❌ Failed")
        print(f"   Error: {graph_test['error']}")
        print("   Check Azure credentials in .env file")
    
    # Export file stats
    print("\n📄 Export Files Status:")
    export_stats = get_export_file_stats()
    
    if not export_stats['exists']:
        print("   Directory: ❌ Does not exist")
        print("   Run export_sharepoint_csv.py to create first export")
    elif 'error' in export_stats:
        print(f"   Error: {export_stats['error']}")
    elif not export_stats['files']:
        print("   Files: ❌ No exports found")
        print("   Run export_sharepoint_csv.py to create first export")
    else:
        print(f"   Total exports: {export_stats['total_exports']:,}")
        print(f"   Latest file: {export_stats['latest_file']}")
        print(f"   Latest size: {export_stats['latest_size_mb']:.2f} MB")
        print(f"   Latest rows: {export_stats['latest_rows']:,}" if isinstance(export_stats['latest_rows'], int) else f"   Latest rows: {export_stats['latest_rows']}")
        print(f"   Last modified: {export_stats['latest_modified']}")
    
    # Next steps
    print("\n🚀 Next Steps:")
    
    if not graph_test["success"]:
        print("   1. Configure Azure credentials in .env file")
        print("   2. Test connection: python graph_client.py")
    elif not target_stats or target_stats['total_sp_candidates'] == 0:
        print("   1. Run setup_sharepoint_db.py to create database")
        print("   2. Run map_sharepoint_links.py to start mapping")
    elif target_stats['mapping_stats'].get('success', 0) == 0:
        print("   1. Run map_sharepoint_links.py to start mapping")
    else:
        success_count = target_stats['mapping_stats'].get('success', 0)
        failed_count = target_stats['mapping_stats'].get('failed', 0)
        
        if failed_count > 0:
            print(f"   1. Review failed mappings: SELECT * FROM gh.sharepoint_mapping_audit WHERE mapping_status='failed';")
        
        if success_count > 0:
            print(f"   2. Export CSV: python export_sharepoint_csv.py")
            print(f"   3. Use CSV with AI agents - SharePoint links are ready!")
        
        if source_stats and target_stats['total_sp_candidates'] < source_stats['total_candidates']:
            remaining = source_stats['total_candidates'] - target_stats['total_sp_candidates']
            print(f"   4. Continue mapping remaining {remaining:,} candidates")

if __name__ == "__main__":
    main()
