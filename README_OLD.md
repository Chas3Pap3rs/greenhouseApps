# Greenhouse Apps - Complete System Documentation

A comprehensive suite of tools for syncing Greenhouse candidate data, downloading resumes, and creating AI-friendly SharePoint integrations.

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Complete Workflow](#complete-workflow)
- [Database Architecture](#database-architecture)
- [Regular Updates](#regular-updates)
- [Troubleshooting](#troubleshooting)
- [Individual Project Details](#individual-project-details)

**📘 For detailed update workflows, see [UPDATE_GUIDE.md](UPDATE_GUIDE.md)**

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
- **4 CSV Export Options** optimized for different use cases:
  - **SharePoint CSV** - Human-friendly links, no resume content (~25MB)
  - **AI Access CSV** - Lightweight, AI-friendly links, no resume content (~24MB, Zapier-compatible)
  - **AI Access CSV (Full)** - Includes resume content (~350MB, for SharePoint/large systems)
  - **dbBuilder CSV** - Raw candidate data, no resume content
- **Resume Content in Greenhouse** - Extracted text stored in custom fields (accessible via API)
- **Automated Update Pipeline** for incremental syncs

---

## 🚀 Quick Start

### First-Time Setup

1. **Set up databases and sync initial data:**
   ```bash
   cd greenhouse_candidate_dbBuilder
   source .venv/bin/activate
   python main.py --full-sync
   ```

2. **Download all resumes:**
   ```bash
   cd ../greenhouse_resume_downloader
   source .venv/bin/activate
   python download_resumes.py
   ```

3. **Create AI_Access folder and map SharePoint links:**
   ```bash
   cd ../greenhouse_sharepoint_mapper
   source .venv/bin/activate
   
   # Create flat folder structure (6-8 hours)
   python create_ai_access_folder.py
   
   # Map human-friendly links (6-7 hours)
   python map_sharepoint_links.py
   
   # Map AI-friendly links (6-7 hours)
   python map_ai_access_links.py
   
   # Export CSVs
   python export_sharepoint_csv.py              # Human-friendly, ~25MB
   python export_ai_access_csv.py               # AI-friendly, lightweight, ~24MB (Zapier-compatible)
   # python export_ai_access_csv_full.py        # Optional: Full version with resume_content, ~350MB
   ```

4. **Sync resume content to Greenhouse custom fields:**
   ```bash
   cd ../greenhouse_resume_content_sync
   source .venv/bin/activate
   
   # Initial full sync (1-2 hours)
   python sync_resume_content.py
   ```

### Regular Updates (After Initial Setup)

```bash
cd greenhouse_sharepoint_mapper
./run_full_update.sh
```

This single command runs all 6 steps automatically (5-15 minutes).

**📘 See [UPDATE_GUIDE.md](UPDATE_GUIDE.md) for complete update workflows and troubleshooting**

---

## 📁 Project Structure

```
greenhouseApps/
├── README.md                           # This file - Complete system documentation
├── UPDATE_GUIDE.md                     # Comprehensive update workflows for all projects
│
├── greenhouse_candidate_dbBuilder/     # Project 1: Candidate Data Sync
│   ├── main.py                         # Main script: Sync candidates from Greenhouse API
│   ├── setup.py                        # Setup script: Create database and schema
│   ├── status.py                       # Status checker: View sync progress and stats
│   ├── test_api.py                     # Testing: Verify Greenhouse API connection
│   ├── schema.sql                      # Database schema definition
│   ├── requirements.txt                # Python dependencies
│   ├── .env                            # Configuration: API keys and DB credentials
│   ├── .env.example                    # Template for .env file
│   ├── .gitignore                      # Git ignore rules
│   ├── README.md                       # Project-specific documentation
│   ├── exports/                        # Output: CSV exports
│   └── .venv/                          # Python virtual environment
│
├── greenhouse_resume_downloader/       # Project 2: Resume Downloader
│   ├── download_resumes.py             # Main script: Download resumes from Greenhouse
│   ├── setup_audit_table.py            # Setup script: Create audit tracking table
│   ├── status.py                       # Status checker: View download progress and stats
│   ├── requirements.txt                # Python dependencies
│   ├── .env                            # Configuration: API keys and paths
│   ├── .env.example                    # Template for .env file
│   ├── .gitignore                      # Git ignore rules
│   ├── README.md                       # Project-specific documentation
│   └── .venv/                          # Python virtual environment
│
├── greenhouse_sharepoint_mapper/       # Project 3: SharePoint Integration
│   │
│   ├── Core Scripts:
│   │   ├── graph_client.py             # Microsoft Graph API client (used by all scripts)
│   │   ├── setup_sharepoint_db.py      # Setup: Create SharePoint databases
│   │
│   ├── AI_Access Folder Management:
│   │   └── create_ai_access_folder.py  # Create flat folder with text extraction
│   │
│   ├── Human-Friendly Mapping (Organized Folders):
│   │   ├── map_sharepoint_links.py     # Full rebuild (6-7 hours)
│   │   └── update_sharepoint_links.py  # Incremental update (minutes)
│   │
│   ├── AI-Friendly Mapping (Flat Folder):
│   │   ├── map_ai_access_links.py      # Full rebuild (6-7 hours)
│   │   └── update_ai_access_links.py   # Incremental update (minutes)
│   │
│   ├── Maintenance Scripts:
│   │   ├── backfill_ai_access.py       # Backfill missing candidates to AI Access DB
│   │   └── update_missing_resumes.py   # Update candidates with NULL resume links
│   │
│   ├── Export Scripts:
│   │   ├── export_sharepoint_csv.py         # Human-friendly CSV (~25MB, no resume_content)
│   │   ├── export_ai_access_csv.py          # AI-friendly CSV (~24MB, lightweight, Zapier-compatible)
│   │   ├── export_ai_access_csv_full.py     # AI-friendly CSV (~350MB, includes resume_content)
│   │   ├── export_segmented_ai.py           # Segmented export (lightweight, <50MB each)
│   │   ├── export_segmented_ai_full.py      # Segmented export (with resume_content)
│   │   ├── export_incremental_ai.py         # Incremental export (new candidates only)
│   │   └── export_lightweight_csv.py        # Minimal CSV (candidate_id, name, email, resume_content)
│   │
│   ├── Status & Monitoring:
│   │   ├── check_sync_status.py        # Check both databases sync status
│   │   ├── check_mapping_status.py     # Check human-friendly mapping progress
│   │   └── status.py                   # Detailed status for all operations
│   │
│   ├── Automation:
│   │   └── run_full_update.sh          # One-command update pipeline (executable)
│   │
│   ├── Documentation:
│   │   ├── README.md                   # Project setup and configuration
│   │   └── UPDATE_GUIDE.md             # Detailed update workflows
│   │
│   ├── Configuration:
│   │   ├── .env                        # Azure/SharePoint credentials and paths
│   │   ├── .env.example                # Template for .env file
│   │   ├── .gitignore                  # Git ignore rules
│   │   ├── requirements.txt            # Python dependencies (core)
│   │   └── requirements_ai_access.txt  # Additional dependencies for text extraction
│   │
│   ├── Output:
│   │   ├── exports/                    # CSV exports with timestamped versions
│   │   └── segmented_exports/          # Segmented and incremental exports
│   │
│   └── .venv/                          # Python virtual environment
│
└── greenhouse_resume_content_sync/    # Project 4: Resume Content Extraction
    ├── sync_resume_content.py          # Full sync: Extract and populate ALL candidates
    ├── update_resume_content.py        # Incremental: Only new/changed candidates
    ├── requirements.txt                # Python dependencies
    ├── .env                            # Configuration: API keys and user ID
    ├── .env.example                    # Template for .env file
    ├── .gitignore                      # Git ignore rules
    ├── README.md                       # Project-specific documentation
    └── .venv/                          # Python virtual environment
```

### File Categories Explained

#### **Setup Scripts** (`setup*.py`)
- Run once during initial setup
- Create databases, schemas, and tables
- Safe to re-run (won't duplicate data)

#### **Main Scripts** (`main.py`, `download_resumes.py`, `map*.py`)
- Core functionality for each project
- Run regularly for syncing data
- Handle incremental updates automatically

#### **Status Scripts** (`status.py`, `check*.py`)
- Monitor progress and health
- View statistics and coverage
- Diagnose issues

#### **Update Scripts** (`update*.py`)
- Fast incremental updates (minutes)
- Only process new/changed data
- Use these for regular updates

#### **Configuration Files** (`.env`, `requirements.txt`)
- `.env` - Credentials and paths (never commit!)
- `.env.example` - Template for setup
- `requirements.txt` - Python package dependencies

#### **Documentation** (`README.md`, `UPDATE_GUIDE.md`)
- Setup instructions
- Usage examples
- Troubleshooting guides

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

### Step-by-Step Process

#### **Step 1: Sync Candidate Data**
- **Script:** `greenhouse_candidate_dbBuilder/main.py`
- **What it does:** Fetches candidate data from Greenhouse API
- **Output:** PostgreSQL database `greenhouse_candidates`
- **Time:** 5-10 minutes (incremental)

#### **Step 2: Download Resumes**
- **Script:** `greenhouse_resume_downloader/download_resumes.py`
- **What it does:** Downloads resume files from Greenhouse
- **Output:** Files in OneDrive organized by year/month
- **Time:** Varies (depends on # of new resumes)

#### **Step 3: Create AI_Access Folder**
- **Script:** `greenhouse_sharepoint_mapper/create_ai_access_folder.py`
- **What it does:** 
  - Copies all resumes to flat folder
  - Extracts text from PDFs/DOCX
  - Creates JSON metadata files
  - Generates master index
- **Output:** `AI_Access/` folder with 41k+ files
- **Time:** 6-8 hours (first run), minutes (updates)

#### **Step 4: Map Human-Friendly Links**
- **Script:** `update_sharepoint_links.py` (incremental) or `map_sharepoint_links.py` (full)
- **What it does:** Maps organized folder files to SharePoint URLs
- **Output:** PostgreSQL database `greenhouse_candidates_sp`
- **Time:** Minutes (incremental), 6-7 hours (full)

#### **Step 5: Map AI-Friendly Links**
- **Script:** `update_ai_access_links.py` (incremental) or `map_ai_access_links.py` (full)
- **What it does:** Maps flat folder files to SharePoint URLs
- **Output:** PostgreSQL database `greenhouse_candidates_ai`
- **Time:** Minutes (incremental), 6-7 hours (full)

#### **Step 6: Export CSVs**
- **Scripts:** 
  - `export_sharepoint_csv.py` - Human-friendly links, no resume_content (~25MB)
  - `export_ai_access_csv.py` - AI-friendly links, lightweight (~24MB, **Zapier-compatible**)
  - `export_ai_access_csv_full.py` - AI-friendly with resume_content (~350MB, for SharePoint)
  - `export_lightweight_csv.py` - Minimal fields with resume_content (~330MB)
- **What it does:** Exports database to CSV with different field combinations
- **Output:** CSV files in `exports/` folder
- **Time:** 1-2 minutes each
- **Use Cases:**
  - **Zapier Tables:** Use `export_ai_access_csv.py` (under 50MB limit)
  - **SharePoint/Large Systems:** Use `export_ai_access_csv_full.py` (includes resume text)
  - **AI Agents:** Use lightweight CSV + Greenhouse API for resume_content on demand

---

## 🗄️ Database Architecture

### Database 1: `greenhouse_candidates` (Source)
**Purpose:** Master database with raw Greenhouse data

**Key Fields:**
- `candidate_id` - Unique identifier
- `first_name`, `last_name`, `full_name`
- `email`, `phone_numbers`
- `resume_links` - S3 URLs from Greenhouse
- `employment_titles`, `employment_companies`
- `degrees`, `jobs_name`
- `created_at`, `updated_at`

**Updated by:** `dbBuilder/main.py`

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

**Updated by:** 
- Full: `map_sharepoint_links.py`
- Incremental: `update_sharepoint_links.py`

**Exported to:** `exports/latest_export.csv`

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

**Updated by:**
- Full: `map_ai_access_links.py`
- Incremental: `update_ai_access_links.py`

**Exported to:** `exports/latest_ai_export.csv`

---

## 📊 CSV Export Options

The system provides **4 different CSV export options** optimized for different use cases:

### 1. **SharePoint CSV** (`export_sharepoint_csv.py`)
- **Database:** `greenhouse_candidates_sp`
- **File Size:** ~25MB
- **Resume Links:** Human-friendly (organized by year/month)
- **Resume Content:** ❌ Not included
- **Best For:** Human navigation, manual lookups
- **Command:** `python export_sharepoint_csv.py`

### 2. **AI Access CSV - Lightweight** (`export_ai_access_csv.py`) ⭐ **Recommended for Zapier**
- **Database:** `greenhouse_candidates_ai`
- **File Size:** ~24MB
- **Resume Links:** AI-friendly (flat folder structure)
- **Resume Content:** ❌ Not included (fetch via Greenhouse API when needed)
- **Best For:** Zapier Tables, AI agents with API access
- **Zapier Compatible:** ✅ Yes (under 50MB limit)
- **Command:** `python export_ai_access_csv.py`
- **Fields:** candidate_id, name, email, phone, addresses, resume_url, metadata_url, employment, education, dates

### 3. **AI Access CSV - Full** (`export_ai_access_csv_full.py`)
- **Database:** `greenhouse_candidates_ai`
- **File Size:** ~350MB
- **Resume Links:** AI-friendly (flat folder structure)
- **Resume Content:** ✅ Included (full extracted resume text)
- **Best For:** SharePoint, large data systems, offline AI processing
- **Zapier Compatible:** ❌ No (exceeds 50MB limit)
- **Command:** `python export_ai_access_csv_full.py`
- **Fields:** Same as lightweight + resume_content

### 4. **Lightweight CSV** (`export_lightweight_csv.py`)
- **Database:** `greenhouse_candidates_ai`
- **File Size:** ~330MB
- **Resume Links:** ❌ Not included
- **Resume Content:** ✅ Included (full extracted resume text)
- **Best For:** Testing, minimal data with resume text
- **Zapier Compatible:** ❌ No (exceeds 50MB limit)
- **Command:** `python export_lightweight_csv.py`
- **Fields:** candidate_id, full_name, email, resume_content (only 4 fields)

### 📋 Quick Comparison Table

| Export Type | File Size | Resume Links | Resume Content | Zapier Compatible | Best Use Case |
|-------------|-----------|--------------|----------------|-------------------|---------------|
| SharePoint CSV | ~25MB | Human-friendly | ❌ | ✅ | Human navigation |
| AI Access (Lightweight) | ~24MB | AI-friendly | ❌ | ✅ | **Zapier + API** |
| AI Access (Full) | ~350MB | AI-friendly | ✅ | ❌ | SharePoint/Offline |
| Lightweight | ~330MB | ❌ | ✅ | ❌ | Testing only |

### 💡 Recommended Workflow for AI Agents

**For Zapier Tables (50MB limit):**
1. Upload `export_ai_access_csv.py` output to Zapier Tables
2. AI agent uses CSV for candidate metadata and SharePoint links
3. When resume text is needed, fetch via Greenhouse API:
   ```
   GET https://harvest.greenhouse.io/v1/candidates/{candidate_id}
   Custom Field: resume_content (ID: 11138961008)
   ```

**For SharePoint or No Size Limit:**
1. Use `export_ai_access_csv_full.py` for complete data
2. AI agent has immediate access to all resume text
3. No API calls needed

---

## 🔄 Regular Updates

**📘 For complete update workflows, see [UPDATE_GUIDE.md](UPDATE_GUIDE.md)**

### Option 1: Automated Pipeline (Recommended)

Run everything with one command:

```bash
cd greenhouse_sharepoint_mapper
./run_full_update.sh
```

**What it does:**
1. ✅ Syncs new candidates from Greenhouse
2. ✅ Downloads new resumes
3. ✅ Copies to AI_Access folder
4. ✅ Updates human-friendly SharePoint links
5. ✅ Updates AI-friendly SharePoint links
6. ✅ Exports both CSVs

**Time:** 5-15 minutes

---

### Option 2: Manual Step-by-Step

If you prefer control over each step:

```bash
# 1. Sync candidates
cd greenhouse_candidate_dbBuilder
source .venv/bin/activate
python main.py

# 2. Download resumes
cd ../greenhouse_resume_downloader
source .venv/bin/activate
python download_resumes.py

# 3. Update AI_Access folder
cd ../greenhouse_sharepoint_mapper
source .venv/bin/activate
python create_ai_access_folder.py

# 4. Update human-friendly links
python update_sharepoint_links.py

# 5. Update AI-friendly links
python update_ai_access_links.py

# 6. Export CSVs
python export_sharepoint_csv.py
python export_ai_access_csv.py
```

---

### Option 3: Check Status First

Before updating, check what needs to be synced:

```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate
python check_sync_status.py
```

This shows:
- Total candidates in each database
- Number with SharePoint links
- Last sync time and ID
- Recommendations for what to update

---

## 🔧 Troubleshooting

**📘 For detailed troubleshooting, see [UPDATE_GUIDE.md](UPDATE_GUIDE.md#troubleshooting)**

### Common Issues

#### "No new candidates to process"
✅ **This is normal!** It means you're already up to date.

#### Script fails with "401 Unauthorized"
❌ **Token expired.** The script will automatically refresh tokens, but if it persists:
- Check your Azure App Registration credentials in `.env`
- Ensure app has proper permissions

#### "File not found in SharePoint"
⚠️ **OneDrive sync issue.** 
- Check OneDrive sync status
- Wait for files to finish syncing
- Re-run the mapper script

#### Database connection errors
❌ **Check PostgreSQL:**
```bash
# Test connection
psql -d greenhouse_candidates -c "SELECT COUNT(*) FROM gh.candidates;"
```

#### Incremental update processes too many candidates
⚠️ **Sync tracking issue.**
- Check sync log tables
- Run `check_sync_status.py` to see last sync point
- If needed, manually update sync log

#### Database candidate counts don't match
⚠️ **Sync discrepancy.** Example: dbBuilder has 48,121 but AI Access has 44,689.

**Solution:**
```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate
python backfill_ai_access.py        # Add missing candidates
python update_missing_resumes.py    # Fix NULL resume links
```

#### Candidates have NULL resume links
⚠️ **Missing resume data.**

**Solution:**
```bash
cd greenhouse_sharepoint_mapper
python update_missing_resumes.py
```

This script:
- Searches for resumes in local folders
- Downloads from Greenhouse API with fresh URLs if not found
- Updates database with SharePoint links

#### Resume downloads fail with 403 Forbidden
⚠️ **Expired S3 URLs.** Greenhouse S3 URLs expire after ~7 days.

**Solution:** The maintenance scripts (`backfill_ai_access.py` and `update_missing_resumes.py`) automatically fetch fresh URLs from the Greenhouse API.

---

## 📚 Individual Project Details

### Project 1: greenhouse_candidate_dbBuilder

**Purpose:** Sync candidate data from Greenhouse API to PostgreSQL

**Key Features:**
- Incremental syncing (only new/updated candidates)
- Batch processing for efficiency
- Automatic schema creation
- CSV export capability

**Configuration:** `.env` file
```
GREENHOUSE_API_KEY=your_api_key
PGHOST=localhost
PGPORT=5432
PGDATABASE=greenhouse_candidates
PGUSER=your_user
PGPASSWORD=your_password
```

**See:** `greenhouse_candidate_dbBuilder/README.md` for details

---

### Project 2: greenhouse_resume_downloader

**Purpose:** Download resume files from Greenhouse to local OneDrive

**Key Features:**
- Downloads resumes from Greenhouse API
- Organizes by year/month folders
- Skips already-downloaded files
- Audit logging for tracking

**Configuration:** `.env` file
```
GREENHOUSE_API_KEY=your_api_key
LOCAL_RESUME_DIR=/path/to/OneDrive/Greenhouse_Resumes
PGHOST=localhost
PGDATABASE=greenhouse_candidates
```

**See:** `greenhouse_resume_downloader/README.md` for details

---

### Project 3: greenhouse_sharepoint_mapper

**Purpose:** Map local resumes to SharePoint URLs and create AI-friendly structure

**Key Features:**
- Microsoft Graph API integration
- Two database structures (human + AI)
- Incremental and full rebuild options
- Text extraction from PDFs/DOCX
- Automated update pipeline

**Configuration:** `.env` file
```
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
SHAREPOINT_SITE_ID=your_site_id
LOCAL_RESUME_DIR=/path/to/OneDrive/Greenhouse_Resumes
PGHOST=localhost
PGDATABASE=greenhouse_candidates_sp
```

**See:** 
- `greenhouse_sharepoint_mapper/README.md` for setup
- `greenhouse_sharepoint_mapper/UPDATE_GUIDE.md` for update workflows

---

### Project 4: greenhouse_resume_content_sync

**Purpose:** Extract resume text and store directly in Greenhouse custom fields for AI agent access

**Key Features:**
- Downloads and extracts text from resume attachments (PDF/DOCX)
- Stores extracted text in Greenhouse `resume_content` custom field
- Two modes: Full sync (all candidates) and Incremental (new/changed only)
- Automatic temp file cleanup
- Uses most recent resume when multiple exist
- No SharePoint dependency - direct API access

**Why Use This:**
- **Bypasses SharePoint access issues** - AI agents read directly from Greenhouse API
- **Single source of truth** - Resume content lives in Greenhouse
- **Faster for AI agents** - No file downloads, just JSON data
- **Automatic updates** - Detects new resumes and updates content

**Configuration:** `.env` file
```
GREENHOUSE_API_KEY=your_api_key
GREENHOUSE_USER_ID=your_user_id
GREENHOUSE_RESUME_CONTENT_FIELD_ID=11138961008
```

**Usage:**

```bash
# Initial full sync (processes ALL candidates, 1-2 hours)
cd greenhouse_resume_content_sync
source .venv/bin/activate
python sync_resume_content.py

# Weekly/monthly incremental updates (only new/changed, minutes)
python update_resume_content.py
```

**What Gets Updated:**
- Custom field: `resume_content` (Long Text)
- Contains: Full extracted text from most recent resume
- Accessible via: Greenhouse Harvest API `/candidates/{id}` endpoint

**For AI Agents:**
```json
GET https://harvest.greenhouse.io/v1/candidates/{id}

Response includes:
{
  "custom_fields": {
    "resume_content": "Full extracted resume text here..."
  }
}
```

**See:** `greenhouse_resume_content_sync/README.md` for detailed documentation

---

## 🎯 Use Cases

### For Humans (Recruiters, HR)
**Use:** `greenhouse_candidates_sp` database and CSV

**Benefits:**
- Organized folder structure by date
- Easy to browse and navigate
- Familiar file organization

**CSV Location:** `greenhouse_sharepoint_mapper/exports/latest_export.csv`

---

### For AI Agents (ChatGPT, Zapier Agents)

**Option 1: Resume Content in Greenhouse (Recommended)**
**Use:** Greenhouse Harvest API with `resume_content` custom field

**Benefits:**
- ✅ No SharePoint authentication required
- ✅ Direct API access - just read JSON
- ✅ Single source of truth in Greenhouse
- ✅ Fastest access method
- ✅ Automatic text extraction

**Setup:** Run `greenhouse_resume_content_sync/sync_resume_content.py` once

**Access:**
```
GET https://harvest.greenhouse.io/v1/candidates/{id}
→ custom_fields.resume_content
```

---

**Option 2: SharePoint Files with Metadata**
**Use:** `greenhouse_candidates_ai` database and CSV

**Benefits:**
- Flat folder structure (no nested paths)
- Direct file access URLs
- JSON metadata with extracted text
- Faster for programmatic access

**CSV Location:** `greenhouse_sharepoint_mapper/exports/latest_ai_export.csv`

**Upload to:** Zapier Tables for agent access

**Note:** Option 1 (Resume Content in Greenhouse) is recommended for most AI agent use cases as it eliminates SharePoint access complexity.

---

## 📊 Monitoring & Maintenance

### Daily/Weekly Checks

1. **Run automated update:**
   ```bash
   cd greenhouse_sharepoint_mapper
   ./run_full_update.sh
   ```

2. **Check sync status:**
   ```bash
   python check_sync_status.py
   ```

3. **Export and upload to Zapier Tables:**
   
   **Option A: Incremental Export (Recommended for weekly/monthly)**
   ```bash
   python export_incremental_ai.py
   # Upload only new candidates to Zapier (append mode)
   ```
   
   **Option B: Full Segmented Export (For complete refresh)**
   ```bash
   python export_segmented_ai.py
   # Upload all segments to Zapier
   ```

### Weekly/Monthly - Resume Content Updates

For AI agents using Greenhouse API (recommended):

```bash
cd greenhouse_resume_content_sync
source .venv/bin/activate
python update_resume_content.py
```

This updates:
- New candidates with resumes
- Existing candidates who uploaded new resumes
- Takes only minutes (not hours)

### Monthly Maintenance

1. **Verify OneDrive sync** is working properly
2. **Check database sizes** and performance
3. **Review error logs** for any issues
4. **Test AI agent access** to resumes
5. **Verify resume_content field** is populated for new candidates

### When to Run Full Rebuilds

Only run full rebuilds (`map_*.py` scripts) when:
- ❌ Major changes to folder structure
- ❌ Database corruption or data loss
- ❌ SharePoint site migration
- ❌ Initial setup

**Otherwise, use incremental updates!**

---

## 🔐 Security Notes

- **Never commit `.env` files** to version control
- **API keys** are stored in `.env` files (gitignored)
- **Azure credentials** have read-only SharePoint access
- **Database passwords** should be strong and rotated regularly

---

## 📞 Support

For issues or questions:
1. **Check [UPDATE_GUIDE.md](UPDATE_GUIDE.md)** for update workflows and troubleshooting
2. Check project-specific README files
3. Run `check_sync_status.py` to diagnose issues
4. Check error logs in terminal output

---

## 📝 Version History

- **v1.0** - Initial setup with candidate sync and resume download
- **v2.0** - Added SharePoint integration with organized folders
- **v3.0** - Added AI-friendly flat folder structure and incremental updates
- **v4.0** - Added resume content extraction and Greenhouse custom field sync

---

## 🎉 Quick Reference

### Most Common Commands

```bash
# Check status
cd greenhouse_sharepoint_mapper
python check_sync_status.py

# Run full update (incremental)
./run_full_update.sh

# Update resume content (for AI agents)
cd ../greenhouse_resume_content_sync
python update_resume_content.py

# Export CSVs only
cd ../greenhouse_sharepoint_mapper
python export_sharepoint_csv.py
python export_ai_access_csv.py
```

### File Locations

- **Resumes (Organized):** `OneDrive/AI Operator - Greenhouse_Resumes/2024/...`
- **Resumes (Flat):** `OneDrive/AI Operator - Greenhouse_Resumes/AI_Access/...`
- **CSV Exports:** `greenhouse_sharepoint_mapper/exports/`
- **Configuration:** Each project's `.env` file

### API Access for AI Agents

- **Greenhouse API:** `https://harvest.greenhouse.io/v1/candidates/{id}`
- **Resume Content Field:** `custom_fields.resume_content`
- **No authentication needed** for agents with API access

---

**Last Updated:** December 9, 2025
