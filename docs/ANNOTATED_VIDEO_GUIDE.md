# Annotated Video Export Feature Guide

## 🎬 Overview

The **Annotated Video Export** feature generates a processed video with real-time analysis overlay, including:

- **Skeleton overlay** on the person performing the exercise
- **Rep counters** (Correct/Incorrect) in the top right corner
- **Real-time feedback** messages in the top left corner
- **Angle indicators** at key joints (elbows, knees)
- **Progress bar** at the bottom
- **Professional visualization** matching your reference image

## ✨ Features

### Visual Elements

1. **Skeleton Overlay**
   - Yellow/cyan lines connecting body joints
   - Magenta circles at key joint positions
   - Smooth tracking throughout the video
   - Visibility-based rendering (only shows visible joints)

2. **Rep Counters (Top Right)**
   ```
   ✓ CORRECT: 2    (Green background)
   ✗ INCORRECT: 2  (Red background)
   ```
   - Real-time counting as reps are completed
   - Color-coded for easy identification
   - Large, readable font

3. **Feedback Messages (Top Left)**
   ```
   SQUAT TOO DEEP  (Red background - form issue)
   Keep knees aligned (Yellow - warning)
   Good form! (Green - positive feedback)
   ```
   - Up to 3 most recent feedback messages
   - Color-coded by severity
   - Truncated for readability

4. **Angle Indicators**
   - Shows joint angles (e.g., "145°" at elbow)
   - Positioned near relevant joints
   - Updates in real-time

5. **Progress Bar**
   - Green progress indicator at bottom
   - Shows video completion percentage

## 🚀 How It Works

### Processing Pipeline

```
1. Upload Video
   ↓
2. Frame-by-Frame Analysis
   - MediaPipe pose detection
   - Exercise-specific analysis
   - Rep counting and form scoring
   ↓
3. Annotated Video Generation
   - Draw skeleton overlay
   - Add rep counters
   - Add feedback messages
   - Add angle indicators
   ↓
4. Upload to Google Drive
   ↓
5. Available for Download/Viewing
```

### Technical Implementation

**Backend Services:**
- `video_annotator.py` - Creates annotated video frames
- `video_processor.py` - Orchestrates analysis and annotation
- `mediapipe_service.py` - Provides pose detection and analysis

**Processing Steps:**
1. Download original video from Google Drive
2. Process each frame with MediaPipe
3. Draw analysis overlay on each frame
4. Write annotated frames to new video file
5. Upload annotated video to Google Drive
6. Store URL in database

## 📊 Usage

### For Users

1. **Upload Your Workout Video**
   - Go to Recording Analysis page
   - Select exercise type
   - Upload video (MP4, AVI, MOV, MKV)

2. **Wait for Processing**
   - Video analysis: ~2-5 minutes
   - Annotation generation: Additional 2-3 minutes
   - Progress updates shown in real-time

3. **View Results**
   - Two video options available:
     - **View Annotated Video** (with overlay) ✨
     - **View Original Video** (without overlay)

4. **Download Options**
   - Download annotated video
   - Download PDF report
   - Share or save for later review

### For Developers

#### Enable Annotated Video Generation

```python
# In video_processor.py
result = await video_processor.process_video_from_url(
    video_url, 
    exercise_name, 
    session_id,
    generate_annotated=True  # Enable annotation
)
```

#### Customize Annotation Style

Edit `app/services/video_annotator.py`:

```python
# Colors (BGR format)
self.COLOR_CORRECT = (0, 255, 0)      # Green
self.COLOR_INCORRECT = (0, 0, 255)    # Red
self.COLOR_SKELETON = (0, 255, 255)   # Yellow

# Font settings
self.FONT_SCALE_LARGE = 1.2
self.FONT_THICKNESS_BOLD = 3
```

## 🎨 Customization Options

### Modify Rep Counter Position

```python
# In _draw_rep_counters method
x_offset = width - 300  # Distance from right edge
y_offset = 40           # Distance from top
```

### Modify Feedback Position

```python
# In _draw_feedback method
x_offset = 20   # Distance from left edge
y_offset = 40   # Distance from top
```

### Change Skeleton Colors

```python
# Different colors for different body parts
if 'shoulder' in name or 'elbow' in name:
    color = (255, 0, 0)  # Blue for arms
elif 'hip' in name or 'knee' in name:
    color = (0, 0, 255)  # Red for legs
```

## 📈 Performance

### Processing Times

