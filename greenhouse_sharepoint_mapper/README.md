# Greenhouse SharePoint Mapper

Creates a duplicate candidate database with SharePoint links instead of original Greenhouse S3 URLs, ensuring AI agents have reliable access to resume files.

## Features

- Maps original candidate database to SharePoint-enabled version
- Generates proper SharePoint sharing links via Microsoft Graph API
- Creates `greenhouse_candidates_sp` database with same structure
- Exports CSV with format `gh_spCandidates_export_{type}_{MM.DD.YYYY}_{HH.MM.SS}.csv`
- Maintains all original candidate data with updated resume links
- Handles candidates without downloaded resumes (empty links)

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and configure:

```env
# Database connection (same as other projects)
PGHOST=localhost
PGPORT=5432
PGDATABASE=greenhouse_candidates_sp
PGUSER=chasepoulton
PGPASSWORD=

# Original database to map from
SOURCE_PGDATABASE=greenhouse_candidates

# Microsoft Graph API (from Azure App Registration)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# SharePoint configuration
SHAREPOINT_SITE_ID=sites/AIOperator
SHAREPOINT_BASE_URL=https://azureadmincooksys.sharepoint.com
RESUME_FOLDER_PATH=AI Operator - Greenhouse_Resumes

# Local resume directory (from downloader project)
LOCAL_RESUME_DIR=/Users/chasepoulton/Library/CloudStorage/OneDrive-CookSystems/AI Operator - Greenhouse_Resumes
```

### 3. Setup Database

```bash
python setup_sharepoint_db.py
```

### 4. Run Mapping

```bash
# Map all candidates to SharePoint version
python map_sharepoint_links.py

# Export CSV with SharePoint links
python export_sharepoint_csv.py

# Check status
python status.py
```

## File Structure

```
greenhouse_sharepoint_mapper/
├── Core Scripts:
│   ├── graph_client.py             # Microsoft Graph API client
│   ├── setup_sharepoint_db.py      # Database setup
│
├── Mapping Scripts:
│   ├── map_sharepoint_links.py     # Full rebuild (human-friendly)
│   ├── map_ai_access_links.py      # Full rebuild (AI-friendly)
│   ├── update_sharepoint_links.py  # Incremental update (human-friendly)
│   ├── update_ai_access_links.py   # Incremental update (AI-friendly)
│
├── Maintenance Scripts:
│   ├── backfill_ai_access.py       # Backfill missing candidates to AI Access DB
│   ├── update_missing_resumes.py   # Update candidates with missing resumes
│   ├── create_ai_access_folder.py  # Create/update AI_Access folder
│
├── Export Scripts:
│   ├── export_sharepoint_csv.py         # Human-friendly CSV
│   ├── export_ai_access_csv.py          # AI-friendly CSV (lightweight)
│   ├── export_ai_access_csv_full.py     # AI-friendly CSV (with resume_content)
│   ├── export_segmented_ai.py           # Segmented export (lightweight)
│   ├── export_segmented_ai_full.py      # Segmented export (with resume_content)
│   ├── export_incremental_ai.py         # Incremental export (new candidates only)
│
├── Status & Monitoring:
│   ├── status.py                   # Detailed status checker
│   ├── check_sync_status.py        # Check database sync status
│   ├── check_mapping_status.py     # Check mapping progress
│
├── Configuration:
│   ├── .env                        # Configuration
│   ├── .env.example               # Configuration template
│   ├── requirements.txt            # Dependencies
│   ├── README.md                  # This file
│   └── UPDATE_GUIDE.md            # Update workflows
│
└── Output:
    ├── exports/                   # CSV exports
    └── segmented_exports/         # Segmented CSV exports
```

## Database Schema

The `greenhouse_candidates_sp` database has identical structure to the original, with updated resume links:

```sql
-- Same fields as original database
candidate_id BIGINT PRIMARY KEY,
full_name TEXT,
email TEXT,
-- ... all other fields ...

-- Updated with SharePoint links
resume_links TEXT[],           -- SharePoint sharing URLs
resume_filenames TEXT[],       -- SharePoint filenames
raw JSONB                      -- Updated JSON with SP links
```

## Mapping Process

1. **Read Original Database**: Load all candidates from `greenhouse_candidates`
2. **Match Downloaded Files**: Find corresponding resume files in local SharePoint folder
3. **Generate SharePoint Links**: Use Graph API to create sharing links
4. **Update Database**: Insert mapped candidates into `greenhouse_candidates_sp`
5. **Export CSV**: Create AI-agent-ready CSV with SharePoint links

## SharePoint URL Format

Generated URLs will be proper SharePoint sharing links:
```
https://azureadmincooksys.sharepoint.com/:w:/s/AIOperator/[unique_token]?e=[access_token]
```

## AI Agent Compatibility

- **Reliable Access**: SharePoint links don't expire like S3 URLs
- **Permission-Based**: Uses your SharePoint site permissions
- **Direct Download**: AI agents can access resume content directly
- **Same CSV Format**: Drop-in replacement for existing exports

## Troubleshooting

- **Graph API errors**: Check Azure app registration permissions
- **SharePoint access**: Verify site permissions and folder structure
- **File matching**: Ensure resume downloader completed successfully
- **Database connection**: Verify PostgreSQL access and credentials

## Maintenance & Troubleshooting

### Database Sync Issues

If you notice discrepancies between `greenhouse_candidates` and `greenhouse_candidates_ai`:

**Backfill Missing Candidates:**
```bash
python backfill_ai_access.py
```
This script:
- Finds candidates in dbBuilder missing from AI Access
- Downloads resumes with fresh Greenhouse API URLs
- Copies to AI_Access folder
- Inserts into AI Access database

**Update Missing Resumes:**
```bash
python update_missing_resumes.py
```
This script:
- Finds candidates with NULL resume links
- Searches for existing resumes in local folders
- Downloads from Greenhouse API if not found
- Updates database with SharePoint URLs

### Incremental Exports

For weekly/monthly updates without re-exporting everything:

```bash
# First time - exports all candidates and saves tracking
python export_incremental_ai.py

# Subsequent runs - only exports NEW candidates
python export_incremental_ai.py

# Reset tracking for next full export
python export_incremental_ai.py --reset
```

## Prerequisites

- Completed resume download from `greenhouse_resume_downloader` project
- Azure App Registration with Graph API permissions
- SharePoint site access for "AI Operator" site
- PostgreSQL database access
- Greenhouse API key for fresh resume URL fetching
