# Script Duplicate Evaluation
**Generated:** 2026-01-26
**Purpose:** Evaluate potentially duplicate scripts to determine which to keep

---

## 1. Export Scripts Comparison

### `export_lightweight_csv.py` vs `export_ai_access_csv.py`

**export_lightweight_csv.py:**
- **Purpose**: Ultra-minimal export with only 4 fields (candidate_id, full_name, email, resume_content)
- **Database**: greenhouse_candidates_ai
- **Resume Content**: ✅ INCLUDES resume_content
- **Fields**: Minimal (4 fields only)
- **Use Case**: Extremely lightweight for Zapier when you only need basic info + resume text

**export_ai_access_csv.py:**
- **Purpose**: Lightweight export with metadata but NO resume_content
- **Database**: greenhouse_candidates_ai
- **Resume Content**: ❌ EXCLUDES resume_content (by design)
- **Fields**: Comprehensive (candidate_id, names, email, phone, addresses, resume_url, metadata_url, employment history, etc.)
- **Use Case**: AI agents that fetch resume_content via API when needed

**VERDICT**: ✅ **KEEP BOTH** - They serve different purposes:
- `export_lightweight_csv.py`: When you need resume_content in CSV (minimal fields)
- `export_ai_access_csv.py`: When you need metadata without resume_content (comprehensive fields)

**RECOMMENDATION**: Rename for clarity:
- `export_lightweight_csv.py` → `export_minimal_with_content.py`
- `export_ai_access_csv.py` → Keep name (already clear)

---

## 2. Metadata Mapping Scripts

### `map_metadata_links.py` vs `map_metadata_links_batch.py`

**map_metadata_links.py:**
- **Approach**: Individual file lookups
- **Method**: For each candidate, searches local directory for metadata file, then gets SharePoint URL
- **Performance**: Slower for large batches (multiple API calls)
- **Use Case**: Incremental updates, small batches

**map_metadata_links_batch.py:**
- **Approach**: Batch processing
- **Method**: Gets all files from SharePoint folder at once, then matches by filename
- **Performance**: Faster for large batches (fewer API calls)
- **Use Case**: Full rebuilds, large batches

**VERDICT**: ✅ **KEEP BOTH** - Different performance characteristics:
- `map_metadata_links.py`: For incremental/small updates
- `map_metadata_links_batch.py`: For full rebuilds/large batches

**RECOMMENDATION**: Document when to use each in master scripts

---

## 3. Duplicate Files

### `check_greenhouse_stats.py` vs `check_greenhouse_stats 2.py`

**Analysis**: The "2" version appears to be an accidental duplicate (likely from file system sync)

**VERDICT**: ❌ **DELETE** `check_greenhouse_stats 2.py`

---

## 4. Temporary/Deprecated Scripts

### `sync_resume_content_temp.py` (in dbBuilder folder)

**Analysis**: 
- Name suggests it's temporary
- Located in wrong folder (should be in resume_content_sync if active)
- Likely superseded by proper sync scripts in resume_content_sync folder

**VERDICT**: 🗄️ **MOVE TO _deprecated/** - Appears to be old/temporary version

---

## Summary of Actions

### Keep As-Is (No Changes)
- `export_ai_access_csv.py` ✅
- `map_metadata_links.py` ✅
- `map_metadata_links_batch.py` ✅

### Rename for Clarity
- `export_lightweight_csv.py` → `export_minimal_with_content.py`

### Delete
- `check_greenhouse_stats 2.py` ❌

### Move to _deprecated/
- `greenhouse_candidate_dbBuilder/sync_resume_content_temp.py` 🗄️

---

## Export Scripts Final Lineup

After evaluation, here's the complete export script lineup with clear purposes:

### From AI Database (greenhouse_candidates_ai)

**Single File Exports:**
1. `export_ai_access_csv.py` - Lightweight, NO resume_content, comprehensive metadata
2. `export_ai_access_csv_full.py` - Full export WITH resume_content, all fields
3. `export_minimal_with_content.py` - Ultra-minimal (4 fields) WITH resume_content

**Segmented Exports (for Zapier <50MB limit):**
4. `export_segmented_ai.py` - Segmented, NO resume_content
5. `export_segmented_ai_full.py` - Segmented WITH resume_content

**Incremental Exports:**
6. `export_incremental_ai.py` - Only new/updated candidates since last export

### From SharePoint Database (greenhouse_candidates_sp)
7. `export_sharepoint_csv.py` - SharePoint-specific export

### From Main Database (greenhouse_candidates)
8. `greenhouse_candidate_dbBuilder/export_appending.py` - Append mode export
9. `greenhouse_candidate_dbBuilder/export_segmented.py` - Segmented export

**Total: 9 distinct export scripts, each with unique purpose**

---

## Recommendations for Master Scripts

When creating master orchestration scripts, use:

**For Full Rebuild:**
- Use batch processing scripts: `map_metadata_links_batch.py`
- Use full exports: `export_ai_access_csv_full.py`, `export_segmented_ai_full.py`

**For Incremental Updates:**
- Use individual processing: `map_metadata_links.py`
- Use incremental exports: `export_incremental_ai.py`

**For Zapier Integration:**
- Use segmented exports: `export_segmented_ai.py` or `export_segmented_ai_full.py`
- Each segment stays under 50MB limit
