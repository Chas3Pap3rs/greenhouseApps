# Master Orchestration Scripts

These master scripts automate the complete workflows for the Greenhouse Apps system. They orchestrate multiple individual scripts in the correct order to perform common tasks.

---

## 🚀 Quick Start

### First Time Setup (Complete Rebuild)
```bash
python3 master_full_rebuild.py
```

### Regular Updates (Weekly/Monthly)
```bash
python3 master_incremental_update.py
```

### Verify Data Integrity
```bash
python3 master_verify_integrity.py
```

---

## Master Scripts Overview

### 1. `master_full_rebuild.py` - Complete System Rebuild

**Purpose:** Rebuild the entire system from scratch, pulling all data from Greenhouse API.

**When to use:**
- ✅ Initial setup of the system
- ✅ Complete data refresh needed
- ✅ Database corruption or major data issues
- ✅ After significant schema changes
- ✅ Monthly full refresh (recommended)

**Estimated time:** 4-8 hours (depends on number of candidates and network speed)

**What it does:**
1. Pulls ALL candidates from Greenhouse API → `greenhouse_candidates` database
2. Downloads ALL resumes to local storage and SharePoint
3. Creates AI_Access folder structure with metadata files
4. Maps SharePoint links → `greenhouse_candidates_sp` database
5. Maps AI_Access links → `greenhouse_candidates_ai` database
6. Maps metadata JSON file links
7. Syncs resume_content from metadata to database
8. Syncs resume_content to Greenhouse API
9. Runs comprehensive verification
10. Exports all CSVs (full and segmented)

**Prerequisites:**
- `.env` file configured with all credentials
- Sufficient disk space (~50GB+ for resumes)
- Greenhouse API access
- SharePoint access via Microsoft Graph API
- All three PostgreSQL databases created

**Usage:**
```bash
# Run with confirmation prompts
python3 master_full_rebuild.py

# The script will ask for confirmation before proceeding
# Type 'yes' and then 'REBUILD' to confirm
```

**Safety features:**
- ⚠️ Requires double confirmation (prevents accidental runs)
- ⚠️ Shows estimated time and requirements
- ⚠️ Provides detailed progress logging
- ⚠️ Continues on non-critical errors
- ⚠️ Generates final summary of any failed steps

---

### 2. `master_incremental_update.py` - Regular Updates

**Purpose:** Update the system with new and modified candidates only (incremental sync).

**When to use:**
- ✅ Weekly updates (recommended)
- ✅ After adding new candidates to Greenhouse
- ✅ To sync recent changes without full rebuild
- ✅ Regular maintenance updates

**Estimated time:** 30 minutes - 2 hours (depends on number of new candidates)

**What it does:**
1. Pulls NEW/UPDATED candidates from Greenhouse API (since last update)
2. Downloads NEW resumes only
3. Adds new resumes to AI_Access folder and generates metadata
4. Maps SharePoint links for new resumes
5. Maps AI_Access links for new candidates
6. Maps metadata links (individual mode, faster for small batches)
7. Syncs resume_content from metadata to database
8. Updates resume_content in Greenhouse API (incremental mode)
9. Verifies AI database status
10. Exports incremental CSV (new/updated candidates only)

**Prerequisites:**
- System already initialized with `master_full_rebuild.py`
- `.env` file configured
- Greenhouse and SharePoint API access

**Usage:**
```bash
# Run incremental update
python3 master_incremental_update.py

# No confirmation needed - safe to run regularly
```

**Scheduling recommendation:**
```bash
# Add to crontab for weekly updates (every Sunday at 2 AM)
0 2 * * 0 cd /path/to/greenhouseApps && python3 master_incremental_update.py >> logs/incremental_$(date +\%Y\%m\%d).log 2>&1
```

---

### 3. `master_verify_integrity.py` - Comprehensive Verification

**Purpose:** Run all verification checks and generate detailed data quality reports.

**When to use:**
- ✅ After running `master_full_rebuild.py`
- ✅ After running `master_incremental_update.py`
- ✅ Before exporting CSVs to production
- ✅ When investigating data quality issues
- ✅ Monthly data quality audits

**Estimated time:** 5-10 minutes

