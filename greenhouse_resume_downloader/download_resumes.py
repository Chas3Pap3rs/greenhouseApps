#!/usr/bin/env python3
"""
Greenhouse Resume Downloader

Downloads candidate resumes from Greenhouse and saves them with structured naming.
Prefers PDF files and tracks download status to avoid duplicates.
"""

import os
import re
import sys
import time
import mimetypes
import pathlib
import psycopg2
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "greenhouse_candidates"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

GREENHOUSE_API_KEY = os.getenv("GREENHOUSE_API_KEY")
SAVE_DIR = os.path.expanduser(os.getenv("RESUME_SAVE_DIR", "./downloads/resumes"))
SKIP_IF_ALREADY_DOWNLOADED = os.getenv("SKIP_IF_ALREADY_DOWNLOADED", "true").lower() == "true"
PREFER_PDF_FORMAT = os.getenv("PREFER_PDF_FORMAT", "true").lower() == "true"

# File naming helpers
SAFE_CHARS = re.compile(r"[^A-Za-z0-9_.\- ]+")

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def sanitize_filename(text):
    """Make text safe for filenames"""
    if not text:
        return "unknown"
    
    # Replace problematic characters
    text = text.strip().replace("/", "-").replace("\\", "-")
    text = SAFE_CHARS.sub("_", text)
    text = re.sub(r"\s+", " ", text).strip()
    
    # Limit length to avoid filesystem issues
    return text[:100] if len(text) > 100 else text

def format_timestamp(ts_string):
    """Convert timestamp to compact format for filename"""
    if not ts_string:
        return "unknown"
    
    try:
        # Parse ISO timestamp and convert to compact format
        dt = datetime.fromisoformat(ts_string.replace("Z", "+00:00"))
        return dt.strftime("%Y%m%d")
    except Exception:
        return "unknown"

def choose_best_resume(attachments):
    """
    Select the best resume from candidate attachments
    Prefers PDFs when available, then most recent by timestamp
    """
    if not attachments:
        return None
    
    # Filter to only resume attachments
    resumes = [a for a in attachments if isinstance(a, dict) and a.get("type") == "resume"]
    if not resumes:
        return None
    
    # If we prefer PDFs and have PDF resumes, filter to those
    if PREFER_PDF_FORMAT:
        pdf_resumes = [r for r in resumes if r.get("filename", "").lower().endswith('.pdf')]
        if pdf_resumes:
            resumes = pdf_resumes
    
    # Sort by creation date (most recent first)
    def get_timestamp(resume):
        for field in ["created_at", "updated_at"]:
            ts = resume.get(field)
            if ts:
                try:
                    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    continue
        return datetime.min
    
    resumes.sort(key=get_timestamp, reverse=True)
    return resumes[0]

def detect_file_extension(response, url, fallback_filename=None):
    """Detect file extension from response headers, filename, or URL"""
    
    # Try Content-Disposition header first
    cd = response.headers.get("Content-Disposition", "")
    if cd:
        filename_match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^\";]+)"?', cd)
        if filename_match:
            ext = pathlib.Path(filename_match.group(1)).suffix
            if ext:
                return ext
    
    # Try provided filename
    if fallback_filename:
        ext = pathlib.Path(fallback_filename).suffix
        if ext:
            return ext
    
    # Try Content-Type header
    content_type = response.headers.get("Content-Type", "")
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ext
    
    # Try URL path
    ext = pathlib.Path(url.split("?")[0]).suffix
    return ext or ".bin"

def build_filename(candidate_id, full_name, created_at, extension):
    """Build standardized filename: {candidate_id}_{full_name}_{date}.{ext}"""
    safe_name = sanitize_filename(full_name or "Unknown")
    date_str = format_timestamp(created_at)
    
    base_name = f"{candidate_id}_{safe_name}_{date_str}"
    return f"{base_name}{extension}"

