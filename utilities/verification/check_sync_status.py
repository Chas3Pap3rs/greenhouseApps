#!/usr/bin/env python3
"""
Check Sync Status for Both Databases

Shows current state of human-friendly and AI-friendly databases.
"""

import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PG_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

def get_db_stats(dbname, db_type):
    """Get statistics for a database"""
    config = PG_CONFIG.copy()
    config["dbname"] = dbname
    
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                # Total candidates
                cur.execute("SELECT COUNT(*) FROM gh.candidates")
                total = cur.fetchone()[0]
                
                # With resume links
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM gh.candidates 
                    WHERE resume_links IS NOT NULL AND array_length(resume_links, 1) > 0
                """)
                with_links = cur.fetchone()[0]
                
                # Last sync info
                sync_table = "sharepoint_sync_log" if db_type == "human" else "ai_sync_log"
                sync_type = "human_friendly" if db_type == "human" else "ai_friendly"
                
                cur.execute(f"""
                    SELECT last_synced_candidate_id, sync_completed_at
                    FROM gh.{sync_table}
                    WHERE sync_type = %s
                    ORDER BY sync_completed_at DESC
                    LIMIT 1
                """, (sync_type,))
                
                sync_info = cur.fetchone()
                
                return {
                    "total": total,
                    "with_links": with_links,
                    "last_sync_id": sync_info[0] if sync_info else None,
                    "last_sync_time": sync_info[1] if sync_info else None
                }
    except Exception as e:
        return {"error": str(e)}

def main():
    """Main execution"""
    print("="*60)
    print("GREENHOUSE SHAREPOINT SYNC STATUS")
    print("="*60)
    print()
    
    # Source database
    print("📊 SOURCE DATABASE (greenhouse_candidates)")
    print("-"*60)
    source_stats = get_db_stats("greenhouse_candidates", "source")
    if "error" not in source_stats:
        print(f"Total candidates: {source_stats['total']:,}")
        print(f"With resumes: {source_stats['with_links']:,}")
        coverage = (source_stats['with_links'] / source_stats['total'] * 100) if source_stats['total'] > 0 else 0
        print(f"Coverage: {coverage:.1f}%")
    else:
        print(f"❌ Error: {source_stats['error']}")
    print()
    
    # Human-friendly database
    print("👥 HUMAN-FRIENDLY DATABASE (greenhouse_candidates_sp)")
    print("-"*60)
    human_stats = get_db_stats("greenhouse_candidates_sp", "human")
    if "error" not in human_stats:
        print(f"Total candidates: {human_stats['total']:,}")
        print(f"With SharePoint links: {human_stats['with_links']:,}")
        coverage = (human_stats['with_links'] / human_stats['total'] * 100) if human_stats['total'] > 0 else 0
        print(f"Coverage: {coverage:.1f}%")
        if human_stats['last_sync_id']:
            print(f"Last synced ID: {human_stats['last_sync_id']}")
            print(f"Last sync time: {human_stats['last_sync_time']}")
        else:
            print("Last sync: Never (use full rebuild)")
    else:
        print(f"❌ Error: {human_stats['error']}")
    print()
    
    # AI-friendly database
    print("🤖 AI-FRIENDLY DATABASE (greenhouse_candidates_ai)")
    print("-"*60)
    ai_stats = get_db_stats("greenhouse_candidates_ai", "ai")
    if "error" not in ai_stats:
        print(f"Total candidates: {ai_stats['total']:,}")
        print(f"With AI_Access links: {ai_stats['with_links']:,}")
        coverage = (ai_stats['with_links'] / ai_stats['total'] * 100) if ai_stats['total'] > 0 else 0
        print(f"Coverage: {coverage:.1f}%")
        if ai_stats['last_sync_id']:
            print(f"Last synced ID: {ai_stats['last_sync_id']}")
            print(f"Last sync time: {ai_stats['last_sync_time']}")
        else:
            print("Last sync: Never (use full rebuild)")
    else:
        print(f"❌ Error: {ai_stats['error']}")
    print()
    
    # Recommendations
    print("="*60)
    print("💡 RECOMMENDATIONS")
    print("="*60)
    
    if "error" not in source_stats and "error" not in human_stats:
        if source_stats['total'] > human_stats['total']:
            diff = source_stats['total'] - human_stats['total']
            print(f"⚠️  Human DB is behind by {diff:,} candidates")
            print("   Run: python update_sharepoint_links.py")
        else:
            print("✅ Human DB is up to date")
    
    if "error" not in source_stats and "error" not in ai_stats:
        if source_stats['total'] > ai_stats['total']:
            diff = source_stats['total'] - ai_stats['total']
            print(f"⚠️  AI DB is behind by {diff:,} candidates")
            print("   Run: python update_ai_access_links.py")
        else:
            print("✅ AI DB is up to date")
    
    print()
    print("To update everything at once, run: ./run_full_update.sh")
    print("="*60)

if __name__ == "__main__":
    main()
