# CSV Export Options - Complete Guide

This document explains all available CSV export options for the Greenhouse Apps system.

## 📋 Quick Reference Table

| Export Type | Script | Size | Resume Content | Zapier OK | Use Case |
|-------------|--------|------|----------------|-----------|----------|
| **Standard Exports** |
| dbBuilder | `main.py --export-only` | ~29MB | ❌ | ✅ | Standard candidate data |
| SharePoint | `export_sharepoint_csv.py` | ~25MB | ❌ | ✅ | Human-friendly links |
| AI Access (Light) | `export_ai_access_csv.py` | ~24MB | ❌ | ✅ | **Zapier + API** ⭐ |
| AI Access (Full) | `export_ai_access_csv_full.py` | ~350MB | ✅ | ❌ | SharePoint/Offline |
| **Incremental Exports** |
| Appending (dbBuilder) | `export_appending.py` | Varies | ❌ | ✅ | **New candidates only** ⭐ |
| Incremental (AI Access) | `export_incremental_ai.py` | Varies | ❌ | ✅ | **New AI candidates only** ⭐ |
| **Segmented Exports** |
| dbBuilder Segmented | `export_segmented.py` | <50MB each | ❌ | ✅ | **Multi-file Zapier** ⭐ |
| AI Segmented (Light) | `export_segmented_ai.py` | <50MB each | ❌ | ✅ | **Multi-file Zapier** ⭐ |
| AI Segmented (Full) | `export_segmented_ai_full.py` | >50MB each | ✅ | ❌ | SharePoint/Large systems |

---

## 🎯 Standard Exports

### 1. dbBuilder Export
**Location:** `greenhouse_candidate_dbBuilder/`

```bash
cd greenhouse_candidate_dbBuilder
source .venv/bin/activate
python main.py --export-only
```

**What it includes:**
- All candidate data from `greenhouse_candidates` database
- S3 resume links from Greenhouse
- Employment titles and companies (indexed with `|` separator)
- Degrees, jobs, contact info

**File size:** ~29MB  
**Zapier compatible:** ✅ Yes  
**Resume content:** ❌ No (fetch via API)

---

### 2. SharePoint CSV Export
**Location:** `greenhouse_sharepoint_mapper/`

```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate
python export_sharepoint_csv.py
```

**What it includes:**
- Human-friendly SharePoint links (organized by year/month)
- Same candidate data as dbBuilder
- Optimized for human navigation

**File size:** ~25MB  
**Zapier compatible:** ✅ Yes  
**Resume content:** ❌ No

---

### 3. AI Access CSV (Lightweight) ⭐ **Recommended for Zapier**
**Location:** `greenhouse_sharepoint_mapper/`

```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate
python export_ai_access_csv.py
```

**What it includes:**
- AI-friendly SharePoint links (flat folder structure)
- Metadata JSON URLs for text extraction
- Employment indexed with `|` separator
- All candidate metadata

**File size:** ~24MB  
**Zapier compatible:** ✅ Yes  
**Resume content:** ❌ No (fetch via Greenhouse API when needed)

**AI Agent Workflow:**
1. Load CSV into Zapier Tables
2. Use SharePoint links for resume files
3. Fetch `resume_content` via API:
   ```
   GET https://harvest.greenhouse.io/v1/candidates/{candidate_id}
   Custom Field: resume_content (ID: 11138961008)
   ```

---

### 4. AI Access CSV (Full)
**Location:** `greenhouse_sharepoint_mapper/`

```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate
python export_ai_access_csv_full.py
```

**What it includes:**
- Everything from lightweight version
- PLUS full `resume_content` text

**File size:** ~350MB  
**Zapier compatible:** ❌ No (exceeds 50MB limit)  
**Resume content:** ✅ Yes  
**Best for:** SharePoint, large systems, offline processing

---

## 🔄 Incremental Exports

### 5. Appending Export ⭐ **For Incremental Zapier Updates**
**Location:** `greenhouse_candidate_dbBuilder/`

```bash
cd greenhouse_candidate_dbBuilder
source .venv/bin/activate
python export_appending.py
```

**What it does:**
- Exports ONLY new candidates since last run
- Tracks last exported candidate_id automatically
- Perfect for appending to existing Zapier Tables

