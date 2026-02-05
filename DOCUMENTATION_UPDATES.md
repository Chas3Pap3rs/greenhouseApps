# Documentation Updates - December 9, 2025

## Summary of Changes

This document summarizes all documentation updates made to reflect the new maintenance and export scripts created during the database backfill project.

---

## New Scripts Added

### 1. **backfill_ai_access.py**
**Location:** `greenhouse_sharepoint_mapper/`

**Purpose:** Backfill missing candidates from `greenhouse_candidates` (dbBuilder) to `greenhouse_candidates_ai` (AI Access)

**Key Features:**
- Identifies candidates present in dbBuilder but missing from AI Access
- Downloads resumes using fresh Greenhouse API URLs (avoids expired S3 links)
- Copies resumes to AI_Access folder with retry logic for OneDrive sync
- Gets SharePoint URLs for copied resumes
- Inserts candidates into AI Access database
- Adds ALL candidates (with or without resumes) to maintain database parity

**When to Use:**
- After discovering candidate count discrepancies between databases
- When AI Access database is missing candidates
- After major database issues or rebuilds

---

### 2. **update_missing_resumes.py**
**Location:** `greenhouse_sharepoint_mapper/`

**Purpose:** Update candidates in AI Access database that have NULL resume links

**Key Features:**
- Finds candidates with NULL resume_links in AI Access
- Searches for existing resumes in local organized folders
- Downloads from Greenhouse API with fresh URLs if not found locally
- Copies to AI_Access folder
- Updates database with SharePoint URLs
- Handles expired S3 URLs automatically

**When to Use:**
- After running backfill_ai_access.py
- When candidates have NULL resume links
- To fix resume link issues without re-processing all candidates

---

### 3. **export_incremental_ai.py**
**Location:** `greenhouse_sharepoint_mapper/`

**Purpose:** Export only NEW candidates added since last export for efficient Zapier Table updates

**Key Features:**
- Tracks last exported candidate_id in `.last_incremental_export` file
- Only exports candidates added since last run
- Creates segments under 50MB for Zapier compatibility
- Supports manual date/ID filtering
- Can be reset for next full export

**When to Use:**
- Weekly/monthly Zapier Table updates
- After running backfill scripts
- When you want to append new data without re-uploading everything

**Usage:**
```bash
# Regular incremental export
python export_incremental_ai.py

# Export since specific date
python export_incremental_ai.py --since 2025-01-01

# Export candidates after specific ID
python export_incremental_ai.py --since-id 49000000000

# Reset tracking for next full export
python export_incremental_ai.py --reset
```

---

## Documentation Files Updated

### 1. **greenhouse_sharepoint_mapper/README.md**

**Changes:**
- Updated File Structure section to include:
  - Maintenance Scripts category
  - All export script variations
  - Segmented exports directory
- Added "Maintenance & Troubleshooting" section with:
  - Database sync issue resolution
  - Backfill missing candidates instructions
  - Update missing resumes instructions
  - Incremental export usage
- Updated Prerequisites to include Greenhouse API key requirement

---

### 2. **greenhouse_sharepoint_mapper/UPDATE_GUIDE.md**

**Changes:**
- Added "🔧 Maintenance Scripts" section with:
  - Database Sync Issues subsection
  - Backfill Missing Candidates instructions
  - Update Missing Resumes instructions
- Added "📦 Incremental CSV Exports" section with:
  - Weekly/Monthly update workflow
  - First run vs subsequent runs explanation
  - Zapier upload instructions
  - Reset tracking instructions
  - Manual control options
- Updated "💡 Tips" section to include:
  - Use incremental exports for weekly/monthly updates
  - Run maintenance scripts for database discrepancies
- Expanded "🆘 Troubleshooting" section with:
  - Database candidate counts don't match
  - Candidates have NULL resume links
  - Resume download fails with 403 Forbidden
  - Zapier file too large solutions

---

### 3. **EXPORT_OPTIONS.md**

**Changes:**
- Updated Quick Reference Table to include:
  - Incremental (AI Access) export option
- Added new export option #6: "AI Access Incremental Export"
  - Full documentation with usage patterns
  - Manual control options
  - When to use guidelines
- Renumbered subsequent export options (7, 8, 9)
- Updated "Last Updated" date to December 9, 2025

---

### 4. **README.md** (Main Project)