**What it does:**
1. Verifies database schemas
2. Checks data coverage across all three databases
3. Analyzes null fields
4. Verifies sync status between databases
5. Checks resume_content coverage in Greenhouse API
6. Validates SharePoint links
7. Verifies AI_Access metadata coverage
8. Runs cross-database consistency checks
9. Generates comprehensive summary report

**Usage:**
```bash
# Run verification and view output
python3 master_verify_integrity.py

# Save output to file for record-keeping
python3 master_verify_integrity.py > verification_report_$(date +%Y%m%d).txt
```

**Interpreting results:**
- ✅ **Excellent:** >95% coverage on all key fields
- ✅ **Good:** >90% coverage on all key fields
- ⚠️ **Fair:** >80% coverage (consider incremental update)
- ❌ **Poor:** <80% coverage (consider full rebuild)

---

## Workflow Recommendations

### Initial Setup
```bash
1. Configure .env file with all credentials
2. Create PostgreSQL databases (greenhouse_candidates, greenhouse_candidates_sp, greenhouse_candidates_ai)
3. Run: python3 master_full_rebuild.py
4. Run: python3 master_verify_integrity.py
5. Upload exported CSVs to Zapier Tables or other destinations
```

### Weekly Maintenance
```bash
1. Run: python3 master_incremental_update.py
2. Run: python3 master_verify_integrity.py (optional, but recommended)
3. Upload incremental CSV to Zapier Tables (append mode)
```

### Monthly Maintenance
```bash
1. Run: python3 master_verify_integrity.py
2. Review coverage statistics
3. If coverage is good (>90%): Continue with weekly incremental updates
4. If coverage is fair (<90%): Run python3 master_incremental_update.py
5. If coverage is poor (<80%): Run python3 master_full_rebuild.py
```

### Troubleshooting
```bash
1. Run: python3 master_verify_integrity.py
2. Identify specific issues (null fields, missing data, etc.)
3. Check utilities/investigation/ scripts for detailed analysis
4. Run specific fix scripts from utilities/fixes/ if needed
5. Re-run: python3 master_verify_integrity.py to confirm fixes
```

---

## Script Output and Logging

### Color-Coded Output
All master scripts use color-coded output for easy reading:
- 🔹 **Cyan:** Step headers
- ✅ **Green:** Success messages
- ⚠️ **Yellow:** Warnings
- ❌ **Red:** Errors
- **Purple:** Section headers

### Exit Codes
- `0` - All steps completed successfully
- `1` - One or more steps failed (check output for details)
- `130` - Interrupted by user (Ctrl+C)

### Logging Best Practices
```bash
# Create logs directory
mkdir -p logs

# Log full rebuild
python3 master_full_rebuild.py 2>&1 | tee logs/rebuild_$(date +%Y%m%d_%H%M%S).log

# Log incremental update
python3 master_incremental_update.py 2>&1 | tee logs/update_$(date +%Y%m%d_%H%M%S).log

# Log verification
python3 master_verify_integrity.py > logs/verification_$(date +%Y%m%d).txt
```

---

## Error Handling

### What happens if a step fails?

All master scripts are designed to be resilient:

