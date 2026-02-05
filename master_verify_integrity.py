#!/usr/bin/env python3
"""
Master Verify Integrity Script
===============================

This script runs comprehensive verification checks across all databases and
generates detailed reports on data integrity, coverage, and sync status.

CHECKS PERFORMED:
1. Database schema verification
2. Data coverage statistics (all three databases)
3. Null field analysis
4. Sync status between databases
5. Resume_content coverage in Greenhouse API
6. SharePoint link validation
7. AI_Access metadata coverage
8. Cross-database consistency checks

WHEN TO USE:
- After running master_full_rebuild.py
- After running master_incremental_update.py
- Before exporting CSVs to production
- When investigating data quality issues
- Monthly data quality audits

ESTIMATED TIME: 5-10 minutes

OUTPUT:
- Comprehensive report printed to console
- Can be redirected to file for record-keeping
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
        print(f"\n{Colors.OKCYAN}{Colors.BOLD}[{timestamp}] 🔍 {message}{Colors.ENDC}")
    else:
        print(f"[{timestamp}] {message}")

def run_verification(script_path, description, cwd=None):
    """Run a verification script and capture output"""
    log(f"{description}", "STEP")
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
        log(f"Verification script failed: {description} (after {elapsed:.1f}s)", "ERROR")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        log(f"Unexpected error in {description} (after {elapsed:.1f}s)", "ERROR")
        log(f"Error: {str(e)}", "ERROR")
        return False

def print_section_header(title):
    """Print a section header"""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{'─'*80}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{Colors.BOLD}{'─'*80}{Colors.ENDC}\n")

def main():
    """Main verification function"""
    
    # Get project root directory
    project_root = Path(__file__).parent
    
    log("GREENHOUSE APPS - MASTER INTEGRITY VERIFICATION", "HEADER")
    log(f"Project root: {project_root}")
    log(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("Running comprehensive verification checks across all databases...")
    
    overall_start = time.time()
    failed_checks = []
    
    # =========================================================================
    # SECTION 1: Database Schema Verification
    # =========================================================================
    print_section_header("SECTION 1: DATABASE SCHEMA VERIFICATION")
    
    step_success = run_verification(
        "utilities/verification/check_ai_schema.py",
        "Check 1.1: Verify AI database schema",
        cwd=project_root
    )
    if not step_success:
        failed_checks.append("AI database schema verification")
    
    # =========================================================================
    # SECTION 2: Comprehensive Database Status
    # =========================================================================
    print_section_header("SECTION 2: COMPREHENSIVE DATABASE STATUS")
    
    step_success = run_verification(
        "utilities/verification/comprehensive_database_check.py",
        "Check 2.1: Comprehensive check across all three databases",
        cwd=project_root
    )
    if not step_success:
        failed_checks.append("Comprehensive database check")
    
    # =========================================================================
    # SECTION 3: AI Database Detailed Status
    # =========================================================================
    print_section_header("SECTION 3: AI DATABASE DETAILED STATUS")
    
    step_success = run_verification(
        "utilities/verification/check_ai_database_status.py",
        "Check 3.1: AI database coverage and statistics",
        cwd=project_root
    )
    if not step_success:
        failed_checks.append("AI database status check")
    
    # =========================================================================
    # SECTION 4: Null Field Analysis
    # =========================================================================
    print_section_header("SECTION 4: NULL FIELD ANALYSIS")
    
    step_success = run_verification(
        "utilities/verification/check_ai_null_fields.py",
        "Check 4.1: Analyze null fields in AI database",
        cwd=project_root
    )
    if not step_success:
        failed_checks.append("Null field analysis")
    
    # =========================================================================
    # SECTION 5: Main Database Statistics
    # =========================================================================
    print_section_header("SECTION 5: MAIN DATABASE STATISTICS")
    
    step_success = run_verification(
        "utilities/verification/check_greenhouse_stats.py",
        "Check 5.1: Main database (greenhouse_candidates) statistics",
        cwd=project_root
    )
    if not step_success:
        failed_checks.append("Main database statistics")
    
    # =========================================================================
    # SECTION 6: Database Status Scripts (from each project)
    # =========================================================================
    print_section_header("SECTION 6: PROJECT-SPECIFIC STATUS CHECKS")
    
    step_success = run_verification(
        "greenhouse_candidate_dbBuilder/status.py",
        "Check 6.1: Database builder status",
        cwd=project_root
    )
    if not step_success:
        failed_checks.append("Database builder status")
    
    step_success = run_verification(
        "greenhouse_resume_downloader/status.py",
        "Check 6.2: Resume downloader status",
        cwd=project_root
    )
    if not step_success:
        failed_checks.append("Resume downloader status")
    
    step_success = run_verification(
        "greenhouse_sharepoint_mapper/status.py",
        "Check 6.3: SharePoint mapper status",
        cwd=project_root
    )
    if not step_success:
        failed_checks.append("SharePoint mapper status")
    
    # =========================================================================
    # SECTION 7: Resume Content Sync Verification
    # =========================================================================
    print_section_header("SECTION 7: RESUME CONTENT SYNC VERIFICATION")
    
    step_success = run_verification(
        "utilities/verification/check_completion.py",
        "Check 7.1: Resume content sync completion status",
        cwd=project_root
    )
    if not step_success:
        failed_checks.append("Resume content sync completion")
    
    step_success = run_verification(
        "utilities/verification/verify_final_count.py",
        "Check 7.2: Verify final resume content count",
        cwd=project_root
    )
    if not step_success:
        failed_checks.append("Resume content count verification")
    
    step_success = run_verification(
        "utilities/verification/final_summary.py",
        "Check 7.3: Generate final summary report",
        cwd=project_root
    )
    if not step_success:
        failed_checks.append("Final summary report")
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    overall_elapsed = time.time() - overall_start
    minutes = int(overall_elapsed // 60)
    seconds = int(overall_elapsed % 60)
    
    log("VERIFICATION COMPLETE", "HEADER")
    
    if failed_checks:
        log(f"Verification completed with {len(failed_checks)} failed check(s)", "WARNING")
        log("Failed checks:", "WARNING")
        for check in failed_checks:
            log(f"  - {check}", "ERROR")
        log("\nSome verification scripts may have failed. Review the output above.", "WARNING")
        log("This could indicate:", "WARNING")
        print("  - Missing data in databases")
        print("  - Sync issues between databases")
        print("  - Schema mismatches")
        print("  - Script errors (check if verification scripts exist)")
    else:
        log("All verification checks completed successfully! 🎉", "SUCCESS")
        log("\nYour Greenhouse Apps system appears to be in good health.", "SUCCESS")
    
    log(f"\nTotal verification time: {minutes}m {seconds}s")
    log(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    log("\nRecommendations:", "STEP")
    print("  1. Review all coverage percentages above")
    print("  2. Investigate any null fields or missing data")
    print("  3. If coverage is low (<90%), consider running master_full_rebuild.py")
    print("  4. If only minor gaps, run master_incremental_update.py")
    print("  5. Save this output for record-keeping:")
    print(f"     python3 master_verify_integrity.py > verification_report_{datetime.now().strftime('%Y%m%d')}.txt")
    
    log("\nData Quality Guidelines:", "STEP")
    print("  ✅ Excellent: >95% coverage on all key fields")
    print("  ✅ Good: >90% coverage on all key fields")
    print("  ⚠️  Fair: >80% coverage (consider incremental update)")
    print("  ❌ Poor: <80% coverage (consider full rebuild)")
    
    if failed_checks:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nVerification interrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        log(f"\n\nUnexpected error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
