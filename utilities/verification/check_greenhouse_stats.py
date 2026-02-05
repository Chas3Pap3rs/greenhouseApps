#!/usr/bin/env python3
"""
Check Greenhouse candidate statistics directly from API
"""

import os
import base64
import requests
from dotenv import load_dotenv

# Load environment from greenhouse_candidate_dbBuilder
load_dotenv(os.path.join(os.path.dirname(__file__), 'greenhouse_candidate_dbBuilder', '.env'))

GREENHOUSE_API_KEY = os.getenv("GREENHOUSE_API_KEY")
GREENHOUSE_BASE_URL = "https://harvest.greenhouse.io/v1"

def get_greenhouse_headers():
    """Get headers for Greenhouse API requests"""
    auth_string = f"{GREENHOUSE_API_KEY}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    return {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json"
    }

def check_greenhouse_stats():
    """Check total candidates and candidates with resumes"""
    print("=" * 70)
    print("GREENHOUSE CANDIDATE STATISTICS (Direct from API)")
    print("=" * 70)
    print()
    
    total_candidates = 0
    candidates_with_resumes = 0
    page = 1
    per_page = 500
    
    print("Fetching candidates from Greenhouse API...")
    print("(This may take several minutes for large datasets)")
    print()
    
    while True:
        print(f"Page {page}...", end=" ", flush=True)
        
        url = f"{GREENHOUSE_BASE_URL}/candidates"
        params = {
            "per_page": per_page,
            "page": page
        }
        
        try:
            # Add timeout to prevent hanging
            response = requests.get(
                url, 
                headers=get_greenhouse_headers(), 
                params=params,
                timeout=30  # 30 second timeout
            )
            response.raise_for_status()
            candidates = response.json()
            
            if not candidates:
                print("(empty - end of data)")
                break
            
            print(f"{len(candidates)} candidates", end="")
            
            for candidate in candidates:
                total_candidates += 1
                
                # Check if candidate has resume attachments
                attachments = candidate.get('attachments', [])
                has_resume = any(att.get('type') == 'resume' for att in attachments)
                
                if has_resume:
                    candidates_with_resumes += 1
            
            print(f" | Total so far: {total_candidates:,}")
            
            # Check if there are more pages
            if len(candidates) < per_page:
                print("\nReached last page of results.")
                break
            
            page += 1
            
        except requests.exceptions.Timeout:
            print(f"\n⚠️  Timeout on page {page}. Retrying...")
            continue
            
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error on page {page}: {e}")
            print(f"\nPartial results up to page {page-1}:")
            break
    
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Total candidates in Greenhouse: {total_candidates:,}")
    print(f"Candidates with resume attachments: {candidates_with_resumes:,}")
    print(f"Candidates without resumes: {(total_candidates - candidates_with_resumes):,}")
    if total_candidates > 0:
        print(f"Resume coverage: {(candidates_with_resumes/total_candidates*100):.1f}%")
    print("=" * 70)

if __name__ == "__main__":
    check_greenhouse_stats()
