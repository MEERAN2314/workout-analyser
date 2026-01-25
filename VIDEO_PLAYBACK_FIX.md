# Video Playback Issue - Fix Guide

## Problem
Annotated videos are created but cannot be played back (showing 0:00 duration).

## Root Cause
Video codec compatibility issue with OpenCV VideoWriter.

## Solutions

### Solution 1: Install FFmpeg (Recommended)

FFmpeg provides the most reliable video encoding.

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/ and add to PATH

**Verify installation:**
```bash
ffmpeg -version
```

### Solution 2: Diagnose and Fix OpenCV

Run the diagnostic script:
```bash
python diagnose_video_issue.py
```

This will:
- Test all available video codecs
- Check FFmpeg availability
- Create a test video
- Provide specific recommendations

### Solution 3: Reinstall OpenCV

Sometimes OpenCV needs to be reinstalled with proper codec support:

```bash
# Uninstall current OpenCV
pip uninstall opencv-python opencv-python-headless

# Install with full codec support
pip install opencv-python

# Or try headless version
pip install opencv-python-headless
```

### Solution 4: Use Alternative Method

The code now includes a fallback method that:
1. Saves frames as images
2. Uses FFmpeg to combine them (if available)
3. Falls back to OpenCV with different settings

This happens automatically if the primary method fails.

## Testing

### Test 1: Check Available Codecs
```bash
python diagnose_video_issue.py
```

### Test 2: Test with Sample Video
```bash
python diagnose_video_issue.py path/to/your/video.mp4
```

### Test 3: Create Test Annotated Video
```python
import asyncio
from app.services.video_annotator import video_annotator

asyncio.run(video_annotator.create_annotated_video(
    "input.mp4",
    "output.mp4", 
    "push_ups",
    "test_session"
))
```

## Quick Fix Applied

I've updated the code to:

1. **Try Multiple Codecs** - Tests H.264, x264, MPEG-4 in order
2. **Validate FPS** - Fixes invalid frame rates
3. **Ensure Even Dimensions** - Required by some codecs
4. **Verify Output** - Checks file size and frame count
5. **Fallback Method** - Uses frame-by-frame + FFmpeg if needed

## Immediate Action

1. **Install FFmpeg:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # macOS
   brew install ffmpeg
   ```

2. **Restart your server:**
   ```bash
   python run.py
   ```

3. **Upload a new video** - The system will now use the most compatible method

## Verification

After applying fixes, verify:

```bash
# 1. Check FFmpeg
ffmpeg -version

# 2. Run diagnostic
python diagnose_video_issue.py

# 3. Test video creation
python test_video_annotation.py

# 4. Upload video through web interface
# Go to http://localhost:8000/recording/
```

## Expected Output

After fixes, you should see:
- Video file created with proper size (not 0 bytes)
- Video duration shown correctly (not 0:00)
- Video plays in browser
- Video can be downloaded and played locally

## Troubleshooting

### Issue: "No working codecs found"
**Solution:** Install FFmpeg (see Solution 1)

### Issue: "FFmpeg not found"
**Solution:** Install FFmpeg and ensure it's in PATH

### Issue: "Output video has 0 frames"
**Solution:** Check input video is valid, try different codec

### Issue: Video created but won't play
**Solution:** 
1. Check file size (should be > 1MB for typical video)
2. Try opening with VLC player
3. Check browser console for errors
4. Try different browser

## Code Changes Made

### video_annotator.py
- Added multiple codec fallback
- Added FPS validation
- Added dimension correction
- Added output verification
- Added simple fallback method with FFmpeg

### Files to Check
1. `app/services/video_annotator.py` - Main annotation logic
2. `diagnose_video_issue.py` - Diagnostic tool
3. `VIDEO_PLAYBACK_FIX.md` - This guide

## Status

✅ Code updated with fixes
✅ Diagnostic tool created
✅ Fallback methods implemented
⏳ Requires FFmpeg installation (recommended)
⏳ Requires server restart

## Next Steps

1. Install FFmpeg
2. Run diagnostic script
3. Restart server
4. Test with new video upload
5. Verify playback works

---

**Last Updated:** January 25, 2026
**Issue:** Video playback failure
**Status:** Fixes implemented, requires FFmpeg
