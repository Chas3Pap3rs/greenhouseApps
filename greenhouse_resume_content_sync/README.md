# Greenhouse Resume Content Sync

Automatically extract text from resume attachments and store in Greenhouse custom field for easy AI agent access.

## Three Scripts Available

1. **`sync_resume_content.py`** - Full sync (processes ALL candidates, overwrites existing)
2. **`update_resume_content.py`** - Incremental update (only new/changed candidates)
3. **`sync_from_sharepoint.py`** - Hybrid sync (fills gaps using SharePoint metadata)

## Overview

This tool solves the SharePoint content access issue by:
1. Fetching candidates from Greenhouse Harvest API
2. Downloading resume attachments (PDF/DOCX)
3. Extracting text content
4. Storing text in the `resume_content` custom field

**Benefits:**
- ✅ No SharePoint authentication issues
- ✅ Direct API access for your Zapier agent
- ✅ Single source of truth in Greenhouse
- ✅ Automatic text extraction
- ✅ No permanent local file storage

## Prerequisites

1. **Greenhouse Custom Field**: Create a custom field called `resume_content` (Long Text type)
2. **API Key**: Greenhouse Harvest API key with read/write permissions
3. **Python 3.8+**: With pip for installing dependencies

## Setup

### 1. Install Dependencies

```bash
cd greenhouse_resume_content_sync
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Add to your `.env` file in the project root:

```bash
# Greenhouse API
GREENHOUSE_API_KEY=your_api_key_here
```

**Note:** The API key should be Base64 encoded or the script will encode it automatically.

## Usage

### Initial Sync (All Candidates) - First Time Only

```bash
python sync_resume_content.py
```

**Use this for:**
- Initial population of all candidates
- Complete refresh/rebuild of all resume content
- Fixing data issues

**This will:**
- Fetch all candidates from Greenhouse
- Process ALL candidates with resume attachments
- **Overwrite existing resume_content** (including test data)
- Extract text from most recent resume
- Takes 1-2 hours for ~44K candidates

### Incremental Update - Weekly/Monthly

```bash
python update_resume_content.py
```

**Use this for:**
- Regular updates (weekly, monthly)
- Processing new candidates only
- Updating candidates with new resumes

**This will:**
- Fetch all candidates from Greenhouse
- **Only process candidates that need updates:**
  - New candidates (no resume_content)
  - Candidates with resumes newer than last update
- Skip candidates already up to date
- Much faster than full sync (minutes instead of hours)

---

### Hybrid Sync - Fill Gaps from SharePoint

```bash
python sync_from_sharepoint.py
```

**Use this for:**
- Filling gaps after initial full sync
- Candidates with .rtf, .doc, or other unsupported formats
- Leveraging pre-extracted text from SharePoint metadata

**This will:**
- Query database for candidates with SharePoint metadata URLs
- Check which candidates are missing resume_content in Greenhouse
- Download metadata JSON files from SharePoint
- Extract pre-extracted text from metadata
- Update Greenhouse resume_content field
- **Captures ~20K additional candidates** that direct extraction missed

**Why this works:**
- SharePoint metadata already has text extracted from .rtf/.doc files
- No need to add support for old file formats
- Reuses existing extraction work from `create_ai_access_folder.py`
- Complements direct extraction perfectly

**Time:** 2-4 hours (depends on SharePoint response time)

### Expected Output

```
[2025-11-10 16:00:00] ============================================================
[2025-11-10 16:00:00] GREENHOUSE RESUME CONTENT SYNC
[2025-11-10 16:00:00] ============================================================
[2025-11-10 16:00:00] Fetching candidates from Greenhouse API...
[2025-11-10 16:00:01]   Fetched page 1: 500 candidates (total: 500)
[2025-11-10 16:00:02]   Fetched page 2: 500 candidates (total: 1000)
[2025-11-10 16:00:03] ✅ Total candidates fetched: 1,234

[2025-11-10 16:00:03] Processing 1,234 candidates...

[2025-11-10 16:00:05]   📄 Processing 5199825008 (ramya v) - Ramya-Resume-April-2024.docx
[2025-11-10 16:00:06]   ✅ Extracted 15,234 characters of text
[2025-11-10 16:00:07]   ✅ Updated resume_content for 5199825008 (ramya v)

...

[2025-11-10 16:30:00] ============================================================
[2025-11-10 16:30:00] SYNC SUMMARY
[2025-11-10 16:30:00] ============================================================
[2025-11-10 16:30:00] Total candidates: 1,234
[2025-11-10 16:30:00] Successfully updated: 856
[2025-11-10 16:30:00] Already had content (skipped): 200
[2025-11-10 16:30:00] Failed to update: 12
[2025-11-10 16:30:00] No resume attachment: 166
```

## How It Works

### 1. Fetch Candidates
- Uses Greenhouse Harvest API v1
- Paginates through all candidates (500 per page)
- Gets detailed candidate info including custom fields

### 2. Check Existing Content
- Skips candidates that already have `resume_content`
- Only processes candidates with resume attachments
- Efficient incremental updates

### 3. Download & Extract
- Downloads resume to temporary file
- Extracts text using PyPDF2 (PDF) or python-docx (DOCX)
- **Automatically deletes temp file** after extraction
- No permanent local storage

### 4. Update Greenhouse
- Sends extracted text to `resume_content` custom field
- Truncates if text exceeds 50,000 characters
- Uses PATCH endpoint to update candidate

## For Your Zapier Agent

After running this sync, your agent can access resume content directly:

```json
GET https://harvest.greenhouse.io/v1/candidates/{id}

Response includes:
{
  "custom_fields": {
    "resume_content": "Full extracted resume text here..."
  }
}
```

**No more SharePoint file access needed!** 🎉

## Incremental Updates

The script automatically skips candidates that already have `resume_content`, making it safe to run multiple times:

- **First run**: Processes all candidates with resumes
- **Subsequent runs**: Only processes new candidates or those without content
- **No duplicates**: Existing content is preserved

## Troubleshooting

### API Authentication Errors
- Verify your `GREENHOUSE_API_KEY` in `.env`
- Ensure the key has read/write permissions
- Check that the key is properly formatted

### Text Extraction Failures
- Ensure PyPDF2 and python-docx are installed
- Some PDFs may be scanned images (no extractable text)
- Check file format is actually PDF or DOCX

### Rate Limiting
- Greenhouse API has rate limits
- Script includes error handling and will continue on failures
- Consider adding delays if you hit rate limits

## File Structure

```
greenhouse_resume_content_sync/
├── sync_resume_content.py    # Main sync script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Technical Details

- **API Version**: Greenhouse Harvest API v1
- **Authentication**: Basic Auth (API key as username)
- **Custom Field**: `resume_content` (Long Text)
- **Text Extraction**: PyPDF2 for PDF, python-docx for DOCX
- **Temp Files**: Auto-deleted after processing
- **Max Text Length**: 50,000 characters (configurable)

## Next Steps

1. Run the initial sync
2. Verify content in Greenhouse UI
3. Update your Zapier agent to use the `resume_content` field
4. Remove SharePoint dependencies from your workflow

## Support

For issues or questions, check:
- Greenhouse API docs: https://developers.greenhouse.io/harvest.html
- Script logs for detailed error messages
- Verify custom field name matches exactly: `resume_content`
