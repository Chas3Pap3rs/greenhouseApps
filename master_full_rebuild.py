#!/usr/bin/env python3
"""
Master Full Rebuild Script
===========================

This script orchestrates a complete rebuild of the entire Greenhouse Apps system
from scratch. Use this when you need to rebuild all databases and regenerate all
data from the Greenhouse API.

WORKFLOW:
1. Pull ALL candidates from Greenhouse API → greenhouse_candidates database
2. Download ALL resumes to local storage and SharePoint
3. Create AI_Access folder structure with metadata files
4. Map SharePoint links for resumes → greenhouse_candidates_sp database
5. Map AI_Access links and metadata → greenhouse_candidates_ai database
6. Sync resume_content to Greenhouse API
7. Verify all databases are in sync
8. Export all CSVs (full and segmented)

WHEN TO USE:
- Initial setup of the system
- Complete data refresh needed
- Database corruption or major data issues
- After significant schema changes

ESTIMATED TIME: 4-8 hours (depending on number of candidates and network speed)

PREREQUISITES:
- .env file configured with all credentials
- Sufficient disk space for resumes (~50GB+)
- Greenhouse API access
- SharePoint access via Microsoft Graph API
- PostgreSQL databases created (greenhouse_candidates, greenhouse_candidates_sp, greenhouse_candidates_ai)
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log(message, level="INFO"):
    """Print timestamped log message with color coding"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if level == "HEADER":
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    elif level == "SUCCESS":
        print(f"{Colors.OKGREEN}[{timestamp}] ✅ {message}{Colors.ENDC}")
    elif level == "ERROR":
        print(f"{Colors.FAIL}[{timestamp}] ❌ {message}{Colors.ENDC}")
    elif level == "WARNING":
        print(f"{Colors.WARNING}[{timestamp}] ⚠️  {message}{Colors.ENDC}")
    elif level == "STEP":
        print(f"\n{Colors.OKCYAN}{Colors.BOLD}[{timestamp}] 🔹 {message}{Colors.ENDC}")
    else:
        print(f"[{timestamp}] {message}")

def run_script(script_path, description, cwd=None):
    """Run a Python script and handle errors"""
    log(f"Starting: {description}", "STEP")
    log(f"Running: {script_path}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ["python3", script_path],
            cwd=cwd,
            capture_output=False,
            text=True,
            check=True
        )
        
        elapsed = time.time() - start_time
        log(f"Completed: {description} (took {elapsed:.1f}s)", "SUCCESS")
        return True
        
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        log(f"Failed: {description} (after {elapsed:.1f}s)", "ERROR")
        log(f"Error: {str(e)}", "ERROR")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        log(f"Unexpected error in {description} (after {elapsed:.1f}s)", "ERROR")
        log(f"Error: {str(e)}", "ERROR")
        return False

def confirm_rebuild():
    """Ask user to confirm full rebuild"""
    log("FULL REBUILD CONFIRMATION", "HEADER")
    print(f"{Colors.WARNING}⚠️  WARNING: This will perform a COMPLETE REBUILD of all databases!{Colors.ENDC}\n")
    print("This process will:")
    print("  1. Pull ALL candidates from Greenhouse API")
    print("  2. Download ALL resumes (may take several hours)")
    print("  3. Rebuild all three databases from scratch")
    print("  4. Regenerate all SharePoint links")
    print("  5. Sync all resume_content to Greenhouse")
    print("  6. Export all CSVs")
    print(f"\n{Colors.WARNING}Estimated time: 4-8 hours{Colors.ENDC}")
    print(f"{Colors.WARNING}Requires: Stable internet connection, sufficient disk space{Colors.ENDC}\n")
    
    response = input(f"{Colors.BOLD}Are you sure you want to proceed? (yes/no): {Colors.ENDC}").strip().lower()
    
    if response != 'yes':
        log("Rebuild cancelled by user", "WARNING")
        return False
    
    print()
    response = input(f"{Colors.BOLD}Type 'REBUILD' to confirm: {Colors.ENDC}").strip()
    
    if response != 'REBUILD':
        log("Rebuild cancelled - confirmation failed", "WARNING")
        return False
    
    return True

