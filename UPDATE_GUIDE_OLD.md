# Greenhouse Apps - Update Guide

Complete guide for updating and maintaining all Greenhouse applications.

## 📋 Table of Contents

- [Quick Reference](#quick-reference)
- [Daily/Weekly Updates](#dailyweekly-updates)
- [Monthly Maintenance](#monthly-maintenance)
- [Individual App Updates](#individual-app-updates)
- [Full System Rebuild](#full-system-rebuild)
- [CSV Export Options](#csv-export-options)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Reference

### Most Common Update Scenarios

| Scenario | Command | Time | Frequency |
|----------|---------|------|-----------|
| **Everything (Recommended)** | `cd greenhouse_sharepoint_mapper && ./run_full_update.sh` | 5-15 min | Weekly |
| **Resume Content Only** | `cd greenhouse_resume_content_sync && python update_resume_content.py` | 2-5 min | Weekly/Monthly |
| **Candidate Data Only** | `cd greenhouse_candidate_dbBuilder && python main.py` | 2-5 min | As needed |
| **Check Status** | `cd greenhouse_sharepoint_mapper && python check_sync_status.py` | <1 min | Anytime |

---

## 📅 Daily/Weekly Updates

### Option 1: Automated Full Update (Recommended)

**Best for:** Regular maintenance, keeping everything in sync

```bash
cd greenhouse_sharepoint_mapper
./run_full_update.sh
```

**What it does:**
1. ✅ Syncs new candidates from Greenhouse API
2. ✅ Downloads new resume files
3. ✅ Updates AI_Access folder with new files
4. ✅ Maps human-friendly SharePoint links
5. ✅ Maps AI-friendly SharePoint links  
6. ✅ Exports both CSV files

**Time:** 5-15 minutes  
**Output:** Updated databases and CSV exports

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

## 🗓️ Monthly Maintenance

### Complete System Health Check

Run these commands monthly to ensure everything is working:

#### 1. Check Sync Status

```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate
python check_sync_status.py
```

**What to look for:**
- Total candidates in each database
- Number with SharePoint links
- Last sync timestamps
- Any gaps or issues

---

#### 2. Verify Resume Content Population

```bash
# Check a recent candidate in Greenhouse
curl -u "YOUR_API_KEY:" https://harvest.greenhouse.io/v1/candidates/CANDIDATE_ID | grep resume_content
```

**What to look for:**
- `resume_content` field is populated
- Text is readable and complete
- No truncation issues

---

#### 3. Test AI Agent Access

**For SharePoint approach:**
- Open latest CSV export
- Verify SharePoint links are accessible
- Test metadata JSON files

**For Greenhouse API approach:**
- Test API endpoint with a candidate ID
- Verify `custom_fields.resume_content` is populated
- Confirm text extraction quality

---

#### 4. Database Maintenance

```bash
# Check database sizes
psql -d greenhouse_candidates -c "SELECT COUNT(*) FROM gh.candidates;"
psql -d greenhouse_candidates_sp -c "SELECT COUNT(*) FROM gh.candidates;"
psql -d greenhouse_candidates_ai -c "SELECT COUNT(*) FROM gh.candidates;"
```

**What to look for:**
- All databases have similar candidate counts
- No major discrepancies
- Growth is consistent with new hires

---

#### 5. OneDrive Sync Verification

**Check:**
- OneDrive is running and synced
- No pending uploads in `Greenhouse_Resumes/`
- `AI_Access/` folder is up to date
- No sync errors in OneDrive

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
# Download new resumes only (default)
python download_resumes.py

# Check download status
python status.py
```

**Time:** Varies (depends on # of new resumes)

**Output:** Files in `OneDrive/Greenhouse_Resumes/YYYY/MM_Month/`

---

### App 3: SharePoint Mapper

**When to run:**
- After downloading new resumes
- Need updated CSV exports
- SharePoint links need updating

#### Quick Incremental Update

```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate

# Update AI_Access folder
python create_ai_access_folder.py

# Update human-friendly links
python update_sharepoint_links.py

# Update AI-friendly links
python update_ai_access_links.py

# Export CSVs
python export_sharepoint_csv.py
python export_ai_access_csv.py
```

**Time:** 5-10 minutes total

#### Full Rebuild (Rarely Needed)

```bash
# Only run if databases are corrupted or major changes
python map_sharepoint_links.py      # 6-7 hours
python map_ai_access_links.py       # 6-7 hours
```

**See:** `greenhouse_sharepoint_mapper/UPDATE_GUIDE.md` for detailed mapper workflows

---

### App 4: Resume Content Sync

**When to run:**
- Weekly/monthly for AI agent updates
- After new candidates added
- When resumes are updated

#### Incremental Update (Regular Use)

```bash
cd greenhouse_resume_content_sync
source .venv/bin/activate
python update_resume_content.py
```

**What it processes:**
- New candidates (no `resume_content`)
- Candidates with resumes newer than last update

**Time:** 2-5 minutes

---

#### Full Sync (Initial Setup or Rebuild)

```bash
python sync_resume_content.py
```

**What it processes:**
- ALL candidates with resumes
- Overwrites existing content

**Time:** 1-2 hours

**When to use:**
- Initial setup
- Fixing data issues
- Complete refresh needed

---

## 🔄 Full System Rebuild

**⚠️ Only run when absolutely necessary!**

### When to Rebuild

Run full rebuilds only for:
- ❌ Initial setup
- ❌ Database corruption or data loss
- ❌ Major folder structure changes
- ❌ SharePoint site migration
- ❌ Testing/development environments

### Full Rebuild Process

**Time Required:** 8-10 hours total

#### Step 1: Candidate Data (10-15 min)

```bash
cd greenhouse_candidate_dbBuilder
source .venv/bin/activate
python main.py --full-sync
```

---

#### Step 2: Download All Resumes (2-4 hours)

```bash
cd ../greenhouse_resume_downloader
source .venv/bin/activate
python download_resumes.py
```

---

#### Step 3: Create AI_Access Folder (6-8 hours)

```bash
cd ../greenhouse_sharepoint_mapper
source .venv/bin/activate
python create_ai_access_folder.py
```

**Note:** This is the longest step - extracts text from all resumes

---

#### Step 4: Map SharePoint Links (6-7 hours each)

```bash
# Human-friendly mapping
python map_sharepoint_links.py

# AI-friendly mapping  
python map_ai_access_links.py
```

---

#### Step 5: Export CSVs (2-3 min)

```bash
# Human-friendly CSV (~25MB)
python export_sharepoint_csv.py

# AI-friendly CSV - Lightweight (~24MB, Zapier-compatible)
python export_ai_access_csv.py

# Optional: AI-friendly CSV - Full with resume_content (~350MB)
# python export_ai_access_csv_full.py
```

**📊 See "CSV Export Options" section below for detailed comparison**

---

#### Step 6: Sync Resume Content (1-2 hours)

```bash
cd ../greenhouse_resume_content_sync
source .venv/bin/activate
python sync_resume_content.py
```

---

## 📊 CSV Export Options

The system provides **4 different CSV export options** to accommodate different file size limits and use cases:

### Quick Comparison

| Export Script | File Size | Resume Content | Zapier Compatible | Best For |
|---------------|-----------|----------------|-------------------|----------|
| `export_sharepoint_csv.py` | ~25MB | ❌ No | ✅ Yes | Human navigation |
| `export_ai_access_csv.py` | ~24MB | ❌ No | ✅ Yes | **Zapier + API** ⭐ |
| `export_ai_access_csv_full.py` | ~350MB | ✅ Yes | ❌ No | SharePoint/Offline |
| `export_lightweight_csv.py` | ~330MB | ✅ Yes | ❌ No | Testing only |

### When to Use Each Export

#### 1. **For Zapier Tables (50MB limit)** ⭐ Recommended

```bash
cd greenhouse_sharepoint_mapper
python export_ai_access_csv.py
```

**Use this when:**
- Uploading to Zapier Tables
- AI agents have Greenhouse API access
- Need lightweight file with all metadata
- Want SharePoint links for resume files

**AI Agent Workflow:**
1. Load CSV into Zapier Tables for candidate metadata
2. Use SharePoint links for resume file access
3. Fetch `resume_content` via Greenhouse API when needed:
   ```
   GET https://harvest.greenhouse.io/v1/candidates/{candidate_id}
   Custom Field: resume_content (ID: 11138961008)
   ```

---

#### 2. **For SharePoint or Large Systems**

```bash
cd greenhouse_sharepoint_mapper
python export_ai_access_csv_full.py
```

**Use this when:**
- No file size restrictions
- Want all data in one file
- Offline AI processing needed
- Don't want to make API calls

**Includes:**
- All candidate metadata
- SharePoint links
- Full resume_content text (extracted)

---

#### 3. **For Human Users**

```bash
cd greenhouse_sharepoint_mapper
python export_sharepoint_csv.py
```

**Use this when:**
- Recruiters need organized folder structure
- Human navigation by year/month
- Don't need resume text in CSV

---

#### 4. **For Testing Only**

```bash
cd greenhouse_sharepoint_mapper
python export_lightweight_csv.py
```

**Use this when:**
- Testing resume_content extraction
- Only need 4 fields: candidate_id, full_name, email, resume_content
- Not for production use

---

### Export Commands Summary

```bash
cd greenhouse_sharepoint_mapper
source .venv/bin/activate

# Choose ONE based on your needs:

# Option 1: Lightweight for Zapier (RECOMMENDED)
python export_ai_access_csv.py

# Option 2: Full version with resume_content
python export_ai_access_csv_full.py

# Option 3: Human-friendly links
python export_sharepoint_csv.py

# Option 4: Minimal testing export
python export_lightweight_csv.py
```

**💡 Tip:** The automated update script (`./run_full_update.sh`) runs `export_ai_access_csv.py` by default (lightweight version).

---

## 🔍 Troubleshooting

### Common Issues and Solutions

#### "No new candidates to process"

✅ **This is normal!** It means you're already up to date.

**To verify:**
```bash
cd greenhouse_sharepoint_mapper
python check_sync_status.py
```

---

#### Script fails with "401 Unauthorized"

❌ **Token expired or invalid credentials**

**Fix:**
1. Check `.env` file has correct API keys
2. For Azure/SharePoint: Token auto-refreshes, wait and retry
3. For Greenhouse API: Verify API key is valid
4. Check API key hasn't been rotated

**Test Greenhouse API:**
```bash
curl -u "YOUR_API_KEY:" https://harvest.greenhouse.io/v1/candidates?per_page=1
```

---

#### "File not found in SharePoint"

⚠️ **OneDrive sync issue**

**Fix:**
1. Check OneDrive is running and synced
2. Look for sync errors in OneDrive app
3. Wait for pending uploads to complete
4. Re-run the mapper script after sync completes

**Verify sync:**
- Open OneDrive folder in Finder
- Check for cloud icons (not synced) vs checkmarks (synced)

---

#### Database connection errors

❌ **PostgreSQL connection issue**

**Fix:**
1. Verify PostgreSQL is running:
   ```bash
   pg_isready
   ```

2. Test connection:
   ```bash
   psql -d greenhouse_candidates -c "SELECT 1;"
   ```

3. Check `.env` credentials:
   - `PGHOST`, `PGPORT`, `PGDATABASE`
   - `PGUSER`, `PGPASSWORD`

---

#### Resume content field not updating

❌ **API or field configuration issue**

**Troubleshooting:**

1. **Verify custom field exists:**
   ```bash
   curl -u "YOUR_API_KEY:" https://harvest.greenhouse.io/v1/candidates/CANDIDATE_ID
   ```
   Look for `custom_fields.resume_content`

2. **Check field ID is correct:**
   - Should be `11138961008` in `.env`
   - Verify in Greenhouse settings

3. **Check user ID for On-Behalf-Of:**
   - Should be `4371230008` (Chase Poulton)
   - User must have permission to edit candidates

4. **Review script logs:**
   ```bash
   tail -50 greenhouse_resume_content_sync/sync_output.log
   ```

---

#### Incremental update processes too many candidates

⚠️ **Sync tracking issue**

**Fix:**
1. Check sync log tables in database
2. Run status checker to see last sync point
3. Verify `last_processed_candidate_id` is correct

**For SharePoint mapper:**
```bash
cd greenhouse_sharepoint_mapper
python check_sync_status.py
```

---

#### Text extraction fails for certain resumes

⚠️ **File format or corruption issue**

**Common causes:**
- `.doc` files (only `.docx` supported)
- Password-protected PDFs
- Corrupted files
- Scanned PDFs (no text layer)

**Fix:**
- Script logs which files fail
- These candidates will be skipped
- Resume content will be empty for these candidates

---

#### SharePoint links return 404

❌ **File moved or deleted**

**Fix:**
1. Verify file exists in OneDrive folder
2. Check SharePoint site is accessible
3. Re-run mapper to refresh links:
   ```bash
   cd greenhouse_sharepoint_mapper
   python update_sharepoint_links.py
   python update_ai_access_links.py
   ```

---

## 📊 Monitoring Best Practices

### What to Monitor

#### Weekly Checks
- [ ] Run automated update (`./run_full_update.sh`)
- [ ] Check for script errors in output
- [ ] Verify new candidates were processed
- [ ] Update resume content for AI agents

#### Monthly Checks
- [ ] Run `check_sync_status.py`
- [ ] Verify database counts match
- [ ] Test AI agent access
- [ ] Check OneDrive sync health
- [ ] Review error logs

#### Quarterly Checks
- [ ] Database performance review
- [ ] Storage space check
- [ ] API key rotation (if needed)
- [ ] Update documentation if workflows changed

---

## 🎯 Update Strategy by Use Case

### For AI Agents Using Greenhouse API

**Recommended workflow:**
```bash
# Weekly
cd greenhouse_resume_content_sync
python update_resume_content.py
```

**Why:**
- Fastest update method
- No SharePoint dependency
- Direct API access for agents
- Only updates what's needed

---

### For AI Agents Using SharePoint Files

**Recommended workflow:**
```bash
# Weekly
cd greenhouse_sharepoint_mapper
./run_full_update.sh

# Upload new CSV to Zapier Tables
```

**Why:**
- Keeps SharePoint links current
- Updates metadata JSON files
- Provides CSV for Zapier integration

---

### For Human Users (Recruiters)

**Recommended workflow:**
```bash
# As needed
cd greenhouse_sharepoint_mapper
./run_full_update.sh
```

**Why:**
- Maintains organized folder structure
- Keeps human-friendly CSV updated
- Easy browsing by date

---

## 📞 Getting Help

### Diagnostic Steps

1. **Check status first:**
   ```bash
   cd greenhouse_sharepoint_mapper
   python check_sync_status.py
   ```

2. **Review recent logs:**
   ```bash
   # For resume content sync
   tail -100 greenhouse_resume_content_sync/sync_output.log
   
   # For other scripts, check terminal output
   ```

3. **Test individual components:**
   - Database connection
   - API access
   - OneDrive sync
   - File permissions

4. **Consult project-specific READMEs:**
   - `greenhouse_candidate_dbBuilder/README.md`
   - `greenhouse_resume_downloader/README.md`
   - `greenhouse_sharepoint_mapper/README.md`
   - `greenhouse_resume_content_sync/README.md`

---

## 📝 Update Checklist

Use this checklist for regular updates:

### Weekly Update
- [ ] Run `./run_full_update.sh` OR `update_resume_content.py`
- [ ] Check for errors in output
- [ ] Verify new candidates processed
- [ ] Upload new CSVs (if using SharePoint approach)

### Monthly Maintenance
- [ ] Run `check_sync_status.py`
- [ ] Verify database counts
- [ ] Test AI agent access
- [ ] Check OneDrive sync
- [ ] Review error logs
- [ ] Verify resume_content field population

### Quarterly Review
- [ ] Database performance check
- [ ] Storage space review
- [ ] API key rotation (if needed)
- [ ] Documentation updates
- [ ] Test full workflow end-to-end

---

**Last Updated:** November 10, 2025
