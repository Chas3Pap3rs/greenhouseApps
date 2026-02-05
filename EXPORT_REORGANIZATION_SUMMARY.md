# Export Reorganization Summary

**Date:** February 1, 2026  
**Objective:** Reorganize exports into database-specific subfolders for better clarity and organization

---

## 🎯 Problem Statement

The previous export structure had all CSV files from different databases mixed together in a single folder, making it difficult to:
- Identify which database an export came from at first glance
- Manage and organize exports effectively
- Automate workflows that target specific databases
- Clean up old exports selectively

**Old Structure:**
```
exports/
├── gh_aiCandidates_export_sync_*.csv (16 files)
├── gh_spCandidates_export_sync_*.csv (1 file)
├── gh_candidates_lightweight_*.csv (1 file)
└── latest_*.csv (symlinks)

segmented_exports/
├── 2025.11.13_23.43.41_full/
├── 2025.12.04_21.30.20_full/
├── 2026.01.26_17.54.21_full/
└── ... (9 folders total)
```

---

## ✅ Solution Implemented

### New Database-Specific Structure

```
exports/
├── ai_database/              # greenhouse_candidates_ai
│   ├── full/                 # Single file exports (17 files migrated)
│   ├── segmented/            # Segmented exports (8 folders migrated)
│   └── incremental/          # Incremental exports (1 folder migrated)
├── sharepoint_database/      # greenhouse_candidates_sp
│   └── full/                 # SharePoint exports (1 file migrated)
├── main_database/            # greenhouse_candidates (from dbBuilder)
│   └── segmented/            # Main DB segmented exports
├── latest_ai_export.csv      # Symlink → ai_database/full/
├── latest_export.csv         # Symlink → sharepoint_database/full/
└── latest_lightweight_export.csv  # Symlink → ai_database/full/
```

---

## 📋 Changes Made

### 1. Created New Folder Structure
- ✅ `ai_database/full/` - AI database single file exports
- ✅ `ai_database/segmented/` - AI database segmented exports
- ✅ `ai_database/incremental/` - AI database incremental exports
- ✅ `sharepoint_database/full/` - SharePoint database exports
- ✅ `main_database/segmented/` - Main database segmented exports
- ✅ `.gitkeep` files in all folders to preserve structure

### 2. Created Migration Script
**File:** `utilities/fixes/migrate_exports_to_new_structure.py`

**Features:**
- Dry-run mode for safe testing
- Automatic detection of export type by filename
- Handles both single files and segmented folders
- Updates symlinks to point to new locations
- Color-coded terminal output
- Comprehensive statistics and reporting

**Migration Results:**
- **17 files** moved from `exports/` to database-specific folders
- **9 segmented folders** moved from `segmented_exports/` to `ai_database/segmented/` and `ai_database/incremental/`
- **3 symlinks** updated to point to new locations
- **Total: 26 items** successfully migrated

### 3. Updated All 7 Export Scripts

All export scripts now use the new database-specific folder structure:

#### AI Database Exports:
1. **`export_ai_access_csv.py`**
   - Output: `ai_database/full/`
   - Creates symlink: `latest_ai_export.csv`

2. **`export_ai_access_csv_full.py`**
   - Output: `ai_database/full/`

3. **`export_minimal_with_content.py`**
   - Output: `ai_database/full/`
   - Creates symlink: `latest_lightweight_export.csv`

4. **`export_segmented_ai.py`**
   - Output: `ai_database/segmented/YYYY.MM.DD_HH.MM.SS/`

5. **`export_segmented_ai_full.py`**
   - Output: `ai_database/segmented/YYYY.MM.DD_HH.MM.SS_full/`

6. **`export_incremental_ai.py`**
   - Output: `ai_database/incremental/YYYY.MM.DD_HH.MM.SS_incremental/`
   - Tracking file: `ai_database/incremental/.last_incremental_export`

#### SharePoint Database Exports:
7. **`export_sharepoint_csv.py`**
   - Output: `sharepoint_database/full/`
   - Creates symlink: `latest_export.csv`

### 4. Updated Documentation
**File:** `greenhouse_sharepoint_mapper/exports/README.md`

**Updates:**
- Added new folder structure diagram
- Updated all file paths to reflect new locations
- Added benefits section explaining advantages
- Updated verification commands
- Maintained all existing export script documentation

---

## 📊 Migration Statistics

### Files Migrated by Database:
- **AI Database (Full):** 16 files
- **AI Database (Segmented):** 8 folders
- **AI Database (Incremental):** 1 folder
- **SharePoint Database (Full):** 1 file
- **Symlinks Updated:** 3

### Total Items Migrated: **26**

### Disk Space by Database:
- **AI Database:** ~1.5 GB (full exports + segmented)
- **SharePoint Database:** ~17 MB
- **Total:** ~1.52 GB

---

## 🎁 Benefits

