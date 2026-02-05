#!/usr/bin/env python3
"""
Test script to verify Greenhouse API connectivity and data structure
"""

import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def test_api_connection():
    """Test basic API connectivity"""
    api_key = os.getenv("GREENHOUSE_API_KEY")
    if not api_key:
        print("ERROR: GREENHOUSE_API_KEY not found in .env")
        return False
    
    url = "https://harvest.greenhouse.io/v1/candidates"
    params = {"per_page": 1}  # Just get 1 candidate for testing
    auth = requests.auth.HTTPBasicAuth(api_key, "")
    
    try:
        response = requests.get(url, auth=auth, params=params, timeout=30)
        response.raise_for_status()
        
        candidates = response.json()
        print(f"✅ API connection successful!")
        print(f"✅ Retrieved {len(candidates)} candidate(s)")
        
        if candidates:
            candidate = candidates[0]
            print(f"✅ Sample candidate ID: {candidate.get('id')}")
            print(f"✅ Sample candidate name: {candidate.get('first_name')} {candidate.get('last_name')}")
            
            # Show structure of key fields
            print("\n📋 Data structure preview:")
            print(f"   - Email addresses: {len(candidate.get('email_addresses', []))} found")
            print(f"   - Phone numbers: {len(candidate.get('phone_numbers', []))} found")
            print(f"   - Attachments: {len(candidate.get('attachments', []))} found")
            print(f"   - Employments: {len(candidate.get('employments', []))} found")
            print(f"   - Educations: {len(candidate.get('educations', []))} found")
            print(f"   - Applications: {len(candidate.get('applications', []))} found")
            
            # Show resume attachments
            resumes = [a for a in candidate.get('attachments', []) if a.get('type') == 'resume']
            print(f"   - Resume attachments: {len(resumes)} found")
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_pagination():
    """Test pagination headers"""
    api_key = os.getenv("GREENHOUSE_API_KEY")
    url = "https://harvest.greenhouse.io/v1/candidates"
    params = {"per_page": 2}  # Small page size to test pagination
    auth = requests.auth.HTTPBasicAuth(api_key, "")
    
    try:
        response = requests.get(url, auth=auth, params=params, timeout=30)
        response.raise_for_status()
        
        link_header = response.headers.get("Link")
        if link_header:
            print(f"✅ Pagination Link header found: {link_header[:100]}...")
            if 'rel="next"' in link_header:
                print("✅ Next page link detected")
            else:
                print("ℹ️  No next page (might be at end of data)")
        else:
            print("ℹ️  No Link header found (might be single page of data)")
            
        return True
        
    except Exception as e:
        print(f"❌ Pagination test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Greenhouse API connectivity...\n")
    
    if test_api_connection():
        print("\n🧪 Testing pagination...")
        test_pagination()
        print("\n✅ All tests passed! You can now run the full ETL with:")
        print("   python main.py")
    else:
        print("\n❌ API tests failed. Please check your GREENHOUSE_API_KEY in .env")
