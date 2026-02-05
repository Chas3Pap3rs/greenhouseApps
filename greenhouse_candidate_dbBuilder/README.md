# Greenhouse Candidates ETL

A Python ETL pipeline that syncs candidate data from Greenhouse Harvest API to a local PostgreSQL database and exports it to CSV for Zapier Table uploads.

## Features

- **Incremental Sync**: Automatically syncs only new/updated candidates since last run
- **Full Backfill**: Option to sync all candidates from a specified date
- **Deduplication**: Uses candidate_id as primary key to prevent duplicates
- **Parallel Arrays**: Maintains index alignment for multi-value fields (resumes, employment history)
- **Zapier Compatible**: Exports CSV with exact column names expected by Zapier Tables
- **Rate Limiting**: Built-in exponential backoff for API rate limits
- **Robust Error Handling**: Comprehensive error handling and logging

## Quick Start

### 1. Prerequisites

- Python 3.8+
- PostgreSQL database named `greenhouse_candidates`
- Greenhouse Harvest API key

### 2. Installation

```bash
# Clone or download the project files
cd greenhouse_candidate_dbBuilder

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and update with your settings:

```bash
cp .env.example .env
```

Edit `.env` with your database and API credentials:

```env
# PostgreSQL connection
PGHOST=localhost
PGPORT=5432
PGDATABASE=greenhouse_candidates
PGUSER=chasepoulton
PGPASSWORD=your_password_here

# Greenhouse API
GREENHOUSE_API_KEY=7c802e75606c15b0978c55063df2ff30-8

# ETL settings
INITIAL_SINCE=2020-01-01T00:00:00Z
PAGE_SIZE=500
CSV_PATH=./candidates_export.csv
```

### 4. Database Setup

Run the setup script to create the database schema:

```bash
python setup.py
```

This will:
- Verify environment variables
- Test database connection
- Create the `gh.candidates` table with proper indexes
- Verify the schema was created correctly

### 5. Run the ETL

```bash
# Run incremental sync + CSV export
python main.py

# Force full sync from INITIAL_SINCE date
python main.py --full-sync

