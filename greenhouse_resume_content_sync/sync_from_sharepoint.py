#!/usr/bin/env python3
"""
HYBRID SYNC - Populate resume_content from local metadata files for missing candidates

This script fills gaps left by the direct extraction script by:
1. Finding candidates with NULL resume_content in Greenhouse
2. Looking up their metadata files in the local AI_Access folder
3. Reading the pre-extracted text from metadata JSON files
4. Updating the resume_content field in Greenhouse

Use this after running sync_resume_content.py to capture .rtf, .doc, and other
files that couldn't be extracted directly from Greenhouse.
"""

import os
import sys
import json
import glob
import requests
import base64
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Greenhouse API configuration
GREENHOUSE_API_KEY = os.getenv("GREENHOUSE_API_KEY")
GREENHOUSE_USER_ID = os.getenv("GREENHOUSE_USER_ID", "4371230008")
GREENHOUSE_RESUME_CONTENT_FIELD_ID = int(os.getenv("GREENHOUSE_RESUME_CONTENT_FIELD_ID", "11138961008"))
GREENHOUSE_BASE_URL = "https://harvest.greenhouse.io/v1"

# Local AI_Access folder path
LOCAL_AI_ACCESS_DIR = os.getenv("LOCAL_AI_ACCESS_DIR", 
    "/Users/chasepoulton/Library/CloudStorage/OneDrive-CookSystems/AI Operator - Greenhouse_Resumes/AI_Access")

if not GREENHOUSE_API_KEY:
    print("ERROR: GREENHOUSE_API_KEY not found in .env file")
    sys.exit(1)

if not os.path.exists(LOCAL_AI_ACCESS_DIR):
    print(f"ERROR: AI_Access directory not found: {LOCAL_AI_ACCESS_DIR}")
    sys.exit(1)

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def get_greenhouse_headers(include_on_behalf_of=False):
    """Get headers for Greenhouse API requests"""
    auth_string = f"{GREENHOUSE_API_KEY}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json"
    }
    
    if include_on_behalf_of:
        headers["On-Behalf-Of"] = GREENHOUSE_USER_ID
    
    return headers

def find_metadata_file(candidate_id):
    """Find metadata JSON file for a candidate in local AI_Access folder"""
    # Metadata files are named: {candidate_id}_*_metadata.json
    pattern = os.path.join(LOCAL_AI_ACCESS_DIR, f"{candidate_id}_*_metadata.json")
    matches = glob.glob(pattern)
    
    if matches:
        return matches[0]  # Return first match
    return None

def get_candidates_from_local_files():
    """
    Get all candidate IDs that have metadata files in the local AI_Access folder
    Returns list of candidate_ids
    """
    log(f"Scanning local AI_Access folder: {LOCAL_AI_ACCESS_DIR}")
    
    # Find all metadata JSON files
    pattern = os.path.join(LOCAL_AI_ACCESS_DIR, "*_metadata.json")
    metadata_files = glob.glob(pattern)
    
    log(f"Found {len(metadata_files)} metadata files")
    
    # Extract candidate IDs from filenames
    candidate_ids = []
    for filepath in metadata_files:
        filename = os.path.basename(filepath)
        # Filename format: {candidate_id}_Name_Date_metadata.json
        candidate_id = filename.split('_')[0]
        try:
            # Validate it's a number
            int(candidate_id)
            candidate_ids.append(candidate_id)
        except ValueError:
            continue
    
    return sorted(candidate_ids)

def check_resume_content_exists(candidate_id):
    """Check if candidate already has resume_content in Greenhouse"""
    url = f"{GREENHOUSE_BASE_URL}/candidates/{candidate_id}"
    
    try:
        response = requests.get(url, headers=get_greenhouse_headers(), timeout=10)
        response.raise_for_status()
        
        candidate = response.json()
        resume_content = candidate.get('custom_fields', {}).get('resume_content')
        
        # Return True if content exists and is not empty
        return bool(resume_content and resume_content.strip())
        
    except Exception as e:
        log(f"  ⚠️  Error checking candidate {candidate_id}: {e}")
        return None  # Unknown status

