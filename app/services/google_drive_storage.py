import os
import pickle
from typing import Optional, BinaryIO
import uuid
import logging
from datetime import datetime
import mimetypes

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload
from googleapiclient.errors import HttpError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Scopes required for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveService:
    def __init__(self):
        self.service = None
        self.initialized = False
        
    def initialize(self):
        """Initialize Google Drive API service"""
        if self.initialized:
            return
            
        try:
            creds = self._get_credentials()
            if creds:
                self.service = build('drive', 'v3', credentials=creds)
                self.initialized = True
                logger.info("Google Drive service initialized successfully")
            else:
                logger.error("Failed to get Google Drive credentials")
                
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            self.service = None
            self.initialized = False
    
    def _get_credentials(self) -> Optional[Credentials]:
        """Get Google Drive API credentials"""
        creds = None
        
        # Load existing token
        if os.path.exists(settings.GOOGLE_DRIVE_TOKEN_FILE):
            with open(settings.GOOGLE_DRIVE_TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(settings.GOOGLE_DRIVE_CREDENTIALS_FILE):
                    logger.error(f"Credentials file not found: {settings.GOOGLE_DRIVE_CREDENTIALS_FILE}")
                    return None
                    
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        settings.GOOGLE_DRIVE_CREDENTIALS_FILE, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Failed to authenticate: {e}")
                    return None
            
            # Save the credentials for the next run
            try:
                with open(settings.GOOGLE_DRIVE_TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                logger.error(f"Failed to save credentials: {e}")
        
        return creds
    
    def upload_video(self, file: BinaryIO, filename: str, user_id: str) -> Optional[str]:
        """
        Upload video file to Google Drive
        
        Args:
            file: File object to upload
            filename: Original filename
            user_id: User ID for organizing files
            
        Returns:
            Shareable URL of uploaded file or None if failed
        """
        if not self.initialized:
            self.initialize()
            
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
            
        try:
            # Generate unique filename
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
            
            # Prepare file metadata
            file_metadata = {
                'name': unique_filename,
                'description': f'Workout video uploaded by user {user_id} on {datetime.utcnow().isoformat()}',
            }
            
            # Add to specific folder if configured
            if settings.GOOGLE_DRIVE_FOLDER_ID:
                file_metadata['parents'] = [settings.GOOGLE_DRIVE_FOLDER_ID]
            
            # Determine MIME type
            mime_type = self._get_mime_type(file_extension)
            
            # Create media upload object
            media = MediaIoBaseUpload(
                file, 
                mimetype=mime_type,
                resumable=True
            )
            
            # Upload file
            uploaded_file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,webContentLink'
            ).execute()
            
            # Make file publicly viewable
            file_id = uploaded_file.get('id')
            self._make_file_public(file_id)
            
            # Get shareable link
            shareable_url = self._get_shareable_url(file_id)
            
            logger.info(f"Video uploaded successfully: {unique_filename} (ID: {file_id})")
            return shareable_url
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to upload video: {e}")
            return None
    
    def upload_processed_video(self, file_path: str, original_filename: str, user_id: str) -> Optional[str]:
        """
        Upload processed video file to Google Drive
        
        Args:
            file_path: Local path to processed video file
            original_filename: Original filename for reference
            user_id: User ID for organizing files
            
        Returns:
            Shareable URL of uploaded file or None if failed
        """
        if not self.initialized:
            self.initialize()
            
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
            
        try:
            # Generate unique filename for processed video
            file_extension = os.path.splitext(original_filename)[1]
            unique_filename = f"{user_id}_{uuid.uuid4()}_processed{file_extension}"
            
            # Prepare file metadata
            file_metadata = {
                'name': unique_filename,
                'description': f'Processed workout video for user {user_id} on {datetime.utcnow().isoformat()}',
            }
            
            # Add to specific folder if configured
            if settings.GOOGLE_DRIVE_FOLDER_ID:
                file_metadata['parents'] = [settings.GOOGLE_DRIVE_FOLDER_ID]
            
            # Determine MIME type
            mime_type = self._get_mime_type(file_extension)
            
            # Create media upload object
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            # Upload file
            uploaded_file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,webContentLink'
            ).execute()
            
            # Make file publicly viewable
            file_id = uploaded_file.get('id')
            self._make_file_public(file_id)
            
            # Get shareable link
            shareable_url = self._get_shareable_url(file_id)
            
            logger.info(f"Processed video uploaded successfully: {unique_filename} (ID: {file_id})")
            return shareable_url
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to upload processed video: {e}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            self.initialize()
            
        if not self.service:
            logger.error("Google Drive service not initialized")
            return False
            
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"File deleted successfully: {file_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Google Drive API error while deleting: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def list_user_videos(self, user_id: str) -> list:
        """
        List all videos for a specific user
        
        Args:
            user_id: User ID
            
        Returns:
            List of video files
        """
        if not self.initialized:
            self.initialize()
            
        if not self.service:
            logger.error("Google Drive service not initialized")
            return []
            
        try:
            # Search for files with user_id in name
            query = f"name contains '{user_id}' and mimeType contains 'video/'"
            
            if settings.GOOGLE_DRIVE_FOLDER_ID:
                query += f" and '{settings.GOOGLE_DRIVE_FOLDER_ID}' in parents"
            
            results = self.service.files().list(
                q=query,
                fields="files(id,name,size,createdTime,webViewLink)"
            ).execute()
            
            return results.get('files', [])
            
        except HttpError as e:
            logger.error(f"Google Drive API error while listing: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to list user videos: {e}")
            return []
    
    def get_file_info(self, file_id: str) -> Optional[dict]:
        """
        Get file information from Google Drive
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            File information dict or None if failed
        """
        if not self.initialized:
            self.initialize()
            
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
            
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id,name,size,createdTime,modifiedTime,mimeType,webViewLink,webContentLink"
            ).execute()
            
            return file_info
            
        except HttpError as e:
            logger.error(f"Google Drive API error while getting file info: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return None
    
    def _make_file_public(self, file_id: str):
        """Make file publicly viewable"""
        try:
            permission = {
                'role': 'reader',
                'type': 'anyone'
            }
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
        except Exception as e:
            logger.warning(f"Failed to make file public: {e}")
    
    def _get_shareable_url(self, file_id: str) -> str:
        """Get shareable URL for the file"""
        # Return direct download link for videos
        return f"https://drive.google.com/uc?id={file_id}&export=download"
    
    def _get_mime_type(self, file_extension: str) -> str:
        """Get MIME type based on file extension"""
        mime_type, _ = mimetypes.guess_type(f"file{file_extension}")
        if mime_type and mime_type.startswith('video/'):
            return mime_type
        
        # Fallback to common video types
        mime_types = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm'
        }
        return mime_types.get(file_extension.lower(), 'video/mp4')

# Global instance
google_drive_storage = GoogleDriveService()