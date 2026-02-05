import os
import glob
import json

LOCAL_AI_ACCESS_DIR = "/Users/chasepoulton/Library/CloudStorage/OneDrive-CookSystems/AI Operator - Greenhouse_Resumes/AI_Access"

print("=" * 70)
print("ANALYZING METADATA FILES")
print("=" * 70)
print()

# Get all metadata files
pattern = os.path.join(LOCAL_AI_ACCESS_DIR, "*_metadata.json")
metadata_files = glob.glob(pattern)

total_files = len(metadata_files)
has_text = 0
no_text = 0

# Sample check
for filepath in metadata_files[:1000]:  # Check first 1000
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            if data.get('text_content'):
                has_text += 1
            else:
                no_text += 1
    except:
        pass

print(f"Total metadata files: {total_files:,}")
print(f"Sample of 1000 files:")
print(f"  - With text content: {has_text}")
print(f"  - Without text content: {no_text}")
print()

# Estimate
estimated_with_text = int((has_text / 1000) * total_files)
print(f"Estimated files with extractable text: ~{estimated_with_text:,}")
print("=" * 70)

