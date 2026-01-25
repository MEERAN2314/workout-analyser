"""
Professional Video Annotator - Creates polished annotated videos with analysis overlay
"""
import cv2
import numpy as np
from typing import Dict, List, Optional
import logging
import os

from app.services.mediapipe_service import mediapipe_service

logger = logging.getLogger(__name__)

class SimpleVideoAnnotator:
    """Creates professional annotated videos with skeleton overlay and analysis data"""
    
    def __init__(self):
        # Professional color scheme (BGR format for OpenCV)
        self.COLOR_CORRECT = (76, 175, 80)        # Material Green
        self.COLOR_INCORRECT = (244, 67, 54)      # Material Red
        self.COLOR_FEEDBACK_BG = (33, 33, 33)     # Dark Gray
        self.COLOR_FEEDBACK_TEXT = (255, 255, 255) # White
        self.COLOR_SKELETON_PRIMARY = (255, 193, 7)  # Amber/Gold
        self.COLOR_SKELETON_SECONDARY = (33, 150, 243) # Blue
        self.COLOR_JOINT = (156, 39, 176)         # Purple
        self.COLOR_OVERLAY_BG = (0, 0, 0)         # Black for backgrounds
        
        # Font settings - Professional
        self.FONT = cv2.FONT_HERSHEY_DUPLEX  # More professional font
        self.FONT_SCALE_LARGE = 0.9
        self.FONT_SCALE_MEDIUM = 0.65
        self.FONT_SCALE_SMALL = 0.5
        self.FONT_THICKNESS_BOLD = 2
        self.FONT_THICKNESS_NORMAL = 1
        
        # UI settings
        self.PADDING = 15
        self.CORNER_RADIUS = 8
        self.SHADOW_OFFSET = 3
    
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
                
                # Draw professional branding (bottom center)
                frame = self._draw_branding(frame, exercise_name)
                
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
        """Draw professional skeleton overlay with smooth lines and gradients"""
        if not landmarks:
            return frame
        
        height, width = frame.shape[:2]
        
        # Create overlay for transparency effects
        overlay = frame.copy()
        
        # Define skeleton connections with grouping
        torso_connections = [
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_hip'),
            ('right_shoulder', 'right_hip'),
            ('left_hip', 'right_hip'),
        ]
        
        left_arm_connections = [
            ('left_shoulder', 'left_elbow'),
            ('left_elbow', 'left_wrist'),
        ]
        
        right_arm_connections = [
            ('right_shoulder', 'right_elbow'),
            ('right_elbow', 'right_wrist'),
        ]
        
        left_leg_connections = [
            ('left_hip', 'left_knee'),
            ('left_knee', 'left_ankle'),
        ]
        
        right_leg_connections = [
            ('right_hip', 'right_knee'),
            ('right_knee', 'right_ankle'),
        ]
        
        # Draw connections with smooth anti-aliased lines
        def draw_connection_group(connections, color, thickness=4):
            for start_name, end_name in connections:
                if start_name in landmarks and end_name in landmarks:
                    start_landmark = landmarks[start_name]
                    end_landmark = landmarks[end_name]
                    
                    if start_landmark.visibility > 0.5 and end_landmark.visibility > 0.5:
                        start_point = (int(start_landmark.x * width), int(start_landmark.y * height))
                        end_point = (int(end_landmark.x * width), int(end_landmark.y * height))
                        
                        # Draw shadow for depth
                        shadow_offset = 2
                        cv2.line(overlay, 
                                (start_point[0] + shadow_offset, start_point[1] + shadow_offset),
                                (end_point[0] + shadow_offset, end_point[1] + shadow_offset),
                                (0, 0, 0), thickness + 2, cv2.LINE_AA)
                        
                        # Draw main line with anti-aliasing
                        cv2.line(overlay, start_point, end_point, color, thickness, cv2.LINE_AA)
        
        # Draw different body parts with different colors
        draw_connection_group(torso_connections, self.COLOR_SKELETON_PRIMARY, 5)
        draw_connection_group(left_arm_connections, self.COLOR_SKELETON_SECONDARY, 4)
        draw_connection_group(right_arm_connections, self.COLOR_SKELETON_SECONDARY, 4)
        draw_connection_group(left_leg_connections, self.COLOR_SKELETON_PRIMARY, 4)
        draw_connection_group(right_leg_connections, self.COLOR_SKELETON_PRIMARY, 4)
        
        # Blend overlay with original frame for smooth appearance
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        
        # Draw joints with professional styling
        key_joints = {
            'shoulders': ['left_shoulder', 'right_shoulder'],
            'elbows': ['left_elbow', 'right_elbow'],
            'wrists': ['left_wrist', 'right_wrist'],
            'hips': ['left_hip', 'right_hip'],
            'knees': ['left_knee', 'right_knee'],
            'ankles': ['left_ankle', 'right_ankle']
        }
        
        for joint_group, joint_names in key_joints.items():
            for joint_name in joint_names:
                if joint_name in landmarks:
                    landmark = landmarks[joint_name]
                    if landmark.visibility > 0.5:
                        point = (int(landmark.x * width), int(landmark.y * height))
                        
                        # Draw shadow
                        cv2.circle(frame, (point[0] + 2, point[1] + 2), 8, (0, 0, 0), -1, cv2.LINE_AA)
                        
                        # Draw outer ring
                        cv2.circle(frame, point, 8, (255, 255, 255), 2, cv2.LINE_AA)
                        
                        # Draw inner fill
                        cv2.circle(frame, point, 6, self.COLOR_JOINT, -1, cv2.LINE_AA)
        
        return frame
    
    def _draw_rounded_rectangle(self, frame: np.ndarray, pt1: tuple, pt2: tuple, color: tuple, thickness: int = -1, radius: int = 8):
        """Draw a rounded rectangle with smooth corners"""
        x1, y1 = pt1
        x2, y2 = pt2
        
        # Draw rectangles
        cv2.rectangle(frame, (x1 + radius, y1), (x2 - radius, y2), color, thickness, cv2.LINE_AA)
        cv2.rectangle(frame, (x1, y1 + radius), (x2, y2 - radius), color, thickness, cv2.LINE_AA)
        
        # Draw circles for corners
        cv2.circle(frame, (x1 + radius, y1 + radius), radius, color, thickness, cv2.LINE_AA)
        cv2.circle(frame, (x2 - radius, y1 + radius), radius, color, thickness, cv2.LINE_AA)
        cv2.circle(frame, (x1 + radius, y2 - radius), radius, color, thickness, cv2.LINE_AA)
        cv2.circle(frame, (x2 - radius, y2 - radius), radius, color, thickness, cv2.LINE_AA)
        
        return frame
    
    def _draw_text_with_background(self, frame: np.ndarray, text: str, position: tuple, 
                                   font_scale: float, text_color: tuple, bg_color: tuple, 
                                   padding: int = 10, alpha: float = 0.85):
        """Draw text with a professional background box"""
        x, y = position
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(
            text, self.FONT, font_scale, self.FONT_THICKNESS_BOLD
        )
        
        # Create overlay for transparency
        overlay = frame.copy()
        
        # Draw shadow
        shadow_offset = 3
        self._draw_rounded_rectangle(
            overlay,
            (x - padding + shadow_offset, y - text_height - padding + shadow_offset),
            (x + text_width + padding + shadow_offset, y + baseline + padding + shadow_offset),
            (0, 0, 0),
            -1,
            self.CORNER_RADIUS
        )
        
        # Draw background
        self._draw_rounded_rectangle(
            overlay,
            (x - padding, y - text_height - padding),
            (x + text_width + padding, y + baseline + padding),
            bg_color,
            -1,
            self.CORNER_RADIUS
        )
        
        # Blend overlay
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Draw text with shadow
        cv2.putText(frame, text, (x + 1, y + 1), self.FONT, font_scale, 
                   (0, 0, 0), self.FONT_THICKNESS_BOLD + 1, cv2.LINE_AA)
        cv2.putText(frame, text, (x, y), self.FONT, font_scale, 
                   text_color, self.FONT_THICKNESS_BOLD, cv2.LINE_AA)
        
        return text_height + baseline + 2 * padding
    
    def _draw_rep_counters(self, frame: np.ndarray, correct: int, incorrect: int) -> np.ndarray:
        """Draw professional rep counters in top right corner"""
        height, width = frame.shape[:2]
        
        # Position (top right with margin)
        margin = 20
        x_offset = width - 280
        y_offset = margin + 35
        
        # Draw CORRECT counter (without Unicode symbols)
        correct_text = f"CORRECT: {correct}"
        y_offset += self._draw_text_with_background(
            frame, correct_text, (x_offset, y_offset),
            self.FONT_SCALE_LARGE, (255, 255, 255), self.COLOR_CORRECT,
            padding=12, alpha=0.9
        )
        
        # Add spacing
        y_offset += 10
        
        # Draw INCORRECT counter (without Unicode symbols)
        incorrect_text = f"INCORRECT: {incorrect}"
        self._draw_text_with_background(
            frame, incorrect_text, (x_offset, y_offset),
            self.FONT_SCALE_LARGE, (255, 255, 255), self.COLOR_INCORRECT,
            padding=12, alpha=0.9
        )
        
        return frame
    
    def _draw_feedback(self, frame: np.ndarray, feedback_list: List[str]) -> np.ndarray:
        """Draw professional feedback messages in top left corner"""
        if not feedback_list:
            return frame
        
        height, width = frame.shape[:2]
        
        # Position (top left with margin)
        margin = 20
        x_offset = margin
        y_offset = margin + 30
        
        # Draw title
        y_offset += self._draw_text_with_background(
            frame, "FORM FEEDBACK", (x_offset, y_offset),
            self.FONT_SCALE_MEDIUM, (255, 193, 7), self.COLOR_FEEDBACK_BG,
            padding=8, alpha=0.85
        )
        
        y_offset += 8
        
        # Draw each feedback message
        for feedback in feedback_list[:3]:  # Max 3 messages
            # Truncate if too long
            if len(feedback) > 35:
                feedback = feedback[:32] + "..."
            
            y_offset += self._draw_text_with_background(
                frame, feedback, (x_offset, y_offset),
                self.FONT_SCALE_SMALL, self.COLOR_FEEDBACK_TEXT, self.COLOR_FEEDBACK_BG,
                padding=8, alpha=0.8
            )
            
            y_offset += 5
        
        return frame

    def _draw_branding(self, frame: np.ndarray, exercise_name: str) -> np.ndarray:
        """Draw professional branding at the bottom"""
        height, width = frame.shape[:2]
        
        # Position (bottom center)
        exercise_display = exercise_name.replace('_', ' ').upper()
        branding_text = f"{exercise_display} ANALYSIS"  # Removed emoji
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(
            branding_text, self.FONT, self.FONT_SCALE_MEDIUM, self.FONT_THICKNESS_NORMAL
        )
        
        x_offset = (width - text_width) // 2
        y_offset = height - 30
        
        # Create semi-transparent overlay
        overlay = frame.copy()
        
        # Draw background bar
        bar_height = 50
        cv2.rectangle(overlay, (0, height - bar_height), (width, height), 
                     self.COLOR_OVERLAY_BG, -1)
        
        # Blend
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Draw text with glow effect
        cv2.putText(frame, branding_text, (x_offset + 2, y_offset + 2), 
                   self.FONT, self.FONT_SCALE_MEDIUM, (0, 0, 0), 
                   self.FONT_THICKNESS_BOLD, cv2.LINE_AA)
        cv2.putText(frame, branding_text, (x_offset, y_offset), 
                   self.FONT, self.FONT_SCALE_MEDIUM, self.COLOR_SKELETON_PRIMARY, 
                   self.FONT_THICKNESS_NORMAL, cv2.LINE_AA)
        
        return frame

# Global instance
video_annotator_simple = SimpleVideoAnnotator()
