#!/usr/bin/env python3
"""
Debug script to test video upload functionality
"""
import asyncio
import aiohttp
import os

async def test_upload_debug():
    """Test the upload debug endpoint"""
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Upload Debug Endpoint...")
    
    # Create a small test file
    test_file_path = "test_video.mp4"
    
    # Create a dummy MP4 file for testing (just a few bytes)
    with open(test_file_path, 'wb') as f:
        # Write minimal MP4 header (not a real video, just for testing)
        f.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom')
        f.write(b'\x00' * 100)  # Add some padding
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test the debug endpoint
            with open(test_file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='test_video.mp4', content_type='video/mp4')
                
                async with session.post(f"{base_url}/recording/debug-upload", data=data) as resp:
                    result = await resp.json()
                    
                    print(f"Status Code: {resp.status}")
                    print(f"Response: {result}")
                    
                    if result.get('status') == 'success':
                        print("✅ Upload validation passed!")
                        print(f"   Google Drive Status: {result.get('google_drive_status')}")
                        print(f"   File Size: {result.get('size')} bytes")
                        print(f"   Content Type: {result.get('content_type')}")
                    elif result.get('status') == 'validation_failed':
                        print("❌ Upload validation failed!")
                        print(f"   Error: {result.get('error')}")
                        print(f"   File: {result.get('filename')}")
                        print(f"   Content Type: {result.get('content_type')}")
                        print(f"   Size: {result.get('size')}")
                    else:
                        print("⚠️  Unexpected response!")
                        print(f"   Status: {result.get('status')}")
                        print(f"   Error: {result.get('error')}")
    
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

async def test_main_upload():
    """Test the main upload endpoint with better error handling"""
    base_url = "http://localhost:8000"
    
    print("\n🧪 Testing Main Upload Endpoint...")
    
    # Create a small test file
    test_file_path = "test_video.mp4"
    
    with open(test_file_path, 'wb') as f:
        f.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom')
        f.write(b'\x00' * 1000)  # 1KB test file
    
    try:
        async with aiohttp.ClientSession() as session:
            with open(test_file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='test_video.mp4', content_type='video/mp4')
                data.add_field('exercise_name', 'push_ups')
                data.add_field('user_id', 'test_user')
                
                async with session.post(f"{base_url}/recording/upload", data=data) as resp:
                    print(f"Status Code: {resp.status}")
                    
                    if resp.status == 200:
                        result = await resp.json()
                        print("✅ Upload successful!")
                        print(f"   Session ID: {result.get('session_id')}")
                        print(f"   Status: {result.get('status')}")
                        print(f"   Message: {result.get('message')}")
                    else:
                        error_text = await resp.text()
                        print("❌ Upload failed!")
                        print(f"   Error: {error_text}")
    
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == "__main__":
    print("Starting upload debug tests...")
    print("=" * 50)
    
    try:
        asyncio.run(test_upload_debug())
        asyncio.run(test_main_upload())
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure the server is running on http://localhost:8000")
    
    print("\n" + "=" * 50)
    print("🔧 If upload is still failing:")
    print("1. Check server logs for detailed error messages")
    print("2. Verify Google Drive credentials are set up")
    print("3. Check file format and size limits")
    print("4. Try with a real video file")