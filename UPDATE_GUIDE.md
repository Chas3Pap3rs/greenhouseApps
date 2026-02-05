# Greenhouse Apps - Update Guide

Complete guide for updating and maintaining all Greenhouse applications.

**🎯 NEW: Use Master Scripts for automated workflows!** See [Master Scripts](#-master-scripts-recommended) below.

---

## 📋 Table of Contents

- [Quick Reference](#-quick-reference)
- [Master Scripts (Recommended)](#-master-scripts-recommended)
- [Daily/Weekly Updates](#-dailyweekly-updates)
- [Monthly Maintenance](#️-monthly-maintenance)
- [Individual App Updates](#-individual-app-updates)
- [Full System Rebuild](#-full-system-rebuild)
- [CSV Export Options](#-csv-export-options)
- [Verification & Diagnostics](#-verification--diagnostics)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Reference

### Most Common Update Scenarios

| Scenario | Command | Time | Frequency |
|----------|---------|------|-----------|
| **🆕 Incremental Update (Recommended)** | `python3 master_incremental_update.py` | 30m-2h | Weekly |
| **🆕 Verify Data Quality** | `python3 master_verify_integrity.py` | 5-10m | After updates |
| **🆕 Complete Rebuild** | `python3 master_full_rebuild.py` | 4-8h | Monthly/As needed |
| **Resume Content Only** | `cd greenhouse_resume_content_sync && python update_resume_content.py` | 2-5m | Weekly |
| **Check Status** | `cd utilities/verification && python check_ai_database_status.py` | <1m | Anytime |

---

## 🎛️ Master Scripts (Recommended)

The system now includes three master orchestration scripts that automate complete workflows.

### 1. Weekly/Monthly Updates

**Use:** `master_incremental_update.py`

```bash
# Run from project root
python3 master_incremental_update.py
```

**What it does:**
1. ✅ Pulls NEW/UPDATED candidates from Greenhouse API
2. ✅ Downloads new resumes only
3. ✅ Updates AI_Access folder with new files
4. ✅ Maps SharePoint links for new resumes
5. ✅ Maps AI_Access links for new candidates
6. ✅ Maps metadata JSON links
7. ✅ Syncs resume_content from metadata to database
8. ✅ Updates resume_content in Greenhouse API (incremental)
9. ✅ Verifies AI database status
10. ✅ Exports incremental CSV

**Time:** 30 minutes - 2 hours (depends on number of new candidates)  
**Output:** 
- Updated databases
- Incremental CSV in `greenhouse_sharepoint_mapper/exports/ai_database/incremental/`
- Detailed progress log with color-coded output

**When to use:**
- ✅ Weekly maintenance
- ✅ After adding new candidates to Greenhouse
- ✅ Regular updates without full rebuild

**Recommended schedule:** Weekly (e.g., every Sunday)

---

### 2. Verify Data Integrity

**Use:** `master_verify_integrity.py`

```bash
# Run from project root
python3 master_verify_integrity.py
```

**What it does:**
- ✅ Verifies database schemas
- ✅ Checks data coverage across all 3 databases
- ✅ Analyzes null fields
- ✅ Verifies sync status between databases
- ✅ Checks resume_content coverage
- ✅ Validates SharePoint links
- ✅ Runs cross-database consistency checks
- ✅ Generates comprehensive quality report

**Time:** 5-10 minutes  
**Output:** Detailed verification report with data quality scoring

**When to use:**
- ✅ After running `master_incremental_update.py`
- ✅ Before exporting CSVs to production
- ✅ When investigating data quality issues
- ✅ Monthly data quality audits

**Data Quality Guidelines:**
- ✅ **Excellent:** >95% coverage on all key fields
- ✅ **Good:** >90% coverage on all key fields
- ⚠️ **Fair:** >80% coverage (consider incremental update)
- ❌ **Poor:** <80% coverage (consider full rebuild)

**Save report for records:**
```bash
python3 master_verify_integrity.py > logs/verification_$(date +%Y%m%d).txt
```

---

### 3. Complete System Rebuild

**Use:** `master_full_rebuild.py`

```bash
# Run from project root
python3 master_full_rebuild.py
```

**What it does:**
1. ✅ Pulls ALL candidates from Greenhouse API
2. ✅ Downloads ALL resumes
3. ✅ Creates complete AI_Access folder structure
4. ✅ Maps all SharePoint links (human-friendly)
5. ✅ Maps all AI_Access links (AI-friendly)
6. ✅ Maps all metadata JSON links (batch mode)
7. ✅ Syncs all resume_content from metadata
8. ✅ Syncs all resume_content to Greenhouse API
9. ✅ Runs comprehensive verification
10. ✅ Exports all CSVs (full and segmented)

**Time:** 4-8 hours (depends on number of candidates and network speed)  
**Output:** 
- Completely rebuilt databases
- Full CSV exports in database-specific folders:
  - AI Database: `greenhouse_sharepoint_mapper/exports/ai_database/`
  - SharePoint: `greenhouse_sharepoint_mapper/exports/sharepoint_database/`
  - Main DB: `greenhouse_sharepoint_mapper/exports/main_database/`
- Comprehensive summary report

**When to use:**
- ✅ Initial setup of the system
- ✅ Complete data refresh needed
- ✅ Database corruption or major data issues
- ✅ After significant schema changes
- ✅ Monthly full refresh (recommended)

**Safety features:**
- ⚠️ Requires double confirmation (type 'yes' then 'REBUILD')
- ⚠️ Shows estimated time and requirements
- ⚠️ Detailed progress logging
- ⚠️ Continues on non-critical errors

**Prerequisites:**
- Stable internet connection
- Sufficient disk space (~50GB+)
- All credentials configured in `.env` files
- PostgreSQL databases created

---

## 📅 Daily/Weekly Updates

### Option 1: Master Script (Recommended) ⭐

```bash
# Weekly incremental update
python3 master_incremental_update.py

# Verify data quality
python3 master_verify_integrity.py

# Upload incremental CSV to Zapier Tables
# File location: greenhouse_sharepoint_mapper/exports/ai_database/incremental/
```

**Time:** 30 min - 2 hours + 5-10 min verification  
**Best for:** Regular maintenance, keeping everything in sync

---

### Option 2: Resume Content Update Only

**Best for:** AI agents using Greenhouse API (no SharePoint needed)

```bash
cd greenhouse_resume_content_sync
source .venv/bin/activate
python update_resume_content.py
```

**What it does:**
- ✅ Processes new candidates with resumes
- ✅ Updates candidates who uploaded new resumes
- ✅ Extracts text and updates `resume_content` custom field
- ✅ Skips candidates already up to date

**Time:** 2-5 minutes  
**Output:** Updated Greenhouse custom fields

**When to use:**
- Your AI agents read from Greenhouse API
- You don't need SharePoint CSV exports
- Faster than full update

---

### Option 3: Individual Scripts (Manual Control)

If you need granular control over each step:

```bash
# 1. Sync candidates
cd greenhouse_candidate_dbBuilder
python main.py

# 2. Download resumes
cd ../greenhouse_resume_downloader
python download_resumes.py

# 3. Update AI_Access folder
cd ../greenhouse_sharepoint_mapper
python create_ai_access_folder.py

# 4. Map links
python map_sharepoint_links.py
python map_ai_access_links.py
python map_metadata_links.py

# 5. Sync resume_content
cd ../greenhouse_resume_content_sync
python update_resume_content.py

# 6. Export CSVs
cd ../greenhouse_sharepoint_mapper/exports
python export_incremental_ai.py
```

---

## 🗓️ Monthly Maintenance

### Complete System Health Check

#### 1. Run Comprehensive Verification

```bash
# Run from project root
python3 master_verify_integrity.py

# Save report for records
python3 master_verify_integrity.py > logs/verification_$(date +%Y%m%d).txt
```

**Review:**
- Coverage percentages for all databases
- Null field analysis
- Sync status between databases
- Data quality score

**Action based on results:**
- **>90% coverage:** ✅ Continue with weekly incremental updates
- **80-90% coverage:** ⚠️ Run `master_incremental_update.py`
- **<80% coverage:** ❌ Run `master_full_rebuild.py`

---

#### 2. Database Candidate Counts

```bash
# Check all three databases
psql -d greenhouse_candidates -c "SELECT COUNT(*) FROM gh.candidates;"
psql -d greenhouse_candidates_sp -c "SELECT COUNT(*) FROM gh.candidates;"
psql -d greenhouse_candidates_ai -c "SELECT COUNT(*) FROM gh.candidates;"
```

**What to look for:**
- All databases have similar candidate counts
- No major discrepancies (>5% difference)
- Growth is consistent with new hires

**If counts don't match:**
```bash
# Run verification to identify gaps
python3 master_verify_integrity.py

# If needed, run incremental update
python3 master_incremental_update.py
```

---

#### 3. OneDrive Sync Verification

**Check:**
- ✅ OneDrive is running and synced
- ✅ No pending uploads in `Greenhouse_Resumes/`
- ✅ `AI_Access/` folder is up to date
- ✅ No sync errors in OneDrive

---

#### 4. CSV Export Freshness

**Check export timestamps:**
```bash
ls -lh greenhouse_sharepoint_mapper/exports/ai_database/full/
ls -lh greenhouse_sharepoint_mapper/exports/ai_database/segmented/
ls -lh greenhouse_sharepoint_mapper/exports/ai_database/incremental/
ls -lh greenhouse_sharepoint_mapper/exports/sharepoint_database/full/
```

**If exports are old (>1 week):**
```bash
# Run incremental update (includes export)
python3 master_incremental_update.py

# Or export manually
cd greenhouse_sharepoint_mapper/exports
python export_incremental_ai.py
```

---

## 🔧 Individual App Updates

### App 1: Candidate Database Builder

**When to run:**
- Need latest candidate data
- Before running other updates
- Checking for new candidates

```bash
cd greenhouse_candidate_dbBuilder
source .venv/bin/activate
python main.py
```

**Options:**
```bash
# Incremental update (default)
python main.py

# Full sync (rebuilds everything)
python main.py --full-sync

# Check status
python status.py
```

**Time:** 2-5 minutes (incremental), 10-15 minutes (full)

---

### App 2: Resume Downloader

**When to run:**
- After syncing new candidates
- Need physical resume files
- Before SharePoint mapping

```bash
cd greenhouse_resume_downloader
source .venv/bin/activate
python download_resumes.py
```

**Options:**
```bash
# Download new resumes (default)
python download_resumes.py

# Check status
python status.py
```

**Time:** Varies (depends on number of new resumes)

---

### App 3: SharePoint Mapper

**When to run:**
- After downloading resumes
- Need updated SharePoint links
- Before CSV exports

```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate

# Update AI_Access folder
python create_ai_access_folder.py

# Map links (incremental)
python map_sharepoint_links.py
python map_ai_access_links.py
python map_metadata_links.py

# Check status
python status.py
```

**Time:** Minutes (incremental), hours (full rebuild)

---

### App 4: Resume Content Sync

**When to run:**
- After downloading resumes
- Need resume text in Greenhouse
- For AI agent API access

```bash
cd greenhouse_resume_content_sync
source .venv/bin/activate

# Incremental update (recommended)
python update_resume_content.py

# Full sync (all candidates)
python sync_resume_content.py

# Sync from SharePoint metadata
python sync_from_sharepoint.py
```

**Time:** 2-5 minutes (incremental), 1-2 hours (full)

---

## 🏗️ Full System Rebuild

### When to Rebuild

Only run full rebuilds when:
- ❌ Initial setup of the system
- ❌ Database corruption or major data loss
- ❌ Major changes to folder structure
- ❌ SharePoint site migration
- ❌ Data quality is very poor (<80% coverage)

**Otherwise, use incremental updates!**

### Using Master Script (Recommended)

```bash
# Run from project root
python3 master_full_rebuild.py

# Follow prompts:
# 1. Type 'yes' to confirm
# 2. Type 'REBUILD' to double-confirm
# 3. Wait 4-8 hours for completion
```

**What happens:**
- All 10 steps run automatically
- Color-coded progress output
- Error handling and recovery
- Final summary report
- All CSVs exported

---

### Manual Rebuild (Advanced)

If you need manual control:

```bash
# 1. Pull all candidates
cd greenhouse_candidate_dbBuilder
python main.py --full-sync

# 2. Download all resumes
cd ../greenhouse_resume_downloader
python download_resumes.py

# 3. Create AI_Access folder
cd ../greenhouse_sharepoint_mapper
python create_ai_access_folder.py

# 4. Map all links (full rebuild)
python map_sharepoint_links.py
python map_ai_access_links.py
python map_metadata_links_batch.py  # Batch mode for full rebuild

# 5. Sync resume_content
cd ../greenhouse_resume_content_sync
python sync_resume_content.py

# 6. Export all CSVs
cd ../greenhouse_sharepoint_mapper/exports
python export_ai_access_csv_full.py
python export_segmented_ai_full.py
python export_sharepoint_csv.py
```

**Time:** 4-8 hours total

---

## 📊 CSV Export Options

**📘 Complete guide:** [exports/README.md](greenhouse_sharepoint_mapper/exports/README.md)

### Quick Export Commands

```bash
cd greenhouse_sharepoint_mapper/exports

# Lightweight (no resume_content) - Zapier compatible
python export_ai_access_csv.py              # ~33MB, single file
python export_segmented_ai.py               # <50MB each, multiple files

# With resume_content
python export_ai_access_csv_full.py         # ~500MB, single file
python export_segmented_ai_full.py          # <50MB each, with content

# Incremental (new candidates only)
python export_incremental_ai.py             # Varies, for weekly updates

# Human-friendly (organized folders)
python export_sharepoint_csv.py             # ~33MB, organized structure

# Minimal fields with content
python export_minimal_with_content.py       # ~50MB, 4 fields only
```

### Export Decision Guide

**For Zapier Tables (50MB limit):**
- Initial upload: `export_segmented_ai.py` or `export_segmented_ai_full.py`
- Weekly updates: `export_incremental_ai.py` (append mode)

**For Offline AI Processing:**
- Use `export_ai_access_csv_full.py` (includes all resume text)

**For API-Based AI Agents:**
- Use `export_ai_access_csv.py` + fetch resume_content via Greenhouse API

---

## 🔍 Verification & Diagnostics

### Master Verification Script

```bash
# Comprehensive verification
python3 master_verify_integrity.py

# Save report
python3 master_verify_integrity.py > logs/verification_$(date +%Y%m%d).txt
```

---

### Individual Verification Scripts

All verification scripts are in `utilities/verification/`:

```bash
cd utilities/verification

# AI database status
python check_ai_database_status.py

# Null field analysis
python check_ai_null_fields.py

# Schema verification
python check_ai_schema.py

# Main database stats
python check_greenhouse_stats.py

# Comprehensive check (all databases)
python comprehensive_database_check.py

# Resume content sync status
python check_completion.py
python verify_final_count.py
python final_summary.py

# Mapping status
python check_mapping_status.py
python check_sync_status.py
```

---

### Investigation Scripts

For deeper analysis, use scripts in `utilities/investigation/`:

```bash
cd utilities/investigation

# Investigate null fields
python investigate_null_fields.py

# Analyze database structure
python analyze_database_structure.py

# Verify link types
python verify_link_types.py

# Investigate null resume links
python investigate_null_resume_links.py
```

---

### Analysis Scripts

For detailed data analysis, use scripts in `utilities/analysis/`:

```bash
cd utilities/analysis

# Analyze failed resume extractions
python analyze_failed_extractions.py
```

---

## 🔧 Troubleshooting

### Quick Diagnostics

```bash
# Run comprehensive verification
python3 master_verify_integrity.py

# Check specific database
cd utilities/verification
python check_ai_database_status.py

# Investigate issues
cd utilities/investigation
python investigate_null_fields.py
```

---

### Common Issues

#### Issue: Database candidate counts don't match

**Symptoms:**
- `greenhouse_candidates`: 48,121
- `greenhouse_candidates_sp`: 48,121
- `greenhouse_candidates_ai`: 44,689

**Solution:**
```bash
# 1. Run verification to identify gaps
python3 master_verify_integrity.py

# 2. If coverage is >80%, run incremental update
python3 master_incremental_update.py

# 3. If coverage is <80%, run full rebuild
python3 master_full_rebuild.py
```

---

#### Issue: Master script step fails

**Symptoms:**
- Master script reports failed step
- Exit code 1

**Solution:**
```bash
# 1. Check which step failed in the output
# 2. Run that specific script manually for more details
# 3. Fix the issue
# 4. Re-run master script or continue from failed step
```

**Example:**
```bash
# If Step 3 (AI_Access folder) failed:
cd greenhouse_sharepoint_mapper
python create_ai_access_folder.py

# Then re-run master script
cd ../..
python3 master_incremental_update.py
```

---

#### Issue: Missing resume_content

**Symptoms:**
- Some candidates have NULL resume_content
- Coverage is 86-93% (normal)

**Solution:**
```bash
# This is normal! ~7-14% gap due to unsupported file formats

# Analyze the gap
cd utilities/analysis
python analyze_failed_extractions.py

# Common causes:
# - RTF files (not supported)
# - Legacy DOC files (not DOCX)
# - Image-based PDFs (no text layer)
# - Corrupted files
```

---

#### Issue: "Cannot connect to database"

**Solution:**
```bash
# 1. Check PostgreSQL is running
psql -l

# 2. Verify .env file has correct credentials
cat greenhouse_candidate_dbBuilder/.env

# 3. Test connection
psql -d greenhouse_candidates -c "SELECT COUNT(*) FROM gh.candidates;"

# 4. Check database exists
psql -l | grep greenhouse
```

---

#### Issue: "Greenhouse API rate limit exceeded"

**Solution:**
- Wait for rate limit to reset (usually 1 hour)
- Run during off-peak hours
- Contact Greenhouse support to increase rate limit
- Use incremental updates instead of full rebuilds

---

#### Issue: "SharePoint authentication failed"

**Solution:**
```bash
# 1. Check Azure credentials in .env
cat greenhouse_sharepoint_mapper/.env

# 2. Verify app registration permissions
# - Files.Read.All
# - Sites.Read.All

# 3. Re-authenticate if token expired
# The script will automatically refresh tokens
```

---

#### Issue: "Disk space full"

**Solution:**
```bash
# 1. Check disk space
df -h

# 2. Clean up old exports (use cleanup script - see utilities/)
# Or manually:
rm greenhouse_sharepoint_mapper/exports/ai_database/full/*_old.csv
rm greenhouse_sharepoint_mapper/exports/sharepoint_database/full/*_old.csv

# 3. Archive old resumes if needed
# 4. Ensure at least 50GB free space
```

---

#### Issue: Incremental update processes too many candidates

**Solution:**
```bash
# 1. Check sync status
cd utilities/verification
python check_sync_status.py

# 2. Verify sync log tables
psql -d greenhouse_candidates_ai -c "SELECT * FROM sync_log ORDER BY sync_date DESC LIMIT 5;"

# 3. If needed, manually update sync log
# (Advanced - contact support)
```

---

### Getting Help

**Documentation:**
- [README.md](README.md) - Main system documentation
- [MASTER_SCRIPTS_README.md](MASTER_SCRIPTS_README.md) - Master scripts guide
- [utilities/README.md](utilities/README.md) - Utilities documentation
- [exports/README.md](greenhouse_sharepoint_mapper/exports/README.md) - Export guide

**Diagnostic Tools:**
- `utilities/investigation/` - Database investigation
- `utilities/verification/` - Status checks
- `utilities/analysis/` - Data analysis
- `utilities/fixes/` - One-time fix scripts

---

## 📊 Monitoring Best Practices

### Weekly Checklist

- [ ] Run `python3 master_incremental_update.py`
- [ ] Run `python3 master_verify_integrity.py`
- [ ] Review verification report
- [ ] Upload incremental CSV to Zapier Tables
- [ ] Check OneDrive sync status
- [ ] Review any error messages

### Monthly Checklist

- [ ] Run `python3 master_verify_integrity.py`
- [ ] Save verification report for records
- [ ] Review coverage percentages
- [ ] Check database candidate counts
- [ ] Verify OneDrive sync health
- [ ] Test AI agent access
- [ ] Review disk space usage
- [ ] Consider full rebuild if coverage <90%

### Automation Setup

```bash
# Create logs directory
mkdir -p logs

# Add to crontab for weekly updates (every Sunday at 2 AM)
0 2 * * 0 cd /path/to/greenhouseApps && python3 master_incremental_update.py >> logs/update_$(date +\%Y\%m\%d).log 2>&1

# Add verification after update (every Sunday at 5 AM)
0 5 * * 0 cd /path/to/greenhouseApps && python3 master_verify_integrity.py > logs/verification_$(date +\%Y\%m\%d).txt 2>&1
```

---

**Last Updated:** January 28, 2026 - v5.0 (Master Scripts Integration)
