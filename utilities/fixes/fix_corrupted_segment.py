#!/usr/bin/env python3
"""
Fix Corrupted CSV Segment
==========================

This script regenerates a specific corrupted CSV segment from the segmented export.
Use this when a segment has fields that exceed CSV field size limits or other corruption issues.

The issue: Some resume_content fields can be extremely long (>131KB), causing CSV parsing errors.
The fix: Truncate resume_content to a reasonable size (100KB) while preserving all other data.
"""

import os
import sys
import csv
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Increase CSV field size limit
csv.field_size_limit(10 * 1024 * 1024)  # 10MB limit

# Load environment variables
load_dotenv('/Users/chasepoulton/Library/Mobile Documents/com~apple~CloudDocs/Cook Systems/Projects/greenhouseApps/greenhouse_sharepoint_mapper/.env')

def get_segment_range(segment_num, total_segments, total_candidates):
    """Calculate the candidate ID range for a specific segment"""
    candidates_per_segment = total_candidates // total_segments
    start_idx = (segment_num - 1) * candidates_per_segment
    
    if segment_num == total_segments:
        end_idx = total_candidates
    else:
        end_idx = start_idx + candidates_per_segment
    
    return start_idx, end_idx

def truncate_resume_content(content, max_length=100000):
    """Truncate resume content to a reasonable size"""
    if content and len(content) > max_length:
        return content[:max_length] + "\n\n[Content truncated due to length...]"
    return content

def regenerate_segment(segment_num, output_dir):
    """Regenerate a specific segment with proper field size handling"""
    
    print(f"Regenerating segment {segment_num}...")
    
    # Connect to database
    conn = psycopg2.connect(
        host=os.getenv('PGHOST'),
        port=os.getenv('PGPORT', 5432),
        database=os.getenv('AI_PGDATABASE', 'greenhouse_candidates_ai'),
        user=os.getenv('PGUSER'),
        password=os.getenv('PGPASSWORD')
    )
    
    try:
        cursor = conn.cursor()
        
        # Get total candidate count
        cursor.execute("SELECT COUNT(*) FROM gh.candidates")
        total_candidates = cursor.fetchone()[0]
        
        # Determine segment range (assuming 27 segments based on your export)
        total_segments = 27
        start_idx, end_idx = get_segment_range(segment_num, total_segments, total_candidates)
        
        print(f"Total candidates: {total_candidates:,}")
        print(f"Segment range: {start_idx:,} to {end_idx:,}")
        print(f"Candidates in segment: {end_idx - start_idx:,}")
        
        # Query for this segment's candidates
        query = """
            SELECT 
                candidate_id,
                first_name,
                last_name,
                full_name,
                email,
                phone_numbers,
                addresses,
                resume_links,
                metadata_url,
                resume_filenames,
                employment_titles,
                employment_companies,
                degrees,
                jobs_name,
                resume_content,
                created_at,
                updated_at
            FROM gh.candidates
            ORDER BY candidate_id
            OFFSET %s LIMIT %s
        """
        
        cursor.execute(query, (start_idx, end_idx - start_idx))
        
        # Create output filename
        timestamp = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
        output_file = os.path.join(output_dir, f"segment_{segment_num:03d}_of_{total_segments:03d}_full_FIXED.csv")
        
        print(f"Writing to: {output_file}")
        
        # Write CSV with truncated resume_content
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)  # Quote ALL fields for safety
            
            # Write header
            writer.writerow([
                'candidate_id', 'first_name', 'last_name', 'full_name', 'email',
                'phone_numbers', 'addresses', 'resume_url', 'metadata_url',
                'resume_filename', 'employment_titles', 'employment_companies',
                'degrees', 'jobs_name', 'resume_content', 'created_at', 'updated_at'
            ])
            
            # Write data rows
            row_count = 0
            truncated_count = 0
            
            for row in cursor:
                # Truncate resume_content if too long and clean data
                row_list = list(row)
                
                # Clean resume_content (index 14)
                if row_list[14]:
                    original_length = len(row_list[14])
                    # Remove any problematic characters
                    cleaned_content = row_list[14].replace('\x00', '').replace('\r\n', '\n')
                    row_list[14] = truncate_resume_content(cleaned_content)
                    if len(row_list[14]) < original_length:
                        truncated_count += 1
                
                # Convert arrays to strings for CSV
                for i in range(len(row_list)):
                    if row_list[i] is None:
                        row_list[i] = ''
                    elif isinstance(row_list[i], list):
                        row_list[i] = ', '.join(str(x) for x in row_list[i] if x)
                    else:
                        row_list[i] = str(row_list[i])
                
                writer.writerow(row_list)
                row_count += 1
                
                if row_count % 1000 == 0:
                    print(f"  Processed {row_count:,} rows...")
            
            print(f"\n✓ Successfully wrote {row_count:,} rows")
            print(f"✓ Truncated {truncated_count} resume_content fields")
            
            # Get file size
            file_size = os.path.getsize(output_file)
            print(f"✓ File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
            
            if file_size > 50 * 1024 * 1024:
                print(f"⚠ Warning: File exceeds 50MB Zapier limit!")
            else:
                print(f"✓ File is under 50MB Zapier limit")
        
        return output_file
        
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("Usage: python fix_corrupted_segment.py <segment_number> [output_directory]")
        print("\nExample:")
        print("  python fix_corrupted_segment.py 25")
        print("  python fix_corrupted_segment.py 25 /path/to/output")
        sys.exit(1)
    
    segment_num = int(sys.argv[1])
    
    if len(sys.argv) >= 3:
        output_dir = sys.argv[2]
    else:
        # Use the same directory as the corrupted file
        output_dir = "/Users/chasepoulton/Library/Mobile Documents/com~apple~CloudDocs/Cook Systems/Projects/greenhouseApps/greenhouse_sharepoint_mapper/segmented_exports/2026.01.26_17.54.21_full"
    
    print("=" * 80)
    print("FIX CORRUPTED CSV SEGMENT")
    print("=" * 80)
    print(f"\nSegment number: {segment_num}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Regenerate the segment
    output_file = regenerate_segment(segment_num, output_dir)
    
    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)
    print(f"\nFixed file created: {output_file}")
    print("\nNext steps:")
    print("1. Upload the FIXED file to Zapier")
    print("2. Delete the original corrupted file if upload succeeds")
    print("3. Verify data integrity in Zapier Tables")

if __name__ == "__main__":
    main()