1. **Non-critical failures:** Script continues to next step
2. **Critical failures:** Script stops (e.g., can't pull candidates from API)
3. **Final summary:** Lists all failed steps for manual review
4. **Exit code:** Returns 1 if any step failed

### Manual recovery after failures

If a step fails, you can run it manually:

```bash
# Example: If Step 3 (AI_Access folder creation) failed
cd greenhouse_sharepoint_mapper
python3 create_ai_access_folder.py

# Then continue with remaining steps or re-run master script
```

---

## Performance Optimization

### For faster full rebuilds:
- Use batch processing scripts (already configured in master_full_rebuild.py)
- Ensure good network connection to Greenhouse and SharePoint
- Run during off-peak hours
- Consider running on a server with better bandwidth

### For faster incremental updates:
- Run more frequently (weekly vs monthly) to reduce batch sizes
- Individual processing is faster for small batches (already configured)

---

## Monitoring and Alerts

### Set up monitoring (optional):
```bash
# Example: Send email on failure
python3 master_incremental_update.py || echo "Update failed" | mail -s "Greenhouse Update Failed" admin@example.com

# Example: Slack notification
python3 master_incremental_update.py && curl -X POST -H 'Content-type: application/json' --data '{"text":"Greenhouse update completed successfully"}' YOUR_SLACK_WEBHOOK_URL
```

---

## Common Issues and Solutions

### Issue: "Cannot connect to database"
**Solution:** 
- Check `.env` file has correct database credentials
- Verify PostgreSQL is running
- Check database names match (greenhouse_candidates, greenhouse_candidates_sp, greenhouse_candidates_ai)

### Issue: "Greenhouse API rate limit exceeded"
**Solution:**
- Wait for rate limit to reset (usually 1 hour)
- Run during off-peak hours
- Contact Greenhouse support to increase rate limit

### Issue: "SharePoint authentication failed"
**Solution:**
- Check Microsoft Graph API credentials in `.env`
- Verify app registration has correct permissions
- Re-authenticate if token expired

### Issue: "Disk space full"
**Solution:**
- Clean up old exports in `exports/` and `segmented_exports/`
- Archive old resumes if needed
- Ensure at least 50GB free space

### Issue: "Some candidates missing resume_content"
**Solution:**
- This is normal (~7-14% gap due to unsupported file formats)
- Run `utilities/analysis/analyze_failed_extractions.py` for details
- See DUPLICATE_EVALUATION.md for explanation

---

## Integration with Existing Scripts

The master scripts call existing production scripts in the correct order:

**Database Builder:**
- `greenhouse_candidate_dbBuilder/main.py`
- `greenhouse_candidate_dbBuilder/export_segmented.py`

**Resume Downloader:**
- `greenhouse_resume_downloader/download_resumes.py`

**SharePoint Mapper:**
- `greenhouse_sharepoint_mapper/create_ai_access_folder.py`
- `greenhouse_sharepoint_mapper/map_sharepoint_links.py`
- `greenhouse_sharepoint_mapper/map_ai_access_links.py`
- `greenhouse_sharepoint_mapper/map_metadata_links.py` (incremental)
- `greenhouse_sharepoint_mapper/map_metadata_links_batch.py` (full rebuild)
- `greenhouse_sharepoint_mapper/sync_resume_content_from_metadata.py`

**Resume Content Sync:**
- `greenhouse_resume_content_sync/sync_resume_content.py` (full)
- `greenhouse_resume_content_sync/update_resume_content.py` (incremental)

**Exports:**
- `greenhouse_sharepoint_mapper/exports/export_ai_access_csv_full.py`
- `greenhouse_sharepoint_mapper/exports/export_segmented_ai_full.py`
- `greenhouse_sharepoint_mapper/exports/export_incremental_ai.py`
- `greenhouse_sharepoint_mapper/exports/export_sharepoint_csv.py`

**Verification:**
- All scripts in `utilities/verification/`

---

## Next Steps After Running Master Scripts

### After `master_full_rebuild.py`:
1. Review verification output
2. Check exported CSVs in `greenhouse_sharepoint_mapper/exports/`
3. Upload segmented CSVs to Zapier Tables
4. Set up weekly cron job for `master_incremental_update.py`

### After `master_incremental_update.py`:
1. Review verification output
2. Check incremental CSV in `greenhouse_sharepoint_mapper/segmented_exports/`
3. Upload incremental CSV to Zapier Tables (append mode)
4. Monitor for any failed steps

### After `master_verify_integrity.py`:
1. Review coverage percentages
2. Investigate any data quality issues
3. Run appropriate fix scripts if needed
4. Save report for record-keeping

---

## Support and Documentation

For more information, see:
- `README.md` - Main project documentation
- `UPDATE_GUIDE.md` - Detailed update procedures
- `SCRIPT_INVENTORY.md` - Complete script catalog
- `utilities/README.md` - Utility scripts documentation
- `greenhouse_sharepoint_mapper/exports/README.md` - Export scripts guide

For troubleshooting:
- Check `utilities/investigation/` for diagnostic scripts
- Check `utilities/verification/` for status checks
- Check `utilities/analysis/` for detailed analysis tools
