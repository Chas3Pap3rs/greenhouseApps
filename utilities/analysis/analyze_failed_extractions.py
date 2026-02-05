#!/usr/bin/env python3
"""
Analyze candidates with failed text extraction to determine:
1. File type distribution
2. File integrity (size, readability)
3. Potential recoverability (OCR candidates, corrupted files, etc.)
"""

import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
import json
from collections import defaultdict
import PyPDF2
from docx import Document

load_dotenv()

def get_db_connection():
    """Create database connection to AI Access database."""
    return psycopg2.connect(
        host=os.getenv('PGHOST', 'localhost'),
        port=int(os.getenv('PGPORT', '5432')),
        database='greenhouse_candidates_ai',
        user=os.getenv('PGUSER'),
        password=os.getenv('PGPASSWORD', '')
    )

def analyze_failed_extractions():
    """Analyze candidates missing resume_content despite having resume files."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("ANALYZING FAILED TEXT EXTRACTIONS")
    print("=" * 80)
    print()
    
    # Get candidates with resume_filename but no resume_content
    cursor.execute("""
        SELECT candidate_id, first_name, last_name, resume_filenames[1] as resume_filename, metadata_url
        FROM gh.candidates
        WHERE resume_filenames IS NOT NULL 
        AND array_length(resume_filenames, 1) > 0
        AND (resume_content IS NULL OR resume_content = '')
        ORDER BY candidate_id
    """)
    
    failed_candidates = cursor.fetchall()
    total_failed = len(failed_candidates)
    
    print(f"📊 Found {total_failed:,} candidates with resume files but no resume_content")
    print()
    
    if total_failed == 0:
        print("✅ No failed extractions to analyze!")
        cursor.close()
        conn.close()
        return
    
    # Analysis variables
    local_resume_dir = os.getenv('LOCAL_RESUME_DIR')
    ai_access_folder = os.path.join(local_resume_dir, 'AI_Access')
    file_stats = {
        'total': total_failed,
        'file_exists': 0,
        'file_missing': 0,
        'file_empty': 0,
        'by_extension': defaultdict(int),
        'by_size': {'0-1KB': 0, '1-10KB': 0, '10-100KB': 0, '100KB-1MB': 0, '1MB+': 0},
        'pdf_analysis': {'total': 0, 'readable': 0, 'corrupted': 0, 'image_based': 0},
        'docx_analysis': {'total': 0, 'readable': 0, 'corrupted': 0},
        'has_metadata': 0,
        'no_metadata': 0
    }
    
    sample_issues = {
        'corrupted_pdfs': [],
        'image_pdfs': [],
        'empty_files': [],
        'missing_files': [],
        'corrupted_docx': []
    }
    
    print("Analyzing files...")
    analyzed = 0
    
    for candidate_id, first_name, last_name, resume_filename, metadata_url in failed_candidates:
        analyzed += 1
        if analyzed % 500 == 0:
            print(f"  Progress: {analyzed:,} / {total_failed:,} ({analyzed*100//total_failed}%)")
        
        # Check metadata
        if metadata_url:
            file_stats['has_metadata'] += 1
        else:
            file_stats['no_metadata'] += 1
        
        # Check if file exists
        resume_path = os.path.join(ai_access_folder, resume_filename)
        
        if not os.path.exists(resume_path):
            file_stats['file_missing'] += 1
            if len(sample_issues['missing_files']) < 10:
                sample_issues['missing_files'].append({
                    'id': candidate_id,
                    'name': f"{first_name} {last_name}",
                    'filename': resume_filename
                })
            continue
        
        file_stats['file_exists'] += 1
        
        # Get file size
        file_size = os.path.getsize(resume_path)
        
        if file_size == 0:
            file_stats['file_empty'] += 1
            if len(sample_issues['empty_files']) < 10:
                sample_issues['empty_files'].append({
                    'id': candidate_id,
                    'name': f"{first_name} {last_name}",
                    'filename': resume_filename
                })
            continue
        
        # Categorize by size
        if file_size < 1024:
            file_stats['by_size']['0-1KB'] += 1
        elif file_size < 10240:
            file_stats['by_size']['1-10KB'] += 1
        elif file_size < 102400:
            file_stats['by_size']['10-100KB'] += 1
        elif file_size < 1048576:
            file_stats['by_size']['100KB-1MB'] += 1
        else:
            file_stats['by_size']['1MB+'] += 1
        
        # Get file extension
        ext = Path(resume_filename).suffix.lower()
        file_stats['by_extension'][ext] += 1
        
        # Analyze PDF files
        if ext == '.pdf':
            file_stats['pdf_analysis']['total'] += 1
            try:
                with open(resume_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    num_pages = len(pdf_reader.pages)
                    
                    if num_pages > 0:
                        # Try to extract text from first page
                        first_page = pdf_reader.pages[0]
                        text = first_page.extract_text().strip()
                        
                        if len(text) > 50:
                            file_stats['pdf_analysis']['readable'] += 1
                        else:
                            # Likely image-based PDF
                            file_stats['pdf_analysis']['image_based'] += 1
                            if len(sample_issues['image_pdfs']) < 10:
                                sample_issues['image_pdfs'].append({
                                    'id': candidate_id,
                                    'name': f"{first_name} {last_name}",
                                    'filename': resume_filename,
                                    'pages': num_pages,
                                    'text_length': len(text)
                                })
                    else:
                        file_stats['pdf_analysis']['corrupted'] += 1
            except Exception as e:
                file_stats['pdf_analysis']['corrupted'] += 1
                if len(sample_issues['corrupted_pdfs']) < 10:
                    sample_issues['corrupted_pdfs'].append({
                        'id': candidate_id,
                        'name': f"{first_name} {last_name}",
                        'filename': resume_filename,
                        'error': str(e)[:100]
                    })
        
        # Analyze DOCX files
        elif ext in ['.docx', '.doc']:
            file_stats['docx_analysis']['total'] += 1
            try:
                doc = Document(resume_path)
                text = '\n'.join([para.text for para in doc.paragraphs])
                
                if len(text.strip()) > 50:
                    file_stats['docx_analysis']['readable'] += 1
                else:
                    file_stats['docx_analysis']['corrupted'] += 1
            except Exception as e:
                file_stats['docx_analysis']['corrupted'] += 1
                if len(sample_issues['corrupted_docx']) < 10:
                    sample_issues['corrupted_docx'].append({
                        'id': candidate_id,
                        'name': f"{first_name} {last_name}",
                        'filename': resume_filename,
                        'error': str(e)[:100]
                    })
    
    print()
    print("=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    print()
    
    # File existence
    print("📁 File Existence:")
    print(f"  Files exist: {file_stats['file_exists']:,} ({file_stats['file_exists']*100//total_failed}%)")
    print(f"  Files missing: {file_stats['file_missing']:,} ({file_stats['file_missing']*100//total_failed}%)")
    print(f"  Files empty: {file_stats['file_empty']:,} ({file_stats['file_empty']*100//total_failed}%)")
    print()
    
    # Metadata status
    print("🔗 Metadata Status:")
    print(f"  Has metadata_url: {file_stats['has_metadata']:,} ({file_stats['has_metadata']*100//total_failed}%)")
    print(f"  No metadata_url: {file_stats['no_metadata']:,} ({file_stats['no_metadata']*100//total_failed}%)")
    print()
    
    # File types
    print("📄 File Type Distribution:")
    for ext, count in sorted(file_stats['by_extension'].items(), key=lambda x: x[1], reverse=True):
        pct = count * 100 // total_failed
        print(f"  {ext}: {count:,} ({pct}%)")
    print()
    
    # File sizes
    print("📏 File Size Distribution:")
    for size_range, count in file_stats['by_size'].items():
        if count > 0:
            pct = count * 100 // total_failed
            print(f"  {size_range}: {count:,} ({pct}%)")
    print()
    
    # PDF analysis
    if file_stats['pdf_analysis']['total'] > 0:
        print("📕 PDF Analysis:")
        pdf_total = file_stats['pdf_analysis']['total']
        print(f"  Total PDFs: {pdf_total:,}")
        print(f"  Readable (has text): {file_stats['pdf_analysis']['readable']:,} ({file_stats['pdf_analysis']['readable']*100//pdf_total}%)")
        print(f"  Image-based (no text): {file_stats['pdf_analysis']['image_based']:,} ({file_stats['pdf_analysis']['image_based']*100//pdf_total}%)")
        print(f"  Corrupted: {file_stats['pdf_analysis']['corrupted']:,} ({file_stats['pdf_analysis']['corrupted']*100//pdf_total}%)")
        print()
    
    # DOCX analysis
    if file_stats['docx_analysis']['total'] > 0:
        print("📘 DOCX Analysis:")
        docx_total = file_stats['docx_analysis']['total']
        print(f"  Total DOCX: {docx_total:,}")
        print(f"  Readable: {file_stats['docx_analysis']['readable']:,} ({file_stats['docx_analysis']['readable']*100//docx_total}%)")
        print(f"  Corrupted: {file_stats['docx_analysis']['corrupted']:,} ({file_stats['docx_analysis']['corrupted']*100//docx_total}%)")
        print()
    
    # Sample issues
    print("=" * 80)
    print("SAMPLE ISSUES (First 10 of each type)")
    print("=" * 80)
    print()
    
    if sample_issues['missing_files']:
        print("❌ Missing Files:")
        for issue in sample_issues['missing_files']:
            print(f"  ID {issue['id']}: {issue['name']} - {issue['filename']}")
        print()
    
    if sample_issues['empty_files']:
        print("⚠️  Empty Files:")
        for issue in sample_issues['empty_files']:
            print(f"  ID {issue['id']}: {issue['name']} - {issue['filename']}")
        print()
    
    if sample_issues['image_pdfs']:
        print("🖼️  Image-based PDFs (OCR candidates):")
        for issue in sample_issues['image_pdfs']:
            print(f"  ID {issue['id']}: {issue['name']} - {issue['filename']} ({issue['pages']} pages, {issue['text_length']} chars)")
        print()
    
    if sample_issues['corrupted_pdfs']:
        print("💔 Corrupted PDFs:")
        for issue in sample_issues['corrupted_pdfs']:
            print(f"  ID {issue['id']}: {issue['name']} - {issue['filename']}")
            print(f"     Error: {issue['error']}")
        print()
    
    if sample_issues['corrupted_docx']:
        print("💔 Corrupted DOCX:")
        for issue in sample_issues['corrupted_docx']:
            print(f"  ID {issue['id']}: {issue['name']} - {issue['filename']}")
            print(f"     Error: {issue['error']}")
        print()
    
    # Recommendations
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()
    
    ocr_candidates = file_stats['pdf_analysis']['image_based']
    corrupted_total = (file_stats['pdf_analysis']['corrupted'] + 
                      file_stats['docx_analysis']['corrupted'] + 
                      file_stats['file_empty'] + 
                      file_stats['file_missing'])
    
    if ocr_candidates > 0:
        print(f"🔍 OCR Opportunity: {ocr_candidates:,} image-based PDFs could be processed with OCR")
        print(f"   This would improve coverage by ~{ocr_candidates*100//total_failed}%")
        print()
    
    if corrupted_total > 0:
        print(f"❌ Unrecoverable: {corrupted_total:,} files are corrupted, empty, or missing")
        print(f"   These represent ~{corrupted_total*100//total_failed}% of failed extractions")
        print()
    
    readable_but_failed = file_stats['pdf_analysis']['readable'] + file_stats['docx_analysis']['readable']
    if readable_but_failed > 0:
        print(f"⚠️  Unexpected: {readable_but_failed:,} files appear readable but extraction failed")
        print(f"   These may need individual investigation")
        print()
    
    print("=" * 80)
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    analyze_failed_extractions()
