#!/usr/bin/env python3
"""
Fix Expired SharePoint Links

Identifies candidates with temporary downloadUrl links (containing tempauth tokens)
and replaces them with permanent webUrl links.

Usage:
    python fix_expired_sharepoint_links.py                # Dry-run mode
    python fix_expired_sharepoint_links.py --execute      # Actually fix the links
"""

import os
import sys
from pathlib import Path
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "greenhouse_sharepoint_mapper"))
from graph_client import GraphClient

load_dotenv()

# Color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(message, level="INFO"):
    """Print colored log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if level == "HEADER":
        print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    elif level == "SUCCESS":
        print(f"{Colors.GREEN}✅ [{timestamp}] {message}{Colors.ENDC}")
    elif level == "ERROR":
        print(f"{Colors.RED}❌ [{timestamp}] {message}{Colors.ENDC}")
    elif level == "WARNING":
        print(f"{Colors.YELLOW}⚠️  [{timestamp}] {message}{Colors.ENDC}")
    elif level == "STEP":
        print(f"{Colors.CYAN}{Colors.BOLD}[{timestamp}] {message}{Colors.ENDC}")
    else:
        print(f"[{timestamp}] {message}")

# Database config
PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": "greenhouse_candidates_ai",
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

def has_tempauth_token(url):
    """Check if URL contains temporary auth token"""
    if not url:
        return False
    return 'tempauth=' in url or 'download.aspx' in url

def get_permanent_url(graph_client, filename):
    """Get permanent webUrl for a file"""
    try:
        relative_path = f"AI_Access/{filename}"
        file_info = graph_client.find_file_by_path(relative_path)
        
        if file_info and 'webUrl' in file_info:
            return file_info['webUrl']
    except Exception as e:
        log(f"Error getting URL for {filename}: {e}", "ERROR")
    
    return None

def find_candidates_with_temp_links():
    """Find all candidates with temporary download links"""
    log("Scanning database for temporary SharePoint links...", "STEP")
    
    conn = psycopg2.connect(**PG)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT candidate_id, full_name, resume_links, resume_filenames
        FROM gh.candidates
        WHERE resume_links IS NOT NULL 
        AND array_length(resume_links, 1) > 0
        ORDER BY candidate_id
    """)
    
    candidates = cur.fetchall()
    temp_link_candidates = []
    
    for candidate_id, full_name, resume_links, resume_filenames in candidates:
        if resume_links and len(resume_links) > 0:
            url = resume_links[0]
            if has_tempauth_token(url):
                temp_link_candidates.append({
                    'candidate_id': candidate_id,
                    'full_name': full_name,
                    'old_url': url,
                    'filename': resume_filenames[0] if resume_filenames else None
                })
    
    cur.close()
    conn.close()
    
    return temp_link_candidates

def fix_candidate_links(candidates, dry_run=True):
    """Fix temporary links for candidates"""
    log("\nConnecting to SharePoint...", "STEP")
    
    try:
        graph_client = GraphClient()
        site_info = graph_client.get_site_info()
        log(f"Connected to: {site_info.get('displayName')}", "SUCCESS")
    except Exception as e:
        log(f"Failed to connect to SharePoint: {e}", "ERROR")
        return 0, 0
    
    log(f"\n{'DRY-RUN: ' if dry_run else ''}Fixing links for {len(candidates)} candidates...", "STEP")
    
    conn = psycopg2.connect(**PG)
    fixed_count = 0
    failed_count = 0
    
    for idx, candidate in enumerate(candidates, 1):
        candidate_id = candidate['candidate_id']
        full_name = candidate['full_name']
        filename = candidate['filename']
        
        if not filename:
            log(f"[{idx}/{len(candidates)}] {full_name}: No filename found", "WARNING")
            failed_count += 1
            continue
        
        # Get permanent URL
        new_url = get_permanent_url(graph_client, filename)
        
        if new_url:
            if dry_run:
                log(f"[{idx}/{len(candidates)}] Would fix: {full_name} (ID: {candidate_id})")
            else:
                try:
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE gh.candidates
                        SET resume_links = ARRAY[%s]
                        WHERE candidate_id = %s
                    """, (new_url, candidate_id))
                    conn.commit()
                    cur.close()
                    
                    log(f"[{idx}/{len(candidates)}] Fixed: {full_name} (ID: {candidate_id})", "SUCCESS")
                    fixed_count += 1
                except Exception as e:
                    log(f"[{idx}/{len(candidates)}] Failed to update {full_name}: {e}", "ERROR")
                    failed_count += 1
        else:
            log(f"[{idx}/{len(candidates)}] {full_name}: Could not find file in SharePoint", "WARNING")
            failed_count += 1
    
    conn.close()
    return fixed_count, failed_count

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix expired SharePoint links')
    parser.add_argument('--execute', action='store_true',
                       help='Actually fix the links (default is dry-run)')
    
    args = parser.parse_args()
    
    log("="*80, "HEADER")
    log("FIX EXPIRED SHAREPOINT LINKS", "HEADER")
    log("="*80, "HEADER")
    print()
    
    # Find candidates with temporary links
    candidates = find_candidates_with_temp_links()
    
    if not candidates:
        log("No candidates found with temporary links! ✅", "SUCCESS")
        log("\nAll SharePoint links are permanent.", "SUCCESS")
        sys.exit(0)
    
    log(f"Found {len(candidates)} candidates with temporary links", "WARNING")
    print()
    
    # Show sample of affected candidates
    log("Sample of affected candidates:", "STEP")
    for candidate in candidates[:10]:
        print(f"  • {candidate['full_name']} (ID: {candidate['candidate_id']})")
    
    if len(candidates) > 10:
        print(f"  ... and {len(candidates) - 10} more")
    
    print()
    
    # Fix the links
    if args.execute:
        log("EXECUTING FIX (this will update the database)", "WARNING")
        print()
        fixed, failed = fix_candidate_links(candidates, dry_run=False)
        
        log("="*80, "HEADER")
        log("FIX SUMMARY", "HEADER")
        log("="*80, "HEADER")
        print()
        log(f"Total candidates processed: {len(candidates)}")
        log(f"Successfully fixed: {fixed}", "SUCCESS")
        log(f"Failed: {failed}", "ERROR" if failed > 0 else "INFO")
        
        if fixed > 0:
            print()
            log("Next step: Re-export CSV with fixed links", "STEP")
            print("  cd greenhouse_sharepoint_mapper/exports")
            print("  python export_ai_access_csv.py")
    else:
        log("DRY-RUN MODE - No changes made", "WARNING")
        print()
        fixed, failed = fix_candidate_links(candidates, dry_run=True)
        
        log("="*80, "HEADER")
        log("DRY-RUN SUMMARY", "HEADER")
        log("="*80, "HEADER")
        print()
        log(f"Would fix: {len(candidates) - failed} candidates")
        log(f"Would fail: {failed} candidates")
        print()
        log("Run with --execute to actually fix the links", "WARNING")
    
    print()
    log("="*80, "HEADER")
    
    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nInterrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        log(f"\n\nUnexpected error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
