#!/usr/bin/env python3
"""
Google Drive Setup Script
This script helps you authenticate with Google Drive and generate the token file.
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes required for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def setup_google_drive():
    """Set up Google Drive authentication and create token file"""
    
    # Configuration
    CREDENTIALS_FILE = 'credentials.json'  # Your downloaded credentials file
    TOKEN_FILE = 'google_drive_token.pickle'  # Token file to be created
    
    print("🚀 Setting up Google Drive authentication...")
    
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Error: {CREDENTIALS_FILE} not found!")
        print("\n📋 To get credentials.json:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a project or select existing one")
        print("3. Enable Google Drive API")
        print("4. Go to APIs & Services → Credentials")
        print("5. Create Credentials → OAuth client ID → Desktop application")
        print("6. Download the JSON file and rename it to 'credentials.json'")
        return False
    
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        print(f"📁 Found existing token file: {TOKEN_FILE}")
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                print("✅ Credentials refreshed successfully!")
            except Exception as e:
                print(f"❌ Failed to refresh credentials: {e}")
                creds = None
        
        if not creds:
            print("🔐 Starting authentication flow...")
            print("📱 Your browser will open for authentication...")
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
                print("✅ Authentication successful!")
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                return False
        
        # Save the credentials for the next run
        try:
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
            print(f"💾 Token saved to: {TOKEN_FILE}")
        except Exception as e:
            print(f"❌ Failed to save token: {e}")
            return False
    else:
        print("✅ Valid credentials found!")
    
    # Test the connection
    try:
        print("🧪 Testing Google Drive connection...")
        service = build('drive', 'v3', credentials=creds)
        
        # Get user info
        about = service.about().get(fields="user").execute()
        user_email = about.get('user', {}).get('emailAddress', 'Unknown')
        
        print(f"✅ Connected to Google Drive as: {user_email}")
        
        # Check storage quota
        about_storage = service.about().get(fields="storageQuota").execute()
        storage_quota = about_storage.get('storageQuota', {})
        
        if storage_quota:
            limit = int(storage_quota.get('limit', 0))
            usage = int(storage_quota.get('usage', 0))
            
            if limit > 0:
                limit_gb = limit / (1024**3)
                usage_gb = usage / (1024**3)
                available_gb = limit_gb - usage_gb
                
                print(f"📊 Storage: {usage_gb:.2f}GB used / {limit_gb:.2f}GB total")
                print(f"💾 Available: {available_gb:.2f}GB")
            else:
                print("📊 Storage: Unlimited")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test connection: {e}")
        return False

def create_workout_folder():
    """Create a dedicated folder for workout videos"""
    try:
        # Load credentials
        with open('google_drive_token.pickle', 'rb') as token:
            creds = pickle.load(token)
        
        service = build('drive', 'v3', credentials=creds)
        
        # Check if folder already exists
        results = service.files().list(
            q="name='Workout Videos' and mimeType='application/vnd.google-apps.folder'",
            fields="files(id, name)"
        ).execute()
        
        folders = results.get('files', [])
        
        if folders:
            folder_id = folders[0]['id']
            print(f"📁 Found existing 'Workout Videos' folder: {folder_id}")
        else:
            # Create new folder
            folder_metadata = {
                'name': 'Workout Videos',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')
            print(f"📁 Created 'Workout Videos' folder: {folder_id}")
        
        print(f"\n📋 Add this to your .env file:")
        print(f"GOOGLE_DRIVE_FOLDER_ID={folder_id}")
        
        return folder_id
        
    except Exception as e:
        print(f"❌ Failed to create folder: {e}")
        return None

if __name__ == "__main__":
    print("=" * 50)
    print("🏋️  Workout Analyzer - Google Drive Setup")
    print("=" * 50)
    
    success = setup_google_drive()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Google Drive setup completed successfully!")
        
        # Ask if user wants to create a dedicated folder
        create_folder = input("\n📁 Create a dedicated 'Workout Videos' folder? (y/n): ").lower().strip()
        
        if create_folder in ['y', 'yes']:
            folder_id = create_workout_folder()
        
        print("\n📋 Next steps:")
        print("1. Update your .env file with the correct paths:")
        print(f"   GOOGLE_DRIVE_CREDENTIALS_FILE=credentials.json")
        print(f"   GOOGLE_DRIVE_TOKEN_FILE=google_drive_token.pickle")
        if 'folder_id' in locals() and folder_id:
            print(f"   GOOGLE_DRIVE_FOLDER_ID={folder_id}")
        print("2. Run your workout analyzer app: python -m app.main")
        
    else:
        print("\n❌ Setup failed. Please check the errors above and try again.")
    
    print("\n" + "=" * 50)