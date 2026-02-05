#!/bin/bash
# Update database and CSV with resume_content

echo "========================================================================"
echo "UPDATE DATABASE AND CSV WITH RESUME CONTENT"
echo "========================================================================"
echo ""

# Step 1: Sync resume_content to database
echo "Step 1: Syncing resume_content to database..."
echo ""
python sync_to_database.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Database sync failed!"
    exit 1
fi

echo ""
echo "========================================================================"
echo ""

# Step 2: Export updated CSV
echo "Step 2: Exporting updated CSV..."
echo ""
cd ../greenhouse_sharepoint_mapper
python export_ai_access_csv.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ CSV export failed!"
    exit 1
fi

echo ""
echo "========================================================================"
echo "✅ ALL DONE!"
echo "========================================================================"
echo ""
echo "Database and CSV have been updated with resume_content field!"
echo ""
