#!/usr/bin/env python3
"""
INCREMENTAL UPDATE - Update resume content for new/changed candidates only
Downloads resume attachments, extracts text, and updates the resume_content custom field

This script only processes:
1. Candidates with NO resume_content (new candidates)
2. Candidates whose most recent resume is newer than their last update

Safe to run daily/weekly/monthly without re-processing everyone.
"""

import os
import sys
import requests
import tempfile
import base64
import time
from datetime import datetime
from dotenv import load_dotenv

# Text extraction functions
def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        import PyPDF2
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return None

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        print(f"Error extracting DOCX text: {e}")
        return None

# Load environment variables
load_dotenv()

# Greenhouse API configuration
GREENHOUSE_API_KEY = os.getenv("GREENHOUSE_API_KEY")
GREENHOUSE_USER_ID = os.getenv("GREENHOUSE_USER_ID", "4371230008")
GREENHOUSE_RESUME_CONTENT_FIELD_ID = int(os.getenv("GREENHOUSE_RESUME_CONTENT_FIELD_ID", "11138961008"))
GREENHOUSE_BASE_URL = "https://harvest.greenhouse.io/v1"

if not GREENHOUSE_API_KEY:
    print("ERROR: GREENHOUSE_API_KEY not found in .env file")
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

def get_all_candidates(per_page=500):
    """Fetch all candidates from Greenhouse API with pagination"""
    log("Fetching candidates from Greenhouse API...")
    
    all_candidates = []
    page = 1
    
    while True:
        url = f"{GREENHOUSE_BASE_URL}/candidates"
        params = {
            "per_page": per_page,
            "page": page
        }
        
        try:
            response = requests.get(url, headers=get_greenhouse_headers(), params=params)
            response.raise_for_status()
            
            candidates = response.json()
            
            if not candidates:
                break
            
            all_candidates.extend(candidates)
            log(f"  Fetched page {page}: {len(candidates)} candidates (total: {len(all_candidates)})")
            
            if len(candidates) < per_page:
                break
            
            page += 1
            
        except Exception as e:
            log(f"❌ Error fetching candidates: {e}")
            break
    
    log(f"✅ Total candidates fetched: {len(all_candidates)}")
    return all_candidates

def get_candidate_details(candidate_id):
    """Get detailed candidate information including custom fields"""
    url = f"{GREENHOUSE_BASE_URL}/candidates/{candidate_id}"
    
    try:
        response = requests.get(url, headers=get_greenhouse_headers())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log(f"❌ Error fetching candidate {candidate_id}: {e}")
        return None

def download_resume(resume_url):
    """Download resume to temporary file and return file path"""
    try:
        response = requests.get(resume_url, timeout=30)
        response.raise_for_status()
        
        # Determine file extension
        if resume_url.endswith('.pdf'):
            suffix = '.pdf'
        elif resume_url.endswith('.docx') or resume_url.endswith('.doc'):
            suffix = '.docx'
        else:
            content_type = response.headers.get('content-type', '')
            if 'pdf' in content_type:
                suffix = '.pdf'
            elif 'word' in content_type or 'document' in content_type:
                suffix = '.docx'
            else:
                suffix = '.tmp'
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(response.content)
            return tmp_file.name
            
    except Exception as e:
        log(f"  ❌ Error downloading resume: {e}")
        return None

