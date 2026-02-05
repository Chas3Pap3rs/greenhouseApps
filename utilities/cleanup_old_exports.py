#!/usr/bin/env python3
"""
Export Cleanup Utility

Cleans up old CSV exports from database-specific folders, keeping only the N most recent.
Helps manage disk space by removing outdated exports.

Usage:
    python cleanup_old_exports.py                 # Interactive mode (dry-run first)
    python cleanup_old_exports.py --keep 5        # Keep 5 most recent exports
    python cleanup_old_exports.py --auto          # Auto-confirm deletion
    python cleanup_old_exports.py --db ai         # Clean only AI database exports
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import shutil

# Color codes for terminal output
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

def get_exports_dir():
    """Get the exports directory path"""
    project_root = Path(__file__).parent.parent
    exports_dir = project_root / "greenhouse_sharepoint_mapper" / "exports"
    return exports_dir

def get_file_age_days(filepath):
    """Get file age in days"""
    mtime = filepath.stat().st_mtime
    age_seconds = datetime.now().timestamp() - mtime
    return age_seconds / 86400  # Convert to days

def format_size(size_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def cleanup_single_files(folder_path, keep_count, dry_run=True):
    """Clean up single CSV files in a folder"""
    if not folder_path.exists():
        return 0, 0
    
    # Find all CSV files (excluding symlinks)
    csv_files = [
        f for f in folder_path.glob("*.csv") 
        if f.is_file() and not f.is_symlink()
    ]
    
    if not csv_files:
        return 0, 0
    
    # Sort by modification time (newest first)
    csv_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    # Files to keep and delete
    files_to_keep = csv_files[:keep_count]
    files_to_delete = csv_files[keep_count:]
    
    if not files_to_delete:
        return 0, 0
    
    # Calculate total size to free
    total_size = sum(f.stat().st_size for f in files_to_delete)
    
    # Delete or report
    deleted_count = 0
    for file in files_to_delete:
        age_days = get_file_age_days(file)
        size = format_size(file.stat().st_size)
        
        if dry_run:
            log(f"Would delete: {file.name} ({size}, {age_days:.0f} days old)", "WARNING")
        else:
            try:
                file.unlink()
                log(f"Deleted: {file.name} ({size}, {age_days:.0f} days old)")
                deleted_count += 1
            except Exception as e:
                log(f"Failed to delete {file.name}: {e}", "ERROR")
    
    return len(files_to_delete), total_size

def cleanup_segmented_folders(folder_path, keep_count, dry_run=True):
    """Clean up segmented export folders"""
    if not folder_path.exists():
        return 0, 0
    
    # Find all timestamped folders
    folders = [
        d for d in folder_path.iterdir() 
        if d.is_dir() and not d.name.startswith('.')
    ]
    
    if not folders:
        return 0, 0
    
    # Sort by modification time (newest first)
    folders.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    
    # Folders to keep and delete
    folders_to_keep = folders[:keep_count]
    folders_to_delete = folders[keep_count:]
    
    if not folders_to_delete:
        return 0, 0
    
    # Calculate total size to free
    total_size = 0
    for folder in folders_to_delete:
        for file in folder.rglob('*'):
            if file.is_file():
                total_size += file.stat().st_size
    
    # Delete or report
    deleted_count = 0
    for folder in folders_to_delete:
        age_days = get_file_age_days(folder)
        
        # Count files in folder
        file_count = sum(1 for _ in folder.rglob('*.csv'))
        
        if dry_run:
            log(f"Would delete folder: {folder.name}/ ({file_count} files, {age_days:.0f} days old)", "WARNING")
        else:
            try:
                shutil.rmtree(folder)
                log(f"Deleted folder: {folder.name}/ ({file_count} files, {age_days:.0f} days old)")
                deleted_count += 1
            except Exception as e:
                log(f"Failed to delete {folder.name}: {e}", "ERROR")
    
    return len(folders_to_delete), total_size

def cleanup_database_exports(db_name, exports_dir, keep_count, dry_run=True):
    """Clean up exports for a specific database"""
    log(f"\n{'='*80}", "HEADER")
    log(f"CLEANING UP: {db_name.upper()} DATABASE EXPORTS", "HEADER")
    log(f"{'='*80}", "HEADER")
    print()
    
    db_path = exports_dir / db_name
    if not db_path.exists():
        log(f"Database folder not found: {db_path}", "WARNING")
        return 0, 0
    
    total_items = 0
    total_size = 0
    
    # Clean up full exports (single files)
    full_path = db_path / "full"
    if full_path.exists():
        log(f"Checking: {db_name}/full/", "STEP")
        count, size = cleanup_single_files(full_path, keep_count, dry_run)
        total_items += count
        total_size += size
        if count > 0:
            log(f"Found {count} old file(s) to remove ({format_size(size)})")
        else:
            log("No old files to remove", "SUCCESS")
        print()
    
    # Clean up segmented exports (folders)
    segmented_path = db_path / "segmented"
    if segmented_path.exists():
        log(f"Checking: {db_name}/segmented/", "STEP")
        count, size = cleanup_segmented_folders(segmented_path, keep_count, dry_run)
        total_items += count
        total_size += size
        if count > 0:
            log(f"Found {count} old folder(s) to remove ({format_size(size)})")
        else:
            log("No old folders to remove", "SUCCESS")
        print()
    
    # Clean up incremental exports (folders)
    incremental_path = db_path / "incremental"
    if incremental_path.exists():
        log(f"Checking: {db_name}/incremental/", "STEP")
        count, size = cleanup_segmented_folders(incremental_path, keep_count, dry_run)
        total_items += count
        total_size += size
        if count > 0:
            log(f"Found {count} old folder(s) to remove ({format_size(size)})")
        else:
            log("No old folders to remove", "SUCCESS")
        print()
    
    return total_items, total_size

def main():
    """Main cleanup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up old CSV exports')
    parser.add_argument('--keep', type=int, default=3,
                       help='Number of recent exports to keep per type (default: 3)')
    parser.add_argument('--db', choices=['ai_database', 'sharepoint_database', 'main_database', 'all'],
                       default='all', help='Which database exports to clean')
    parser.add_argument('--auto', action='store_true',
                       help='Auto-confirm deletion (skip dry-run)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    log("="*80, "HEADER")
    log("EXPORT CLEANUP UTILITY", "HEADER")
    log("="*80, "HEADER")
    print()
    
    # Get exports directory
    exports_dir = get_exports_dir()
    if not exports_dir.exists():
        log(f"Exports directory not found: {exports_dir}", "ERROR")
        sys.exit(1)
    
    log(f"Exports directory: {exports_dir}")
    log(f"Keeping: {args.keep} most recent exports per type")
    print()
    
    # Determine which databases to clean
    if args.db == 'all':
        databases = ['ai_database', 'sharepoint_database', 'main_database']
    else:
        databases = [args.db]
    
    # First pass: dry-run (unless --auto specified)
    if not args.auto and not args.dry_run:
        log("DRY-RUN MODE - No files will be deleted", "WARNING")
        log("="*80, "WARNING")
        print()
        
        total_items = 0
        total_size = 0
        
        for db_name in databases:
            count, size = cleanup_database_exports(db_name, exports_dir, args.keep, dry_run=True)
            total_items += count
            total_size += size
        
        # Summary
        log("="*80, "HEADER")
        log("DRY-RUN SUMMARY", "HEADER")
        log("="*80, "HEADER")
        print()
        log(f"Total items to delete: {total_items}")
        log(f"Total space to free: {format_size(total_size)}")
        print()
        
        if total_items == 0:
            log("No old exports to clean up! ✅", "SUCCESS")
            sys.exit(0)
        
        # Confirm
        response = input(f"{Colors.YELLOW}Proceed with deletion? (yes/no): {Colors.ENDC}").strip().lower()
        if response not in ['yes', 'y']:
            log("Cleanup cancelled by user", "WARNING")
            sys.exit(0)
        
        print()
        log("="*80, "HEADER")
        log("EXECUTING CLEANUP", "HEADER")
        log("="*80, "HEADER")
        print()
    
    # Second pass: actual deletion
    dry_run = args.dry_run
    total_items = 0
    total_size = 0
    
    for db_name in databases:
        count, size = cleanup_database_exports(db_name, exports_dir, args.keep, dry_run=dry_run)
        total_items += count
        total_size += size
    
    # Final summary
    log("="*80, "HEADER")
    log("CLEANUP SUMMARY", "HEADER")
    log("="*80, "HEADER")
    print()
    
    if dry_run:
        log(f"Would delete: {total_items} items")
        log(f"Would free: {format_size(total_size)}")
        log("\nRun without --dry-run to actually delete files", "WARNING")
    else:
        log(f"Deleted: {total_items} items", "SUCCESS")
        log(f"Freed: {format_size(total_size)}", "SUCCESS")
        log("\nCleanup completed successfully! ✅", "SUCCESS")
    
    print()
    log("="*80, "HEADER")
    
    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nCleanup interrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        log(f"\n\nUnexpected error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
