#!/usr/bin/env python3
"""
Test script to verify annotated video functionality
"""
import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_annotated_video():
    """Test the annotated video feature"""
    
    print("="*80)
    print("🧪 ANNOTATED VIDEO TEST")
    print("="*80)
    
    # Step 1: Check if server is running
    print("\n1️⃣  Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running")
        else:
            print(f"   ❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to server: {e}")
        print("   💡 Make sure to run: python run.py")
        return False
    
    # Step 2: Ask user for session ID
    print("\n2️⃣  Enter a session ID to test:")
    print("   (Upload a video first at http://localhost:8000/recording/)")
    print("   Then check the browser console for the session ID")
    
    session_id = input("\n   Session ID: ").strip()
    
    if not session_id:
        print("   ❌ No session ID provided")
        return False
    
    # Step 3: Check if session exists
    print(f"\n3️⃣  Checking session: {session_id}")
    try:
        response = requests.get(f"{BASE_URL}/recording/results/{session_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Session found")
            print(f"      Exercise: {data.get('exercise_name', 'unknown')}")
            print(f"      Total Reps: {data.get('total_reps', 0)}")
            print(f"      Accuracy: {data.get('accuracy_score', 0) * 100:.1f}%")
        else:
            print(f"   ❌ Session not found (status {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Error checking session: {e}")
        return False
    
    # Step 4: Check if annotated video exists
    print(f"\n4️⃣  Checking annotated video...")
    try:
        response = requests.head(f"{BASE_URL}/recording/annotated-video/{session_id}")
        if response.status_code == 200:
            print(f"   ✅ Annotated video is available!")
            content_length = response.headers.get('Content-Length', 'unknown')
            if content_length != 'unknown':
                size_mb = int(content_length) / (1024 * 1024)
                print(f"      Size: {size_mb:.2f} MB")
        elif response.status_code == 404:
            print(f"   ⚠️  Annotated video not found")
            print(f"      This might mean:")
            print(f"      - Video is still being processed")
            print(f"      - Annotation failed during upload")
            print(f"      - Video was uploaded before annotation feature was added")
            return False
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error checking annotated video: {e}")
        return False
    
    # Step 5: Test video streaming
    print(f"\n5️⃣  Testing video streaming...")
    try:
        response = requests.get(
            f"{BASE_URL}/recording/annotated-video/{session_id}",
            stream=True,
            timeout=10
        )
        
        if response.status_code == 200:
            # Read first chunk
            chunk = next(response.iter_content(chunk_size=8192))
            if chunk:
                print(f"   ✅ Video streaming works!")
                print(f"      First chunk size: {len(chunk)} bytes")
                print(f"      Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        else:
            print(f"   ❌ Streaming failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error streaming video: {e}")
        return False
    
    # Success!
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED!")
    print("="*80)
    print(f"\n🎥 View your annotated video at:")
    print(f"   {BASE_URL}/recording/annotated-video/{session_id}")
    print(f"\n💡 Or click 'View Annotated Video' button in the web interface")
    print("="*80)
    
    return True

if __name__ == "__main__":
    success = test_annotated_video()
    sys.exit(0 if success else 1)