**Changes:**
- Updated Project Structure section to include:
  - Maintenance Scripts category in sharepoint_mapper
  - All new export scripts
  - Segmented exports directory
- Updated "🔧 Troubleshooting" section with:
  - Database candidate counts don't match
  - Candidates have NULL resume links
  - Resume downloads fail with 403 Forbidden
  - Solutions using new maintenance scripts
- Updated "📊 Monitoring & Maintenance" section:
  - Added incremental export option for Zapier updates
  - Recommended workflow for weekly/monthly exports
- Updated "Last Updated" date to December 9, 2025

---

## Key Concepts Documented

### 1. **Database Parity**
- All candidates should exist in both `greenhouse_candidates` and `greenhouse_candidates_ai`
- Candidates without resumes are still added (with NULL resume links)
- Resume links are populated when available

### 2. **Fresh URL Fetching**
- S3 URLs from Greenhouse expire after ~7 days
- Maintenance scripts fetch fresh URLs from Greenhouse API
- Prevents 403 Forbidden errors during downloads

### 3. **Incremental Workflows**
- Incremental updates for database syncing (update_*.py)
- Incremental exports for Zapier uploads (export_incremental_ai.py)
- Tracking files maintain state between runs

### 4. **Zapier Compatibility**
- 50MB file size limit
- Segmented exports split data into <50MB chunks
- Incremental exports only send new data
- Both approaches avoid re-uploading all candidates

---

## Workflow Recommendations

### Initial Setup (One-time)
1. Run full database sync
2. Download all resumes
3. Create AI_Access folder
4. Map SharePoint links
5. Export full segmented CSV
6. Upload to Zapier Tables

### Weekly/Monthly Updates
1. Run `./run_full_update.sh` (syncs databases, downloads resumes, updates links)
2. Run `export_incremental_ai.py` (exports only new candidates)
3. Upload incremental segments to Zapier (append mode)

### Maintenance (As Needed)
1. Check database sync: `check_sync_status.py`
2. If discrepancies found:
   - Run `backfill_ai_access.py`
   - Run `update_missing_resumes.py`
3. Export and upload updated data

### Annual Full Refresh (1-2x per year)
1. Run full segmented export: `export_segmented_ai.py`
2. Replace Zapier Table data completely
3. Reset incremental tracking: `export_incremental_ai.py --reset`

---

## Files Not Modified

The following documentation files were reviewed but did not require updates:

- `greenhouse_candidate_dbBuilder/README.md` - No changes needed
- `greenhouse_resume_downloader/README.md` - No changes needed
- `greenhouse_resume_content_sync/README.md` - No changes needed
- `greenhouse_candidate_dbBuilder/RESUME_CONTENT_SETUP.md` - No changes needed
- `UPDATE_GUIDE.md` (root) - Covered by project-specific guides

---

## Testing Performed

### Incremental Export Script
- Dry run with 100 candidates: ✅ Success
- Tracking file creation: ✅ Success
- Cleanup of test files: ✅ Success

### Backfill Script
- Processed 782 missing candidates: ✅ Success
- Database parity achieved (48,121 in both databases): ✅ Success

### Update Missing Resumes Script
- Processed 5,312 candidates with NULL resumes: ✅ Success
- Updated 2,065 candidates with resumes: ✅ Success
- 3,247 candidates confirmed without resumes in Greenhouse: ✅ Documented

---

## Future Maintenance Notes

### When to Update Documentation

1. **New Scripts Added:**
   - Add to appropriate README.md file structure section
   - Add to EXPORT_OPTIONS.md if it's an export script
   - Add to UPDATE_GUIDE.md if it's part of regular workflow
   - Update main README.md project structure

2. **Workflow Changes:**
   - Update UPDATE_GUIDE.md with new procedures
   - Update troubleshooting sections if new issues discovered
   - Update monitoring sections if new checks added

3. **Database Schema Changes:**
   - Update database architecture sections
   - Update export field lists
   - Update troubleshooting for migration issues

### Documentation Standards

- Use emoji headers for visual organization (🚀 🔧 📦 💡 🆘)
- Include code blocks with bash commands
- Provide "When to Use" guidance for each script
- Include file size estimates for exports
- Mark Zapier-compatible exports with ✅
- Update "Last Updated" dates when making changes

---

**Documentation Updated By:** Cascade AI Assistant  
**Date:** December 9, 2025  
**Project:** Greenhouse Apps - Database Backfill & Incremental Exports