def main():
    """Main orchestration function"""
    
    # Get project root directory
    project_root = Path(__file__).parent
    
    log("GREENHOUSE APPS - MASTER FULL REBUILD", "HEADER")
    log(f"Project root: {project_root}")
    log(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Confirm rebuild
    if not confirm_rebuild():
        sys.exit(0)
    
    log("Starting full rebuild process...", "SUCCESS")
    
    overall_start = time.time()
    failed_steps = []
    
    # =========================================================================
    # STEP 1: Pull all candidates from Greenhouse API
    # =========================================================================
    step_success = run_script(
        "greenhouse_candidate_dbBuilder/main.py",
        "Step 1: Pull all candidates from Greenhouse API → greenhouse_candidates database",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 1: Pull candidates from API")
    
    # =========================================================================
    # STEP 2: Download all resumes
    # =========================================================================
    step_success = run_script(
        "greenhouse_resume_downloader/download_resumes.py",
        "Step 2: Download all resumes to local storage and SharePoint",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 2: Download resumes")
    
    # =========================================================================
    # STEP 3: Create AI_Access folder structure
    # =========================================================================
    step_success = run_script(
        "greenhouse_sharepoint_mapper/create_ai_access_folder.py",
        "Step 3: Create AI_Access folder with metadata files",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 3: Create AI_Access folder")
    
    # =========================================================================
    # STEP 4: Map SharePoint links for resumes
    # =========================================================================
    step_success = run_script(
        "greenhouse_sharepoint_mapper/map_sharepoint_links.py",
        "Step 4: Map SharePoint links → greenhouse_candidates_sp database",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 4: Map SharePoint links")
    
    # =========================================================================
    # STEP 5: Map AI_Access links
    # =========================================================================
    step_success = run_script(
        "greenhouse_sharepoint_mapper/map_ai_access_links.py",
        "Step 5: Map AI_Access links → greenhouse_candidates_ai database",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 5: Map AI_Access links")
    
    # =========================================================================
    # STEP 6: Map metadata links (batch mode for full rebuild)
    # =========================================================================
    step_success = run_script(
        "greenhouse_sharepoint_mapper/map_metadata_links_batch.py",
        "Step 6: Map metadata JSON links (batch mode)",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 6: Map metadata links")
    
    # =========================================================================
    # STEP 7: Sync resume_content from metadata to database
    # =========================================================================
    step_success = run_script(
        "greenhouse_sharepoint_mapper/sync_resume_content_from_metadata.py",
        "Step 7: Sync resume_content from metadata files to database",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 7: Sync resume_content to database")
    
    # =========================================================================
    # STEP 8: Sync resume_content to Greenhouse API
    # =========================================================================
    step_success = run_script(
        "greenhouse_resume_content_sync/sync_resume_content.py",
        "Step 8: Sync resume_content to Greenhouse API (full sync)",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 8: Sync resume_content to Greenhouse")
    
    # =========================================================================
    # STEP 9: Verify database integrity
    # =========================================================================
    log("Running comprehensive verification...", "STEP")
    step_success = run_script(
        "utilities/verification/comprehensive_database_check.py",
        "Step 9: Verify all databases are in sync",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 9: Database verification")
    
    # =========================================================================
    # STEP 10: Export CSVs (to database-specific folders)
    # =========================================================================
    log("Exporting CSVs to database-specific folders...", "STEP")
    
    # Export full AI Access CSV → exports/ai_database/full/
    step_success = run_script(
        "greenhouse_sharepoint_mapper/exports/export_ai_access_csv_full.py",
        "Step 10a: Export full AI Access CSV → ai_database/full/",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 10a: Export full CSV")
    
    # Export segmented AI Access CSV → exports/ai_database/segmented/
    step_success = run_script(
        "greenhouse_sharepoint_mapper/exports/export_segmented_ai_full.py",
        "Step 10b: Export segmented AI Access CSV → ai_database/segmented/",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 10b: Export segmented CSV")
    
    # Export SharePoint CSV → exports/sharepoint_database/full/
    step_success = run_script(
        "greenhouse_sharepoint_mapper/exports/export_sharepoint_csv.py",
        "Step 10c: Export SharePoint database CSV → sharepoint_database/full/",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 10c: Export SharePoint CSV")
    
    # Export from main database → exports/main_database/segmented/
    step_success = run_script(
        "greenhouse_candidate_dbBuilder/export_segmented.py",
        "Step 10d: Export segmented CSV from main database → main_database/segmented/",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 10d: Export main database CSV")
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    overall_elapsed = time.time() - overall_start
    hours = int(overall_elapsed // 3600)
    minutes = int((overall_elapsed % 3600) // 60)
    
    log("REBUILD COMPLETE", "HEADER")
    
    if failed_steps:
        log(f"Rebuild completed with {len(failed_steps)} failed step(s)", "WARNING")
        log("Failed steps:", "WARNING")
        for step in failed_steps:
            log(f"  - {step}", "ERROR")
        log("\nPlease review the errors above and run the failed steps manually.", "WARNING")
    else:
        log("All steps completed successfully! 🎉", "SUCCESS")
    
    log(f"\nTotal time: {hours}h {minutes}m")
    log(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    log("\nNext steps:", "STEP")
    print("  1. Review verification output above")
    print("  2. Check exported CSVs in database-specific folders:")
    print("     - AI Database: greenhouse_sharepoint_mapper/exports/ai_database/")
    print("     - SharePoint: greenhouse_sharepoint_mapper/exports/sharepoint_database/")
    print("     - Main DB: greenhouse_sharepoint_mapper/exports/main_database/")
    print("  3. Upload CSVs to Zapier Tables or other destinations")
    print("  4. Run master_verify_integrity.py for detailed verification")
    
    if failed_steps:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nRebuild interrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        log(f"\n\nUnexpected error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
