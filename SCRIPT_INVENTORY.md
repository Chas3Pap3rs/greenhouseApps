# Greenhouse Apps - Complete Script Inventory
**Generated:** 2026-01-26
**Purpose:** Comprehensive catalog of all scripts for reorganization project

---

## Main Directory Scripts (Investigation/Verification)

### Investigation Scripts
| Script | Purpose | Status | Recommendation |
|--------|---------|--------|----------------|
| `investigate_null_fields.py` | Investigates null fields in databases | Active | Move to utilities/investigation/ |
| `analyze_database_structure.py` | Analyzes database schema and structure | Active | Move to utilities/investigation/ |
| `check_ai_null_fields.py` | Checks for null fields in AI database | Active | Move to utilities/verification/ |

### Verification Scripts
| Script | Purpose | Status | Recommendation |
|--------|---------|--------|----------------|
| `check_ai_database_status.py` | Checks AI database status and coverage | Active | Move to utilities/verification/ |
| `check_ai_schema.py` | Verifies AI database schema | Active | Move to utilities/verification/ |
| `check_greenhouse_stats.py` | Gets statistics from Greenhouse database | Active | Move to utilities/verification/ |
| `check_greenhouse_stats 2.py` | Duplicate of above | **DUPLICATE** | **DELETE** |
| `comprehensive_database_check.py` | Comprehensive check across all databases | Active | Move to utilities/verification/ |

### Fix Scripts (One-time)
| Script | Purpose | Status | Recommendation |
|--------|---------|--------|----------------|
| `fix_all_databases.py` | One-time fix for all databases | One-time | Move to utilities/fixes/ |

---

## 1. greenhouse_candidate_dbBuilder/

### Core Production Scripts
| Script | Purpose | Dependencies | Status |
|--------|---------|--------------|--------|
| `main.py` | **PRIMARY**: Pulls candidates from Greenhouse API to database | Greenhouse API | **KEEP** - Core script |
| `setup.py` | Sets up database schema and tables | PostgreSQL | **KEEP** - Setup script |
| `status.py` | Shows database status and statistics | Database | **KEEP** - Status check |

### Export Scripts
| Script | Purpose | Status | Recommendation |
|--------|---------|--------|----------------|
| `export_appending.py` | Exports candidates with append mode | Active | **KEEP** - Unique functionality |
| `export_segmented.py` | Exports in segments for large datasets | Active | **KEEP** - Unique functionality |

### Testing/Temporary Scripts
| Script | Purpose | Status | Recommendation |
|--------|---------|--------|----------------|
| `test_api.py` | Tests Greenhouse API connection | Testing | Move to utilities/testing/ |
| `sync_resume_content_temp.py` | Temporary sync script | **DEPRECATED** | Move to _deprecated/ |

---

## 2. greenhouse_resume_downloader/

### Core Production Scripts
| Script | Purpose | Dependencies | Status |
|--------|---------|--------------|--------|
| `download_resumes.py` | **PRIMARY**: Downloads resumes from Greenhouse to local/SharePoint | Greenhouse API, SharePoint | **KEEP** - Core script |
| `setup_audit_table.py` | Sets up audit table for tracking downloads | Database | **KEEP** - Setup script |
| `status.py` | Shows download status and statistics | Database | **KEEP** - Status check |

---

## 3. greenhouse_resume_content_sync/

### Core Production Scripts
| Script | Purpose | Dependencies | Status |
|--------|---------|--------------|--------|
| `sync_resume_content.py` | **PRIMARY**: Syncs resume_content to Greenhouse API | Greenhouse API, Database | **KEEP** - Core script |
| `update_resume_content.py` | **INCREMENTAL**: Updates resume_content for new candidates only | Greenhouse API, Database | **KEEP** - Incremental version |
| `sync_to_database.py` | Syncs resume_content to local database | Database | **KEEP** - Database sync |
| `sync_from_sharepoint.py` | Syncs resume_content from SharePoint metadata | SharePoint, Database | **KEEP** - Alternative sync method |

### Verification Scripts
| Script | Purpose | Status | Recommendation |
|--------|---------|--------|----------------|
| `check_completion.py` | Checks sync completion status | Active | Move to utilities/verification/ |
| `verify_final_count.py` | Verifies final count after sync | Active | Move to utilities/verification/ |
| `final_summary.py` | Generates final summary report | Active | Move to utilities/verification/ |

---

## 4. greenhouse_sharepoint_mapper/

