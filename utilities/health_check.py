#!/usr/bin/env python3
"""
System Health Check Utility

Performs comprehensive health checks on the Greenhouse Apps system.
Checks database connectivity, export freshness, disk space, and data integrity.

Usage:
    python health_check.py                    # Full health check
    python health_check.py --quick            # Quick check (skip detailed queries)
    python health_check.py --export-only      # Check only export freshness
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    if level == "HEADER":
        print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    elif level == "SUCCESS":
        print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")
    elif level == "ERROR":
        print(f"{Colors.RED}❌ {message}{Colors.ENDC}")
    elif level == "WARNING":
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")
    elif level == "INFO":
        print(f"{Colors.CYAN}{message}{Colors.ENDC}")
    else:
        print(message)

# Database configurations
DATABASES = {
    'main': {
        'name': 'greenhouse_candidates',
        'description': 'Main Database',
        'env_var': 'PGDATABASE'
    },
    'sharepoint': {
        'name': 'greenhouse_candidates_sp',
        'description': 'SharePoint Database',
        'env_var': 'PGDATABASE'
    },
    'ai': {
        'name': 'greenhouse_candidates_ai',
        'description': 'AI Access Database',
        'env_var': 'AI_PGDATABASE'
    }
}

def check_database_connection(db_name, db_description):
    """Check if database is accessible"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=int(os.getenv('PGPORT', '5432')),
            dbname=db_name,
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD')
        )
        
        # Get candidate count
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM gh.candidates")
            count = cursor.fetchone()[0]
        
        conn.close()
        return True, count, None
    except Exception as e:
        return False, 0, str(e)

def check_export_freshness(exports_dir, max_age_days=7):
    """Check if exports are recent"""
    issues = []
    
    # Check AI database exports
    ai_full = exports_dir / "ai_database" / "full"
    if ai_full.exists():
        csv_files = list(ai_full.glob("*.csv"))
        csv_files = [f for f in csv_files if not f.is_symlink()]
        if csv_files:
            latest = max(csv_files, key=lambda f: f.stat().st_mtime)
            age_days = (datetime.now().timestamp() - latest.stat().st_mtime) / 86400
            if age_days > max_age_days:
                issues.append(f"AI database full exports are {age_days:.0f} days old (> {max_age_days} days)")
        else:
            issues.append("No AI database full exports found")
    else:
        issues.append("AI database full export folder not found")
    
    # Check incremental exports
    ai_incremental = exports_dir / "ai_database" / "incremental"
    if ai_incremental.exists():
        folders = [d for d in ai_incremental.iterdir() if d.is_dir() and not d.name.startswith('.')]
        if folders:
            latest = max(folders, key=lambda d: d.stat().st_mtime)
            age_days = (datetime.now().timestamp() - latest.stat().st_mtime) / 86400
            if age_days > max_age_days:
                issues.append(f"AI database incremental exports are {age_days:.0f} days old (> {max_age_days} days)")
        else:
            issues.append("No AI database incremental exports found")
    
    # Check SharePoint exports
    sp_full = exports_dir / "sharepoint_database" / "full"
    if sp_full.exists():
        csv_files = list(sp_full.glob("*.csv"))
        csv_files = [f for f in csv_files if not f.is_symlink()]
        if csv_files:
            latest = max(csv_files, key=lambda f: f.stat().st_mtime)
            age_days = (datetime.now().timestamp() - latest.stat().st_mtime) / 86400
            if age_days > max_age_days:
                issues.append(f"SharePoint exports are {age_days:.0f} days old (> {max_age_days} days)")
        else:
            issues.append("No SharePoint exports found")
    
    return issues

def check_disk_space(min_free_gb=50):
    """Check available disk space"""
    import shutil
    
    project_root = Path(__file__).parent.parent
    stat = shutil.disk_usage(project_root)
    
    free_gb = stat.free / (1024**3)
    total_gb = stat.total / (1024**3)
    used_gb = stat.used / (1024**3)
    percent_used = (stat.used / stat.total) * 100
    
    return {
        'free_gb': free_gb,
        'total_gb': total_gb,
        'used_gb': used_gb,
        'percent_used': percent_used,
        'sufficient': free_gb >= min_free_gb
    }

def check_environment_variables():
    """Check if required environment variables are set"""
    required_vars = ['PGHOST', 'PGPORT', 'PGUSER', 'PGPASSWORD', 'PGDATABASE', 'AI_PGDATABASE']
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    return missing

