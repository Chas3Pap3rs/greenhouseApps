#!/usr/bin/env python3
"""
Database Backup Utility

Creates backups of all three PostgreSQL databases before major operations.
Recommended to run before master_full_rebuild.py or any destructive operations.

Usage:
    python backup_databases.py                    # Backup all databases
    python backup_databases.py --db ai            # Backup only AI database
    python backup_databases.py --db sharepoint    # Backup only SharePoint database
    python backup_databases.py --db main          # Backup only main database
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
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

# Database configurations
DATABASES = {
    'main': {
        'name': 'greenhouse_candidates',
        'description': 'Main database (from dbBuilder)',
        'env_var': 'PGDATABASE'
    },
    'sharepoint': {
        'name': 'greenhouse_candidates_sp',
        'description': 'SharePoint database',
        'env_var': 'PGDATABASE'
    },
    'ai': {
        'name': 'greenhouse_candidates_ai',
        'description': 'AI Access database',
        'env_var': 'AI_PGDATABASE'
    }
}

def get_backup_dir():
    """Get or create backup directory"""
    # Create backups directory in project root
    project_root = Path(__file__).parent.parent
    backup_dir = project_root / "backups" / "databases"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir

def get_db_connection_params():
    """Get database connection parameters from environment"""
    return {
        'host': os.getenv('PGHOST', 'localhost'),
        'port': os.getenv('PGPORT', '5432'),
        'user': os.getenv('PGUSER'),
        'password': os.getenv('PGPASSWORD')
    }

def backup_database(db_key, db_info, backup_dir, connection_params):
    """Backup a single database using pg_dump"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{db_info['name']}_{timestamp}.sql"
    backup_path = backup_dir / backup_filename
    
    log(f"Backing up {db_info['description']}...", "STEP")
    log(f"Database: {db_info['name']}")
    log(f"Output: {backup_path}")
    
    # Build pg_dump command
    cmd = [
        'pg_dump',
        '-h', connection_params['host'],
        '-p', connection_params['port'],
        '-U', connection_params['user'],
        '-d', db_info['name'],
        '-f', str(backup_path),
        '--verbose',
        '--no-owner',
        '--no-acl'
    ]
    
    # Set password in environment
    env = os.environ.copy()
    env['PGPASSWORD'] = connection_params['password']
    
    try:
        # Run pg_dump
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check file was created and get size
        if backup_path.exists():
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            log(f"Backup completed: {backup_filename} ({size_mb:.1f} MB)", "SUCCESS")
            return True, backup_path, size_mb
        else:
            log(f"Backup file not created: {backup_path}", "ERROR")
            return False, None, 0
            
    except subprocess.CalledProcessError as e:
        log(f"Backup failed: {e}", "ERROR")
        if e.stderr:
            log(f"Error details: {e.stderr}", "ERROR")
        return False, None, 0
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        return False, None, 0

def cleanup_old_backups(backup_dir, keep_count=5):
    """Keep only the N most recent backups for each database"""
    log(f"\nCleaning up old backups (keeping {keep_count} most recent per database)...", "STEP")
    
    for db_key, db_info in DATABASES.items():
        db_name = db_info['name']
        
        # Find all backups for this database
        backups = sorted(
            backup_dir.glob(f"{db_name}_*.sql"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Delete old backups
        deleted_count = 0
        for old_backup in backups[keep_count:]:
            try:
                old_backup.unlink()
                deleted_count += 1
                log(f"Deleted old backup: {old_backup.name}")
            except Exception as e:
                log(f"Failed to delete {old_backup.name}: {e}", "WARNING")
        
        if deleted_count > 0:
            log(f"Cleaned up {deleted_count} old backup(s) for {db_name}", "SUCCESS")

def restore_instructions(backup_path):
    """Print instructions for restoring from backup"""
    log("\n" + "="*80, "HEADER")
    log("RESTORE INSTRUCTIONS", "HEADER")
    log("="*80, "HEADER")
    print(f"\nTo restore from this backup, run:\n")
    print(f"psql -h $PGHOST -p $PGPORT -U $PGUSER -d <database_name> -f {backup_path}\n")
    print("Or use the restore_database.py utility (if available)\n")

def main():
    """Main backup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backup Greenhouse databases')
    parser.add_argument('--db', choices=['main', 'sharepoint', 'ai', 'all'], 
                       default='all', help='Which database to backup')
    parser.add_argument('--keep', type=int, default=5, 
                       help='Number of recent backups to keep (default: 5)')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Skip cleanup of old backups')
    
    args = parser.parse_args()
    
    log("="*80, "HEADER")
    log("DATABASE BACKUP UTILITY", "HEADER")
    log("="*80, "HEADER")
    print()
    
    # Get backup directory
    backup_dir = get_backup_dir()
    log(f"Backup directory: {backup_dir}")
    print()
    
    # Get connection parameters
    connection_params = get_db_connection_params()
    
    if not connection_params['user'] or not connection_params['password']:
        log("Database credentials not found in environment variables!", "ERROR")
        log("Please ensure .env file is configured with PGUSER and PGPASSWORD", "ERROR")
        sys.exit(1)
    
    # Determine which databases to backup
    if args.db == 'all':
        databases_to_backup = DATABASES.keys()
    else:
        databases_to_backup = [args.db]
    
    # Backup each database
    results = []
    total_size = 0
    
    for db_key in databases_to_backup:
        db_info = DATABASES[db_key]
        success, backup_path, size_mb = backup_database(
            db_key, db_info, backup_dir, connection_params
        )
        results.append((db_key, success, backup_path, size_mb))
        if success:
            total_size += size_mb
        print()
    
    # Cleanup old backups
    if not args.no_cleanup:
        cleanup_old_backups(backup_dir, args.keep)
    
    # Summary
    log("="*80, "HEADER")
    log("BACKUP SUMMARY", "HEADER")
    log("="*80, "HEADER")
    print()
    
    successful = sum(1 for _, success, _, _ in results if success)
    failed = len(results) - successful
    
    log(f"Total databases backed up: {successful}/{len(results)}")
    log(f"Total backup size: {total_size:.1f} MB")
    log(f"Backup location: {backup_dir}")
    
    if failed > 0:
        log(f"\n{failed} backup(s) failed!", "WARNING")
        for db_key, success, _, _ in results:
            if not success:
                log(f"  - {DATABASES[db_key]['description']}", "ERROR")
    else:
        log("\nAll backups completed successfully! ✅", "SUCCESS")
    
    # Show restore instructions for first successful backup
    for db_key, success, backup_path, _ in results:
        if success and backup_path:
            restore_instructions(backup_path)
            break
    
    print()
    log("="*80, "HEADER")
    
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nBackup interrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        log(f"\n\nUnexpected error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