def get_organized_save_path(base_dir, created_at, filename, is_failed=False):
    """
    Build organized directory structure based on creation date
    
    Structure:
    base_dir/
    ├── 2025/
    │   ├── 01_January/
    │   └── 02_February/
    └── Failed_Downloads/
    """
    if is_failed:
        # Put failed downloads in separate folder
        subfolder = "Failed_Downloads"
        full_path = os.path.join(base_dir, subfolder)
    else:
        # Organize by year and month
        try:
            if created_at:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                dt = datetime.now()
            
            year = dt.strftime("%Y")
            month = dt.strftime("%m_%B")  # "01_January"
            
            subfolder = os.path.join(year, month)
            full_path = os.path.join(base_dir, subfolder)
        except Exception:
            # Fallback to current date if parsing fails
            now = datetime.now()
            year = now.strftime("%Y")
            month = now.strftime("%m_%B")
            subfolder = os.path.join(year, month)
            full_path = os.path.join(base_dir, subfolder)
    
    # Ensure directory exists
    ensure_directory_exists(full_path)
    
    return os.path.join(full_path, filename)

def ensure_directory_exists(path):
    """Create directory if it doesn't exist"""
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def already_downloaded(conn, candidate_id):
    """Check if candidate resume already downloaded successfully"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT download_status FROM gh.resume_download_audit 
            WHERE candidate_id = %s
        """, (candidate_id,))
        result = cur.fetchone()
        return result and result[0] == 'success'

def record_download_attempt(conn, candidate_id, resume_data, status, saved_path=None, error_msg=None, file_size=None):
    """Record download attempt in audit table"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO gh.resume_download_audit (
                candidate_id, attachment_url, attachment_filename, 
                attachment_created, saved_path, download_status, 
                error_message, file_size_bytes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (candidate_id) DO UPDATE SET
                attachment_url = EXCLUDED.attachment_url,
                attachment_filename = EXCLUDED.attachment_filename,
                attachment_created = EXCLUDED.attachment_created,
                saved_path = EXCLUDED.saved_path,
                download_status = EXCLUDED.download_status,
                error_message = EXCLUDED.error_message,
                downloaded_at = NOW(),
                file_size_bytes = EXCLUDED.file_size_bytes
        """, (
            candidate_id,
            resume_data.get("url"),
            resume_data.get("filename"),
            resume_data.get("created_at"),
            saved_path,
            status,
            error_msg,
            file_size
        ))
    conn.commit()

def download_resume(resume_url, save_path, auth=None):
    """Download resume file with streaming"""
    try:
        # Don't use auth for S3 signed URLs - they have their own signature
        with requests.get(resume_url, stream=True, timeout=120) as response:
            response.raise_for_status()
            
            total_size = 0
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        total_size += len(chunk)
            
            return total_size, None
            
    except requests.exceptions.RequestException as e:
        return 0, f"Download failed: {str(e)}"
    except Exception as e:
        return 0, f"Unexpected error: {str(e)}"

def get_unique_filepath(base_path):
    """Generate unique filepath if file already exists"""
    if not os.path.exists(base_path):
        return base_path
    
    path_obj = pathlib.Path(base_path)
    base = path_obj.stem
    suffix = path_obj.suffix
    parent = path_obj.parent
    
    counter = 1
    while True:
        new_path = parent / f"{base}_{counter}{suffix}"
        if not new_path.exists():
            return str(new_path)
        counter += 1