- **Analysis Only:** ~2-5 minutes for 1-minute video
- **With Annotation:** ~4-8 minutes for 1-minute video
- **Factors:** Video length, resolution, frame rate

### Optimization Tips

1. **Lower Resolution:** Process at 720p for faster results
2. **Frame Sampling:** Process every 2nd or 3rd frame
3. **Parallel Processing:** Use multiple Celery workers
4. **GPU Acceleration:** Enable if available for MediaPipe

### Resource Usage

- **CPU:** High during processing (80-100%)
- **Memory:** ~500MB-1GB per video
- **Storage:** Annotated video ~2x original size
- **Network:** Upload/download bandwidth dependent

## 🔧 Configuration

### Video Output Settings

```python
# In video_annotator.py
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec
fps = int(cap.get(cv2.CAP_PROP_FPS))      # Match input FPS
```

### Quality Settings

```python
# Higher quality (larger file)
fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec

# Lower quality (smaller file)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MPEG-4 codec
```

## 🐛 Troubleshooting

### Issue: Annotated video not generated

**Solutions:**
1. Check server logs for errors
2. Verify MediaPipe is working
3. Ensure sufficient disk space
4. Check Google Drive permissions

### Issue: Skeleton not visible

**Solutions:**
1. Verify pose detection is working
2. Check landmark visibility thresholds
3. Ensure good lighting in original video
4. Try different exercise type

### Issue: Rep counters not updating

**Solutions:**
1. Check exercise-specific thresholds
2. Verify rep counting logic
3. Review MediaPipe analysis results
4. Test with known good video

### Issue: Video playback issues

**Solutions:**
1. Try different browser
2. Check video codec compatibility
3. Download and play locally
4. Verify Google Drive link is accessible

## 📝 API Reference

### Generate Annotated Video

```python
from app.services.video_annotator import video_annotator

stats = await video_annotator.create_annotated_video(
    input_video_path="path/to/input.mp4",
    output_video_path="path/to/output.mp4",
    exercise_name="push_ups",
    session_id="session_123",
    progress_callback=my_callback  # Optional
)
```

### Response Format

```python
{
    "total_frames": 300,
    "processed_frames": 300,
    "correct_reps": 8,
    "incorrect_reps": 2,
    "total_reps": 10,
    "output_path": "path/to/output.mp4"
}
```

## 🎯 Best Practices

### For Best Results

1. **Good Lighting:** Ensure person is well-lit
2. **Full Body Visible:** Keep entire body in frame
3. **Stable Camera:** Use tripod or stable surface
4. **Clear Background:** Minimize clutter
5. **Proper Distance:** 6-10 feet from camera

### Video Recording Tips

1. **Orientation:** Landscape mode preferred
2. **Resolution:** 720p or 1080p recommended
3. **Frame Rate:** 30 FPS minimum
4. **Duration:** Keep under 5 minutes for faster processing
5. **Format:** MP4 with H.264 codec

## 🚀 Future Enhancements

Potential improvements:

- [ ] Multiple camera angles
- [ ] Side-by-side comparison with ideal form
- [ ] Slow-motion replay of key moments
- [ ] 3D skeleton visualization
- [ ] Custom branding/watermarks
- [ ] Social media optimized formats
- [ ] Real-time streaming annotation
- [ ] AR overlay for mobile devices

## 📊 Example Output

Your annotated video will look like this:

```
┌─────────────────────────────────────────────────┐
│ SQUAT TOO DEEP          ✓ CORRECT: 2           │
│                         ✗ INCORRECT: 2          │
│                                                  │
│                                                  │
│              [Person with skeleton overlay]      │
│                    145° (at elbow)              │
│                    90° (at knee)                │
│                                                  │
│                                                  │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░  │
└─────────────────────────────────────────────────┘
```

## ✅ Status

**Feature Status:** ✅ Fully Implemented

**Available In:** Phase 3 (Current)

**Components:**
- ✅ Video annotation service
- ✅ Skeleton overlay rendering
- ✅ Rep counter display
- ✅ Feedback message system
- ✅ Google Drive integration
- ✅ Frontend video player
- ✅ Download functionality

## 📞 Support

For issues or questions:
1. Check server logs: `tail -f logs/app.log`
2. Test annotation service: `python test_video_annotation.py`
3. Review MediaPipe output
4. Check Google Drive permissions

---

**Last Updated:** January 25, 2026
**Version:** 3.4 (Annotated Video Export)
**Status:** Production Ready ✅
