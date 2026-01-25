"""
Simple Video Annotator - Creates annotated videos with analysis overlay
Matches the reference image: skeleton, rep counters, feedback
"""
import cv2
import numpy as np
from typing import Dict, List, Optional
import logging
import os

from app.services.mediapipe_service import mediapipe_service

logger = logging.getLogger(__name__)

class SimpleVideoAnnotator:
    """Creates annotated videos with skeleton overlay and analysis data"""
    
    def __init__(self):
        # Colors (BGR format for OpenCV)
        self.COLOR_CORRECT = (0, 255, 0)      # Green
        self.COLOR_INCORRECT = (0, 0, 255)    # Red
        self.COLOR_FEEDBACK = (255, 255, 255) # White
        self.COLOR_SKELETON = (0, 255, 255)   # Yellow/Cyan
        self.COLOR_JOINT = (255, 0, 255)      # Magenta
        
        # Font settings
        self.FONT = cv2.FONT_HERSHEY_SIMPLEX
        self.FONT_SCALE_LARGE = 1.0
        self.FONT_SCALE_MEDIUM = 0.7
        self.FONT_THICKNESS = 2
    
    async def create_annotated_video(
        self,
        input_video_path: str,
        output_video_path: str,
        exercise_name: str,
        session_id: str
    ) -> Dict:
        """
        Create annotated video with skeleton overlay and rep counters
        """
        print(f"\n🎨 Creating annotated video...")
        print(f"   Input: {input_video_path}")
        print(f"   Output: {output_video_path}")
        
        cap = None
        out = None
        temp_output = None
        
        try:
            # Verify input exists
            if not os.path.exists(input_video_path):
                raise Exception(f"Input video not found: {input_video_path}")
            
            # Open input video
            cap = cv2.VideoCapture(input_video_path)
            if not cap.isOpened():
                raise Exception("Cannot open input video")
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            if fps <= 0 or fps > 120:
                fps = 30
                print(f"   Using default FPS: {fps}")
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Ensure even dimensions
            if width % 2 != 0:
                width -= 1
            if height % 2 != 0:
                height -= 1
            
            print(f"   Video: {width}x{height}, {fps} FPS, {total_frames} frames")
            
            # Create temporary output with OpenCV
            temp_output = output_video_path.replace('.mp4', '_temp.avi')
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Use XVID for temp file
            out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
            
            if not out or not out.isOpened():
                raise Exception("Cannot create output video writer")
            
            print(f"   Video writer created successfully")
            
            # Processing state
            frame_count = 0
            correct_reps = 0
            incorrect_reps = 0
            current_feedback = []
            last_rep_count = 0
            
            print(f"   Processing frames...")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Resize frame if needed
                if frame.shape[1] != width or frame.shape[0] != height:
                    frame = cv2.resize(frame, (width, height))
                
                # Process frame with MediaPipe
                try:
                    analysis = mediapipe_service.process_frame(frame, exercise_name, session_id)
                    
                    if analysis:
                        # Check for new rep
                        if analysis.rep_count > last_rep_count:
                            if analysis.accuracy_score >= 0.7:
                                correct_reps += 1
                            else:
                                incorrect_reps += 1
                            last_rep_count = analysis.rep_count
                        
                        # Update feedback (keep last 3)
                        if analysis.form_feedback:
                            current_feedback = analysis.form_feedback[-3:]
                        
                        # Draw skeleton overlay
                        frame = self._draw_skeleton(frame, analysis.landmarks)
                except Exception as e:
                    # Continue even if MediaPipe fails on this frame
                    pass
                
                # Draw rep counters (top right)
                frame = self._draw_rep_counters(frame, correct_reps, incorrect_reps)
                
                # Draw feedback (top left)
                frame = self._draw_feedback(frame, current_feedback)
                
                # Write annotated frame
                out.write(frame)
                
                # Progress
                if frame_count % 100 == 0:
                    progress = (frame_count / total_frames) * 100
                    print(f"   Progress: {progress:.0f}%")
            
            print(f"   Processed {frame_count} frames")
            
            # Release resources
            cap.release()
            out.release()
            mediapipe_service.reset_session(session_id)
            
            # Convert to browser-compatible MP4 using FFmpeg
            print(f"   Converting to browser-compatible MP4...")
            
            try:
                import subprocess
                
                # Use FFmpeg to convert to H.264 MP4
                ffmpeg_cmd = [
                    'ffmpeg', '-y',
                    '-i', temp_output,
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '23',
                    '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart',
                    output_video_path
                ]
                
                result = subprocess.run(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=300
                )
                
                if result.returncode != 0:
                    print(f"   FFmpeg error: {result.stderr.decode()}")
                    # If FFmpeg fails, just use the temp file
                    import shutil
                    shutil.move(temp_output, output_video_path)
                    print(f"   Using original format (FFmpeg conversion failed)")
                else:
                    print(f"   ✅ Converted to H.264 MP4")
                    # Remove temp file
                    try:
                        os.remove(temp_output)
                    except:
                        pass
                
            except Exception as conv_error:
                print(f"   Conversion error: {conv_error}")
                # If conversion fails, use temp file
                import shutil
                if os.path.exists(temp_output):
                    shutil.move(temp_output, output_video_path)
                    print(f"   Using original format")
            
            # Verify output file
            if not os.path.exists(output_video_path):
                raise Exception("Output video file was not created")
            
            output_size = os.path.getsize(output_video_path)
            if output_size < 1000:
                raise Exception(f"Output video is too small: {output_size} bytes")
            
            print(f"✅ Annotated video created!")
            print(f"   File size: {output_size / (1024*1024):.2f} MB")
            print(f"   Correct reps: {correct_reps}")
            print(f"   Incorrect reps: {incorrect_reps}")
            
            return {
                "total_frames": total_frames,
                "processed_frames": frame_count,
                "correct_reps": correct_reps,
                "incorrect_reps": incorrect_reps,
                "output_path": output_video_path
            }
            
        except Exception as e:
            print(f"❌ Error creating annotated video: {e}")
            import traceback
            print(traceback.format_exc())
            raise
            
        finally:
            if cap:
                try:
                    cap.release()
                except:
                    pass
            if out:
                try:
                    out.release()
                except:
                    pass
            # Clean up temp file if it exists
            if temp_output and os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except:
                    pass
    
    def _draw_skeleton(self, frame: np.ndarray, landmarks: Dict) -> np.ndarray:
        """Draw skeleton overlay on frame"""
        if not landmarks:
            return frame
        
        height, width = frame.shape[:2]
        
        # Define skeleton connections
        connections = [
            # Torso
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_hip'),
            ('right_shoulder', 'right_hip'),
            ('left_hip', 'right_hip'),
            # Left arm
            ('left_shoulder', 'left_elbow'),
            ('left_elbow', 'left_wrist'),
            # Right arm
            ('right_shoulder', 'right_elbow'),
            ('right_elbow', 'right_wrist'),
            # Left leg
            ('left_hip', 'left_knee'),
            ('left_knee', 'left_ankle'),
            # Right leg
            ('right_hip', 'right_knee'),
            ('right_knee', 'right_ankle')
        ]
        
        # Draw connections (lines)
        for start_name, end_name in connections:
            if start_name in landmarks and end_name in landmarks:
                start_landmark = landmarks[start_name]
                end_landmark = landmarks[end_name]
                
                if start_landmark.visibility > 0.5 and end_landmark.visibility > 0.5:
                    start_point = (int(start_landmark.x * width), int(start_landmark.y * height))
                    end_point = (int(end_landmark.x * width), int(end_landmark.y * height))
                    
                    # Draw line with glow effect
                    cv2.line(frame, start_point, end_point, (0, 0, 0), 6)  # Black outline
                    cv2.line(frame, start_point, end_point, self.COLOR_SKELETON, 3)  # Cyan line
        
        # Draw joints (circles)
        key_joints = ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
                      'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
                      'left_knee', 'right_knee', 'left_ankle', 'right_ankle']
        
        for joint_name in key_joints:
            if joint_name in landmarks:
                landmark = landmarks[joint_name]
                if landmark.visibility > 0.5:
                    point = (int(landmark.x * width), int(landmark.y * height))
                    # Draw circle with glow
                    cv2.circle(frame, point, 8, (0, 0, 0), -1)  # Black outline
                    cv2.circle(frame, point, 6, self.COLOR_JOINT, -1)  # Magenta fill
                    cv2.circle(frame, point, 6, (255, 255, 255), 1)  # White border
        
        return frame
    
    def _draw_rep_counters(self, frame: np.ndarray, correct: int, incorrect: int) -> np.ndarray:
        """Draw rep counters in top right corner (like reference image)"""
        height, width = frame.shape[:2]
        
        # Position (top right)
        x_offset = width - 280
        y_offset = 30
        
        # Draw CORRECT counter (green)
        correct_text = f"CORRECT: {correct}"
        text_size = cv2.getTextSize(correct_text, self.FONT, self.FONT_SCALE_LARGE, self.FONT_THICKNESS)[0]
        
        # Background rectangle
        cv2.rectangle(frame,
                     (x_offset - 10, y_offset - text_size[1] - 10),
                     (x_offset + text_size[0] + 10, y_offset + 10),
                     (0, 150, 0), -1)  # Dark green background
        
        # Checkmark icon
        cv2.putText(frame, "✓", (x_offset - 5, y_offset),
                   self.FONT, self.FONT_SCALE_LARGE, (255, 255, 255), self.FONT_THICKNESS)
        
        # Text
        cv2.putText(frame, correct_text, (x_offset + 25, y_offset),
                   self.FONT, self.FONT_SCALE_LARGE, self.COLOR_CORRECT, self.FONT_THICKNESS)
        
        # Draw INCORRECT counter (red)
        y_offset += 50
        incorrect_text = f"INCORRECT: {incorrect}"
        text_size = cv2.getTextSize(incorrect_text, self.FONT, self.FONT_SCALE_LARGE, self.FONT_THICKNESS)[0]
        
        # Background rectangle
        cv2.rectangle(frame,
                     (x_offset - 10, y_offset - text_size[1] - 10),
                     (x_offset + text_size[0] + 10, y_offset + 10),
                     (0, 0, 150), -1)  # Dark red background
        
        # X icon
        cv2.putText(frame, "✗", (x_offset - 5, y_offset),
                   self.FONT, self.FONT_SCALE_LARGE, (255, 255, 255), self.FONT_THICKNESS)
        
        # Text
        cv2.putText(frame, incorrect_text, (x_offset + 25, y_offset),
                   self.FONT, self.FONT_SCALE_LARGE, self.COLOR_INCORRECT, self.FONT_THICKNESS)
        
        return frame
    
    def _draw_feedback(self, frame: np.ndarray, feedback_list: List[str]) -> np.ndarray:
        """Draw feedback in top left corner (like reference image)"""
        if not feedback_list:
            return frame
        
        height, width = frame.shape[:2]
        
        # Position (top left)
        x_offset = 20
        y_offset = 40
        
        # Draw each feedback message
        for feedback in feedback_list[:3]:  # Max 3 messages
            # Truncate if too long
            if len(feedback) > 25:
                feedback = feedback[:22] + "..."
            
            text_size = cv2.getTextSize(feedback, self.FONT, self.FONT_SCALE_MEDIUM, self.FONT_THICKNESS)[0]
            
            # Background rectangle (red for warnings)
            cv2.rectangle(frame,
                         (x_offset - 5, y_offset - text_size[1] - 5),
                         (x_offset + text_size[0] + 5, y_offset + 5),
                         (0, 0, 150), -1)  # Dark red background
            
            # Text
            cv2.putText(frame, feedback, (x_offset, y_offset),
                       self.FONT, self.FONT_SCALE_MEDIUM, self.COLOR_FEEDBACK, self.FONT_THICKNESS)
            
            y_offset += 40
        
        return frame

# Global instance
video_annotator_simple = SimpleVideoAnnotator()
