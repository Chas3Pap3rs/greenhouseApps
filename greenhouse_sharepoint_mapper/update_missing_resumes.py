#!/usr/bin/env python3
"""
Update Missing Resumes in AI Access Database

This script finds candidates in the AI Access database that have NULL resume_links
and attempts to:
1. Find their resume in the organized folders or AI_Access folder
2. If not found, fetch fresh data from Greenhouse API and download
3. Copy to AI_Access folder
4. Update their resume_links and resume_filenames

This fixes candidates that were added without resumes.
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
    
    name = name.strip('. ')
    
    while '  ' in name:
        name = name.replace('  ', ' ')
    
    return name[:200]

def build_filename(candidate_id, full_name, created_at, extension):
    """Build a standardized filename"""
    safe_name = sanitize_filename(full_name)
    
    if isinstance(created_at, str):
        date_str = created_at[:10].replace('-', '')
    else:
        date_str = created_at.strftime("%Y%m%d") if created_at else "unknown"
    
    return f"{candidate_id}_{safe_name}_{date_str}.{extension}"

def find_resume_file(candidate_id):
    """Find resume in AI_Access or organized folders"""
    # Check AI_Access first
    try:
        for file in os.listdir(AI_ACCESS_DIR):
            if file.startswith(f"{candidate_id}_") and not file.endswith("_metadata.json") and not file.startswith("_"):
                return os.path.join(AI_ACCESS_DIR, file)
    except:
        pass
    
    # Check organized folders
    for root, dirs, files in os.walk(LOCAL_RESUME_DIR):
        if 'AI_Access' in root:
            continue
        
        for file in files:
            if file.startswith(f"{candidate_id}_") and not file.startswith("FAILED_"):
                return os.path.join(root, file)
    
    return None

def copy_to_ai_access(source_path, candidate_id, full_name, created_at):
    """Copy resume to AI_Access folder"""
    if not source_path or not os.path.exists(source_path):
        return None
    
    ext = source_path.split('.')[-1].lower()
    filename = build_filename(candidate_id, full_name, created_at, ext)
    dest_path = os.path.join(AI_ACCESS_DIR, filename)
    
    if not os.path.exists(dest_path) or os.path.getsize(source_path) != os.path.getsize(dest_path):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                shutil.copy2(source_path, dest_path)
                return filename
            except (TimeoutError, OSError) as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    return None
    
    return filename

def get_sharepoint_url(graph_client, filename):
    """Get SharePoint URL for file in AI_Access folder"""
    try:
        relative_path = f"AI_Access/{filename}"
        file_info = graph_client.find_file_by_path(relative_path)
        
        # Use permanent webUrl instead of temporary downloadUrl
        # webUrl provides permanent access, downloadUrl expires after 1-24 hours
        if file_info and 'webUrl' in file_info:
            return file_info['webUrl']
    except:
        pass
    
    return None

def main():
    log("="*70)
    log("UPDATE MISSING RESUMES IN AI ACCESS DATABASE")
    log("="*70)
    
    # Connect to database
    log("\nConnecting to AI Access database...")
    conn = psycopg2.connect(**PG_AI)
    
    # Find candidates with NULL resume_links
    log("Finding candidates with missing resumes...")
    cur = conn.cursor()
    cur.execute("""
        SELECT candidate_id, full_name, first_name, last_name, created_at
        FROM gh.candidates
        WHERE resume_links IS NULL OR array_length(resume_links, 1) IS NULL
        ORDER BY candidate_id
    """)
    
    candidates = cur.fetchall()
    log(f"Found {len(candidates):,} candidates with missing resumes")
    
    if len(candidates) == 0:
        log("✅ No candidates need resume updates!")
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
    
    # Process candidates
    log(f"\nProcessing {len(candidates):,} candidates...")
    
    updated = 0
    found_existing = 0
    downloaded_new = 0
    no_resume = 0
    
    for idx, (candidate_id, full_name, first_name, last_name, created_at) in enumerate(candidates, 1):
        if idx % 100 == 0:
            log(f"Progress: {idx}/{len(candidates)} ({idx/len(candidates)*100:.1f}%)")
        
        # Try to find existing resume
        resume_path = find_resume_file(candidate_id)
        
        if resume_path:
            found_existing += 1
        else:
            # Try to download from Greenhouse with fresh URL
            fresh_data = get_fresh_candidate_data(candidate_id)
            
            if fresh_data:
                attachments = fresh_data.get('attachments', [])
                best_resume = None
                
                for att in attachments:
                    if att.get('type') == 'resume':
                        if not best_resume or att.get('filename', '').lower().endswith('.pdf'):
                            best_resume = att
                
                if best_resume and best_resume.get('url'):
                    # Download resume
                    try:
                        response = requests.get(best_resume['url'], stream=True, timeout=30)
                        response.raise_for_status()
                        
                        ext = best_resume.get('filename', 'resume.pdf').split('.')[-1].lower()
                        filename = build_filename(candidate_id, full_name, created_at, ext)
                        temp_path = os.path.join(LOCAL_RESUME_DIR, '2025', '12_December', filename)
                        
                        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                        
                        with open(temp_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        resume_path = temp_path
                        downloaded_new += 1
                    except:
                        pass
        
        # If we have a resume, copy to AI_Access and update database
        if resume_path:
            ai_filename = copy_to_ai_access(resume_path, candidate_id, full_name, created_at)
            
            if ai_filename:
                ai_url = get_sharepoint_url(graph_client, ai_filename)
                
                if not ai_url:
                    time.sleep(0.5)
                    ai_url = get_sharepoint_url(graph_client, ai_filename)
                
                # Update database
                try:
                    cur.execute("""
                        UPDATE gh.candidates
                        SET resume_links = %s,
                            resume_filenames = %s
                        WHERE candidate_id = %s
                    """, (
                        [ai_url] if ai_url else None,
                        [ai_filename],
                        candidate_id
                    ))
                    
                    updated += 1
                    
                    if updated % 50 == 0:
                        conn.commit()
                except Exception as e:
                    log(f"  ❌ Failed to update {candidate_id}: {e}")
        else:
            no_resume += 1
    
    # Final commit
    conn.commit()
    
    # Summary
    log("\n" + "="*70)
    log("UPDATE SUMMARY")
    log("="*70)
    log(f"Total candidates processed: {len(candidates):,}")
    log(f"Successfully updated: {updated:,}")
    log(f"  - Found existing resumes: {found_existing:,}")
    log(f"  - Downloaded new resumes: {downloaded_new:,}")
    log(f"No resume available: {no_resume:,}")
    log("="*70)
    
    conn.close()

if __name__ == "__main__":
    main()
