#!/usr/bin/env python3
"""
Master Incremental Update Script
=================================

This script orchestrates incremental updates to the Greenhouse Apps system.
Use this for regular (weekly/monthly) updates to sync new and updated candidates.

WORKFLOW:
1. Pull NEW/UPDATED candidates from Greenhouse API (since last update)
2. Download NEW resumes only
3. Add new resumes to AI_Access folder and generate metadata
4. Map SharePoint links for new resumes
5. Map AI_Access links and metadata for new candidates
6. Sync resume_content for new candidates to Greenhouse API
7. Verify sync status
8. Export incremental CSVs

WHEN TO USE:
- Weekly/monthly regular updates
- After adding new candidates to Greenhouse
- To sync recent changes without full rebuild

ESTIMATED TIME: 30 minutes - 2 hours (depending on number of new candidates)

PREREQUISITES:
- System already initialized with master_full_rebuild.py
- .env file configured with all credentials
- Greenhouse API access
- SharePoint access via Microsoft Graph API
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

def main():
    """Main orchestration function"""
    
    # Get project root directory
    project_root = Path(__file__).parent
    
    log("GREENHOUSE APPS - MASTER INCREMENTAL UPDATE", "HEADER")
    log(f"Project root: {project_root}")
    log(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("This will update the system with new and modified candidates only.")
    
    overall_start = time.time()
    failed_steps = []
    
    # =========================================================================
    # STEP 1: Pull new/updated candidates from Greenhouse API
    # =========================================================================
    step_success = run_script(
        "greenhouse_candidate_dbBuilder/main.py",
        "Step 1: Pull new/updated candidates from Greenhouse API",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 1: Pull new candidates from API")
        log("Cannot continue without candidate data. Exiting.", "ERROR")
        sys.exit(1)
    
    # =========================================================================
    # STEP 2: Download new resumes
    # =========================================================================
    step_success = run_script(
        "greenhouse_resume_downloader/download_resumes.py",
        "Step 2: Download new resumes to local storage and SharePoint",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 2: Download new resumes")
    
    # =========================================================================
    # STEP 3: Update AI_Access folder with new resumes and metadata
    # =========================================================================
    step_success = run_script(
        "greenhouse_sharepoint_mapper/create_ai_access_folder.py",
        "Step 3: Add new resumes to AI_Access folder and generate metadata",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 3: Update AI_Access folder")
    
    # =========================================================================
    # STEP 4: Map SharePoint links for new resumes
    # =========================================================================
    step_success = run_script(
        "greenhouse_sharepoint_mapper/map_sharepoint_links.py",
        "Step 4: Map SharePoint links for new resumes",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 4: Map SharePoint links")
    
    # =========================================================================
    # STEP 5: Map AI_Access links for new candidates
    # =========================================================================
    step_success = run_script(
        "greenhouse_sharepoint_mapper/map_ai_access_links.py",
        "Step 5: Map AI_Access links for new candidates",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 5: Map AI_Access links")
    
    # =========================================================================
    # STEP 6: Map metadata links (individual mode for incremental)
    # =========================================================================
    step_success = run_script(
        "greenhouse_sharepoint_mapper/map_metadata_links.py",
        "Step 6: Map metadata JSON links for new candidates",
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
    # STEP 8: Update resume_content in Greenhouse API (incremental)
    # =========================================================================
    step_success = run_script(
        "greenhouse_resume_content_sync/update_resume_content.py",
        "Step 8: Update resume_content in Greenhouse API (incremental)",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 8: Update resume_content in Greenhouse")
    
    # =========================================================================
    # STEP 9: Verify sync status
    # =========================================================================
    log("Verifying sync status...", "STEP")
    step_success = run_script(
        "utilities/verification/check_ai_database_status.py",
        "Step 9: Verify AI database status and coverage",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 9: Database verification")
    
    # =========================================================================
    # STEP 10: Export incremental CSVs (to database-specific folders)
    # =========================================================================
    log("Exporting incremental CSVs to database-specific folders...", "STEP")
    
    # Export incremental AI Access CSV → exports/ai_database/incremental/
    step_success = run_script(
        "greenhouse_sharepoint_mapper/exports/export_incremental_ai.py",
        "Step 10: Export incremental AI Access CSV → ai_database/incremental/",
        cwd=project_root
    )
    if not step_success:
        failed_steps.append("Step 10: Export incremental CSV")
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    overall_elapsed = time.time() - overall_start
    hours = int(overall_elapsed // 3600)
    minutes = int((overall_elapsed % 3600) // 60)
    seconds = int(overall_elapsed % 60)
    
    log("INCREMENTAL UPDATE COMPLETE", "HEADER")
    
    if failed_steps:
        log(f"Update completed with {len(failed_steps)} failed step(s)", "WARNING")
        log("Failed steps:", "WARNING")
        for step in failed_steps:
            log(f"  - {step}", "ERROR")
        log("\nPlease review the errors above and run the failed steps manually.", "WARNING")
    else:
        log("All steps completed successfully! 🎉", "SUCCESS")
    
    if hours > 0:
        log(f"\nTotal time: {hours}h {minutes}m {seconds}s")
    elif minutes > 0:
        log(f"\nTotal time: {minutes}m {seconds}s")
    else:
        log(f"\nTotal time: {seconds}s")
    
    log(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    log("\nNext steps:", "STEP")
    print("  1. Review verification output above")
    print("  2. Check incremental CSV in:")
    print("     - greenhouse_sharepoint_mapper/exports/ai_database/incremental/")
    print("  3. Upload incremental CSV to Zapier Tables (append mode)")
    print("  4. Run master_verify_integrity.py for detailed verification if needed")
    
    log("\nScheduling recommendation:", "STEP")
    print("  - Run this script weekly to keep data fresh")
    print("  - Run master_full_rebuild.py monthly or when major issues occur")
    
    if failed_steps:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nUpdate interrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        log(f"\n\nUnexpected error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
