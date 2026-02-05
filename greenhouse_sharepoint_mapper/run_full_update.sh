#!/bin/bash
# Full Update Pipeline
# Runs all updates in the correct order for incremental sync

set -e  # Exit on error

echo "=========================================="
echo "GREENHOUSE SHAREPOINT UPDATE PIPELINE"
echo "=========================================="
echo ""

# Step 1: Update candidate data from Greenhouse
echo "Step 1/6: Updating candidate data from Greenhouse..."
cd ../greenhouse_candidate_dbBuilder
source .venv/bin/activate
python main.py
echo "✅ Candidate data updated"
echo ""

# Step 2: Download new resumes
echo "Step 2/6: Downloading new resumes..."
cd ../greenhouse_resume_downloader
source .venv/bin/activate
python download_resumes.py
echo "✅ New resumes downloaded"
echo ""

# Step 3: Copy new resumes to AI_Access folder
echo "Step 3/6: Copying new resumes to AI_Access folder..."
cd ../greenhouse_sharepoint_mapper
source .venv/bin/activate
python create_ai_access_folder.py
echo "✅ AI_Access folder updated"
echo ""

# Step 4: Update human-friendly SharePoint links
echo "Step 4/6: Updating human-friendly SharePoint links..."
python update_sharepoint_links.py
echo "✅ Human-friendly links updated"
echo ""

# Step 5: Update AI-friendly SharePoint links
echo "Step 5/6: Updating AI-friendly SharePoint links..."
python update_ai_access_links.py
echo "✅ AI-friendly links updated"
echo ""

# Step 6: Export CSVs
echo "Step 6/6: Exporting CSVs..."
python export_sharepoint_csv.py
python export_ai_access_csv.py
echo "✅ CSVs exported"
echo ""

echo "=========================================="
echo "✅ FULL UPDATE COMPLETE!"
echo "=========================================="
echo ""
echo "📁 Exports available in: exports/"
echo "   - Human-friendly: latest_export.csv"
echo "   - AI-friendly: latest_ai_export.csv"
echo ""
