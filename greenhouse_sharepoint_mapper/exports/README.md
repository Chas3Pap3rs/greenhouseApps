# Export Scripts

This folder contains all CSV export scripts for the Greenhouse Apps system, organized by database.

## 📁 New Database-Specific Structure

Exports are now organized into database-specific subfolders for better clarity:

```
exports/
├── ai_database/              # greenhouse_candidates_ai
│   ├── full/                 # Single file exports
│   ├── segmented/            # Segmented exports (timestamped folders)
│   └── incremental/          # Incremental exports (timestamped folders)
├── sharepoint_database/      # greenhouse_candidates_sp
│   └── full/                 # SharePoint exports
├── main_database/            # greenhouse_candidates (from dbBuilder)
│   └── segmented/            # Main DB segmented exports
├── latest_ai_export.csv      # Symlink to latest AI export
├── latest_export.csv         # Symlink to latest SharePoint export
└── latest_lightweight_export.csv  # Symlink to latest lightweight export
```

**Benefits:**
- ✅ Immediately clear which database each export comes from
- ✅ Organized by export type (full, segmented, incremental)
- ✅ Easier to find and manage exports
- ✅ Better for automation and scripting

---

## Export Scripts Overview

### Single File Exports (AI Database)

#### `export_ai_access_csv.py`
**Purpose:** Lightweight AI Access export WITHOUT resume_content  
**Database:** greenhouse_candidates_ai  
**Size:** ~33MB  
**Resume Content:** ❌ No (fetch via Greenhouse API when needed)  
**Fields:** Comprehensive metadata (candidate_id, names, contact info, resume_url, metadata_url, employment history)  
**Use Case:** AI agents that fetch resume_content on-demand via API  
**Command:** `python export_ai_access_csv.py`

#### `export_ai_access_csv_full.py`
**Purpose:** Full AI Access export WITH resume_content  
**Database:** greenhouse_candidates_ai  
**Size:** Large (~500MB+)  
**Resume Content:** ✅ Yes (included in CSV)  
**Fields:** All fields including full resume text  
**Use Case:** Offline processing, backup, systems that need resume_content in CSV  
**Command:** `python export_ai_access_csv_full.py`

#### `export_minimal_with_content.py`
**Purpose:** Ultra-minimal export with only essential fields  
**Database:** greenhouse_candidates_ai  
**Size:** Small (~50MB)  
**Resume Content:** ✅ Yes (included in CSV)  
**Fields:** Only 4 fields (candidate_id, full_name, email, resume_content)  
**Use Case:** When you only need basic info + resume text, minimal data transfer  
**Command:** `python export_minimal_with_content.py`

---

### Segmented Exports (AI Database - Zapier Compatible)

#### `export_segmented_ai.py`
**Purpose:** Segmented lightweight export WITHOUT resume_content  
**Database:** greenhouse_candidates_ai  
**Size:** Multiple files, each <50MB  
**Resume Content:** ❌ No  
**Segments:** Auto-calculated based on data size  
**Use Case:** Zapier Tables upload (50MB limit), lightweight segmented data  
**Command:** `python export_segmented_ai.py`  
**Output:** `segmented_exports/YYYY.MM.DD_HH.MM.SS/segment_001_of_XXX.csv`

#### `export_segmented_ai_full.py` ⭐ OPTIMIZED
**Purpose:** Segmented full export WITH resume_content  
**Database:** greenhouse_candidates_ai  
**Size:** Multiple files, each <50MB  
**Resume Content:** ✅ Yes  
**Segments:** ~14 segments (optimized with 2x multiplier)  
**Use Case:** Zapier Tables with resume_content, offline processing in chunks  
**Command:** `python export_segmented_ai_full.py`  
**Output:** `ai_database/segmented/YYYY.MM.DD_HH.MM.SS_full/segment_001_of_XXX_full.csv`

**Recent Optimizations (Feb 2026):**
- ✅ **2x multiplier** - Reduced from 27 to 14 segments for faster uploads
- ✅ **QUOTE_ALL** - All CSV fields quoted to prevent Zapier parsing errors
- ✅ **Null byte removal** - Cleans `\x00` characters that corrupt CSV
- ✅ **Content truncation** - Limits resume_content to 100KB max
- ✅ **Newlines preserved** - Resume content remains human-readable
- ✅ **Permanent SharePoint links** - All links use `webUrl` (never expire)

---

### Incremental Exports (AI Database)

#### `export_incremental_ai.py`
**Purpose:** Export only NEW or UPDATED candidates since last export  
**Database:** greenhouse_candidates_ai  
**Size:** Varies (depends on changes since last run)  
**Resume Content:** ❌ No  
**Tracking:** Uses timestamp from last export to identify new/updated records  
**Use Case:** Daily/weekly updates, append to existing Zapier Tables  
**Command:** `python export_incremental_ai.py`  
**Output:** `segmented_exports/YYYY.MM.DD_HH.MM.SS_incremental/segment_001_of_XXX_incremental.csv`

**⚠️ Important:** First run creates baseline (full export). Subsequent runs only export changes.