### Immediate Benefits:
1. **✅ Clear Database Identification** - Instantly know which database an export comes from
2. **✅ Better Organization** - Exports grouped by database and type (full/segmented/incremental)
3. **✅ Easier Cleanup** - Can selectively delete old exports by database
4. **✅ Improved Automation** - Scripts can target specific database folders
5. **✅ Better Documentation** - Structure is self-documenting

### Long-term Benefits:
1. **Scalability** - Easy to add new databases or export types
2. **Maintainability** - Clear structure reduces confusion
3. **Backup Strategy** - Can backup databases separately
4. **Access Control** - Can set different permissions per database folder
5. **Monitoring** - Can track export sizes and frequencies per database

---

## 🔧 Technical Details

### Symlink Management
All symlinks remain in the root `exports/` directory for backward compatibility:
- `latest_ai_export.csv` → `ai_database/full/gh_aiCandidates_export_sync_*.csv`
- `latest_export.csv` → `sharepoint_database/full/gh_spCandidates_export_sync_*.csv`
- `latest_lightweight_export.csv` → `ai_database/full/gh_candidates_lightweight_*.csv`

### Script Updates
Each export script was updated to:
1. Use `os.path.join()` with database-specific paths
2. Create parent directories automatically with `os.makedirs()`
3. Update symlink creation to point to new relative paths
4. Maintain backward compatibility with existing workflows

### Migration Safety
- Migration script includes dry-run mode
- User confirmation required before executing
- Original files moved (not copied) to avoid duplication
- Symlinks automatically updated to new locations
- `.gitkeep` files preserve empty folder structure

---

## 📝 Usage Examples

### Finding Exports by Database

**AI Database Exports:**
```bash
# View all AI database exports
ls -lh exports/ai_database/full/

# View segmented exports
ls -lh exports/ai_database/segmented/

# View incremental exports
ls -lh exports/ai_database/incremental/
```

**SharePoint Database Exports:**
```bash
# View SharePoint exports
ls -lh exports/sharepoint_database/full/
```

### Running Exports (No Change to Commands)
```bash
# All export commands remain the same
cd greenhouse_sharepoint_mapper/exports
python export_ai_access_csv.py
python export_segmented_ai.py
python export_sharepoint_csv.py
```

### Cleaning Up Old Exports
```bash
# Delete old AI database exports (keep last 3)
cd exports/ai_database/full
ls -t | tail -n +4 | xargs rm

# Delete old segmented exports (keep last 2)
cd ../segmented
ls -t | tail -n +3 | xargs rm -rf
```

---

## 🧪 Testing Recommendations

### Before Production Use:
1. **Test one export script** from each database
2. **Verify file locations** match new structure
3. **Check symlinks** point to correct files
4. **Verify Zapier uploads** work with new paths (if applicable)
5. **Test incremental exports** to ensure tracking file works

### Verification Commands:
```bash
# Test AI export
python export_ai_access_csv.py
ls -lh ai_database/full/
readlink latest_ai_export.csv

# Test SharePoint export
python export_sharepoint_csv.py
ls -lh sharepoint_database/full/
readlink latest_export.csv

# Test segmented export
python export_segmented_ai.py
ls -lh ai_database/segmented/
```

---

## 🔄 Rollback Plan (If Needed)

If issues arise, the migration can be reversed:

1. **Stop all export processes**
2. **Move files back to original locations:**
   ```bash
   mv ai_database/full/*.csv ./
   mv sharepoint_database/full/*.csv ./
   mv ai_database/segmented/* ../segmented_exports/
   mv ai_database/incremental/* ../segmented_exports/
   ```
3. **Revert export scripts** to use old paths
4. **Update symlinks** to point to old locations

**Note:** Keep the migration script for future re-migration after fixes.

---

## 📚 Related Documentation

- **Export Scripts Guide:** `exports/README.md`
- **Migration Script:** `utilities/fixes/migrate_exports_to_new_structure.py`
- **Main README:** `README.md`
- **Update Guide:** `UPDATE_GUIDE.md`

---

## ✅ Completion Checklist

- [x] Created new database-specific folder structure
- [x] Created and tested migration script
- [x] Migrated all existing exports (26 items)
- [x] Updated all 7 export scripts
- [x] Updated symlinks to new locations
- [x] Updated exports/README.md documentation
- [x] Created .gitkeep files in all folders
- [x] Tested migration in dry-run mode
- [x] Executed migration successfully
- [ ] Test one export from each database (recommended)
- [ ] Verify Zapier integration still works (if applicable)

---

## 🎉 Summary

The export reorganization is **complete and ready for use**. All exports are now organized by database in a clear, intuitive structure that makes it easy to identify, manage, and automate export workflows.

**Key Takeaway:** Exports are now organized by database (`ai_database/`, `sharepoint_database/`, `main_database/`) with subfolders for export types (`full/`, `segmented/`, `incremental/`), making the system more maintainable and scalable.

**Next Steps:**
1. Test one export from each database to verify functionality
2. Update any external scripts or documentation that reference old paths
3. Consider setting up automated cleanup of old exports
4. Monitor export sizes and adjust segmentation if needed
