#!/usr/bin/env python3
"""
AI Access Folder Creator for SharePoint

This script creates a flat, AI-friendly folder structure in SharePoint:
1. Creates an AI_Access folder with all resumes in one place (no subfolders)
2. Extracts text content from PDFs and DOCX files
3. Creates JSON metadata files with extracted text
4. Generates a master index for quick lookups
5. Updates the database with AI-friendly links

This maintains your organized folder structure while providing simple access for AI agents.
"""

import os
import sys
import json
import shutil
import psycopg2
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Text extraction libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

load_dotenv()

# Configuration
LOCAL_RESUME_DIR = os.getenv("LOCAL_RESUME_DIR")
AI_ACCESS_FOLDER = "AI_Access"  # Will be created in SharePoint
LOCAL_AI_ACCESS_DIR = os.path.join(LOCAL_RESUME_DIR, AI_ACCESS_FOLDER)

PG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "greenhouse_candidates_sp"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD", "")
}

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def extract_text_from_pdf(pdf_path):
    """Extract text content from PDF file"""
    if not PDF_AVAILABLE:
        return None
    
    try:
        text_content = []
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        
        return "\n\n".join(text_content) if text_content else None
    except Exception as e:
        log(f"  ⚠️  PDF extraction failed: {e}")
        return None

def extract_text_from_docx(docx_path):
    """Extract text content from DOCX file"""
    if not DOCX_AVAILABLE:
        return None
    
    try:
        doc = Document(docx_path)
        text_content = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content.append(paragraph.text)
        
        return "\n\n".join(text_content) if text_content else None
    except Exception as e:
        log(f"  ⚠️  DOCX extraction failed: {e}")
        return None

def extract_text_from_doc(doc_path):
    """Extract text from .doc file (older Word format)"""
    # .doc files are harder to parse - we'll skip for now
    # Could use textract or antiword if needed
    return None

def extract_text_from_file(file_path):
    """Extract text from resume file based on extension"""
    ext = Path(file_path).suffix.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext == '.doc':
        return extract_text_from_doc(file_path)
    elif ext == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return None
    
    return None

def create_metadata_file(resume_path, candidate_info, output_dir):
    """Create JSON metadata file with extracted text"""
    filename = Path(resume_path).name
    base_name = Path(resume_path).stem
    metadata_filename = f"{base_name}_metadata.json"
    metadata_path = os.path.join(output_dir, metadata_filename)
    
    # Extract text content
    text_content = extract_text_from_file(resume_path)
    
    metadata = {
        "candidate_id": candidate_info.get("candidate_id"),
        "candidate_name": candidate_info.get("full_name"),
        "original_filename": filename,
        "file_extension": Path(resume_path).suffix.lower(),
        "file_size_bytes": os.path.getsize(resume_path),
        "created_at": candidate_info.get("created_at"),
        "extracted_at": datetime.now().isoformat(),
        "text_extracted": text_content is not None,
        "text_content": text_content,
        "original_sharepoint_url": candidate_info.get("sharepoint_url"),
        "ai_access_path": f"{AI_ACCESS_FOLDER}/{filename}"
    }
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return metadata_path, text_content is not None