---

### SharePoint Database Export

#### `export_sharepoint_csv.py`
**Purpose:** Export from SharePoint-specific database  
**Database:** greenhouse_candidates_sp  
**Size:** ~33MB  
**Resume Content:** ❌ No  
**Fields:** SharePoint-specific fields (resume_links with SharePoint URLs)  
**Use Case:** SharePoint database verification, SP-specific data needs  
**Command:** `python export_sharepoint_csv.py`

---

## Export Decision Guide

### Choose Your Export Based on Need:

**For Zapier Tables (50MB limit):**
- Without resume_content: `export_segmented_ai.py`
- With resume_content: `export_segmented_ai_full.py`

**For AI Agents (API-based resume_content fetching):**
- Single file: `export_ai_access_csv.py`
- Segmented: `export_segmented_ai.py`

**For Offline Processing (need resume_content in CSV):**
- Single file: `export_ai_access_csv_full.py`
- Segmented: `export_segmented_ai_full.py`

**For Minimal Data Transfer:**
- `export_minimal_with_content.py` (only 4 fields + resume_content)

**For Regular Updates:**
- First time: Run full export (`export_segmented_ai.py` or `export_ai_access_csv.py`)
- Ongoing: Run `export_incremental_ai.py` for new/updated candidates only

**For SharePoint Database:**
- `export_sharepoint_csv.py`

---

## Export Locations

All exports are now saved to database-specific subfolders:

**AI Database Exports:**
- Single file exports: `exports/ai_database/full/`
- Segmented exports: `exports/ai_database/segmented/YYYY.MM.DD_HH.MM.SS/`
- Incremental exports: `exports/ai_database/incremental/YYYY.MM.DD_HH.MM.SS_incremental/`

**SharePoint Database Exports:**
- Single file exports: `exports/sharepoint_database/full/`

**Main Database Exports:**
- Segmented exports: `exports/main_database/segmented/`

Each segmented export creates a timestamped folder with:
- Segment files: `segment_001_of_XXX.csv`, `segment_002_of_XXX.csv`, etc.
- Manifest file: `_manifest.txt` (lists all segments and metadata)

---

## Common Export Workflows

### Initial Setup (First Time)
```bash
# For Zapier Tables without resume_content
cd greenhouse_sharepoint_mapper/exports
python export_segmented_ai.py

# For Zapier Tables with resume_content
python export_segmented_ai_full.py

# For single file (no size limit)
python export_ai_access_csv.py
```

### Weekly Updates
```bash
# Export only new/updated candidates
python export_incremental_ai.py

# Upload the incremental segments to Zapier Tables (append mode)
```

### Full Refresh
```bash
# Re-export everything
python export_segmented_ai.py  # or export_segmented_ai_full.py

# Replace all data in Zapier Tables
```

### Verification After Export
```bash
# Check database status
cd ../../utilities/verification
python check_ai_database_status.py

# Verify exports in new structure
ls -lh ai_database/full/
ls -lh ai_database/segmented/
ls -lh sharepoint_database/full/
```

---

## Export File Naming Convention

**Single Files:**
- `gh_aiCandidates_export_sync_MM.DD.YYYY_HH.MM.SS.csv`
- `latest_ai_export.csv` (symlink to most recent)

**Segmented Files:**
- Folder: `segmented_exports/YYYY.MM.DD_HH.MM.SS/` or `YYYY.MM.DD_HH.MM.SS_full/`
- Files: `segment_001_of_XXX.csv`, `segment_002_of_XXX.csv`, etc.
- Manifest: `_manifest.txt`

**Incremental Files:**
- Folder: `segmented_exports/YYYY.MM.DD_HH.MM.SS_incremental/`
- Files: `segment_001_of_XXX_incremental.csv`

---

## Troubleshooting

**Export fails with memory error:**
- Use segmented exports instead of single file exports
- Segmented exports process data in chunks

**Segments are too large (>50MB):**
- Script auto-adjusts segment size
- If still too large, check for unusually large resume_content fields

**Incremental export shows all candidates:**
- This is expected on first run (creates baseline)
- Subsequent runs will only export new/updated candidates

**Missing resume_content in export:**
- Check which export script you're using
- Scripts without "full" in name exclude resume_content by design
- Use `export_ai_access_csv_full.py` or `export_segmented_ai_full.py` for resume_content

---

## Performance Notes

**Export Times (approximate for 50,000 candidates):**
- `export_ai_access_csv.py`: ~2 seconds (no resume_content)
- `export_ai_access_csv_full.py`: ~5 seconds (with resume_content)
- `export_segmented_ai.py`: ~3 seconds (creates 1 segment)
- `export_segmented_ai_full.py`: ~15 seconds (creates 20-30 segments)
- `export_incremental_ai.py`: Varies (depends on changes since last run)

**File Sizes (approximate for 50,000 candidates):**
- Without resume_content: ~33MB
- With resume_content: ~500MB (varies based on resume lengths)
- Segmented files: Each <50MB (auto-calculated)