def read_metadata_json(metadata_file_path):
    """Read and parse metadata JSON from local file"""
    try:
        with open(metadata_file_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata
        
    except Exception as e:
        log(f"  ❌ Error reading metadata file: {e}")
        return None

def extract_text_from_metadata(metadata):
    """Extract text_content from metadata JSON"""
    try:
        text_content = metadata.get('text_content', '')
        
        if not text_content or not text_content.strip():
            return None
        
        return text_content.strip()
        
    except Exception as e:
        log(f"  ❌ Error extracting text from metadata: {e}")
        return None

def update_resume_content(candidate_id, resume_text):
    """Update the resume_content custom field for a candidate"""
    url = f"{GREENHOUSE_BASE_URL}/candidates/{candidate_id}"
    
    # Truncate if too long
    max_length = 50000
    if len(resume_text) > max_length:
        log(f"  ⚠️  Resume text too long ({len(resume_text)} chars), truncating to {max_length}")
        resume_text = resume_text[:max_length] + "\n\n[TRUNCATED]"
    
    payload = {
        "custom_fields": [
            {
                "id": GREENHOUSE_RESUME_CONTENT_FIELD_ID,
                "value": resume_text
            }
        ]
    }
    
    try:
        response = requests.patch(
            url, 
            headers=get_greenhouse_headers(include_on_behalf_of=True), 
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return True
    except Exception as e:
        log(f"  ❌ Error updating candidate {candidate_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            log(f"     Response: {e.response.text[:200]}")
        return False

def process_candidate(candidate_id):
    """Process a single candidate: check status, read metadata, update field"""
    
    # Check if candidate already has resume_content
    has_content = check_resume_content_exists(candidate_id)
    
    if has_content is None:
        # Error checking - skip this candidate
        return None
    
    if has_content:
        log(f"  ⏭️  Skipping {candidate_id} - already has resume_content")
        return None  # Skipped
    
    # Find metadata file
    metadata_file = find_metadata_file(candidate_id)
    if not metadata_file:
        log(f"  ⚠️  No metadata file found for {candidate_id}")
        return False
    
    log(f"  📄 Processing {candidate_id} - reading from local metadata")
    
    # Read metadata JSON
    metadata = read_metadata_json(metadata_file)
    if not metadata:
        log(f"  ❌ Failed to read metadata for {candidate_id}")
        return False
    
    # Extract text content
    resume_text = extract_text_from_metadata(metadata)
    if not resume_text:
        log(f"  ⚠️  No text content in metadata for {candidate_id}")
        return False
    
    log(f"  ✅ Extracted {len(resume_text)} characters from metadata")
    
    # Update Greenhouse
    success = update_resume_content(candidate_id, resume_text)
    
    if success:
        log(f"  ✅ Updated resume_content for {candidate_id}")
    
    return success

def sync_from_sharepoint():
    """Main function to sync resume content from local metadata files"""
    log("="*60)
    log("GREENHOUSE RESUME CONTENT - LOCAL METADATA HYBRID SYNC")
    log("="*60)
    
    # Get candidates from local metadata files
    candidate_ids = get_candidates_from_local_files()
    
    if not candidate_ids:
        log("❌ No metadata files found in AI_Access folder")
        return
    
    log(f"✅ Found {len(candidate_ids)} candidates with metadata files")
    log("")
    log("Checking which candidates need updates...")
    log("")
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, candidate_id in enumerate(candidate_ids, 1):
        if i % 100 == 0:
            log(f"\nProgress: {i}/{len(candidate_ids)} ({i/len(candidate_ids)*100:.1f}%)")
            log(f"  Updated: {success_count} | Failed: {failed_count} | Skipped: {skipped_count}\n")
        
        result = process_candidate(candidate_id)
        
        if result is True:
            success_count += 1
        elif result is False:
            failed_count += 1
        else:  # None means skipped
            skipped_count += 1
    
    # Final summary
    log("")
    log("="*60)
    log("SYNC SUMMARY")
    log("="*60)
    log(f"Total candidates checked: {len(candidate_ids)}")
    log(f"Updated from local metadata: {success_count}")
    log(f"Skipped (already had content): {skipped_count}")
    log(f"Failed: {failed_count}")
    
    if success_count > 0:
        log("")
        log(f"✅ Successfully synced {success_count} candidates from local metadata files!")
    
    log("="*60)

if __name__ == "__main__":
    sync_from_sharepoint()
