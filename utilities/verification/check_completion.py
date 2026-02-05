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

# Test candidates that should have been updated by hybrid sync
# These are ones that failed in the first sync (unsupported formats)
test_candidates = [
    "5200380008",   # Avinash K - .doc file
    "5200391008",   # Bench Sales - failed before
    "10018100008",  # Updated in hybrid sync
    "10018124008",  # Updated in hybrid sync
    "10019423008",  # Updated in hybrid sync
]

print("=" * 70)
print("CHECKING HYBRID SYNC RESULTS")
print("=" * 70)
print()

has_content = 0
no_content = 0
errors = 0

for cid in test_candidates:
    try:
        response = requests.get(f"{GREENHOUSE_BASE_URL}/candidates/{cid}", headers=get_headers(), timeout=10)
        response.raise_for_status()
        candidate = response.json()
        
        name = f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".strip()
        resume_content = candidate.get('custom_fields', {}).get('resume_content', '')
        
        if resume_content:
            print(f"✅ {cid} ({name}): {len(resume_content):,} characters")
            has_content += 1
        else:
            print(f"❌ {cid} ({name}): NO CONTENT")
            no_content += 1
    except Exception as e:
        print(f"⚠️  {cid}: Error - {str(e)[:50]}")
        errors += 1

print()
print("=" * 70)
print(f"Results: {has_content} with content, {no_content} without, {errors} errors")
print("=" * 70)

if has_content >= 4:
    print()
    print("🎉 SUCCESS! Hybrid sync filled the gaps!")
    print("   Candidates that failed in first sync now have content!")