def create_ai_access_structure():
    """Create the AI Access folder structure locally"""
    log("Creating AI Access folder structure...")
    
    # Create local AI_Access directory
    os.makedirs(LOCAL_AI_ACCESS_DIR, exist_ok=True)
    log(f"✅ Created local directory: {LOCAL_AI_ACCESS_DIR}")
    
    # Get all candidates with resumes from database
    log("Fetching candidates with resumes from database...")
    
    try:
        with psycopg2.connect(**PG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        candidate_id,
                        full_name,
                        resume_links,
                        resume_filenames,
                        created_at
                    FROM gh.candidates
                    WHERE resume_links IS NOT NULL 
                    AND array_length(resume_links, 1) > 0
                    ORDER BY candidate_id
                """)
                
                candidates = cur.fetchall()
                log(f"Found {len(candidates)} candidates with resumes")
    
    except Exception as e:
        log(f"❌ Database error: {e}")
        return False
    
    # Process each candidate
    total_processed = 0
    total_copied = 0
    total_metadata_created = 0
    total_text_extracted = 0
    
    master_index = []
    
    for candidate_id, full_name, resume_links, resume_filenames, created_at in candidates:
        total_processed += 1
        
        if total_processed % 100 == 0:
            log(f"Progress: {total_processed}/{len(candidates)} candidates processed...")
        
        # Find the local resume file
        local_file = None
        for root, dirs, files in os.walk(LOCAL_RESUME_DIR):
            # Skip AI_Access folder itself
            if AI_ACCESS_FOLDER in root:
                continue
            
            for file in files:
                if file.startswith(f"{candidate_id}_") and not file.startswith("FAILED_"):
                    local_file = os.path.join(root, file)
                    break
            if local_file:
                break
        
        if not local_file or not os.path.exists(local_file):
            continue
        
        # Copy file to AI_Access folder with standardized name
        filename = Path(local_file).name
        dest_path = os.path.join(LOCAL_AI_ACCESS_DIR, filename)
        
        try:
            # Copy file if it doesn't exist or is different
            if not os.path.exists(dest_path) or os.path.getsize(local_file) != os.path.getsize(dest_path):
                shutil.copy2(local_file, dest_path)
                total_copied += 1
            
            # Create metadata file
            candidate_info = {
                "candidate_id": candidate_id,
                "full_name": full_name,
                "created_at": created_at.isoformat() if created_at else None,
                "sharepoint_url": resume_links[0] if resume_links else None
            }
            
            metadata_path, text_extracted = create_metadata_file(local_file, candidate_info, LOCAL_AI_ACCESS_DIR)
            total_metadata_created += 1
            
            if text_extracted:
                total_text_extracted += 1
            
            # Add to master index
            master_index.append({
                "candidate_id": candidate_id,
                "candidate_name": full_name,
                "filename": filename,
                "metadata_file": Path(metadata_path).name,
                "text_extracted": text_extracted,
                "ai_access_path": f"{AI_ACCESS_FOLDER}/{filename}"
            })
            
        except Exception as e:
            log(f"  ❌ Failed to process candidate {candidate_id}: {e}")
            continue
    
    # Create master index file
    log("Creating master index file...")
    index_path = os.path.join(LOCAL_AI_ACCESS_DIR, "_master_index.json")
    
    index_data = {
        "created_at": datetime.now().isoformat(),
        "total_resumes": len(master_index),
        "text_extracted_count": total_text_extracted,
        "resumes": master_index
    }
    
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    log("\n" + "="*60)
    log("AI ACCESS FOLDER CREATION SUMMARY")
    log("="*60)
    log(f"Total candidates processed: {total_processed}")
    log(f"Files copied to AI_Access: {total_copied}")
    log(f"Metadata files created: {total_metadata_created}")
    log(f"Text successfully extracted: {total_text_extracted}")
    log(f"Master index created: {index_path}")
    log(f"\nLocal AI_Access folder: {LOCAL_AI_ACCESS_DIR}")
    log("\n✅ AI Access structure created successfully!")
    log("\n📤 Next steps:")
    log("1. The AI_Access folder will sync to SharePoint via OneDrive")
    log("2. Wait for sync to complete (check OneDrive status)")
    log("3. Run 'python update_ai_access_links.py' to update database with AI-friendly links")
    log("="*60)
    
    return True

def check_dependencies():
    """Check if required libraries are installed"""
    log("Checking dependencies...")
    
    missing = []
    if not PDF_AVAILABLE:
        missing.append("PyPDF2")
    if not DOCX_AVAILABLE:
        missing.append("python-docx")
    
    if missing:
        log(f"⚠️  Missing optional libraries: {', '.join(missing)}")
        log("   Text extraction will be limited. Install with:")
        log(f"   pip install {' '.join(missing)}")
        log("\n   Continuing anyway - files will be copied without text extraction...")
        return True
    
    log("✅ All dependencies available")
    return True

def main():
    """Main execution"""
    log("="*60)
    log("AI ACCESS FOLDER CREATOR")
    log("="*60)
    
    if not check_dependencies():
        return
    
    if not LOCAL_RESUME_DIR or not os.path.exists(LOCAL_RESUME_DIR):
        log(f"❌ Resume directory not found: {LOCAL_RESUME_DIR}")
        log("   Check your .env file LOCAL_RESUME_DIR setting")
        return
    
    log(f"Source directory: {LOCAL_RESUME_DIR}")
    log(f"Target directory: {LOCAL_AI_ACCESS_DIR}")
    log("")
    
    success = create_ai_access_structure()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