# Only export CSV from existing data
python main.py --export-only
```

### 📁 **Export Files**

CSV exports are automatically saved to the `exports/` directory with descriptive timestamps:
- **Format**: `gh_candidates_export_{type}_{MM.DD.YYYY}_{HH.MM.SS}.csv`
- **Types**: `full` (full sync) or `sync` (incremental sync)
- **Latest Symlink**: `exports/latest_export.csv` always points to the most recent export
- **Examples**: 
  - `gh_candidates_export_full_10.22.2025_22.50.37.csv`
  - `gh_candidates_export_sync_10.23.2025_08.15.30.csv`

This allows you to:
- Keep a history of all exports with clear sync type identification
- Easily identify when and what type of sync created each export
- Always access the latest export via the symlink

## Database Schema

The `gh.candidates` table stores:

| Column | Type | Description |
|--------|------|-------------|
| `candidate_id` | BIGINT | Primary key from Greenhouse |
| `first_name` | TEXT | Candidate's first name |
| `last_name` | TEXT | Candidate's last name |
| `full_name` | TEXT | Normalized full name |
| `email` | TEXT | Primary email address |
| `phone_numbers` | TEXT | Primary phone number |
| `addresses` | TEXT | Primary address |
| `resume_links` | TEXT[] | Array of resume URLs |
| `resume_filenames` | TEXT[] | Array of resume filenames |
| `employment_titles` | TEXT[] | Array of job titles |
| `employment_companies` | TEXT[] | Array of company names |
| `degrees` | TEXT[] | Array of education degrees |
| `jobs_name` | TEXT[] | Array of applied job names |
| `created_at` | TIMESTAMPTZ | Greenhouse creation timestamp |
| `updated_at` | TIMESTAMPTZ | Greenhouse update timestamp |
| `raw` | JSONB | Complete raw JSON from API |

## CSV Export Format

The exported CSV matches your Zapier Table structure:

| Column | Description | Source |
|--------|-------------|--------|
| `candidate_id` | Unique ID | From Greenhouse |
| `full_name` | Full name | `first_name + last_name` normalized |
| `email` | Email address | First email value |
| `phone_numbers` | Phone number | First phone value |
| `addresses` | Address | First address value |
| `created_at` | Created timestamp | Greenhouse created date |
| `updated_at` | Updated timestamp | Greenhouse updated date |
| `resume_links` | Resume URLs | Newline-separated list |
| `resume_filenames` | Resume filenames | Comma-separated list |
| `degrees` | Education degrees | Comma-separated list |
| `employment_titles` | Job titles | Comma-separated list |
| `employment_companies` | Company names | Comma-separated list |
| `jobs_name` | Applied jobs | Comma-separated list |

## Usage Examples

### Initial Full Sync
```bash
# Sync all candidates since 2020
python main.py --full-sync
```

### Incremental Updates (Run Anytime)
```bash
# Run weekly, monthly, or anytime - syncs all candidates updated since last run
python main.py
```

### Export Only
```bash
# Just export existing data to CSV
python main.py --export-only
```

## How It Works

### Incremental Sync Logic
1. **First Run**: Uses `INITIAL_SINCE` date to backfill all candidates
2. **Subsequent Runs**: Queries `MAX(updated_at)` from database and syncs only candidates updated since then (with 2-minute safety overlap)
3. **Deduplication**: Uses `ON CONFLICT (candidate_id) DO UPDATE` to handle duplicates

### Array Field Alignment
Multi-value fields are stored as parallel arrays where indices correspond:
- `resume_links[0]` matches `resume_filenames[0]`
- `employment_titles[0]` matches `employment_companies[0]`

### Rate Limiting
- Built-in exponential backoff for 429/5xx responses
- 200ms delay between API calls
- Configurable page size (max 500 per Greenhouse limits)

## Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Test connection manually
psql greenhouse_candidates -c "SELECT 1;"
```

**API Authentication Error**
- Verify your `GREENHOUSE_API_KEY` in `.env`
- Ensure the key has Harvest API permissions

**Missing Data**
- Check the `raw` JSONB column for complete API response
- Verify field mappings in `flatten_candidate()` function

**Performance Issues**
- Reduce `PAGE_SIZE` if hitting rate limits
- Add more delay between requests if needed

### Logs and Monitoring

The script provides detailed logging:
```
[2025-10-22 18:03:45] Starting candidate sync...
[2025-10-22 18:03:45] Starting incremental sync from 2025-10-20T16:03:45+00:00
[2025-10-22 18:03:46] Fetching page 1...
[2025-10-22 18:03:47] Processed 500 candidates (total: 500)
[2025-10-22 18:03:48] Sync completed! Total candidates processed: 1247
[2025-10-22 18:03:49] CSV export completed! 45123 rows exported to ./candidates_export.csv
```

## File Structure

```
greenhouse_candidate_dbBuilder/
├── main.py              # Main ETL script
├── setup.py             # Database setup script
├── test_api.py          # API connectivity test
├── status.py            # Database status checker
├── schema.sql           # Database schema
├── requirements.txt     # Python dependencies
├── .env                 # Configuration (create from .env.example)
├── .env.example         # Configuration template
├── README.md           # This file
├── exports/            # Timestamped CSV exports
│   ├── gh_candidates_export_{type}_{MM-DD-YYYY}_{HH-MM-SS}.csv
│   └── latest_export.csv # Symlink to latest export
└── images/             # Zapier setup screenshots
```

## Next Steps

1. **Schedule Regular Runs**: Set up a cron job or launchd task for daily syncs
2. **Monitor Data Quality**: Review the `raw` JSONB field for any missing mappings
3. **Zapier Upload**: Upload the generated CSV to your Zapier Table
4. **Optimize Performance**: Adjust `PAGE_SIZE` and delays based on your API limits

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify your `.env` configuration
3. Test database connectivity with `python setup.py`
4. Review the Greenhouse API documentation for field changes
