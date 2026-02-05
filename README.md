# Greenhouse Apps - Complete System Documentation

A comprehensive suite of tools for syncing Greenhouse candidate data, downloading resumes, and creating AI-friendly SharePoint integrations.

**🎯 NEW: Master Orchestration Scripts** - Automate complete workflows with single commands! See [Quick Start](#-quick-start) below.

---

## 📋 Table of Contents

- [System Overview](#-system-overview)
- [Quick Start](#-quick-start)
- [Master Scripts](#-master-orchestration-scripts)
- [Project Structure](#-project-structure)
- [Complete Workflow](#-complete-workflow)
- [Database Architecture](#️-database-architecture)
- [CSV Export Options](#-csv-export-options)
- [Regular Updates](#-regular-updates)
- [Troubleshooting](#-troubleshooting)
- [Individual Project Details](#-individual-project-details)

**📘 For detailed workflows, see:**
- [MASTER_SCRIPTS_README.md](MASTER_SCRIPTS_README.md) - Master orchestration scripts guide
- [UPDATE_GUIDE.md](UPDATE_GUIDE.md) - Detailed update procedures
- [utilities/README.md](utilities/README.md) - Diagnostic and verification tools

---

## 🎯 System Overview

This system consists of four integrated applications that work together to:

1. **Sync candidate data** from Greenhouse API to PostgreSQL
2. **Download resumes** from Greenhouse to local OneDrive folder
3. **Map resumes to SharePoint** with two structures:
   - **Human-friendly**: Organized by year/month folders
   - **AI-friendly**: Flat folder structure for AI agents
4. **Extract and sync resume content** directly to Greenhouse custom fields for AI agent access

### What You Get

- **3 PostgreSQL Databases** with candidate data
- **2 SharePoint Structures** (organized + flat)
- **7 CSV Export Options** optimized for different use cases
- **Resume Content in Greenhouse** - Extracted text stored in custom fields (accessible via API)
- **Master Orchestration Scripts** - Automated workflows for rebuild, updates, and verification
- **Organized Utilities** - Diagnostic, verification, and analysis tools

---

## 🚀 Quick Start

### First-Time Setup (Complete Rebuild)

Use the master rebuild script to set up everything automatically:

```bash
# Run complete system rebuild (4-8 hours)
python3 master_full_rebuild.py
```

**What it does:**
1. ✅ Pulls ALL candidates from Greenhouse API
2. ✅ Downloads ALL resumes
3. ✅ Creates AI_Access folder with metadata
4. ✅ Maps all SharePoint links (both databases)
5. ✅ Syncs resume_content to Greenhouse
6. ✅ Runs comprehensive verification
7. ✅ Exports all CSVs

**Prerequisites:**
- `.env` files configured in each project folder
- PostgreSQL databases created
- Greenhouse API access
- SharePoint access via Microsoft Graph API
- Sufficient disk space (~50GB+)

---

### Regular Updates (Weekly/Monthly)

Use the incremental update script for regular maintenance:

```bash
# Run incremental update (30 min - 2 hours)
python3 master_incremental_update.py
```

**What it does:**
1. ✅ Pulls NEW/UPDATED candidates only
2. ✅ Downloads new resumes
3. ✅ Updates AI_Access folder
4. ✅ Maps new SharePoint links
5. ✅ Syncs new resume_content
6. ✅ Exports incremental CSV

**Recommended schedule:** Weekly

---

### Verify Data Integrity

Check system health and data quality:

```bash
# Run comprehensive verification (5-10 minutes)
python3 master_verify_integrity.py
```

**What it does:**
- ✅ Verifies all database schemas
- ✅ Checks data coverage (all 3 databases)
- ✅ Analyzes null fields
- ✅ Verifies sync status
- ✅ Generates quality report

---

## 🎛️ Master Orchestration Scripts

The system now includes three master scripts that automate complete workflows:

### 1. `master_full_rebuild.py` - Complete System Rebuild
**Use when:** Initial setup, major data issues, monthly full refresh

```bash
python3 master_full_rebuild.py
```

- Requires double confirmation (safety feature)
- Rebuilds everything from scratch
- Estimated time: 4-8 hours
- See [MASTER_SCRIPTS_README.md](MASTER_SCRIPTS_README.md) for details

### 2. `master_incremental_update.py` - Regular Updates
**Use when:** Weekly/monthly updates, syncing new candidates

```bash
python3 master_incremental_update.py
```

- No confirmation needed (safe to automate)
- Only processes new/updated candidates
- Estimated time: 30 min - 2 hours
- Perfect for cron jobs

### 3. `master_verify_integrity.py` - Comprehensive Verification
**Use when:** After updates, before production exports, monthly audits

```bash
python3 master_verify_integrity.py
```

- Runs all verification checks
- Generates detailed quality reports
- Estimated time: 5-10 minutes
- Provides data quality scoring

**📘 Complete guide:** [MASTER_SCRIPTS_README.md](MASTER_SCRIPTS_README.md)

---

## 📁 Project Structure

```
greenhouseApps/
├── README.md                           # This file - Complete system documentation
├── UPDATE_GUIDE.md                     # Detailed update procedures
├── MASTER_SCRIPTS_README.md            # Master scripts guide
├── SCRIPT_INVENTORY.md                 # Complete script catalog
│
├── master_full_rebuild.py              # 🎯 Master script: Complete rebuild
├── master_incremental_update.py        # 🎯 Master script: Regular updates
├── master_verify_integrity.py          # 🎯 Master script: Verification
│
├── utilities/                          # 🆕 Diagnostic & maintenance tools
│   ├── README.md                       # Utilities documentation
│   ├── investigation/                  # Database investigation scripts (4)
│   ├── verification/                   # Status checks and verification (10)
│   ├── analysis/                       # Data analysis tools (1)
│   ├── fixes/                          # One-time fix scripts (7)
│   └── testing/                        # API testing scripts (1)
│
├── greenhouse_candidate_dbBuilder/     # Project 1: Candidate Data Sync
│   ├── main.py                         # CORE: Sync candidates from Greenhouse API
│   ├── setup.py                        # CORE: Create database and schema
│   ├── status.py                       # CORE: View sync progress and stats
│   ├── export_appending.py             # CORE: Export with append mode
│   ├── export_segmented.py             # CORE: Segmented export
│   ├── _deprecated/                    # 🆕 Archived scripts
│   └── ... (config files, venv)
│
├── greenhouse_resume_downloader/       # Project 2: Resume Downloader
│   ├── download_resumes.py             # CORE: Download resumes from Greenhouse
│   ├── setup_audit_table.py            # CORE: Setup audit table
│   ├── status.py                       # CORE: Show download status
│   ├── _deprecated/                    # 🆕 Archived scripts
│   └── ... (config files, venv)
│
├── greenhouse_resume_content_sync/     # Project 3: Resume Content Extraction
│   ├── sync_resume_content.py          # CORE: Full sync to Greenhouse API
│   ├── update_resume_content.py        # CORE: Incremental updates
│   ├── sync_to_database.py             # CORE: Sync to local database
│   ├── sync_from_sharepoint.py         # CORE: Sync from SharePoint metadata
│   ├── _deprecated/                    # 🆕 Archived scripts
│   └── ... (config files, venv)
│
└── greenhouse_sharepoint_mapper/       # Project 4: SharePoint Integration
    ├── graph_client.py                 # CORE: Microsoft Graph API client
    ├── create_ai_access_folder.py      # CORE: Create AI_Access folder
    ├── map_sharepoint_links.py         # CORE: Map SharePoint resume links
    ├── map_ai_access_links.py          # CORE: Map AI_Access links
    ├── map_metadata_links.py           # CORE: Map metadata links (individual)
    ├── map_metadata_links_batch.py     # CORE: Map metadata links (batch)
    ├── setup_sharepoint_db.py          # CORE: Setup SharePoint database
    ├── sync_ai_database_fields.py      # CORE: Sync database fields
    ├── sync_resume_content_from_metadata.py  # CORE: Sync from metadata
    ├── status.py                       # CORE: Show mapping status
    ├── exports/                        # 🆕 All export scripts (7)
    │   ├── README.md                   # Export scripts documentation
    │   ├── export_ai_access_csv.py
    │   ├── export_ai_access_csv_full.py
    │   ├── export_segmented_ai.py
    │   ├── export_segmented_ai_full.py
    │   ├── export_incremental_ai.py
    │   ├── export_sharepoint_csv.py
    │   └── export_minimal_with_content.py
    ├── _deprecated/                    # 🆕 Archived scripts
    └── ... (config files, venv, output folders)
```

### 🆕 New Organization Features

**Master Scripts** (in root):
- Single-command workflows for rebuild, updates, and verification
- Color-coded output for easy monitoring
- Comprehensive error handling and reporting

**Utilities Folder**:
- All diagnostic and maintenance tools in one place
- Organized by purpose (investigation, verification, analysis, fixes, testing)
- Complete documentation in `utilities/README.md`

**Exports Folder**:
- All 7 export scripts organized together
- Clear documentation of each export type
- Decision guide for choosing the right export

**Deprecated Folders**:
- Old/unused scripts archived (not deleted)
- Keeps production folders clean
- Easy to reference if needed

---

## 🔄 Complete Workflow

### Data Flow Diagram

```
Greenhouse API
      ↓
[1. dbBuilder] → PostgreSQL: greenhouse_candidates
      ↓
[2. Resume Downloader] → OneDrive: Organized Folders (2024/04_April/...)
      ↓
[3. SharePoint Mapper]
      ↓
      ├─→ [Create AI_Access] → OneDrive: Flat Folder (AI_Access/...)
      │                              ↓
      │                         SharePoint Sync
      │                              ↓
      ├─→ [Map Human Links] → PostgreSQL: greenhouse_candidates_sp
      │                              ↓
      │                         CSV: Human-Friendly Export
      │
      └─→ [Map AI Links] → PostgreSQL: greenhouse_candidates_ai
                                ↓
                           CSV: AI-Friendly Export
                                ↓
                           Zapier Tables (for AI Agents)
```

### Automated with Master Scripts

The master scripts automate this entire workflow:

**Full Rebuild** (`master_full_rebuild.py`):
- Executes all 10 steps in correct order
- Handles errors gracefully
- Provides detailed progress logging
- Generates final summary report

**Incremental Update** (`master_incremental_update.py`):
- Optimized for speed (only new data)
- Uses individual processing (faster for small batches)
- Exports incremental CSV
- Perfect for weekly automation

---

## 🗄️ Database Architecture

### Database 1: `greenhouse_candidates` (Source)
**Purpose:** Master database with raw Greenhouse data

**Key Fields:**
- `candidate_id`, `first_name`, `last_name`, `full_name`
- `email`, `phone_numbers`, `addresses`
- `resume_links` - S3 URLs from Greenhouse
- `employment_titles`, `employment_companies`
- `degrees`, `jobs_name`
- `created_at`, `updated_at`

**Updated by:** `dbBuilder/main.py` or `master_full_rebuild.py`

---

### Database 2: `greenhouse_candidates_sp` (Human-Friendly)
**Purpose:** For human navigation with organized folder structure

**Resume Links Format:**
```
https://azureadmincooksys.sharepoint.com/.../2024/04_April/5201234008_John_Doe.pdf
```

**Folder Structure:**
```
Greenhouse_Resumes/
├── 2024/
│   ├── 01_January/
│   ├── 02_February/
│   └── ...
├── 2023/
└── ...
```

**Updated by:** `map_sharepoint_links.py` or master scripts

---

### Database 3: `greenhouse_candidates_ai` (AI-Friendly)
**Purpose:** For AI agents with flat folder structure

**Resume Links Format:**
```
https://azureadmincooksys.sharepoint.com/.../AI_Access/5201234008_John_Doe.pdf
```

**Folder Structure:**
```
AI_Access/
├── 5201234008_John_Doe.pdf
├── 5201234008_John_Doe_metadata.json
├── 5201235008_Jane_Smith.pdf
├── 5201235008_Jane_Smith_metadata.json
└── _master_index.json
```

**Special Features:**
- Flat structure (no subfolders)
- Metadata JSON files with extracted text
- Master index for quick lookups
- `metadata_url` field pointing to JSON files

**Updated by:** `map_ai_access_links.py` or master scripts

---

## 📊 CSV Export Options

The system provides **7 different CSV export options** optimized for different use cases.

**📘 Complete export guide:** [exports/README.md](greenhouse_sharepoint_mapper/exports/README.md)

### Quick Reference

| Export Script | Database | Size | Resume Content | Zapier OK | Best For |
|--------------|----------|------|----------------|-----------|----------|
| `export_ai_access_csv.py` | AI | ~33MB | ❌ | ✅ | **Zapier + API** |
| `export_ai_access_csv_full.py` | AI | ~500MB | ✅ | ❌ | Offline processing |
| `export_segmented_ai.py` | AI | <50MB ea | ❌ | ✅ | Zapier (segmented) |
| `export_segmented_ai_full.py` | AI | <50MB ea | ✅ | ✅ | Zapier with content |
| `export_incremental_ai.py` | AI | Varies | ❌ | ✅ | Weekly updates |
| `export_sharepoint_csv.py` | SP | ~33MB | ❌ | ✅ | Human navigation |
| `export_minimal_with_content.py` | AI | ~50MB | ✅ | ✅ | Minimal fields |

### Recommended Workflows

**For Zapier Tables (50MB limit):**
1. Initial: `export_segmented_ai.py` or `export_segmented_ai_full.py`
2. Weekly: `export_incremental_ai.py` (append mode)

**For Offline AI Processing:**
- Use `export_ai_access_csv_full.py` (includes all resume text)

**For API-Based AI Agents:**
- Use `export_ai_access_csv.py` + fetch resume_content via Greenhouse API

---

## 🔄 Regular Updates

### Option 1: Master Script (Recommended) ⭐

```bash
# Weekly/monthly incremental update
python3 master_incremental_update.py
```

**What it does:**
- Syncs new candidates
- Downloads new resumes
- Updates AI_Access folder
- Maps new SharePoint links
- Syncs resume_content
- Exports incremental CSV

**Time:** 30 min - 2 hours

---

### Option 2: Individual Scripts

If you need more control:

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

### Option 3: Verification First

Check what needs updating:

```bash
# Run comprehensive verification
python3 master_verify_integrity.py

# Or check specific status
cd utilities/verification
python check_ai_database_status.py
python comprehensive_database_check.py
```

---

## 🔧 Troubleshooting

**📘 For detailed troubleshooting, see [UPDATE_GUIDE.md](UPDATE_GUIDE.md#troubleshooting)**

### Quick Diagnostics

```bash
# Run comprehensive verification
python3 master_verify_integrity.py

# Check specific issues
cd utilities/investigation
python investigate_null_fields.py
python analyze_database_structure.py

# Analyze failed extractions
cd utilities/analysis
python analyze_failed_extractions.py
```

### Common Issues

**Database candidate counts don't match:**
```bash
# Check status first
python3 master_verify_integrity.py

# If coverage is low (<90%), run incremental update
python3 master_incremental_update.py

# If coverage is very low (<80%), run full rebuild
python3 master_full_rebuild.py
```

**Script fails with errors:**
```bash
# Check which step failed in master script output
# Run that specific script manually for more details
# Check utilities/verification/ for diagnostic scripts
```

**Missing resume_content:**
```bash
# This is normal (~7-14% gap due to unsupported formats)
# Run analysis to understand the gap
cd utilities/analysis
python analyze_failed_extractions.py
```

**SharePoint links showing "Invalid request token" errors:**
```bash
# CRITICAL: Always use permanent webUrl, never @microsoft.graph.downloadUrl
# The downloadUrl contains tempauth tokens that expire after 1-24 hours
# All scripts have been fixed to use webUrl (permanent links)

# If you encounter expired links in the database:
cd utilities/fixes
python fix_expired_sharepoint_links.py --dry-run  # Preview changes
python fix_expired_sharepoint_links.py            # Fix the links

# Verify the fix worked:
# Check that resume_links no longer contain "tempauth" tokens
```

**Zapier CSV upload fails with "invalid" error:**
```bash
# Issue: CSV fields with embedded newlines can break Zapier's parser
# Solution: Export uses QUOTE_ALL to quote every field

# The segmented export scripts have been optimized:
# - export_segmented_ai_full.py: Uses QUOTE_ALL, removes null bytes, truncates >100KB
# - Segments reduced from 27 to 14 (2x multiplier for efficiency)
# - All segments stay under 50MB for Zapier compatibility

# If a specific segment fails:
cd utilities/fixes
python fix_corrupted_segment.py <segment_number>
```

**Key Learnings - SharePoint Links:**
- ✅ **Always use `webUrl`** - Permanent links that never expire
- ❌ **Never use `@microsoft.graph.downloadUrl`** - Temporary links with expiring tokens
- Scripts fixed: `update_missing_resumes.py`, `map_ai_access_links.py`
- Database field: `resume_links` should contain permanent webUrl links only

**Key Learnings - CSV Exports:**
- Segmented exports optimized for Zapier (50MB limit)
- Use `quoting=1` (QUOTE_ALL) to prevent CSV parsing issues
- Remove null bytes (`\x00`) and truncate resume_content >100KB
- 2x multiplier reduces upload count while staying under limits

---

## 📚 Individual Project Details

### Project 1: greenhouse_candidate_dbBuilder
**Purpose:** Sync candidate data from Greenhouse API to PostgreSQL

**Core Scripts:**
- `main.py` - Pull candidates from API
- `setup.py` - Create database schema
- `status.py` - View sync statistics

**See:** `greenhouse_candidate_dbBuilder/README.md`

---

### Project 2: greenhouse_resume_downloader
**Purpose:** Download resume files from Greenhouse

**Core Scripts:**
- `download_resumes.py` - Download resumes
- `setup_audit_table.py` - Setup tracking
- `status.py` - View download progress

**See:** `greenhouse_resume_downloader/README.md`

---

### Project 3: greenhouse_resume_content_sync
**Purpose:** Extract resume text and store in Greenhouse

**Core Scripts:**
- `sync_resume_content.py` - Full sync (all candidates)
- `update_resume_content.py` - Incremental sync (new only)
- `sync_to_database.py` - Sync to local database
- `sync_from_sharepoint.py` - Sync from SharePoint

**See:** `greenhouse_resume_content_sync/README.md`

---

### Project 4: greenhouse_sharepoint_mapper
**Purpose:** Map resumes to SharePoint URLs

**Core Scripts:**
- `create_ai_access_folder.py` - Create flat folder
- `map_sharepoint_links.py` - Map human-friendly links
- `map_ai_access_links.py` - Map AI-friendly links
- `map_metadata_links.py` - Map metadata files
- `setup_sharepoint_db.py` - Setup databases

**Export Scripts:** See `exports/` folder (7 scripts)

**See:** `greenhouse_sharepoint_mapper/README.md`

---

## 🎯 Use Cases

### For Humans (Recruiters, HR)
**Use:** `greenhouse_candidates_sp` database
**Export:** `export_sharepoint_csv.py`
**Benefits:** Organized by date, easy to browse

### For AI Agents (ChatGPT, Zapier)
**Use:** `greenhouse_candidates_ai` database
**Export:** `export_ai_access_csv.py` or `export_segmented_ai.py`
**Benefits:** Flat structure, metadata files, API-friendly

### For Offline AI Processing
**Use:** `greenhouse_candidates_ai` database
**Export:** `export_ai_access_csv_full.py` or `export_segmented_ai_full.py`
**Benefits:** Includes full resume text in CSV

---

## 📊 Monitoring & Maintenance

### Weekly Maintenance
```bash
# 1. Run incremental update
python3 master_incremental_update.py

# 2. Verify data quality
python3 master_verify_integrity.py

# 3. Export and upload to Zapier
cd greenhouse_sharepoint_mapper/exports
python export_incremental_ai.py
# Upload to Zapier Tables (append mode)
```

### Monthly Maintenance
```bash
# 1. Run comprehensive verification
python3 master_verify_integrity.py

# 2. Review coverage statistics
# If coverage is good (>90%): Continue with weekly updates
# If coverage is fair (<90%): Run master_incremental_update.py
# If coverage is poor (<80%): Run master_full_rebuild.py

# 3. Save verification report
python3 master_verify_integrity.py > logs/verification_$(date +%Y%m%d).txt
```

---

## 🔐 Security Notes

- **Never commit `.env` files** to version control
- **API keys** stored in `.env` files (gitignored)
- **Azure credentials** have read-only SharePoint access
- **Database passwords** should be strong and rotated regularly

---

## 📞 Support & Documentation

**Master Scripts:**
- [MASTER_SCRIPTS_README.md](MASTER_SCRIPTS_README.md) - Complete guide to orchestration scripts

**Utilities:**
- [utilities/README.md](utilities/README.md) - Diagnostic and verification tools

**Exports:**
- [exports/README.md](greenhouse_sharepoint_mapper/exports/README.md) - Export scripts guide

**Updates:**
- [UPDATE_GUIDE.md](UPDATE_GUIDE.md) - Detailed update procedures

**Inventory:**
- [SCRIPT_INVENTORY.md](SCRIPT_INVENTORY.md) - Complete script catalog

---

## 📝 Version History

- **v1.0** - Initial setup with candidate sync and resume download
- **v2.0** - Added SharePoint integration with organized folders
- **v3.0** - Added AI-friendly flat folder structure and incremental updates
- **v4.0** - Added resume content extraction and Greenhouse custom field sync
- **v5.0** - 🆕 **Major reorganization with master orchestration scripts**
  - Added master scripts for automated workflows
  - Organized utilities into central folder
  - Consolidated export scripts
  - Comprehensive documentation updates

---

## 🎉 Quick Reference

### Most Common Commands

```bash
# Full rebuild (first time or major issues)
python3 master_full_rebuild.py

# Weekly/monthly updates
python3 master_incremental_update.py

# Verify data quality
python3 master_verify_integrity.py

# Check specific status
cd utilities/verification
python check_ai_database_status.py
python comprehensive_database_check.py
```

### File Locations

- **Master Scripts:** `greenhouseApps/` (root)
- **Utilities:** `greenhouseApps/utilities/`
- **Exports:** `greenhouseApps/greenhouse_sharepoint_mapper/exports/`
- **Resumes (Organized):** `OneDrive/AI Operator - Greenhouse_Resumes/2024/...`
- **Resumes (Flat):** `OneDrive/AI Operator - Greenhouse_Resumes/AI_Access/...`
- **CSV Exports (Database-Specific):**
  - AI Database: `greenhouse_sharepoint_mapper/exports/ai_database/`
  - SharePoint: `greenhouse_sharepoint_mapper/exports/sharepoint_database/`
  - Main DB: `greenhouse_sharepoint_mapper/exports/main_database/`

### API Access for AI Agents

- **Greenhouse API:** `https://harvest.greenhouse.io/v1/candidates/{id}`
- **Resume Content Field:** `custom_fields.resume_content`
- **Metadata URL:** Available in `greenhouse_candidates_ai` database

---

**Last Updated:** January 28, 2026 - v5.0 (Major Reorganization)
