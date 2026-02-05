# Utilities Folder

This folder contains diagnostic, verification, analysis, and maintenance scripts for the Greenhouse Apps system.

## Folder Structure

### 📊 investigation/
Scripts for investigating database issues and analyzing data structure.

**Scripts:**
- `investigate_null_fields.py` - Investigates null fields across databases
- `analyze_database_structure.py` - Analyzes database schema and structure

**When to use:** When you need to understand data gaps or database structure issues.

---

### ✅ verification/
Scripts for checking status, coverage, and data integrity across all databases.

**Scripts:**
- `check_ai_database_status.py` - Checks AI database status and coverage
- `check_ai_null_fields.py` - Checks for null fields in AI database
- `check_ai_schema.py` - Verifies AI database schema
- `check_greenhouse_stats.py` - Gets statistics from Greenhouse database
- `comprehensive_database_check.py` - Comprehensive check across all databases
- `check_completion.py` - Checks sync completion status (from resume_content_sync)
- `verify_final_count.py` - Verifies final count after sync
- `final_summary.py` - Generates final summary report
- `check_mapping_status.py` - Checks SharePoint mapping status
- `check_sync_status.py` - Checks sync status across databases

**When to use:** 
- Before/after major updates to verify data integrity
- To check coverage percentages
- To verify sync completion

---

### 📈 analysis/
Scripts for analyzing specific data issues and generating reports.

**Scripts:**
- `analyze_failed_extractions.py` - Analyzes failed text extractions (file types, corruption, OCR candidates)

**When to use:** When you need detailed analysis of data quality issues.

---

### 🔧 fixes/
One-time fix scripts for addressing specific data issues. These are archived here after use.

**Scripts:**
- `fix_all_databases.py` - One-time fix for all databases
- `comprehensive_fix.py` - Comprehensive fix for metadata URLs and resume_content (2026-01-26)
- `fix_ai_database_fields.py` - Fixes AI database field issues
- `fix_sp_database_fields.py` - Fixes SP database field issues
- `fix_null_resume_links.py` - Fixes null resume links
- `fix_recent_aws_links.py` - Fixes AWS links to SharePoint
- `backfill_ai_access.py` - Backfills missing AI_Access entries

**When to use:** Reference these for understanding past fixes. Create new fix scripts here for one-time data corrections.

**⚠️ Important:** These scripts are typically run once to fix specific issues. Always verify the issue still exists before running.

---

### 🧪 testing/
Scripts for testing API connections and functionality.

**Scripts:**
- `test_api.py` - Tests Greenhouse API connection

**When to use:** When setting up new environments or troubleshooting API issues.

---

## Usage Guidelines

### Before Running Any Script:
1. Ensure your `.env` file is properly configured
2. Check which database the script targets
3. Review the script's purpose in this README
4. Consider running verification scripts first to understand current state

### After Major Updates:
Run verification scripts in this order:
1. `comprehensive_database_check.py` - Overall status
2. `check_ai_database_status.py` - AI database specifics
3. `check_sync_status.py` - Cross-database sync status

### For Troubleshooting:
1. Start with investigation scripts to understand the issue
2. Use verification scripts to confirm the scope
3. Use analysis scripts for detailed insights
4. Create or use fix scripts only when necessary
5. Re-run verification scripts to confirm fixes

---

## Adding New Scripts

When adding new utility scripts:
- **investigation/** - For exploring and understanding data issues
- **verification/** - For checking status and coverage (should be safe to run anytime)
- **analysis/** - For detailed reporting and insights
- **fixes/** - For one-time data corrections (document the issue and date)
- **testing/** - For API and functionality tests

Always include:
- Clear docstring explaining purpose
- Usage instructions in comments
- Safe error handling
- Logging output for tracking progress
