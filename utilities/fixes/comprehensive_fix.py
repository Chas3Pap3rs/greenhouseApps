#!/usr/bin/env python3
"""
Comprehensive Fix for AI Access Database Gaps

This script addresses all missing data in the AI Access database:
1. Maps metadata_url for all candidates with metadata files
2. Syncs resume_content from metadata files
3. Re-extracts text from resumes where metadata has no text_content
"""

import os
import json
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from graph_client import GraphClient

load_dotenv()

# Configuration
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

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return None

def extract_text_from_docx(docx_path):
    """Extract text from DOCX file"""
    try:
        from docx import Document
        doc = Document(docx_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        return None

def extract_text_from_file(file_path):
    """Extract text from resume file based on extension"""
    ext = Path(file_path).suffix.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    else:
        return None

def fix_metadata_urls(graph_client, conn):
    """Map metadata_url for all candidates with metadata files but no URL"""
    log("="*70)
    log("STEP 1: Mapping Missing Metadata URLs")
    log("="*70)
    log("")
    
    cur = conn.cursor()
    
    # Get candidates with resume_links but no metadata_url
    cur.execute("""
        SELECT candidate_id, full_name
        FROM gh.candidates
        WHERE resume_links IS NOT NULL AND array_length(resume_links, 1) > 0
        AND (metadata_url IS NULL OR metadata_url = '')
        ORDER BY candidate_id
    """)
    
    candidates = cur.fetchall()
    log(f"Found {len(candidates):,} candidates missing metadata_url")
    
    if not candidates:
        log("✅ No missing metadata URLs!")
        return 0
    
    log("")
    log("Processing metadata files...")
    
    mapped = 0
    no_file = 0
    failed = 0
    
    for i, (cid, name) in enumerate(candidates, 1):
        if i % 100 == 0:
            log(f"  Progress: {i:,} / {len(candidates):,} ({i/len(candidates)*100:.1f}%)")
        
        # Find metadata file
        metadata_file = None
        for file in os.listdir(AI_ACCESS_DIR):
            if file.startswith(f"{cid}_") and file.endswith("_metadata.json"):
                metadata_file = os.path.join(AI_ACCESS_DIR, file)
                break
        
        if not metadata_file or not os.path.exists(metadata_file):
            no_file += 1
            continue
        
        # Get SharePoint URL for metadata file
        try:
            url, filename = graph_client.get_sharepoint_url_for_local_file(metadata_file)
            if url:
                cur.execute("""
                    UPDATE gh.candidates
                    SET metadata_url = %s
                    WHERE candidate_id = %s
                """, (url, cid))
                mapped += 1
                
                if mapped % 100 == 0:
                    conn.commit()
            else:
                failed += 1
        except Exception as e:
            failed += 1
            continue
    
    conn.commit()
    
    log("")
    log(f"✅ Mapped {mapped:,} metadata URLs")
    log(f"⚠️  No metadata file: {no_file:,}")
    log(f"❌ Failed: {failed:,}")
    log("")
    
    cur.close()
    return mapped

def sync_resume_content_from_metadata(conn):
    """Sync resume_content from metadata files"""
    log("="*70)
    log("STEP 2: Syncing Resume Content from Metadata Files")
    log("="*70)
    log("")
    
    cur = conn.cursor()
    
    # Get candidates with metadata_url but no resume_content
    cur.execute("""
        SELECT candidate_id, full_name
        FROM gh.candidates
        WHERE metadata_url IS NOT NULL AND metadata_url != ''
        AND (resume_content IS NULL OR resume_content = '')
        ORDER BY candidate_id
    """)
    
    candidates = cur.fetchall()
    log(f"Found {len(candidates):,} candidates needing resume_content")
    
    if not candidates:
        log("✅ All candidates with metadata_url have resume_content!")
        return 0
    
    log("")
    log("Processing metadata files...")
    
    updated = 0
    no_file = 0
    no_text = 0
    failed = 0
    
    for i, (cid, name) in enumerate(candidates, 1):
        if i % 100 == 0:
            log(f"  Progress: {i:,} / {len(candidates):,} ({i/len(candidates)*100:.1f}%)")
        
        # Find metadata file
        metadata_file = None
        for file in os.listdir(AI_ACCESS_DIR):
            if file.startswith(f"{cid}_") and file.endswith("_metadata.json"):
                metadata_file = os.path.join(AI_ACCESS_DIR, file)
                break
        
        if not metadata_file or not os.path.exists(metadata_file):
            no_file += 1
            continue
        
        # Read metadata and extract text_content
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                resume_text = metadata.get('text_content', '') or metadata.get('resume_text', '')
                
                if resume_text:
                    cur.execute("""
                        UPDATE gh.candidates
                        SET resume_content = %s
                        WHERE candidate_id = %s
                    """, (resume_text, cid))
                    updated += 1
                    
                    if updated % 100 == 0:
                        conn.commit()
                else:
                    no_text += 1
        except Exception as e:
            failed += 1
            continue
    
    conn.commit()
    
    log("")
    log(f"✅ Updated {updated:,} candidates with resume_content")
    log(f"⚠️  No metadata file: {no_file:,}")
    log(f"⚠️  No text in metadata: {no_text:,}")
    log(f"❌ Failed: {failed:,}")
    log("")
    
    cur.close()
    return updated, no_text

def re_extract_text_for_empty_metadata(conn):
    """Re-extract text from resume files where metadata has no text_content"""
    log("="*70)
    log("STEP 3: Re-extracting Text from Resumes (Empty Metadata)")
    log("="*70)
    log("")
    
    cur = conn.cursor()
    
    # Get candidates with metadata_url but no resume_content
    cur.execute("""
        SELECT candidate_id, full_name, resume_filenames[1]
        FROM gh.candidates
        WHERE metadata_url IS NOT NULL AND metadata_url != ''
        AND (resume_content IS NULL OR resume_content = '')
        ORDER BY candidate_id
    """)
    
    candidates = cur.fetchall()
    log(f"Found {len(candidates):,} candidates still missing resume_content")
    
    if not candidates:
        log("✅ All candidates have resume_content!")
        return 0
    
    log("")
    log("Re-extracting text from resume files...")
    
    extracted = 0
    no_file = 0
    failed = 0
    
    for i, (cid, name, resume_filename) in enumerate(candidates, 1):
        if i % 100 == 0:
            log(f"  Progress: {i:,} / {len(candidates):,} ({i/len(candidates)*100:.1f}%)")
        
        if not resume_filename:
            no_file += 1
            continue
        
        # Find resume file in AI_Access
        resume_path = os.path.join(AI_ACCESS_DIR, resume_filename)
        
        if not os.path.exists(resume_path):
            no_file += 1
            continue
        
        # Extract text
        try:
            text = extract_text_from_file(resume_path)
            
            if text:
                # Update database
                cur.execute("""
                    UPDATE gh.candidates
                    SET resume_content = %s
                    WHERE candidate_id = %s
                """, (text, cid))
                extracted += 1
                
                # Also update metadata file
                for file in os.listdir(AI_ACCESS_DIR):
                    if file.startswith(f"{cid}_") and file.endswith("_metadata.json"):
                        metadata_file = os.path.join(AI_ACCESS_DIR, file)
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            metadata['text_content'] = text
                            metadata['text_extracted'] = True
                            with open(metadata_file, 'w', encoding='utf-8') as f:
                                json.dump(metadata, f, indent=2)
                        except:
                            pass
                        break
                
                if extracted % 100 == 0:
                    conn.commit()
            else:
                failed += 1
        except Exception as e:
            failed += 1
            continue
    
    conn.commit()
    
    log("")
    log(f"✅ Extracted text for {extracted:,} candidates")
    log(f"⚠️  No resume file: {no_file:,}")
    log(f"❌ Failed extraction: {failed:,}")
    log("")
    
    cur.close()
    return extracted

def main():
    """Run comprehensive fix"""
    log("="*70)
    log("COMPREHENSIVE FIX FOR AI ACCESS DATABASE")
    log("="*70)
    log("")
    
    # Initialize Graph client
    log("Initializing SharePoint connection...")
    try:
        graph_client = GraphClient()
        log("✅ Connected to SharePoint")
    except Exception as e:
        log(f"❌ Failed to connect to SharePoint: {e}")
        return
    
    log("")
    
    # Connect to database
    log("Connecting to database...")
    try:
        conn = psycopg2.connect(**PG_AI)
        log("✅ Connected to database")
    except Exception as e:
        log(f"❌ Failed to connect to database: {e}")
        return
    
    log("")
    
    try:
        # Step 1: Fix metadata URLs
        mapped = fix_metadata_urls(graph_client, conn)
        
        # Step 2: Sync resume content from metadata
        updated, no_text = sync_resume_content_from_metadata(conn)
        
        # Step 3: Re-extract text for empty metadata
        extracted = re_extract_text_for_empty_metadata(conn)
        
        # Final summary
        log("="*70)
        log("COMPREHENSIVE FIX COMPLETE!")
        log("="*70)
        log(f"✅ Metadata URLs mapped: {mapped:,}")
        log(f"✅ Resume content synced from metadata: {updated:,}")
        log(f"✅ Text re-extracted from resumes: {extracted:,}")
        log(f"📊 Total improvements: {mapped + updated + extracted:,}")
        log("")
        
        # Final coverage check
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN resume_links IS NOT NULL AND array_length(resume_links, 1) > 0 THEN 1 END) as with_resume,
                COUNT(CASE WHEN metadata_url IS NOT NULL AND metadata_url != '' THEN 1 END) as with_metadata,
                COUNT(CASE WHEN resume_content IS NOT NULL AND resume_content != '' THEN 1 END) as with_content
            FROM gh.candidates
        """)
        
        result = cur.fetchone()
        log("Final Coverage:")
        log(f"  Total candidates: {result[0]:,}")
        log(f"  With resume_links: {result[1]:,} ({result[1]/result[0]*100:.1f}%)")
        log(f"  With metadata_url: {result[2]:,} ({result[2]/result[0]*100:.1f}%)")
        log(f"  With resume_content: {result[3]:,} ({result[3]/result[0]*100:.1f}%)")
        log("="*70)
        
        cur.close()
        
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ Error: {e}")
        raise