def main():
    """Main health check function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='System health check')
    parser.add_argument('--quick', action='store_true',
                       help='Quick check (skip detailed queries)')
    parser.add_argument('--export-only', action='store_true',
                       help='Check only export freshness')
    
    args = parser.parse_args()
    
    log("="*80, "HEADER")
    log("GREENHOUSE APPS - SYSTEM HEALTH CHECK", "HEADER")
    log("="*80, "HEADER")
    print()
    
    issues_found = []
    
    # Check 1: Environment Variables
    if not args.export_only:
        log("1. Checking environment variables...", "INFO")
        missing_vars = check_environment_variables()
        if missing_vars:
            log(f"Missing environment variables: {', '.join(missing_vars)}", "ERROR")
            issues_found.append("Missing environment variables")
        else:
            log("All required environment variables are set", "SUCCESS")
        print()
    
    # Check 2: Database Connectivity
    if not args.export_only:
        log("2. Checking database connectivity...", "INFO")
        for db_key, db_info in DATABASES.items():
            db_name = db_info['name']
            db_desc = db_info['description']
            
            connected, count, error = check_database_connection(db_name, db_desc)
            
            if connected:
                log(f"{db_desc}: Connected ✓ ({count:,} candidates)", "SUCCESS")
            else:
                log(f"{db_desc}: Connection failed - {error}", "ERROR")
                issues_found.append(f"{db_desc} connection failed")
        print()
    
    # Check 3: Export Freshness
    log("3. Checking export freshness...", "INFO")
    project_root = Path(__file__).parent.parent
    exports_dir = project_root / "greenhouse_sharepoint_mapper" / "exports"
    
    if exports_dir.exists():
        export_issues = check_export_freshness(exports_dir, max_age_days=7)
        if export_issues:
            for issue in export_issues:
                log(issue, "WARNING")
            issues_found.extend(export_issues)
        else:
            log("All exports are fresh (< 7 days old)", "SUCCESS")
    else:
        log(f"Exports directory not found: {exports_dir}", "ERROR")
        issues_found.append("Exports directory not found")
    print()
    
    # Check 4: Disk Space
    if not args.export_only:
        log("4. Checking disk space...", "INFO")
        disk_info = check_disk_space(min_free_gb=50)
        
        log(f"Total: {disk_info['total_gb']:.1f} GB")
        log(f"Used: {disk_info['used_gb']:.1f} GB ({disk_info['percent_used']:.1f}%)")
        log(f"Free: {disk_info['free_gb']:.1f} GB")
        
        if disk_info['sufficient']:
            log("Sufficient disk space available", "SUCCESS")
        else:
            log(f"Low disk space! Only {disk_info['free_gb']:.1f} GB free (need 50 GB)", "WARNING")
            issues_found.append("Low disk space")
        print()
    
    # Check 5: Symlinks
    if not args.export_only:
        log("5. Checking export symlinks...", "INFO")
        symlinks = [
            exports_dir / "latest_ai_export.csv",
            exports_dir / "latest_export.csv",
            exports_dir / "latest_lightweight_export.csv"
        ]
        
        symlink_ok = True
        for symlink in symlinks:
            if symlink.exists() and symlink.is_symlink():
                target = symlink.resolve()
                if target.exists():
                    log(f"{symlink.name} → {target.name}", "SUCCESS")
                else:
                    log(f"{symlink.name} → broken link", "WARNING")
                    symlink_ok = False
            else:
                log(f"{symlink.name} not found", "WARNING")
                symlink_ok = False
        
        if not symlink_ok:
            issues_found.append("Some symlinks are broken or missing")
        print()
    
    # Summary
    log("="*80, "HEADER")
    log("HEALTH CHECK SUMMARY", "HEADER")
    log("="*80, "HEADER")
    print()
    
    if issues_found:
        log(f"Found {len(issues_found)} issue(s):", "WARNING")
        for issue in issues_found:
            log(f"  • {issue}", "WARNING")
        print()
        log("Recommendation: Review issues above and run maintenance scripts", "WARNING")
        print()
        log("Suggested actions:", "INFO")
        print("  - Run master_incremental_update.py to refresh exports")
        print("  - Run cleanup_old_exports.py to free disk space")
        print("  - Check database logs for connection issues")
    else:
        log("All checks passed! System is healthy ✅", "SUCCESS")
        print()
        log("System Status: EXCELLENT", "SUCCESS")
    
    print()
    log("="*80, "HEADER")
    
    sys.exit(0 if not issues_found else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nHealth check interrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        log(f"\n\nUnexpected error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
