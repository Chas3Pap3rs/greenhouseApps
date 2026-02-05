#!/usr/bin/env python3
"""
Backfill AI Access Database

This script finds candidates that exist in greenhouse_candidates (dbBuilder) 
but are missing from greenhouse_candidates_ai (AI Access), then:
1. Downloads missing resumes (if needed)
2. Copies resumes to AI_Access folder
3. Gets SharePoint URLs
4. Inserts candidates into AI Access database

This is a one-time backfill to sync the databases.
"""

import os
import sys
import base64
import psycopg2
import requests
import shutil
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from graph_client import GraphClient

# Add resume downloader utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'greenhouse_resume_downloader'))

load_dotenv()

# Also try loading from parent directory (for GREENHOUSE_API_KEY)
parent_env = os.path.join(os.path.dirname(__file__), '..', 'greenhouse_resume_downloader', '.env')
if os.path.exists(parent_env):
    load_dotenv(parent_env)

# Configuration
GREENHOUSE_API_KEY = os.getenv("GREENHOUSE_API_KEY")
GREENHOUSE_BASE_URL = "https://harvest.greenhouse.io/v1"
LOCAL_RESUME_DIR = os.getenv("LOCAL_RESUME_DIR")
AI_ACCESS_DIR = os.path.join(LOCAL_RESUME_DIR, "AI_Access")

PG_DBBUILDER = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": "greenhouse_candidates",
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

PG_AI = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": "greenhouse_candidates_ai",
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_greenhouse_headers():
    """Get headers for Greenhouse API requests"""
    auth_string = f"{GREENHOUSE_API_KEY}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    return {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json"
    }

def get_fresh_candidate_data(candidate_id):
    """Fetch fresh candidate data from Greenhouse API with current S3 URLs"""
    url = f"{GREENHOUSE_BASE_URL}/candidates/{candidate_id}"
    
    try:
        response = requests.get(url, headers=get_greenhouse_headers())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log(f"  ⚠️  Failed to fetch fresh data for {candidate_id}: {e}")
        return None

def sanitize_filename(name):
    """Remove/replace characters that are problematic in filenames"""
    if not name:
        return "unknown"
    
    replacements = {
        '/': '_', '\\': '_', ':': '_', '*': '_', '?': '_',
        '"': '_', '<': '_', '>': '_', '|': '_', '\n': ' ',
        '\r': ' ', '\t': ' '
    }
    
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    # Remove leading/trailing spaces and dots
    name = name.strip('. ')
    
    # Collapse multiple spaces
    while '  ' in name:
        name = name.replace('  ', ' ')
    
    return name[:200]  # Limit length

def build_filename(candidate_id, full_name, created_at, extension):
    """Build a standardized filename"""
    safe_name = sanitize_filename(full_name)
    
    if isinstance(created_at, str):
        date_str = created_at[:10].replace('-', '')
    else:
        date_str = created_at.strftime("%Y%m%d") if created_at else "unknown"
    
    return f"{candidate_id}_{safe_name}_{date_str}.{extension}"

def detect_file_extension(response, url, original_filename):
    """Detect file extension from response or filename"""
    content_type = response.headers.get('Content-Type', '').lower()
    
    # Try content type first
    if 'pdf' in content_type:
        return 'pdf'
    elif 'msword' in content_type or 'officedocument.wordprocessingml' in content_type:
        return 'docx' if 'officedocument' in content_type else 'doc'
    
    # Try URL
    if url:
        if url.lower().endswith('.pdf'):
            return 'pdf'
        elif url.lower().endswith('.docx'):
            return 'docx'
        elif url.lower().endswith('.doc'):
            return 'doc'
    
    # Try original filename
    if original_filename:
        ext = original_filename.lower().split('.')[-1]
        if ext in ['pdf', 'doc', 'docx']:
            return ext
    
    return 'pdf'  # Default

def download_resume(url, save_path):
    """Download resume from URL to save_path"""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(save_path)
        return file_size, None
    except Exception as e:
        return 0, str(e)

def find_resume_in_organized_folders(candidate_id):
    """Find resume in the organized year/month folders"""
    for root, dirs, files in os.walk(LOCAL_RESUME_DIR):
        # Skip AI_Access folder
        if 'AI_Access' in root:
            continue
        
        for file in files:
            if file.startswith(f"{candidate_id}_") and not file.startswith("FAILED_"):
                return os.path.join(root, file)
    
    return None