def main():
    """Main download process"""
    if not GREENHOUSE_API_KEY:
        log("ERROR: Missing GREENHOUSE_API_KEY in .env file")
        sys.exit(1)
    
    log("Starting resume download process...")
    log(f"Save directory: {SAVE_DIR}")
    log(f"Skip already downloaded: {SKIP_IF_ALREADY_DOWNLOADED}")
    log(f"Prefer PDF format: {PREFER_PDF_FORMAT}")
    
    # Ensure save directory exists
    ensure_directory_exists(SAVE_DIR)
    
    # Setup authentication
    auth = requests.auth.HTTPBasicAuth(GREENHOUSE_API_KEY, "")
    
    # Counters
    total_candidates = 0
    candidates_with_resumes = 0
    successful_downloads = 0
    skipped_downloads = 0
    failed_downloads = 0
    
    try:
        with psycopg2.connect(**PG) as conn:
            log("Connected to database, fetching candidates with resume attachments...")
            
            with conn.cursor() as cur:
                # Get candidates that have attachments in their raw JSON
                # Filter by updated_at to only get recently synced candidates with fresh URLs
                cur.execute("""
                    SELECT 
                        c.candidate_id,
                        COALESCE(NULLIF(TRIM(c.full_name), ''), 
                                CONCAT(COALESCE(c.first_name,''), ' ', COALESCE(c.last_name,''))) AS full_name,
                        c.created_at,
                        c.raw
                    FROM gh.candidates c
                    WHERE c.raw ? 'attachments'
                      AND c.updated_at >= NOW() - INTERVAL '1 day'
                    ORDER BY c.candidate_id
                """)
                
                candidates = cur.fetchall()
                log(f"Found {len(candidates)} candidates with attachments")
            
            for candidate_id, full_name, created_at, raw_data in candidates:
                total_candidates += 1
                
                # Skip if already downloaded successfully
                if SKIP_IF_ALREADY_DOWNLOADED and already_downloaded(conn, candidate_id):
                    skipped_downloads += 1
                    continue
                
                # Extract attachments from raw JSON
                attachments = raw_data.get("attachments", []) if isinstance(raw_data, dict) else []
                
                # Find best resume
                best_resume = choose_best_resume(attachments)
                if not best_resume:
                    continue
                
                candidates_with_resumes += 1
                resume_url = best_resume.get("url")
                
                if not resume_url:
                    record_download_attempt(conn, candidate_id, best_resume, "failed", 
                                          error_msg="No URL found in resume attachment")
                    failed_downloads += 1
                    continue
                
                try:
                    log(f"Downloading resume for candidate {candidate_id}: {full_name}")
                    
                    # Download to temporary location first
                    # Don't use auth for S3 signed URLs - they have their own signature
                    temp_response = requests.get(resume_url, stream=True, timeout=30)
                    temp_response.raise_for_status()
                    
                    # Detect file extension
                    extension = detect_file_extension(temp_response, resume_url, best_resume.get("filename"))
                    
                    # Build final filename
                    filename = build_filename(candidate_id, full_name, 
                                            best_resume.get("created_at") or created_at, extension)
                    
                    # Get organized save path (creates subdirectories)
                    save_path = get_organized_save_path(SAVE_DIR, best_resume.get("created_at") or created_at, filename)
                    
                    # Ensure unique filename if file already exists
                    save_path = get_unique_filepath(save_path)
                    
                    # Download the file
                    file_size, error_msg = download_resume(resume_url, save_path)
                    
                    if error_msg:
                        # Save failed download info to Failed_Downloads folder
                        failed_filename = f"FAILED_{filename}"
                        failed_path = get_organized_save_path(SAVE_DIR, None, failed_filename, is_failed=True)
                        
                        record_download_attempt(conn, candidate_id, best_resume, "failed", 
                                              saved_path=failed_path, error_msg=error_msg)
                        failed_downloads += 1
                        log(f"  Failed: {error_msg}")
                    else:
                        record_download_attempt(conn, candidate_id, best_resume, "success", 
                                              saved_path=save_path, file_size=file_size)
                        successful_downloads += 1
                        
                        # Show organized path in log
                        relative_path = os.path.relpath(save_path, SAVE_DIR)
                        log(f"  Success: {relative_path} ({file_size:,} bytes)")
                    
                except Exception as e:
                    error_msg = f"Unexpected error: {str(e)}"
                    record_download_attempt(conn, candidate_id, best_resume, "failed", 
                                          error_msg=error_msg)
                    failed_downloads += 1
                    log(f"  Error: {error_msg}")
                
                # Be gentle on the API and filesystem
                time.sleep(0.1)
    
    except Exception as e:
        log(f"Database connection error: {e}")
        sys.exit(1)
    
    # Final summary
    log("\n" + "="*50)
    log("DOWNLOAD SUMMARY")
    log("="*50)
    log(f"Total candidates processed: {total_candidates:,}")
    log(f"Candidates with resumes: {candidates_with_resumes:,}")
    log(f"Successful downloads: {successful_downloads:,}")
    log(f"Skipped (already downloaded): {skipped_downloads:,}")
    log(f"Failed downloads: {failed_downloads:,}")
    log(f"Files saved to: {SAVE_DIR}")
    
    if failed_downloads > 0:
        log(f"\nTo see failed download details, check the gh.resume_download_audit table")

if __name__ == "__main__":
    main()
