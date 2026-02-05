# Resume Content Setup Guide

This document explains how `resume_content` is handled in the dbBuilder database.

## 📋 Two Approaches Available

### ✅ **Permanent Solution (Recommended for Future)**
**File:** `main.py` (modified)

The dbBuilder now automatically fetches `resume_content` from Greenhouse API during sync.

**How it works:**
1. When syncing candidates from Greenhouse API, the script extracts `resume_content` from custom fields
2. Custom field ID: `11138961008` (configurable via `RESUME_CONTENT_FIELD_ID` env var)
3. Data is stored directly in `greenhouse_candidates` database during upsert
4. No additional sync step needed

**Usage:**
```bash
cd greenhouse_candidate_dbBuilder
source .venv/bin/activate

# Regular incremental sync (includes resume_content)
python main.py

# Full sync from scratch (includes resume_content)
python main.py --full-sync
```

**Benefits:**
- ✅ Single source of truth (Greenhouse API)
- ✅ Automatic updates during regular syncs
- ✅ No manual intervention needed
- ✅ Always in sync with Greenhouse

---

### 🔧 **Temporary Solution (Currently Active)**
**File:** `sync_resume_content_temp.py`

One-time script to copy `resume_content` from `greenhouse_candidates_ai` to `greenhouse_candidates`.

**How it works:**
1. Adds `resume_content` column to `greenhouse_candidates` if it doesn't exist
2. Copies data from `greenhouse_candidates_ai` database
3. Updates 37,672+ candidates with resume text

**Usage:**
```bash
cd greenhouse_candidate_dbBuilder
source .venv/bin/activate
python sync_resume_content_temp.py
```

**When to use:**
- ✅ Quick one-time backfill of existing data
- ✅ When you need resume_content immediately
- ❌ Not recommended for ongoing updates (use permanent solution instead)

---

## 🎯 Recommended Workflow

### **For New Setups:**
1. Use the **permanent solution** from the start
2. Run `python main.py --full-sync` to populate database with resume_content
3. Future syncs will automatically include resume_content

### **For Existing Setups (Current State):**
1. ✅ **Temporary solution already run** - Database has resume_content
2. ✅ **Permanent solution implemented** - Future syncs will maintain it
3. 🎯 **Next sync:** Just run `python main.py` and it will update resume_content automatically

---

## 📊 Database Schema

The `resume_content` column in `greenhouse_candidates`:

```sql
ALTER TABLE gh.candidates 
ADD COLUMN resume_content TEXT;
```

**Column details:**
- **Type:** TEXT (unlimited length)
- **Nullable:** Yes (empty string for candidates without resumes)
- **Source:** Greenhouse custom field ID `11138961008`
- **Updated:** During every sync via `main.py`

---

## 🔄 How Resume Content Flows

### **Permanent Solution Flow:**
```
Greenhouse API (custom_fields.resume_content)
    ↓
main.py (extracts during sync)
    ↓
greenhouse_candidates database
    ↓
export_segmented.py (includes in CSV)
    ↓
Zapier Tables
```

### **Temporary Solution Flow (One-Time):**
```
greenhouse_candidates_ai database
    ↓
sync_resume_content_temp.py
    ↓
greenhouse_candidates database
    ↓
export_segmented.py (includes in CSV)
    ↓
Zapier Tables
```

---

## 📝 Export Scripts

All export scripts now include `resume_content`:

### **Standard Export:**
```bash
python main.py --export-only
```
- Exports all candidates with resume_content
- File: `exports/gh_candidates_export_sync_*.csv`
- Size: ~29MB (without resume_content in old version)

### **Segmented Export (Recommended for Zapier):**
```bash
python export_segmented.py
```
- Splits into ~50MB chunks
- Includes resume_content
- Greenhouse S3 links (not SharePoint)
- Perfect for Zapier Tables

### **Appending Export (Incremental):**
```bash
python export_appending.py
```
- Only new candidates since last export
- Includes resume_content
- Great for incremental Zapier updates

---

## 🧪 Testing

### **Verify resume_content is populated:**
```bash
psql -d greenhouse_candidates -c "
SELECT 
  COUNT(*) as total,
  COUNT(resume_content) FILTER (WHERE resume_content IS NOT NULL AND resume_content != '') as with_content
FROM gh.candidates;
"
```

### **Check a sample:**
```bash
psql -d greenhouse_candidates -c "
SELECT 
  candidate_id,
  full_name,
  LENGTH(resume_content) as content_length
FROM gh.candidates
WHERE resume_content IS NOT NULL AND resume_content != ''
LIMIT 5;
"
```

---

## 🗑️ Cleanup (Optional)

If you want to remove the temporary solution after confirming the permanent solution works:

```bash
# Remove temporary sync script
rm sync_resume_content_temp.py

# Note: Keep the resume_content column in database
# The permanent solution (main.py) will maintain it going forward
```

---

## ⚙️ Configuration

### **Environment Variables:**

Add to `.env` file:
```bash
# Resume content custom field ID (default: 11138961008)
RESUME_CONTENT_FIELD_ID=11138961008
```

### **Custom Field ID:**

If your Greenhouse instance uses a different custom field ID for resume_content:
1. Find the field ID in Greenhouse settings
2. Update `RESUME_CONTENT_FIELD_ID` in `.env`
3. Re-run sync

---

## 📊 File Sizes

With resume_content included:

| Export Type | Without resume_content | With resume_content |
|-------------|------------------------|---------------------|
| Standard Export | ~29MB | ~29MB |
| Segmented Export | ~29MB total | ~350MB total (15 segments) |
| AI Access Export | ~24MB | ~350MB |

**Note:** Segmented exports keep each segment under 50MB for Zapier compatibility.

---

## 🎯 Summary

- ✅ **Permanent solution implemented** in `main.py`
- ✅ **Temporary solution available** via `sync_resume_content_temp.py`
- ✅ **Both approaches work** - use permanent for ongoing maintenance
- ✅ **All exports include resume_content** automatically
- ✅ **Zapier-compatible** segmented exports available

**Recommendation:** Use `python main.py` for all future syncs. The permanent solution will handle resume_content automatically.

---

**Last Updated:** November 14, 2025