def copy_to_ai_access(source_path, candidate_id, full_name, created_at):
    """Copy resume to AI_Access folder with standardized naming"""
    if not source_path or not os.path.exists(source_path):
        return None
    
    # Get extension from source file
    ext = source_path.split('.')[-1].lower()
    
    # Build target filename
    filename = build_filename(candidate_id, full_name, created_at, ext)
    dest_path = os.path.join(AI_ACCESS_DIR, filename)
    
    # Copy if doesn't exist or is different size
    if not os.path.exists(dest_path) or os.path.getsize(source_path) != os.path.getsize(dest_path):
        # Retry logic for OneDrive sync conflicts
        max_retries = 3
        for attempt in range(max_retries):
            try:
                shutil.copy2(source_path, dest_path)
                return filename
            except (TimeoutError, OSError) as e:
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait for OneDrive sync
                    continue
                else:
                    # Last attempt failed, log and skip
                    log(f"  ⚠️  Failed to copy {filename} after {max_retries} attempts: {e}")
                    return None
        return filename
    
    return filename

def get_sharepoint_url(graph_client, filename):
    """Get SharePoint URL for file in AI_Access folder"""
    try:
        relative_path = f"AI_Access/{filename}"
        file_info = graph_client.find_file_by_path(relative_path)
        
        if file_info and '@microsoft.graph.downloadUrl' in file_info:
            return file_info['@microsoft.graph.downloadUrl']
    except:
        pass
    
    return None

