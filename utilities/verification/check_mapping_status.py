#!/usr/bin/env python3
"""
Quick status check for SharePoint mapping progress
Run this anytime to see how the mapping is progressing
"""

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Database configuration
PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "greenhouse_candidates_sp"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

SOURCE_PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("SOURCE_PGDATABASE", "greenhouse_candidates"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def check_status():
    """Check the current mapping status"""
    
    print_header("📊 SHAREPOINT MAPPING STATUS")
    print(f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Check source database
        with psycopg2.connect(**SOURCE_PG) as source_conn:
            with source_conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM gh.candidates")
                total_source = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE resume_links IS NOT NULL AND array_length(resume_links, 1) > 0")
                source_with_resumes = cur.fetchone()[0]
        
        print(f"📁 Source Database (greenhouse_candidates):")
        print(f"   Total candidates: {total_source:,}")
        print(f"   With resumes: {source_with_resumes:,}")
        
        # Check target database
        with psycopg2.connect(**PG) as target_conn:
            with target_conn.cursor() as cur:
                # Total mapped
                cur.execute("SELECT COUNT(*) FROM gh.candidates")
                total_mapped = cur.fetchone()[0]
                
                # Successfully mapped with SharePoint URLs
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM gh.candidates 
                    WHERE resume_links IS NOT NULL 
                    AND array_length(resume_links, 1) > 0
                    AND resume_links[1] LIKE '%sharepoint%'
                """)
                mapped_with_sharepoint = cur.fetchone()[0]
                
                # Candidates without resumes
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM gh.candidates 
                    WHERE resume_links IS NULL 
                    OR array_length(resume_links, 1) = 0
                """)
                no_resume = cur.fetchone()[0]
                
                # Check audit table for detailed stats
                cur.execute("""
                    SELECT 
                        mapping_status,
                        COUNT(*) as count
                    FROM gh.sharepoint_mapping_audit
                    GROUP BY mapping_status
                    ORDER BY mapping_status
                """)
                audit_stats = cur.fetchall()
        
        print(f"\n📁 Target Database (greenhouse_candidates_sp):")
        print(f"   Total candidates copied: {total_mapped:,}")
        print(f"   Successfully mapped to SharePoint: {mapped_with_sharepoint:,}")
        print(f"   No resume found: {no_resume:,}")
        
        if audit_stats:
            print(f"\n📋 Mapping Audit Details:")
            for status, count in audit_stats:
                print(f"   {status}: {count:,}")
        
        # Calculate progress
        if total_source > 0:
            progress_pct = (total_mapped / total_source) * 100
            print(f"\n📈 Overall Progress:")
            print(f"   {total_mapped:,} / {total_source:,} candidates processed ({progress_pct:.1f}%)")
            
            if mapped_with_sharepoint > 0:
                success_rate = (mapped_with_sharepoint / total_mapped) * 100 if total_mapped > 0 else 0
                print(f"   Success rate: {success_rate:.1f}% of processed candidates")
            
            remaining = total_source - total_mapped
            if remaining > 0:
                print(f"   Remaining: {remaining:,} candidates")
                print(f"\n⏱️  Estimated time remaining: ~{remaining // 100} minutes")
            else:
                print(f"\n✅ MAPPING COMPLETE!")
                print(f"\n🎯 Next step: Run 'python export_sharepoint_csv.py' to generate CSV")
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    check_status()
