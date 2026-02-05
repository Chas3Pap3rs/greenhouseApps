#!/usr/bin/env python3
"""
Microsoft Graph API client for SharePoint operations
Handles authentication and SharePoint file operations
"""

import os
import requests
from msal import ConfidentialClientApplication
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

class GraphClient:
    """Microsoft Graph API client for SharePoint operations"""
    
    def __init__(self):
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.sharepoint_base_url = os.getenv("SHAREPOINT_BASE_URL")
        self.site_id = os.getenv("SHAREPOINT_SITE_ID")
        self.resume_folder_path = os.getenv("RESUME_FOLDER_PATH")
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Missing Azure credentials in .env file")
        
        # Initialize MSAL client
        self.app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        
        self.access_token = None
    
    def get_access_token(self):
        """Get access token for Microsoft Graph API"""
        # Always request a fresh token - MSAL handles caching and refresh internally
        # This prevents token expiration issues during long-running processes
        scopes = ["https://graph.microsoft.com/.default"]
        
        result = self.app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            return self.access_token
        else:
            error = result.get("error_description", result.get("error", "Unknown error"))
            raise Exception(f"Failed to acquire access token: {error}")
    
    def get_headers(self):
        """Get headers for Graph API requests"""
        token = self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def get_site_info(self):
        """Get SharePoint site information"""
        headers = self.get_headers()
        url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def find_file_by_path(self, relative_path):
        """Find a file in SharePoint by its relative path"""
        headers = self.get_headers()
        
        # Encode the path for URL
        encoded_path = quote(relative_path)
        
        # Try to get file info
        url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive/root:/{self.resume_folder_path}/{encoded_path}"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None  # File not found
            raise
    
    def create_sharing_link(self, file_id, link_type="view"):
        """Create a sharing link for a file"""
        headers = self.get_headers()
        
        url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive/items/{file_id}/createLink"
        
        payload = {
            "type": link_type,  # "view" or "edit"
            "scope": "organization"  # "anonymous", "organization", or "users"
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result.get("link", {}).get("webUrl")
    
    def get_sharepoint_url_for_local_file(self, local_file_path):
        """
        Convert local file path to SharePoint URL
        
        Args:
            local_file_path: Full path to local file
            
        Returns:
            tuple: (sharepoint_url, sharepoint_filename) or (None, None) if not found
        """
        try:
            # Extract relative path from local path
            local_resume_dir = os.getenv("LOCAL_RESUME_DIR")
            if not local_file_path.startswith(local_resume_dir):
                return None, None
            
            # Get relative path within SharePoint
            relative_path = os.path.relpath(local_file_path, local_resume_dir)
            filename = os.path.basename(local_file_path)
            
            # Find file in SharePoint
            file_info = self.find_file_by_path(relative_path)
            if not file_info:
                return None, None
            
            # Use direct web URL instead of creating sharing link
            # This works with read-only permissions
            web_url = file_info.get("webUrl")
            if not web_url:
                return None, None
            
            return web_url, filename
            
        except Exception as e:
            print(f"Error getting SharePoint URL for {local_file_path}: {e}")
            return None, None
    
    def test_connection(self):
        """Test the Graph API connection"""
        try:
            site_info = self.get_site_info()
            return {
                "success": True,
                "site_name": site_info.get("displayName"),
                "site_id": site_info.get("id"),
                "web_url": site_info.get("webUrl")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

def test_graph_client():
    """Test function for Graph API client"""
    try:
        client = GraphClient()
        result = client.test_connection()
        
        if result["success"]:
            print("✅ Graph API connection successful!")
            print(f"   Site: {result['site_name']}")
            print(f"   URL: {result['web_url']}")
        else:
            print("❌ Graph API connection failed!")
            print(f"   Error: {result['error']}")
        
        return result["success"]
        
    except Exception as e:
        print(f"❌ Graph API client error: {e}")
        return False

if __name__ == "__main__":
    test_graph_client()
