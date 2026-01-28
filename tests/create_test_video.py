#!/usr/bin/env python3
"""
Create a minimal test video file for testing
"""
import cv2
import numpy as np
import os

def create_test_video(filename="test_workout.mp4", duration_seconds=5):
    """Create a simple test video with moving shapes"""
    
    # Video properties
    width, height = 640, 480
    fps = 30
    total_frames = duration_seconds * fps
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    print(f"Creating test video: {filename}")
    print(f"Duration: {duration_seconds}s, Frames: {total_frames}, FPS: {fps}")
    
    for frame_num in range(total_frames):
        # Create a frame with moving elements (simulating a person)
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Background
        frame[:] = (50, 50, 50)  # Dark gray background
        
        # Simulate a person doing push-ups (moving circle)
        center_x = width // 2
        center_y = int(height // 2 + 50 * np.sin(frame_num * 0.2))  # Up and down motion
        
        # Draw "person" (circle)
        cv2.circle(frame, (center_x, center_y), 30, (0, 255, 0), -1)
        
        # Draw "arms" (lines)
        arm_length = 40
        cv2.line(frame, (center_x - arm_length, center_y), (center_x + arm_length, center_y), (255, 255, 255), 5)
        
        # Add frame number for debugging
        cv2.putText(frame, f"Frame {frame_num}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Write frame
        out.write(frame)
    
    # Release everything
    out.release()
    
    # Check if file was created successfully
    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        print(f"✅ Video created successfully: {filename}")
        print(f"   File size: {file_size / 1024:.1f} KB")
        
        # Verify the video can be opened
        cap = cv2.VideoCapture(filename)
        if cap.isOpened():
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            video_duration = frame_count / video_fps if video_fps > 0 else 0
            
            print(f"   Verification: {frame_count} frames, {video_fps} FPS, {video_duration:.1f}s duration")
            cap.release()
            return True
        else:
            print("❌ Created video cannot be opened")
            return False
    else:
        print("❌ Failed to create video file")
        return False

if __name__ == "__main__":
    print("Creating test video for workout analysis...")
    
    # Create a short test video
    success = create_test_video("test_workout.mp4", duration_seconds=3)
    
    if success:
        print("\n🎉 Test video created successfully!")
        print("You can now upload 'test_workout.mp4' to test the system.")
        print("\nTo test:")
        print("1. Go to http://localhost:8000/recording/")
        print("2. Upload the test_workout.mp4 file")
        print("3. Watch the processing pipeline work!")
    else:
        print("\n❌ Failed to create test video")
        print("Make sure OpenCV is installed: pip install opencv-python")