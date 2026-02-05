import os
import sys
import requests
import base64
import random
from dotenv import load_dotenv

load_dotenv()

GREENHOUSE_API_KEY = os.getenv("GREENHOUSE_API_KEY")
GREENHOUSE_BASE_URL = "https://harvest.greenhouse.io/v1"

def get_headers():
    auth_string = f"{GREENHOUSE_API_KEY}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    return {"Authorization": f"Basic {encoded_auth}"}

print("=" * 70)
print("FINAL VERIFICATION - Counting Candidates with Resume Content")
print("=" * 70)
print()
print("Fetching all candidates from Greenhouse API...")
print("(This will take a few minutes)")
print()

# Fetch all candidates
all_candidates = []
page = 1

while True:
    try:
        response = requests.get(
            f"{GREENHOUSE_BASE_URL}/candidates",
            headers=get_headers(),
            params={"per_page": 500, "page": page},
            timeout=30
        )
        response.raise_for_status()
        candidates = response.json()
        
        if not candidates:
            break
        
        all_candidates.extend(candidates)
        print(f"  Fetched page {page}: {len(candidates)} candidates (total: {len(all_candidates):,})")
        page += 1
        
        if len(candidates) < 500:
            break
            
    except Exception as e:
        print(f"Error on page {page}: {e}")
        break

print()
print(f"✅ Total candidates fetched: {len(all_candidates):,}")
print()
print("Analyzing resume_content field...")
print()

with_content = 0
without_content = 0
no_field = 0

for candidate in all_candidates:
    custom_fields = candidate.get('custom_fields', {})
    resume_content = custom_fields.get('resume_content')
    
    if resume_content and resume_content.strip():
        with_content += 1
    elif resume_content is not None:
        without_content += 1
    else:
        no_field += 1

print("=" * 70)
print("FINAL RESULTS")
print("=" * 70)
print()
print(f"Total Candidates: {len(all_candidates):,}")
print()
print(f"✅ With Resume Content: {with_content:,} ({with_content/len(all_candidates)*100:.1f}%)")
print(f"❌ Without Resume Content: {without_content:,} ({without_content/len(all_candidates)*100:.1f}%)")
print(f"⚠️  No Field: {no_field:,} ({no_field/len(all_candidates)*100:.1f}%)")
print()
print("=" * 70)
print()

# Compare to initial sync
initial_sync = 21559
hybrid_added = with_content - initial_sync

if hybrid_added > 0:
    print(f"📊 IMPROVEMENT:")
    print(f"   Initial Sync: {initial_sync:,} candidates")
    print(f"   Hybrid Sync Added: {hybrid_added:,} candidates")
    print(f"   Total Now: {with_content:,} candidates")
    print()
    print(f"🎉 Coverage increased from 47% to {with_content/len(all_candidates)*100:.1f}%!")
else:
    print(f"Current total: {with_content:,} candidates with resume content")

print()
print("=" * 70)

