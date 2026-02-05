#!/usr/bin/env python3
"""
Migrate Exports to New Database-Specific Structure
===================================================

This script reorganizes existing CSV exports into database-specific subfolders
for better organization and clarity.

NEW STRUCTURE:
greenhouse_sharepoint_mapper/exports/
├── ai_database/           # greenhouse_candidates_ai
│   ├── full/              # Full exports with/without resume_content
│   ├── segmented/         # Segmented exports (in timestamped folders)
│   └── incremental/       # Incremental exports
├── sharepoint_database/   # greenhouse_candidates_sp
│   └── full/              # Full SharePoint exports
└── main_database/         # greenhouse_candidates (from dbBuilder)
    └── segmented/         # Segmented exports from main DB

MIGRATION RULES:
- Files with 'gh_aiCandidates' → ai_database/full/
- Files with 'gh_spCandidates' → sharepoint_database/full/
- Files with 'gh_candidates_lightweight' → ai_database/full/
- Segmented export folders → appropriate database/segmented/
- Incremental exports → ai_database/incremental/
- Symlinks updated to point to new locations
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(message, level="INFO"):
    """Print colored log message"""
    if level == "SUCCESS":
        print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")
    elif level == "ERROR":
        print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")
    elif level == "WARNING":
        print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")
    elif level == "HEADER":
        print(f"\n{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    else:
        print(f"  {message}")

def migrate_exports(exports_dir, dry_run=False):
    """Migrate exports to new structure"""
    
    exports_path = Path(exports_dir)
    
    # Track statistics
    stats = {
        'ai_full': 0,
        'ai_segmented': 0,
        'ai_incremental': 0,
        'sp_full': 0,
        'main_segmented': 0,
        'symlinks': 0,
        'skipped': 0
    }
    
    log("MIGRATION PLAN", "HEADER")
    
    # Get all items in exports directory
    items = list(exports_path.iterdir())
    
    for item in items:
        # Skip the new database folders themselves
        if item.name in ['ai_database', 'sharepoint_database', 'main_database', '.gitkeep', 'README.md']:
            continue
        
        # Handle symlinks
        if item.is_symlink():
            log(f"Symlink: {item.name} (will update after migration)", "WARNING")
            stats['symlinks'] += 1
            continue
        
        # Handle CSV files
        if item.is_file() and item.suffix == '.csv':
            # Determine destination based on filename
            if 'gh_aiCandidates' in item.name:
                dest_dir = exports_path / 'ai_database' / 'full'
                stats['ai_full'] += 1
                category = "AI Database (Full)"
            elif 'gh_spCandidates' in item.name:
                dest_dir = exports_path / 'sharepoint_database' / 'full'
                stats['sp_full'] += 1
                category = "SharePoint Database (Full)"
            elif 'gh_candidates_lightweight' in item.name:
                dest_dir = exports_path / 'ai_database' / 'full'
                stats['ai_full'] += 1
                category = "AI Database (Lightweight)"
            elif 'incremental' in item.name.lower():
                dest_dir = exports_path / 'ai_database' / 'incremental'
                stats['ai_incremental'] += 1
                category = "AI Database (Incremental)"
            else:
                log(f"Unknown file type: {item.name}", "WARNING")
                stats['skipped'] += 1
                continue
            
            dest_file = dest_dir / item.name
            log(f"{item.name} → {category}")
            
            if not dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item), str(dest_file))
        
        # Handle segmented export directories
        elif item.is_dir():
            # Check if it's a segmented export folder (contains segment files)
            segment_files = list(item.glob('segment_*.csv'))
            
            if segment_files:
                # Determine which database based on folder name or contents
                if 'full' in item.name.lower():
                    dest_dir = exports_path / 'ai_database' / 'segmented' / item.name
                    stats['ai_segmented'] += 1
                    category = "AI Database (Segmented)"
                else:
                    # Check first file to determine database
                    first_file = segment_files[0].name
                    if 'ai' in first_file.lower():
                        dest_dir = exports_path / 'ai_database' / 'segmented' / item.name
                        stats['ai_segmented'] += 1
                        category = "AI Database (Segmented)"
                    else:
                        dest_dir = exports_path / 'main_database' / 'segmented' / item.name
                        stats['main_segmented'] += 1
                        category = "Main Database (Segmented)"
                
                log(f"{item.name}/ ({len(segment_files)} segments) → {category}")
                
                if not dry_run:
                    dest_dir.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(item), str(dest_dir))
            else:
                log(f"Empty or non-export directory: {item.name}", "WARNING")
                stats['skipped'] += 1
    
    # Update symlinks
    log("\nUPDATING SYMLINKS", "HEADER")
    
    symlinks_to_update = [
        ('latest_ai_export.csv', 'ai_database/full'),
        ('latest_export.csv', 'sharepoint_database/full'),
        ('latest_lightweight_export.csv', 'ai_database/full')
    ]
    
    for symlink_name, target_dir in symlinks_to_update:
        symlink_path = exports_path / symlink_name
        
        if symlink_path.exists() or symlink_path.is_symlink():
            if not dry_run:
                # Get the target filename
                if symlink_path.is_symlink():
                    target_name = os.path.basename(os.readlink(symlink_path))
                    symlink_path.unlink()
                    
                    # Find the file in new location
                    new_target = exports_path / target_dir / target_name
                    if new_target.exists():
                        # Create relative symlink
                        os.symlink(f"{target_dir}/{target_name}", str(symlink_path))
                        log(f"Updated: {symlink_name} → {target_dir}/{target_name}", "SUCCESS")
                    else:
                        log(f"Target not found: {target_name}", "WARNING")
            else:
                log(f"Will update: {symlink_name}")
    
    # Print summary
    log("\nMIGRATION SUMMARY", "HEADER")
    log(f"AI Database (Full): {stats['ai_full']} files")
    log(f"AI Database (Segmented): {stats['ai_segmented']} folders")
    log(f"AI Database (Incremental): {stats['ai_incremental']} files")
    log(f"SharePoint Database (Full): {stats['sp_full']} files")
    log(f"Main Database (Segmented): {stats['main_segmented']} folders")
    log(f"Symlinks: {stats['symlinks']} to update")
    log(f"Skipped: {stats['skipped']} items")
    
    total_moved = sum([stats['ai_full'], stats['ai_segmented'], stats['ai_incremental'], 
                       stats['sp_full'], stats['main_segmented']])
    
    if dry_run:
        log(f"\nDRY RUN: Would migrate {total_moved} items", "WARNING")
        log("Run with --execute to perform actual migration", "WARNING")
    else:
        log(f"\n✓ Successfully migrated {total_moved} items", "SUCCESS")
    
    return stats

def create_gitkeep_files(exports_dir):
    """Create .gitkeep files in empty directories"""
    exports_path = Path(exports_dir)
    
    dirs_to_keep = [
        'ai_database/full',
        'ai_database/segmented',
        'ai_database/incremental',
        'sharepoint_database/full',
        'main_database/segmented'
    ]
    
    for dir_path in dirs_to_keep:
        full_path = exports_path / dir_path
        gitkeep = full_path / '.gitkeep'
        if not gitkeep.exists():
            gitkeep.touch()
            log(f"Created .gitkeep in {dir_path}", "SUCCESS")

def migrate_segmented_exports(segmented_dir, exports_dir, dry_run=False):
    """Migrate segmented exports to new structure"""
    
    segmented_path = Path(segmented_dir)
    exports_path = Path(exports_dir)
    
    if not segmented_path.exists():
        return 0
    
    log("\nMIGRATING SEGMENTED EXPORTS", "HEADER")
    
    moved_count = 0
    
    for folder in segmented_path.iterdir():
        if not folder.is_dir():
            continue
        
        # Determine destination based on folder name
        if 'incremental' in folder.name.lower():
            dest_dir = exports_path / 'ai_database' / 'incremental' / folder.name
            category = "AI Database (Incremental)"
        elif 'full' in folder.name.lower():
            dest_dir = exports_path / 'ai_database' / 'segmented' / folder.name
            category = "AI Database (Segmented)"
        else:
            # Check if it contains segment files to determine type
            segment_files = list(folder.glob('segment_*.csv'))
            if segment_files:
                dest_dir = exports_path / 'ai_database' / 'segmented' / folder.name
                category = "AI Database (Segmented)"
            else:
                log(f"Skipping unknown folder: {folder.name}", "WARNING")
                continue
        
        segment_count = len(list(folder.glob('segment_*.csv')))
        log(f"{folder.name}/ ({segment_count} segments) → {category}")
        
        if not dry_run:
            dest_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(folder), str(dest_dir))
        
        moved_count += 1
    
    return moved_count

def main():
    """Main function"""
    import sys
    
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}MIGRATE EXPORTS TO NEW DATABASE-SPECIFIC STRUCTURE{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    # Get exports directory
    base_dir = "/Users/chasepoulton/Library/Mobile Documents/com~apple~CloudDocs/Cook Systems/Projects/greenhouseApps/greenhouse_sharepoint_mapper"
    exports_dir = f"{base_dir}/exports"
    segmented_dir = f"{base_dir}/segmented_exports"
    
    # Check if --execute flag is provided
    dry_run = '--execute' not in sys.argv
    
    if dry_run:
        log("Running in DRY RUN mode (no changes will be made)", "WARNING")
        log("Add --execute flag to perform actual migration\n", "WARNING")
    else:
        log("Running in EXECUTE mode (files will be moved)", "WARNING")
        response = input(f"\n{Colors.BOLD}Are you sure you want to migrate all exports? (yes/no): {Colors.ENDC}").strip().lower()
        if response != 'yes':
            log("Migration cancelled", "WARNING")
            sys.exit(0)
        print()
    
    # Run migration for main exports
    stats = migrate_exports(exports_dir, dry_run=dry_run)
    
    # Run migration for segmented exports
    segmented_count = migrate_segmented_exports(segmented_dir, exports_dir, dry_run=dry_run)
    
    if segmented_count > 0:
        log(f"\nMigrated {segmented_count} segmented export folders", "SUCCESS")
    
    # Create .gitkeep files
    if not dry_run:
        log("\nCREATING .GITKEEP FILES", "HEADER")
        create_gitkeep_files(exports_dir)
    
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}MIGRATION COMPLETE{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    if not dry_run:
        log("Next steps:", "HEADER")
        print("1. Verify exports are in correct locations")
        print("2. Update export scripts to use new folder structure")
        print("3. Test exports to ensure they work correctly")
        print("4. Update documentation with new structure")

if __name__ == "__main__":
    main()
