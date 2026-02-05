# Greenhouse SharePoint Update Guide

## 🚀 Quick Update (Incremental - Use This Regularly)

For daily/weekly updates when you just need to sync new candidates:

```bash
cd greenhouse_sharepoint_mapper
./run_full_update.sh
```

This runs all 6 steps automatically:
1. ✅ Sync new candidates from Greenhouse
2. ✅ Download new resumes
3. ✅ Copy to AI_Access folder
4. ✅ Map human-friendly SharePoint links
5. ✅ Map AI-friendly SharePoint links
6. ✅ Export both CSVs

**Time:** ~5-15 minutes (depending on # of new candidates)

---

## 🔄 Manual Step-by-Step Update

If you prefer to run each step manually:

### 1. Update Candidate Data
```bash
cd greenhouse_candidate_dbBuilder
source .venv/bin/activate
python main.py
```

### 2. Download New Resumes
```bash
cd ../greenhouse_resume_downloader
source .venv/bin/activate
python download_resumes.py
```

### 3. Copy to AI_Access Folder
```bash
cd ../greenhouse_sharepoint_mapper
source .venv/bin/activate
python create_ai_access_folder.py
```

### 4. Update Human-Friendly Links
```bash
python update_sharepoint_links.py
```

### 5. Update AI-Friendly Links
```bash
python update_ai_access_links.py
```

### 6. Export CSVs
```bash
python export_sharepoint_csv.py  # Human-friendly
python export_ai_access_csv.py   # AI-friendly
```

---

## 🔨 Full Rebuild (Use Only When Needed)

If you need to completely rebuild the SharePoint mappings (e.g., after major changes):

### Human-Friendly Database
```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate
python map_sharepoint_links.py  # Takes 6-7 hours
python export_sharepoint_csv.py
```

### AI-Friendly Database
```bash
python map_ai_access_links.py   # Takes 6-7 hours
python export_ai_access_csv.py
```

**⚠️ Warning:** Full rebuilds take 6-7 hours each. Only use when necessary!

---

## 📊 Databases

You have **3 databases**:

1. **`greenhouse_candidates`** (Original)
   - Source data from Greenhouse API
   - S3 resume links
   - Updated by: `dbBuilder/main.py`

2. **`greenhouse_candidates_sp`** (Human-Friendly)
   - Organized folder structure: `2024/04_April/...`
   - For human navigation
   - Updated by: `update_sharepoint_links.py` (incremental) or `map_sharepoint_links.py` (full)

3. **`greenhouse_candidates_ai`** (AI-Friendly)
   - Flat folder structure: `AI_Access/...`
   - For AI agents
   - Updated by: `update_ai_access_links.py` (incremental) or `map_ai_access_links.py` (full)

---

## 📁 Output Files

CSVs are exported to: `greenhouse_sharepoint_mapper/exports/`

- **Human-friendly:** `latest_export.csv`
- **AI-friendly:** `latest_ai_export.csv`

Both include timestamped versions for history.

---

## 🔧 Maintenance Scripts

### Database Sync Issues

If databases are out of sync (e.g., dbBuilder has 48,121 but AI Access has 44,689):

#### Backfill Missing Candidates
```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate
python backfill_ai_access.py
```

**What it does:**
- Finds candidates in `greenhouse_candidates` missing from `greenhouse_candidates_ai`
- Downloads resumes using fresh Greenhouse API URLs (avoids expired S3 links)
- Copies resumes to AI_Access folder
- Inserts candidates into AI Access database

**When to use:** After discovering candidate count discrepancies

---

#### Update Missing Resumes
```bash
python update_missing_resumes.py
```

**What it does:**
- Finds candidates with NULL resume_links in AI Access database
- Searches for resumes in local folders
- Downloads from Greenhouse API if not found locally
- Updates database with SharePoint URLs

**When to use:** After backfill or when candidates have NULL resume links

---

## 📦 Incremental CSV Exports

### For Weekly/Monthly Updates

Instead of re-exporting all 48,000+ candidates, export only NEW ones:

```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate
python export_incremental_ai.py
```

**First Run:**
- Exports all candidates
- Saves max candidate_id to tracking file

**Subsequent Runs:**
- Only exports candidates added since last export
- Creates segments ready to append to Zapier Tables

**Upload to Zapier:**
1. Upload incremental segments in append mode
2. No need to re-upload existing data

**Reset Tracking (for next full export):**
```bash
python export_incremental_ai.py --reset
```

**Manual Control:**
```bash
# Export since specific date
python export_incremental_ai.py --since 2025-01-01

# Export candidates after specific ID
python export_incremental_ai.py --since-id 49000000000
```

---

## 💡 Tips

- **Use incremental updates** (`update_*.py`) for regular syncs
- **Use full rebuilds** (`map_*.py`) only when needed
- **Run `./run_full_update.sh`** for one-command updates
- **Check logs** for any errors during processing
- **Upload CSVs to Zapier Tables** after each update
- **Use incremental exports** for weekly/monthly Zapier updates (saves time)
- **Run maintenance scripts** if you notice database discrepancies

---

## 🆘 Troubleshooting

### "No new candidates to process"
✅ This is normal! It means you're already up to date.

### Script fails partway through
- Check the error message
- You can safely re-run the script - it will skip already-processed candidates

### Need to force a full rebuild
- Run the full rebuild scripts (`map_*.py`) instead of incremental (`update_*.py`)

### Database candidate counts don't match
❌ **Problem:** dbBuilder has more candidates than AI Access

✅ **Solution:**
```bash
python backfill_ai_access.py
python update_missing_resumes.py
```

### Candidates have NULL resume links
❌ **Problem:** Some candidates in AI Access have no resume URLs

✅ **Solution:**
```bash
python update_missing_resumes.py
```

### Resume download fails with 403 Forbidden
❌ **Problem:** S3 URLs expired (they expire after ~7 days)

✅ **Solution:** The backfill and update scripts automatically fetch fresh URLs from Greenhouse API

### Zapier file too large (>50MB)
❌ **Problem:** Full export exceeds Zapier's 50MB limit

✅ **Solution:** Use segmented or incremental exports:
```bash
python export_segmented_ai.py        # Split into <50MB segments
python export_incremental_ai.py      # Only new candidates
```