### Core Production Scripts
| Script | Purpose | Dependencies | Status |
|--------|---------|--------------|--------|
| `create_ai_access_folder.py` | **PRIMARY**: Creates AI_Access folder, copies resumes, generates metadata | SharePoint, Database | **KEEP** - Core script |
| `map_sharepoint_links.py` | **PRIMARY**: Maps SharePoint links for resumes to SP database | SharePoint API, Database | **KEEP** - Core script |
| `map_ai_access_links.py` | **PRIMARY**: Maps AI_Access links to AI database | SharePoint API, Database | **KEEP** - Core script |
| `map_metadata_links.py` | Maps metadata JSON file links to AI database | SharePoint API, Database | **KEEP** - Core script |
| `setup_sharepoint_db.py` | Sets up SharePoint database schema | Database | **KEEP** - Setup script |
| `graph_client.py` | **LIBRARY**: Microsoft Graph API client | Microsoft Graph API | **KEEP** - Core library |

### Database Sync Scripts
| Script | Purpose | Status | Recommendation |
|--------|---------|--------|----------------|
| `sync_ai_database_fields.py` | Syncs fields between databases | Active | **KEEP** - Production sync |
| `sync_resume_content_from_metadata.py` | Syncs resume_content from metadata files | Active | **KEEP** - Production sync |

### Export Scripts (Multiple Versions)
| Script | Purpose | Size Limit | Resume Content | Recommendation |
|--------|---------|------------|----------------|----------------|
| `export_ai_access_csv.py` | Lightweight AI export | ~33MB | ❌ No | **KEEP** - Primary lightweight |
| `export_ai_access_csv_full.py` | Full AI export with content | Large | ✅ Yes | **KEEP** - Primary full |
| `export_segmented_ai.py` | Segmented lightweight export | <50MB chunks | ❌ No | **KEEP** - For Zapier |
| `export_segmented_ai_full.py` | Segmented full export | <50MB chunks | ✅ Yes | **KEEP** - For Zapier with content |
| `export_incremental_ai.py` | Incremental export (new/updated only) | Varies | ❌ No | **KEEP** - Incremental updates |
| `export_sharepoint_csv.py` | SharePoint database export | Varies | ❌ No | **KEEP** - SP-specific export |
| `export_lightweight_csv.py` | Generic lightweight export | Small | ❌ No | **EVALUATE** - May duplicate export_ai_access_csv.py |

### Batch Processing Scripts
| Script | Purpose | Status | Recommendation |
|--------|---------|--------|----------------|
| `map_metadata_links_batch.py` | Batch version of metadata mapping | Active | **EVALUATE** - May be redundant with map_metadata_links.py |
| `backfill_ai_access.py` | Backfills missing AI_Access entries | One-time | Move to utilities/fixes/ |

### Fix Scripts (One-time/Deprecated)
| Script | Purpose | Status | Recommendation |
|--------|---------|--------|----------------|
| `comprehensive_fix.py` | One-time comprehensive fix (metadata URLs, resume_content) | **ONE-TIME** | Move to utilities/fixes/ |
| `fix_ai_database_fields.py` | Fixes AI database field issues | **ONE-TIME** | Move to utilities/fixes/ |
| `fix_sp_database_fields.py` | Fixes SP database field issues | **ONE-TIME** | Move to utilities/fixes/ |
| `fix_null_resume_links.py` | Fixes null resume links | **ONE-TIME** | Move to utilities/fixes/ |
| `fix_recent_aws_links.py` | Fixes AWS links to SharePoint | **ONE-TIME** | Move to utilities/fixes/ |

### Analysis Scripts
| Script | Purpose | Status | Recommendation |
|--------|---------|--------|----------------|
| `analyze_failed_extractions.py` | Analyzes failed text extractions | Analysis | Move to utilities/analysis/ |

### Status/Verification Scripts
| Script | Purpose | Status | Recommendation |
|--------|---------|--------|----------------|
| `status.py` | Shows mapping status | Active | **KEEP** - Status check |
| `check_mapping_status.py` | Checks SharePoint mapping status | Active | Move to utilities/verification/ |
| `check_sync_status.py` | Checks sync status across databases | Active | Move to utilities/verification/ |

---

## Summary Statistics

### By Category
- **Core Production Scripts**: 15 (must keep)
- **Setup Scripts**: 4 (must keep)
- **Status/Verification Scripts**: 14 (organize into utilities)
- **Export Scripts**: 7 (keep all, document differences)
- **Fix Scripts (One-time)**: 6 (move to utilities/fixes)
- **Deprecated/Duplicate**: 2 (move to _deprecated or delete)
- **Testing Scripts**: 1 (move to utilities/testing)

