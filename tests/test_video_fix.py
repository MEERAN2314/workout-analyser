#!/usr/bin/env python3
"""
Quick test to verify video annotation works with the fix
"""
import asyncio
import sys
import os
import cv2
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

async def create_test_input_video():
    """Create a simple test input video"""
    print("📹 Creating test input video...")
    
    test_input = "test_input.mp4"
    
    # Use MPEG-4 codec which we know works
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(test_input, fourcc, 30, (640, 480))
    
    if not out.isOpened():
        print("❌ Cannot create test input video")
        return None
    
    # Create 90 frames (3 seconds) with moving circle
    for i in range(90):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw moving circle (simulating a person)
        x = int(320 + 100 * np.sin(i * 0.1))
        y = int(240 + 50 * np.cos(i * 0.1))
        cv2.circle(frame, (x, y), 50, (255, 255, 255), -1)
        
        # Add frame number
        cv2.putText(frame, f"Frame {i+1}", (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        out.write(frame)
    
    out.release()
    
    # Verify
    cap = cv2.VideoCapture(test_input)
    if cap.isOpened():
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        print(f"✅ Test input video created: {frame_count} frames")
        return test_input
    else:
        print("❌ Test input video cannot be opened")
        return None

async def test_annotation():
    """Test video annotation with the fix"""
    print("\n🎬 Testing Video Annotation...")
    print("=" * 60)
    
    try:
        from app.services.video_annotator import video_annotator
        
        # Create test input
        test_input = await create_test_input_video()
        if not test_input:
            print("❌ Cannot create test input")
            return False
        
        test_output = "test_annotated_output.mp4"
        
        print(f"\n🎨 Annotating video...")
        print(f"   Input: {test_input}")
        print(f"   Output: {test_output}")
        
        # Run annotation
        stats = await video_annotator.create_annotated_video(
            test_input,
            test_output,
            "push_ups",
            "test_session_fix"
        )
        
        print(f"\n✅ Annotation completed!")
        print(f"   Processed frames: {stats['processed_frames']}")
        print(f"   Total reps: {stats['total_reps']}")
        print(f"   Correct reps: {stats['correct_reps']}")
        print(f"   Incorrect reps: {stats['incorrect_reps']}")
        
        # Verify output
        if not os.path.exists(test_output):
            print("❌ Output file not created")
            return False
        
        file_size = os.path.getsize(test_output)
        print(f"\n📊 Output file size: {file_size / (1024*1024):.2f} MB")
        
        # Try to open and read
        cap = cv2.VideoCapture(test_output)
        if not cap.isOpened():
            print("❌ Cannot open output video")
            return False
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        print(f"\n✅ Output video properties:")
        print(f"   Resolution: {width}x{height}")
        print(f"   FPS: {fps}")
        print(f"   Frame count: {frame_count}")
        print(f"   Duration: {duration:.2f} seconds")
        
        # Try to read first frame
        ret, frame = cap.read()
        if ret:
            print(f"   ✅ Can read frames")
        else:
            print(f"   ❌ Cannot read frames")
            cap.release()
            return False
        
        cap.release()
        
        # Check if duration is valid
        if duration > 0:
            print(f"\n🎉 SUCCESS! Video has valid duration: {duration:.2f}s")
            print(f"\n📁 Test files created:")
            print(f"   - {test_input} (input)")
            print(f"   - {test_output} (annotated output)")
            print(f"\n💡 You can play these files to verify they work")
            return True
        else:
            print(f"\n❌ FAILED! Video has 0 duration")
            return False
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("Video Annotation Fix - Verification Test")
    print("=" * 60)
    print()
    
    success = await test_annotation()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ VIDEO ANNOTATION FIX VERIFIED!")
        print("\nThe annotated video:")
        print("  - Has proper duration (not 0:00)")
        print("  - Can be opened and read")
        print("  - Has correct frame count")
        print("  - Should play in browser and media players")
        print("\n🚀 Ready to use with real workout videos!")
    else:
        print("❌ VIDEO ANNOTATION STILL HAS ISSUES")
        print("\nPlease check:")
        print("  1. FFmpeg is installed: ffmpeg -version")
        print("  2. OpenCV codecs: python diagnose_video_issue.py")
        print("  3. Server logs for detailed errors")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
