#!/usr/bin/env python3
"""
Diagnostic script to identify video encoding issues
"""
import cv2
import sys
import os

def test_video_codecs():
    """Test which video codecs are available"""
    print("🔍 Testing Video Codecs...")
    print("=" * 60)
    
    codecs_to_test = [
        ('avc1', 'H.264 (avc1)'),
        ('H264', 'H.264 (H264)'),
        ('X264', 'x264'),
        ('mp4v', 'MPEG-4'),
        ('XVID', 'Xvid'),
        ('MJPG', 'Motion JPEG'),
    ]
    
    test_file = "test_codec.mp4"
    working_codecs = []
    
    for codec_str, codec_name in codecs_to_test:
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec_str)
            out = cv2.VideoWriter(test_file, fourcc, 30, (640, 480))
            
            if out.isOpened():
                # Write a test frame
                import numpy as np
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                out.write(frame)
                out.release()
                
                # Try to read it back
                cap = cv2.VideoCapture(test_file)
                if cap.isOpened():
                    ret, _ = cap.read()
                    cap.release()
                    
                    if ret:
                        print(f"   ✅ {codec_name}: WORKING")
                        working_codecs.append((codec_str, codec_name))
                    else:
                        print(f"   ⚠️  {codec_name}: Created but cannot read")
                else:
                    print(f"   ❌ {codec_name}: Cannot open created file")
                
                # Clean up
                try:
                    os.remove(test_file)
                except:
                    pass
            else:
                print(f"   ❌ {codec_name}: Cannot create writer")
                
        except Exception as e:
            print(f"   ❌ {codec_name}: Error - {e}")
    
    print("\n" + "=" * 60)
    if working_codecs:
        print(f"✅ Found {len(working_codecs)} working codec(s):")
        for codec_str, codec_name in working_codecs:
            print(f"   - {codec_name} ('{codec_str}')")
        print("\nRecommendation: Use the first working codec in video_annotator.py")
    else:
        print("❌ No working codecs found!")
        print("\nPossible solutions:")
        print("1. Install FFmpeg: sudo apt-get install ffmpeg (Linux)")
        print("2. Install opencv-python-headless: pip install opencv-python-headless")
        print("3. Reinstall opencv: pip uninstall opencv-python && pip install opencv-python")
    
    return working_codecs

def check_ffmpeg():
    """Check if FFmpeg is available"""
    print("\n🎬 Checking FFmpeg...")
    print("=" * 60)
    
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"   ✅ FFmpeg is installed: {version_line}")
            return True
        else:
            print("   ❌ FFmpeg command failed")
            return False
    except FileNotFoundError:
        print("   ❌ FFmpeg is NOT installed")
        print("\n   Install FFmpeg:")
        print("   - Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("   - macOS: brew install ffmpeg")
        print("   - Windows: Download from https://ffmpeg.org/")
        return False
    except Exception as e:
        print(f"   ❌ Error checking FFmpeg: {e}")
        return False

def test_video_file(video_path):
    """Test if a video file can be read"""
    print(f"\n📹 Testing Video File: {video_path}")
    print("=" * 60)
    
    if not os.path.exists(video_path):
        print(f"   ❌ File does not exist: {video_path}")
        return False
    
    file_size = os.path.getsize(video_path)
    print(f"   File size: {file_size / (1024*1024):.2f} MB")
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print("   ❌ Cannot open video file")
            return False
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"   ✅ Video opened successfully")
        print(f"   Resolution: {width}x{height}")
        print(f"   FPS: {fps}")
        print(f"   Frame count: {frame_count}")
        
        # Try to read first frame
        ret, frame = cap.read()
        if ret:
            print(f"   ✅ Can read frames")
        else:
            print(f"   ❌ Cannot read frames")
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def create_test_video():
    """Create a simple test video"""
    print("\n🎨 Creating Test Video...")
    print("=" * 60)
    
    import numpy as np
    
    output_path = "test_output.mp4"
    
    # Try each codec
    codecs = [
        ('avc1', 'H.264'),
        ('mp4v', 'MPEG-4'),
        ('XVID', 'Xvid'),
    ]
    
    for codec_str, codec_name in codecs:
        try:
            print(f"\n   Testing {codec_name}...")
            
            fourcc = cv2.VideoWriter_fourcc(*codec_str)
            out = cv2.VideoWriter(output_path, fourcc, 30, (640, 480))
            
            if not out.isOpened():
                print(f"   ❌ Cannot create writer")
                continue
            
            # Write 30 frames (1 second)
            for i in range(30):
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                # Draw frame number
                cv2.putText(frame, f"Frame {i}", (50, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
                out.write(frame)
            
            out.release()
            
            # Test if we can read it
            if test_video_file(output_path):
                print(f"   ✅ {codec_name} works! Test video created: {output_path}")
                return True
            else:
                print(f"   ❌ {codec_name} created file but cannot read it")
                try:
                    os.remove(output_path)
                except:
                    pass
                
        except Exception as e:
            print(f"   ❌ {codec_name} failed: {e}")
    
    print("\n   ❌ Could not create working test video with any codec")
    return False

if __name__ == "__main__":
    print("Video Encoding Diagnostic Tool")
    print("=" * 60)
    print()
    
    # Test codecs
    working_codecs = test_video_codecs()
    
    # Check FFmpeg
    has_ffmpeg = check_ffmpeg()
    
    # Create test video
    test_success = create_test_video()
    
    # Test existing video if provided
    if len(sys.argv) > 1:
        test_video_file(sys.argv[1])
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"Working OpenCV codecs: {len(working_codecs)}")
    print(f"FFmpeg available: {'Yes' if has_ffmpeg else 'No'}")
    print(f"Test video creation: {'Success' if test_success else 'Failed'}")
    
    if working_codecs or has_ffmpeg:
        print("\n✅ Your system can create videos")
        if has_ffmpeg:
            print("   Recommendation: Use FFmpeg method (most reliable)")
        else:
            print(f"   Recommendation: Use {working_codecs[0][1]} codec")
    else:
        print("\n❌ Video creation may not work properly")
        print("   Please install FFmpeg or fix OpenCV installation")
    
    print("\n" + "=" * 60)