**File size:** Varies (depends on # of new candidates)  
**Zapier compatible:** ✅ Yes  
**Resume content:** ❌ No

**Usage Pattern:**
1. First run: Exports all candidates
2. Subsequent runs: Only exports new candidates
3. Upload each export to Zapier to append rows

**Reset tracking:**
```bash
python export_appending.py --reset
```

---

### 6. AI Access Incremental Export ⭐ **For Weekly/Monthly AI Updates**
**Location:** `greenhouse_sharepoint_mapper/`

```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate
python export_incremental_ai.py
```

**What it does:**
- Exports ONLY new candidates from AI Access database since last run
- Tracks last exported candidate_id automatically
- Perfect for appending to existing Zapier Tables
- Includes AI-friendly SharePoint links

**File size:** Varies (depends on # of new candidates)  
**Zapier compatible:** ✅ Yes  
**Resume content:** ❌ No

**Usage Pattern:**
1. First run: Exports all candidates and saves tracking
2. Subsequent runs: Only exports new candidates
3. Upload each export to Zapier to append rows

**Manual control:**
```bash
# Export since specific date
python export_incremental_ai.py --since 2025-01-01

# Export candidates after specific ID
python export_incremental_ai.py --since-id 49000000000

# Reset tracking
python export_incremental_ai.py --reset
```

**When to use:**
- Weekly/monthly Zapier Table updates
- After running backfill scripts
- When you only want new candidates, not full re-export

---

## 📦 Segmented Exports

### 7. dbBuilder Segmented Export ⭐ **For Large Zapier Uploads**
**Location:** `greenhouse_candidate_dbBuilder/`

```bash
cd greenhouse_candidate_dbBuilder
source .venv/bin/activate
python export_segmented.py
```

**What it does:**
- Splits all candidates into multiple CSV files
- Each file is under 50MB for Zapier compatibility
- Organized in timestamped folders

**Output:**
```
segmented_exports/
└── 2025.11.13_22.30.45/
    ├── segment_001_of_002.csv  (~45MB)
    ├── segment_002_of_002.csv  (~45MB)
    └── _manifest.txt
```

**File size:** <50MB per segment  
**Zapier compatible:** ✅ Yes  
**Resume content:** ❌ No

**Upload to Zapier:**
1. Upload segment_001 first
2. Then segment_002, segment_003, etc. in order
3. Each segment appends rows to your table

---

### 8. AI Segmented Export (Lightweight) ⭐ **For Zapier with SharePoint Links**
**Location:** `greenhouse_sharepoint_mapper/`

```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate
python export_segmented_ai.py
```

**What it does:**
- Same as AI Access CSV (lightweight)
- But split into <50MB segments
- Includes AI-friendly SharePoint links

**File size:** <50MB per segment  
**Zapier compatible:** ✅ Yes  
**Resume content:** ❌ No (fetch via API)

---

### 9. AI Segmented Export (Full)
**Location:** `greenhouse_sharepoint_mapper/`

```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate
python export_segmented_ai_full.py
```

**What it does:**
- Includes full `resume_content` text
- Split into segments (may still exceed 50MB)

**File size:** Varies (often >50MB per segment)  
**Zapier compatible:** ❌ No  
**Resume content:** ✅ Yes  
**Best for:** SharePoint, backup, archival

---

## 💡 Recommended Workflows

### For Zapier Tables (50MB Limit)

**Option 1: Single File (Best for most cases)**
```bash
cd greenhouse_candidate_dbBuilder
python main.py --export-only
# Upload to Zapier: exports/latest_export.csv (~29MB)
```

**Option 2: Incremental Updates (Best for ongoing sync)**
```bash
cd greenhouse_candidate_dbBuilder
python export_appending.py
# Upload to Zapier to append new rows only
```

**Option 3: Segmented (Best for initial large upload)**
```bash
cd greenhouse_candidate_dbBuilder
python export_segmented.py
# Upload segments in order: 001, 002, 003, etc.
```

---

### For SharePoint or Large Systems

**Full data with resume content:**
```bash
cd greenhouse_sharepoint_mapper
python export_ai_access_csv_full.py
# File: ~350MB with all resume text
```

---

### For AI Agents

**With API Access (Recommended):**
```bash
cd greenhouse_sharepoint_mapper
python export_ai_access_csv.py
# Lightweight CSV + fetch resume_content via API
```

**Without API Access:**
```bash
cd greenhouse_sharepoint_mapper
python export_ai_access_csv_full.py
# Full CSV with resume_content included
```

---

## 🔧 Employment Field Format

All exports now use **indexed employment fields** with `[0]`, `[1]`, `[2]` notation:

**Example:**
```
employment_titles: "Software Engineer[0], Senior Developer[1], Tech Lead[2]"
employment_companies: "Google[0], Microsoft[1], Amazon[2]"
```

This maintains the pairing:
- Position 0: Software Engineer at Google
- Position 1: Senior Developer at Microsoft
- Position 2: Tech Lead at Amazon

**In Zapier:** The index numbers make it crystal clear which title goes with which company. You can split by `, ` and parse the `[N]` index to match them up.

---

## 📊 File Locations

All exports are saved in `exports/` or `segmented_exports/` directories:

```
greenhouse_candidate_dbBuilder/
├── exports/
│   ├── latest_export.csv                    → Standard export
│   ├── latest_appending_export.csv          → Appending export
│   └── .last_appending_export               → Tracking file
└── segmented_exports/
    └── YYYY.MM.DD_HH.MM.SS/                 → Segmented exports
        ├── segment_001_of_NNN.csv
        ├── segment_002_of_NNN.csv
        └── _manifest.txt

greenhouse_sharepoint_mapper/
├── exports/
│   ├── latest_export.csv                    → SharePoint CSV
│   └── latest_ai_export.csv                 → AI Access CSV
└── segmented_exports/
    ├── YYYY.MM.DD_HH.MM.SS/                 → AI segmented (light)
    └── YYYY.MM.DD_HH.MM.SS_full/            → AI segmented (full)
```

---

## 🎯 Quick Decision Tree

**Need to upload to Zapier?**
- ✅ File under 50MB? → Use standard export
- ❌ File over 50MB? → Use segmented export or appending export

**Need resume text in CSV?**
- ✅ Yes → Use `_full` version (not Zapier-compatible)
- ❌ No → Use lightweight version + API

**Need only new candidates?**
- ✅ Yes → Use appending export
- ❌ No → Use standard or segmented export

**Need SharePoint links?**
- ✅ Yes → Use AI Access exports
- ❌ No → Use dbBuilder exports

---

## 📝 Notes

- All exports use timestamped filenames: `YYYY.MM.DD_HH.MM.SS`
- Symlinks (`latest_*.csv`) always point to most recent export
- Segmented exports include a `_manifest.txt` file with details
- Appending export tracks progress in `.last_appending_export` file
- Employment fields use `|` separator to maintain indexed pairing

---

**Last Updated:** December 9, 2025