def extract_text_from_resume(file_path):
    """Extract text from resume file based on extension"""
    if not file_path:
        return None
    
    try:
        if file_path.endswith('.pdf'):
            return extract_text_from_pdf(file_path)
        elif file_path.endswith('.docx') or file_path.endswith('.doc'):
            return extract_text_from_docx(file_path)
        else:
            log(f"  ⚠️  Unsupported file type: {file_path}")
            return None
    finally:
        # Clean up temporary file
        try:
            os.unlink(file_path)
        except:
            pass

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
        response = requests.patch(url, headers=get_greenhouse_headers(include_on_behalf_of=True), json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        log(f"  ❌ Error updating candidate {candidate_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            log(f"     Response: {e.response.text}")
        return False

def needs_update(detailed_candidate):
    """
    Determine if a candidate needs their resume_content updated
    Returns: (needs_update: bool, reason: str)
    """
    candidate_id = detailed_candidate.get('id')
    
    # Check if resume_content exists
    current_resume_content = detailed_candidate.get('custom_fields', {}).get('resume_content')
    
    # If no resume_content, definitely needs update
    if not current_resume_content:
        return True, "no_content"
    
    # Get resume attachments
    attachments = detailed_candidate.get('attachments', [])
    resume_attachments = [att for att in attachments if att.get('type') == 'resume']
    
    if not resume_attachments:
        return False, "no_resume"
    
    # Get most recent resume
    resume_attachments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    most_recent_resume = resume_attachments[0]
    resume_created_at = most_recent_resume.get('created_at', '')
    
    # Get candidate's last update time
    candidate_updated_at = detailed_candidate.get('updated_at', '')
    
    # If resume is newer than last candidate update, needs update
    # This catches cases where a new resume was uploaded
    if resume_created_at > candidate_updated_at:
        return True, "newer_resume"
    
    # Otherwise, skip
    return False, "up_to_date"

def process_candidate(candidate):
    """Process a single candidate: check if update needed, download resume, extract text, update field"""
    candidate_id = candidate.get('id')
    first_name = candidate.get('first_name', '')
    last_name = candidate.get('last_name', '')
    full_name = f"{first_name} {last_name}".strip()
    
    # Get detailed candidate info
    detailed_candidate = get_candidate_details(candidate_id)
    if not detailed_candidate:
        return False
    
    # Check if update is needed
    needs_update_flag, reason = needs_update(detailed_candidate)
    
    if not needs_update_flag:
        if reason == "up_to_date":
            log(f"  ⏭️  Skipping {candidate_id} ({full_name}) - already up to date")
            return None  # Skipped
        elif reason == "no_resume":
            log(f"  ⚠️  No resume attachment for {candidate_id} ({full_name})")
            return False
    
    # Get resume attachments and find the most recent one
    attachments = detailed_candidate.get('attachments', [])
    resume_attachments = [att for att in attachments if att.get('type') == 'resume']
    
    if not resume_attachments:
        log(f"  ⚠️  No resume attachment for {candidate_id} ({full_name})")
        return False
    
    # Sort by created_at date (most recent first)
    resume_attachments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    resume_attachment = resume_attachments[0]
    
    resume_url = resume_attachment.get('url')
    resume_filename = resume_attachment.get('filename', 'unknown')
    
    log(f"  📄 Processing {candidate_id} ({full_name}) - {resume_filename} [{reason}]")
    
    # Download resume to temp file
    temp_file = download_resume(resume_url)
    if not temp_file:
        return False
    
    # Extract text
    resume_text = extract_text_from_resume(temp_file)
    if not resume_text:
        log(f"  ❌ Failed to extract text from {resume_filename}")
        return False
    
    log(f"  ✅ Extracted {len(resume_text)} characters of text")
    
    # Update Greenhouse
    success = update_resume_content(candidate_id, resume_text)
    
    if success:
        log(f"  ✅ Updated resume_content for {candidate_id} ({full_name})")
    
    return success

def update_resume_content_incremental():
    """Main function to incrementally update resume content"""
    log("="*60)
    log("GREENHOUSE RESUME CONTENT - INCREMENTAL UPDATE")
    log("="*60)
    
    # Fetch all candidates
    candidates = get_all_candidates()
    
    if not candidates:
        log("❌ No candidates found")
        return
    
    log(f"\nChecking {len(candidates)} candidates for updates...")
    log("")
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, candidate in enumerate(candidates, 1):
        if i % 100 == 0:
            log(f"\nProgress: {i}/{len(candidates)} ({i/len(candidates)*100:.1f}%)")
            log(f"  Updated: {success_count} | Failed: {failed_count} | Skipped: {skipped_count}\n")
        
        result = process_candidate(candidate)
        
        if result is True:
            success_count += 1
        elif result is False:
            failed_count += 1
        else:  # None means skipped
            skipped_count += 1
        
        # Rate limiting: 0.5 second delay = 2 requests/sec = 120/min (well under 300/min limit)
        time.sleep(0.5)
    
    # Final summary
    log("")
    log("="*60)
    log("UPDATE SUMMARY")
    log("="*60)
    log(f"Total candidates checked: {len(candidates)}")
    log(f"Updated: {success_count}")
    log(f"Skipped (already up to date): {skipped_count}")
    log(f"Failed: {failed_count}")
    
    if success_count > 0:
        log("")
        log(f"✅ Successfully updated {success_count} candidates!")
    else:
        log("")
        log("✅ All candidates already up to date!")
    
    log("="*60)

if __name__ == "__main__":
    update_resume_content_incremental()
