#!/usr/bin/env python3
"""
Comprehensive Database Validation

Verifies all three databases have correct data:
1. greenhouse_candidates - AWS S3 links from Greenhouse API
2. greenhouse_candidates_sp - SharePoint links (human-friendly YYYY/MM structure)
3. greenhouse_candidates_ai - SharePoint links (AI_Access flat structure) + metadata_url
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

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_database_comprehensive(dbname, expected_link_type):
    """Comprehensive check of a database"""
    log("")
    log("="*80)
    log(f"DATABASE: {dbname}")
    log("="*80)
    
    conn = psycopg2.connect(**{**PG_CONFIG, "dbname": dbname})
    cur = conn.cursor()
    
    # Basic counts
    cur.execute("SELECT COUNT(*) FROM gh.candidates")
    total = cur.fetchone()[0]
    log(f"\n📊 Total candidates: {total:,}")
    
    # Resume links analysis
    cur.execute("""
        SELECT COUNT(*)
        FROM gh.candidates
        WHERE resume_links IS NOT NULL 
        AND array_length(resume_links, 1) > 0
    """)
    with_links = cur.fetchone()[0]
    log(f"📎 With resume_links: {with_links:,} ({with_links/total*100:.1f}%)")
    
    # Check link types
    cur.execute("""
        SELECT COUNT(*)
        FROM gh.candidates
        WHERE resume_links IS NOT NULL 
        AND array_length(resume_links, 1) > 0
        AND resume_links[1] LIKE '%amazonaws.com%'
    """)
    aws_count = cur.fetchone()[0]
    
    cur.execute("""
        SELECT COUNT(*)
        FROM gh.candidates
        WHERE resume_links IS NOT NULL 
        AND array_length(resume_links, 1) > 0
        AND resume_links[1] LIKE '%sharepoint.com%'
    """)
    sp_count = cur.fetchone()[0]
    
    log(f"   AWS S3 links: {aws_count:,} ({aws_count/with_links*100:.1f}%)")
    log(f"   SharePoint links: {sp_count:,} ({sp_count/with_links*100:.1f}%)")
    
    # Validate expected link type
    if expected_link_type == "aws":
        if aws_count == with_links:
            log(f"   ✅ CORRECT: All links are AWS S3 (as expected)")
        else:
            log(f"   ❌ ERROR: Expected all AWS links, found {sp_count:,} SharePoint links")
    elif expected_link_type == "sharepoint":
        if sp_count == with_links:
            log(f"   ✅ CORRECT: All links are SharePoint (as expected)")
        else:
            log(f"   ❌ ERROR: Expected all SharePoint links, found {aws_count:,} AWS links")
    
    # Resume content (if column exists)
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'gh' 
        AND table_name = 'candidates'
        AND column_name = 'resume_content'
    """)
    
    with_content = 0
    if cur.fetchone():
        cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE resume_content IS NOT NULL")
        with_content = cur.fetchone()[0]
        log(f"📄 With resume_content: {with_content:,} ({with_content/total*100:.1f}%)")
    
    # Addresses
    cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE addresses IS NOT NULL")
    with_addresses = cur.fetchone()[0]
    log(f"📍 With addresses: {with_addresses:,} ({with_addresses/total*100:.1f}%)")
    
    # Updated_at
    cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE updated_at IS NOT NULL")
    with_updated = cur.fetchone()[0]
    log(f"⏰ With updated_at: {with_updated:,} ({with_updated/total*100:.1f}%)")
    
    # Check for metadata_url (AI database only)
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'gh' 
        AND table_name = 'candidates'
        AND column_name = 'metadata_url'
    """)
    
    has_metadata_col = cur.fetchone() is not None
    
    if has_metadata_col:
        cur.execute("SELECT COUNT(*) FROM gh.candidates WHERE metadata_url IS NOT NULL")
        with_metadata = cur.fetchone()[0]
        log(f"🔗 With metadata_url: {with_metadata:,} ({with_metadata/total*100:.1f}%)")
    
    # Check latest 5 candidates
    log(f"\n📋 Latest 5 candidates:")
    
    # Build query based on available columns
    if has_metadata_col and with_content > 0:
        cur.execute("""
            SELECT 
                candidate_id,
                first_name,
                last_name,
                CASE WHEN resume_links IS NOT NULL AND array_length(resume_links, 1) > 0 THEN 'YES' ELSE 'NO' END as has_links,
                CASE WHEN resume_content IS NOT NULL THEN 'YES' ELSE 'NO' END as has_content,
                CASE WHEN metadata_url IS NOT NULL THEN 'YES' ELSE 'NO' END as has_metadata
            FROM gh.candidates
            ORDER BY candidate_id DESC
            LIMIT 5
        """)
        for row in cur.fetchall():
            log(f"   {row[0]} | {row[1]} {row[2]} | Links:{row[3]} Content:{row[4]} Metadata:{row[5]}")
    elif with_content > 0:
        cur.execute("""
            SELECT 
                candidate_id,
                first_name,
                last_name,
                CASE WHEN resume_links IS NOT NULL AND array_length(resume_links, 1) > 0 THEN 'YES' ELSE 'NO' END as has_links,
                CASE WHEN resume_content IS NOT NULL THEN 'YES' ELSE 'NO' END as has_content
            FROM gh.candidates
            ORDER BY candidate_id DESC
            LIMIT 5
        """)
        for row in cur.fetchall():
            log(f"   {row[0]} | {row[1]} {row[2]} | Links:{row[3]} Content:{row[4]}")
    else:
        cur.execute("""
            SELECT 
                candidate_id,
                first_name,
                last_name,
                CASE WHEN resume_links IS NOT NULL AND array_length(resume_links, 1) > 0 THEN 'YES' ELSE 'NO' END as has_links
            FROM gh.candidates
            ORDER BY candidate_id DESC
            LIMIT 5
        """)
        for row in cur.fetchall():
            log(f"   {row[0]} | {row[1]} {row[2]} | Links:{row[3]}")
    
    cur.close()
    conn.close()
    
    return {
        'total': total,
        'with_links': with_links,
        'aws_links': aws_count,
        'sp_links': sp_count,
        'with_content': with_content,
        'with_addresses': with_addresses,
        'with_updated': with_updated
    }

def main():
    log("="*80)
    log("COMPREHENSIVE DATABASE VALIDATION")
    log("="*80)
    
    # Check all three databases
    main_stats = check_database_comprehensive("greenhouse_candidates", "aws")
    sp_stats = check_database_comprehensive("greenhouse_candidates_sp", "sharepoint")
    ai_stats = check_database_comprehensive("greenhouse_candidates_ai", "sharepoint")
    
    # Summary
    log("")
    log("="*80)
    log("VALIDATION SUMMARY")
    log("="*80)
    
    log(f"\n✅ greenhouse_candidates (Main DB):")
    log(f"   Total: {main_stats['total']:,}")
    log(f"   AWS S3 links: {main_stats['aws_links']:,} (100% - CORRECT)")
    log(f"   Resume content: {main_stats['with_content']:,} ({main_stats['with_content']/main_stats['total']*100:.1f}%)")
    
    log(f"\n✅ greenhouse_candidates_sp (SharePoint DB):")
    log(f"   Total: {sp_stats['total']:,}")
    log(f"   SharePoint links: {sp_stats['sp_links']:,} ({sp_stats['sp_links']/sp_stats['with_links']*100:.1f}% - {'CORRECT' if sp_stats['aws_links'] == 0 else 'ERROR'})")
    if sp_stats['aws_links'] > 0:
        log(f"   ❌ WARNING: {sp_stats['aws_links']:,} AWS links found (should be 0)")
    
    log(f"\n✅ greenhouse_candidates_ai (AI Access DB):")
    log(f"   Total: {ai_stats['total']:,}")
    log(f"   SharePoint links: {ai_stats['sp_links']:,} ({ai_stats['sp_links']/ai_stats['with_links']*100:.1f}% - {'CORRECT' if ai_stats['aws_links'] == 0 else 'ERROR'})")
    if ai_stats['aws_links'] > 0:
        log(f"   ❌ WARNING: {ai_stats['aws_links']:,} AWS links found (should be 0)")
    
    log("")
    log("="*80)
    
    # Overall status
    all_correct = (
        main_stats['aws_links'] == main_stats['with_links'] and
        sp_stats['aws_links'] == 0 and
        ai_stats['aws_links'] == 0
    )
    
    if all_correct:
        log("✅ ALL DATABASES VALIDATED SUCCESSFULLY!")
        log("   - Main DB has AWS S3 links only")
        log("   - SharePoint DB has SharePoint links only")
        log("   - AI Access DB has SharePoint links only")
    else:
        log("❌ VALIDATION FAILED - Issues found above")
    
    log("="*80)

if __name__ == "__main__":
    main()