### By Project
- **dbBuilder**: 7 scripts (1 deprecated)
- **resume_downloader**: 3 scripts (all production)
- **resume_content_sync**: 7 scripts (4 production, 3 verification)
- **sharepoint_mapper**: 27 scripts (6 core, 7 exports, 6 fixes, 5 verification, 3 analysis/batch)
- **Main directory**: 9 scripts (all investigation/verification)

---

## Identified Issues

### Duplicates to Address
1. ✅ `check_greenhouse_stats 2.py` - Delete (exact duplicate)
2. ⚠️ `export_lightweight_csv.py` vs `export_ai_access_csv.py` - Need to compare functionality
3. ⚠️ `map_metadata_links_batch.py` vs `map_metadata_links.py` - Evaluate if batch version is still needed

### Scripts Needing Evaluation
1. `sync_resume_content_temp.py` - Appears to be temporary/deprecated
2. `backfill_ai_access.py` - One-time fix, should be archived
3. Multiple fix scripts - Should be moved to utilities/fixes/ as they're one-time use

---

## Proposed Folder Structure

```
greenhouseApps/
├── utilities/                          # NEW - Central utilities folder
│   ├── investigation/                  # Database investigation scripts
│   ├── verification/                   # Status checks and verification
│   ├── analysis/                       # Analysis and reporting
│   ├── fixes/                          # One-time fix scripts
│   └── testing/                        # Test scripts
│
├── greenhouse_candidate_dbBuilder/
│   ├── main.py                         # CORE
│   ├── setup.py                        # CORE
│   ├── status.py                       # CORE
│   ├── export_appending.py             # CORE
│   ├── export_segmented.py             # CORE
│   ├── test_api.py                     # Move to utilities/testing/
│   └── _deprecated/                    # NEW
│       └── sync_resume_content_temp.py
│
├── greenhouse_resume_downloader/
│   ├── download_resumes.py             # CORE
│   ├── setup_audit_table.py            # CORE
│   └── status.py                       # CORE
│
├── greenhouse_resume_content_sync/
│   ├── sync_resume_content.py          # CORE - Full sync
│   ├── update_resume_content.py        # CORE - Incremental
│   ├── sync_to_database.py             # CORE
│   ├── sync_from_sharepoint.py         # CORE
│   ├── check_completion.py             # Move to utilities/verification/
│   ├── verify_final_count.py           # Move to utilities/verification/
│   └── final_summary.py                # Move to utilities/verification/
│
├── greenhouse_sharepoint_mapper/
│   ├── graph_client.py                 # CORE LIBRARY
│   ├── create_ai_access_folder.py      # CORE
│   ├── map_sharepoint_links.py         # CORE
│   ├── map_ai_access_links.py          # CORE
│   ├── map_metadata_links.py           # CORE
│   ├── setup_sharepoint_db.py          # CORE
│   ├── sync_ai_database_fields.py      # CORE
│   ├── sync_resume_content_from_metadata.py  # CORE
│   ├── status.py                       # CORE
│   ├── exports/                        # NEW - Organize exports
│   │   ├── export_ai_access_csv.py
│   │   ├── export_ai_access_csv_full.py
│   │   ├── export_segmented_ai.py
│   │   ├── export_segmented_ai_full.py
│   │   ├── export_incremental_ai.py
│   │   ├── export_sharepoint_csv.py
│   │   └── export_lightweight_csv.py   # Evaluate first
│   ├── _deprecated/                    # NEW
│   │   └── (TBD after evaluation)
│   └── (Move verification/fix scripts to utilities/)
│
└── master_scripts/                     # NEW - Master orchestration
    ├── master_full_rebuild.py
    ├── master_incremental_update.py
    └── master_verify_integrity.py
```

---

## Next Steps

1. ✅ **Phase 1a**: Complete inventory (DONE)
2. **Phase 1b**: Evaluate duplicate/similar scripts:
   - Compare `export_lightweight_csv.py` vs `export_ai_access_csv.py`
   - Compare `map_metadata_links_batch.py` vs `map_metadata_links.py`
   - Verify `sync_resume_content_temp.py` is truly deprecated
3. **Phase 2**: Create folder structure and move files
4. **Phase 3**: Create master orchestration scripts
5. **Phase 4**: Update all documentation

---

## Questions for User

1. Should we delete `check_greenhouse_stats 2.py` or move to _deprecated?
2. Do you want to keep batch processing scripts separate or merge functionality?
3. Any other scripts you know are deprecated that we should flag?