def main():
    log("="*70)
    log("AI ACCESS DATABASE BACKFILL")
    log("="*70)
    
    # Connect to both databases
    log("\nConnecting to databases...")
    conn_db = psycopg2.connect(**PG_DBBUILDER)
    conn_ai = psycopg2.connect(**PG_AI)
    
    # Find missing candidates
    log("Finding candidates missing from AI Access database...")
    
    cur_db = conn_db.cursor()
    cur_ai = conn_ai.cursor()
    
    cur_db.execute('SELECT candidate_id FROM gh.candidates ORDER BY candidate_id')
    db_ids = set([row[0] for row in cur_db.fetchall()])
    
    cur_ai.execute('SELECT candidate_id FROM gh.candidates ORDER BY candidate_id')
    ai_ids = set([row[0] for row in cur_ai.fetchall()])
    
    missing_ids = sorted(list(db_ids - ai_ids))
    
    log(f"Found {len(missing_ids):,} candidates to backfill")
    
    if len(missing_ids) == 0:
        log("✅ No candidates to backfill! Databases are in sync.")
        return
    
    # Connect to SharePoint
    log("\nConnecting to SharePoint...")
    try:
        graph_client = GraphClient()
        site_info = graph_client.get_site_info()
        log(f"✅ Connected to SharePoint: {site_info.get('displayName')}")
    except Exception as e:
        log(f"❌ Failed to connect to SharePoint: {e}")
        return
    
    # Process missing candidates
    log(f"\nProcessing {len(missing_ids):,} missing candidates...")
    
    success_count = 0
    resume_downloaded = 0
    resume_copied = 0
    no_resume = 0
    failed = 0
    
    for idx, candidate_id in enumerate(missing_ids, 1):
        if idx % 100 == 0:
            log(f"Progress: {idx}/{len(missing_ids)} ({idx/len(missing_ids)*100:.1f}%)")
        
        # Get candidate data from dbBuilder
        cur_db.execute("""
            SELECT candidate_id, full_name, first_name, last_name, 
                   email, phone_numbers, created_at
            FROM gh.candidates
            WHERE candidate_id = %s
        """, (candidate_id,))
        
        row = cur_db.fetchone()
        if not row:
            continue
        
        candidate_id, full_name, first_name, last_name, email, phone_numbers, created_at = row
        
        # Check if resume already downloaded
        resume_path = find_resume_in_organized_folders(candidate_id)
        
        # If not downloaded, fetch FRESH data from Greenhouse API and download
        if not resume_path:
            fresh_data = get_fresh_candidate_data(candidate_id)
            
            if fresh_data:
                attachments = fresh_data.get('attachments', [])
                
                # Find best resume (prefer PDF)
                best_resume = None
                for att in attachments:
                    if att.get('type') == 'resume':
                        if not best_resume or att.get('filename', '').lower().endswith('.pdf'):
                            best_resume = att
                
                if best_resume and best_resume.get('url'):
                    # Download resume with fresh S3 URL
                    try:
                        response = requests.get(best_resume['url'], stream=True, timeout=30)
                        response.raise_for_status()
                        
                        ext = detect_file_extension(response, best_resume['url'], best_resume.get('filename'))
                        filename = build_filename(candidate_id, full_name, created_at, ext)
                        temp_path = os.path.join(LOCAL_RESUME_DIR, '2025', '12_December', filename)
                        
                        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                        
                        file_size, error = download_resume(best_resume['url'], temp_path)
                        
                        if not error:
                            resume_path = temp_path
                            resume_downloaded += 1
                            
                            # Record in audit table (skip if columns don't exist)
                            try:
                                cur_db.execute("""
                                    INSERT INTO gh.resume_download_audit 
                                    (candidate_id, attachment_filename, saved_path, download_status)
                                    VALUES (%s, %s, %s, 'success')
                                    ON CONFLICT (candidate_id) DO NOTHING
                                """, (candidate_id, filename, temp_path))
                                conn_db.commit()
                            except:
                                pass  # Skip audit if table structure is different
                    except Exception as e:
                        # Skip download errors (likely expired URLs) and continue
                        if '403' not in str(e):  # Only log non-403 errors
                            log(f"  ⚠️  Failed to download resume for {candidate_id}: {e}")
        
        # Copy to AI_Access if we have a resume
        ai_filename = None
        ai_url = None
        
        if resume_path:
            ai_filename = copy_to_ai_access(resume_path, candidate_id, full_name, created_at)
            
            if ai_filename:
                resume_copied += 1
                
                # Get SharePoint URL
                ai_url = get_sharepoint_url(graph_client, ai_filename)
                
                # Wait for OneDrive sync
                if not ai_url:
                    time.sleep(0.5)
                    ai_url = get_sharepoint_url(graph_client, ai_filename)
        
        # Insert ALL candidates into AI Access database (with or without resumes)
        try:
            cur_ai.execute("""
                INSERT INTO gh.candidates (
                    candidate_id, full_name, first_name, last_name,
                    email, phone_numbers, created_at,
                    resume_links, resume_filenames
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (candidate_id) DO NOTHING
            """, (
                candidate_id, full_name, first_name, last_name,
                email, phone_numbers, created_at,
                [ai_url] if ai_url else None,
                [ai_filename] if ai_filename else None
            ))
            
            success_count += 1
            
            if success_count % 50 == 0:
                conn_ai.commit()
        
        except Exception as e:
            log(f"  ❌ Failed to insert {candidate_id}: {e}")
            failed += 1
        
        # Track candidates without resumes for reporting
        if not resume_path:
            no_resume += 1
    
    # Final commit
    conn_ai.commit()
    
    # Summary
    log("\n" + "="*70)
    log("BACKFILL SUMMARY")
    log("="*70)
    log(f"Total candidates processed: {len(missing_ids):,}")
    log(f"Successfully added to AI Access DB: {success_count:,}")
    log(f"Resumes downloaded: {resume_downloaded:,}")
    log(f"Resumes copied to AI_Access: {resume_copied:,}")
    log(f"No resume available: {no_resume:,}")
    log(f"Failed: {failed:,}")
    log("="*70)
    
    # Verify final counts
    cur_db.execute('SELECT COUNT(*) FROM gh.candidates')
    db_total = cur_db.fetchone()[0]
    
    cur_ai.execute('SELECT COUNT(*) FROM gh.candidates')
    ai_total = cur_ai.fetchone()[0]
    
    log(f"\n✅ Database sync complete!")
    log(f"   dbBuilder: {db_total:,} candidates")
    log(f"   AI Access: {ai_total:,} candidates")
    log(f"   Gap: {db_total - ai_total:,} candidates")
    
    conn_db.close()
    conn_ai.close()

if __name__ == "__main__":
    main()
