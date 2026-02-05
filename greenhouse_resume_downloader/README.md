# Greenhouse Resume Downloader

Downloads candidate resumes from Greenhouse and saves them to SharePoint for AI agent access.

## Features

- Downloads the most recent resume per candidate
- Intelligent file naming: `{candidate_id}_{full_name}_{created_at}.{ext}`
- Prefers PDF files when multiple resumes exist
- Tracks download status to avoid duplicates
- Handles authentication and rate limiting
- Supports both local testing and SharePoint sync

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
# Database connection (same as ETL project)
PGHOST=localhost
PGPORT=5432
PGDATABASE=greenhouse_candidates
PGUSER=chasepoulton
PGPASSWORD=

# Greenhouse API
GREENHOUSE_API_KEY=7c802e75606c15b0978c55063df2ff30-8

# Download settings
RESUME_SAVE_DIR=./downloads/resumes  # Local testing
# RESUME_SAVE_DIR=/Users/chasepoulton/Library/CloudStorage/OneDrive-CookSystems/Shared Documents/Resumes/Greenhouse  # SharePoint sync
```

### 3. Setup Database

```bash
python setup_audit_table.py
```

### 4. Run Downloads

```bash
# Test with local downloads first
python download_resumes.py

# Check status
python status.py
```

## File Structure

```
greenhouse_resume_downloader/
├── download_resumes.py      # Main download script
├── setup_audit_table.py    # Database setup
├── status.py               # Download status checker
├── requirements.txt        # Dependencies
├── .env                    # Configuration
├── .env.example           # Configuration template
├── README.md              # This file
└── downloads/             # Organized resume downloads
    ├── 2025/
    │   ├── 01_January/     # Resumes from January 2025
    │   ├── 02_February/    # Resumes from February 2025
    │   └── 10_October/     # Resumes from October 2025
    └── Failed_Downloads/   # Failed download attempts for troubleshooting
```

## Resume Selection Logic

1. **Prefer PDFs** when multiple resumes exist (better for AI agents)
2. **Most recent first** based on `created_at` timestamp
3. **Fallback to any format** if no PDFs available
4. **Skip candidates** with no resume attachments

## File Organization

Resumes are automatically organized by creation date for easy management:

### **Successful Downloads:**
```
AI Operator - Greenhouse_Resumes/
├── 2024/
│   ├── 01_January/
│   │   ├── 12345_John_Smith_20240115.pdf
│   │   └── 67890_Jane_Doe_20240128.docx
│   └── 12_December/
│       └── 11111_Bob_Johnson_20241205.pdf
├── 2025/
│   └── 10_October/
│       └── 22222_Alice_Brown_20251023.pdf
```

### **Failed Downloads:**
```
AI Operator - Greenhouse_Resumes/
└── Failed_Downloads/
    ├── FAILED_33333_Mike_Wilson_20241015.pdf
    └── FAILED_44444_Sarah_Davis_20241020.docx
```

**Benefits:**
- **Easy browsing** by time period
- **Separated failures** for troubleshooting
- **Scalable structure** for thousands of resumes
- **AI agent friendly** - clear organization for search

## SharePoint Integration

Once OneDrive is set up:

1. Find your SharePoint sync path (usually `~/Library/CloudStorage/OneDrive-[Tenant]/`)
2. Update `RESUME_SAVE_DIR` in `.env` to point to SharePoint folder
3. Resumes will automatically sync to SharePoint for AI agent access

## Troubleshooting

- **Authentication errors**: Check `GREENHOUSE_API_KEY` in `.env`
- **Database connection**: Ensure ETL database is accessible
- **Download failures**: Check `gh.resume_download_audit` table for error details
- **SharePoint sync**: Verify OneDrive client is running and syncing
