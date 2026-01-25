"""
Video Annotator Service - Creates annotated workout videos with analysis overlay
"""
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import tempfile
import os

from app.services.mediapipe_service import mediapipe_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class VideoAnnotator:
    """
    Creates annotated videos with:
    - Skeleton overlay on the person
    - Rep counters (correct/incorrect) in top right
    - Real-time feedback in top left
    - Form analysis visualization
    """
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        
        # Colors (BGR format for OpenCV)
        self.COLOR_CORRECT = (0, 255, 0)      # Green
        self.COLOR_INCORRECT = (0, 0, 255)    # Red
        self.COLOR_FEEDBACK = (255, 255, 255) # White
        self.COLOR_SKELETON = (0, 255, 255)   # Yellow
        self.COLOR_JOINT = (255, 0, 255)      # Magenta
        
        # Font settings
        self.FONT = cv2.FONT_HERSHEY_SIMPLEX
        self.FONT_SCALE_LARGE = 1.2
        self.FONT_SCALE_MEDIUM = 0.8
        self.FONT_SCALE_SMALL = 0.6
        self.FONT_THICKNESS_BOLD = 3
        self.FONT_THICKNESS_NORMAL = 2
    
    async def create_annotated_video(
        self, 
        input_video_path: str, 
        output_video_path: str,
        exercise_name: str,
        session_id: str,
        progress_callback=None
    ) -> Dict:
        """
        Create annotated video with analysis overlay
        
        Args:
            input_video_path: Path to input video file
            output_video_path: Path to save annotated video
            exercise_name: Type of exercise being analyzed
            session_id: Session identifier for tracking
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info(f"Starting video annotation for session {session_id}")
        
        # Check if FFmpeg is available (more reliable than OpenCV)
        has_ffmpeg = self._check_ffmpeg_available()
        
        if has_ffmpeg:
            logger.info("FFmpeg detected, using FFmpeg method for better compatibility")
            try:
                return await self._create_annotated_video_simple(
                    input_video_path, output_video_path, exercise_name, session_id, progress_callback
                )
            except Exception as e:
                logger.error(f"FFmpeg method failed: {e}, falling back to OpenCV")
        
        # Try OpenCV method
        try:
            return await self._create_annotated_video_opencv(
                input_video_path, output_video_path, exercise_name, session_id, progress_callback
            )
        except Exception as e:
            logger.error(f"OpenCV annotation failed: {e}")
            
            # If OpenCV failed and we haven't tried FFmpeg yet, try it now
            if not has_ffmpeg:
                logger.info("Trying alternative method with frame-by-frame processing...")
                try:
                    return await self._create_annotated_video_simple(
                        input_video_path, output_video_path, exercise_name, session_id, progress_callback
                    )
                except Exception as e2:
                    logger.error(f"Alternative annotation method also failed: {e2}")
            
            raise Exception(f"Video annotation failed: {e}")
    
    def _check_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available on the system"""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    async def _create_annotated_video_opencv(
        self, 
        input_video_path: str, 
        output_video_path: str,
        exercise_name: str,
        session_id: str,
        progress_callback=None
    ) -> Dict:
        """
        Create annotated video with analysis overlay
        
        Args:
            input_video_path: Path to input video file
            output_video_path: Path to save annotated video
            exercise_name: Type of exercise being analyzed
            session_id: Session identifier for tracking
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info(f"Starting video annotation for session {session_id}")
        
        try:
            # Open input video
            cap = cv2.VideoCapture(input_video_path)
            
            if not cap.isOpened():
                raise Exception("Could not open input video")
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Validate and fix FPS if needed
            if fps <= 0 or fps > 120:
                logger.warning(f"Invalid FPS detected: {fps}, using default 30")
                fps = 30
            
            # Ensure dimensions are even numbers (required by some codecs)
            if width % 2 != 0:
                width -= 1
            if height % 2 != 0:
                height -= 1
            
            logger.info(f"Video properties: {width}x{height}, {fps} FPS, {total_frames} frames")
            
            # Create video writer with compatible codec
            # Try multiple codecs in order of preference (based on system compatibility)
            codecs_to_try = [
                ('mp4v', 'MPEG-4'),  # Most compatible, works on this system
                ('XVID', 'Xvid'),    # Alternative
                ('MJPG', 'Motion JPEG'),  # Fallback
                ('avc1', 'H.264'),   # Try H.264 if available
            ]
            
            out = None
            used_codec = None
            
            for codec_str, codec_name in codecs_to_try:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec_str)
                    test_out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
                    
                    if test_out.isOpened():
                        out = test_out
                        used_codec = codec_name
                        logger.info(f"Using codec: {codec_name} ({codec_str})")
                        break
                    else:
                        test_out.release()
                except Exception as e:
                    logger.warning(f"Codec {codec_name} failed: {e}")
                    continue
            
            if out is None or not out.isOpened():
                raise Exception("Could not create output video writer with any codec")
            
            # Processing state
            frame_count = 0
            correct_reps = 0
            incorrect_reps = 0
            current_feedback = []
            last_rep_count = 0
            
            logger.info("Starting frame-by-frame annotation...")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Process frame with MediaPipe
                analysis_result = mediapipe_service.process_frame(frame, exercise_name, session_id)
                
                if analysis_result:
                    # Check if new rep was completed
                    if analysis_result.rep_count > last_rep_count:
                        # Determine if rep was correct based on accuracy
                        if analysis_result.accuracy_score >= 0.7:
                            correct_reps += 1
                        else:
                            incorrect_reps += 1
                        last_rep_count = analysis_result.rep_count
                    
                    # Update feedback
                    current_feedback = analysis_result.form_feedback[-3:] if analysis_result.form_feedback else []
                    
                    # Draw skeleton overlay
                    frame = self._draw_skeleton(frame, analysis_result.landmarks)
                    
                    # Draw angle indicators for key joints
                    frame = self._draw_angle_indicators(frame, analysis_result.angle_data, analysis_result.landmarks)
                
                # Draw rep counters (top right)
                frame = self._draw_rep_counters(frame, correct_reps, incorrect_reps)
                
                # Draw feedback (top left)
                frame = self._draw_feedback(frame, current_feedback)
                
                # Draw progress bar at bottom
                frame = self._draw_progress_bar(frame, frame_count, total_frames)
                
                # Ensure frame dimensions match output video
                if frame.shape[1] != width or frame.shape[0] != height:
                    frame = cv2.resize(frame, (width, height))
                
                # Write annotated frame
                success = out.write(frame)
                
                if not success:
                    logger.warning(f"Failed to write frame {frame_count}")
                
                # Progress callback
                if progress_callback and frame_count % 30 == 0:  # Update every 30 frames
                    progress = int((frame_count / total_frames) * 100)
                    await progress_callback(progress, f"Annotating frame {frame_count}/{total_frames}")
                
                # Log progress periodically
                if frame_count % 100 == 0:
                    logger.info(f"Annotated {frame_count}/{total_frames} frames ({frame_count/total_frames*100:.1f}%)")
            
            # Release resources
            cap.release()
            out.release()
            
            # Verify output file was created and has content
            if not os.path.exists(output_video_path):
                raise Exception("Output video file was not created")
            
            file_size = os.path.getsize(output_video_path)
            if file_size < 1000:  # Less than 1KB is suspicious
                raise Exception(f"Output video file is too small ({file_size} bytes)")
            
            logger.info(f"Output video created: {output_video_path} ({file_size / (1024*1024):.2f} MB)")
            
            # Verify video can be opened
            verify_cap = cv2.VideoCapture(output_video_path)
            if not verify_cap.isOpened():
                verify_cap.release()
                raise Exception("Output video cannot be opened for verification")
            
            verify_frames = int(verify_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            verify_cap.release()
            
            if verify_frames == 0:
                raise Exception("Output video has 0 frames")
            
            logger.info(f"Output video verified: {verify_frames} frames")
            
            # Clean up MediaPipe session
            mediapipe_service.reset_session(session_id)
            
            stats = {
                "total_frames": total_frames,
                "processed_frames": frame_count,
                "correct_reps": correct_reps,
                "incorrect_reps": incorrect_reps,
                "total_reps": correct_reps + incorrect_reps,
                "output_path": output_video_path
            }
            
            logger.info(f"Video annotation completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error creating annotated video: {e}")
            raise
        finally:
            try:
                cap.release()
                out.release()
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
                    cv2.line(frame, start_point, end_point, self.COLOR_SKELETON, 3)  # Yellow line
        
        # Draw joints (circles)
        key_joints = ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 
                      'left_wrist', 'right_wrist', 'left_hip', 'right_hip', 
                      'left_knee', 'right_knee', 'left_ankle', 'right_ankle']
        
        for joint_name in key_joints:
            if joint_name in landmarks:
                landmark = landmarks[joint_name]
                if landmark.visibility > 0.5:
                    point = (int(landmark.x * width), int(landmark.y * height))
                    # Draw circle with glow effect
                    cv2.circle(frame, point, 8, (0, 0, 0), -1)  # Black outline
                    cv2.circle(frame, point, 6, self.COLOR_JOINT, -1)  # Magenta fill
                    cv2.circle(frame, point, 6, (255, 255, 255), 1)  # White border
        
        return frame
    
    def _draw_angle_indicators(self, frame: np.ndarray, angle_data: Dict, landmarks: Dict) -> np.ndarray:
        """Draw angle indicators at key joints"""
        if not angle_data or not landmarks:
            return frame
        
        height, width = frame.shape[:2]
        
        # Draw angle values near joints
        if 'elbow_angle' in angle_data:
            # Draw elbow angle
            if 'left_elbow' in landmarks:
                landmark = landmarks['left_elbow']
                if landmark.visibility > 0.5:
                    point = (int(landmark.x * width) + 20, int(landmark.y * height))
                    angle_text = f"{int(angle_data['elbow_angle'])}°"
                    self._draw_text_with_background(frame, angle_text, point, 
                                                   self.FONT_SCALE_SMALL, (255, 255, 0))
        
        if 'knee_angle' in angle_data:
            # Draw knee angle
            if 'left_knee' in landmarks:
                landmark = landmarks['left_knee']
                if landmark.visibility > 0.5:
                    point = (int(landmark.x * width) + 20, int(landmark.y * height))
                    angle_text = f"{int(angle_data['knee_angle'])}°"
                    self._draw_text_with_background(frame, angle_text, point, 
                                                   self.FONT_SCALE_SMALL, (255, 255, 0))
        
        return frame
    
    def _draw_rep_counters(self, frame: np.ndarray, correct: int, incorrect: int) -> np.ndarray:
        """Draw rep counters in top right corner"""
        height, width = frame.shape[:2]
        
        # Position for counters (top right)
        x_offset = width - 300
        y_offset = 40
        
        # Draw correct reps counter
        correct_text = f"CORRECT: {correct}"
        self._draw_text_with_background(
            frame, correct_text, (x_offset, y_offset),
            self.FONT_SCALE_LARGE, self.COLOR_CORRECT, 
            bg_color=(0, 100, 0), padding=15
        )
        
        # Draw incorrect reps counter
        incorrect_text = f"INCORRECT: {incorrect}"
        self._draw_text_with_background(
            frame, incorrect_text, (x_offset, y_offset + 60),
            self.FONT_SCALE_LARGE, self.COLOR_INCORRECT,
            bg_color=(0, 0, 100), padding=15
        )
        
        return frame
    
    def _draw_feedback(self, frame: np.ndarray, feedback_list: List[str]) -> np.ndarray:
        """Draw real-time feedback in top left corner"""
        if not feedback_list:
            return frame
        
        height, width = frame.shape[:2]
        
        # Position for feedback (top left)
        x_offset = 20
        y_offset = 40
        
        # Draw each feedback message
        for i, feedback in enumerate(feedback_list):
            # Truncate long messages
            if len(feedback) > 30:
                feedback = feedback[:27] + "..."
            
            # Determine color based on feedback content
            if any(word in feedback.lower() for word in ['good', 'great', 'excellent', 'perfect']):
                color = self.COLOR_CORRECT
                bg_color = (0, 100, 0)
            elif any(word in feedback.lower() for word in ['keep', 'maintain', 'watch']):
                color = (0, 255, 255)  # Yellow
                bg_color = (0, 100, 100)
            else:
                color = self.COLOR_INCORRECT
                bg_color = (0, 0, 100)
            
            self._draw_text_with_background(
                frame, feedback, (x_offset, y_offset + (i * 50)),
                self.FONT_SCALE_MEDIUM, color,
                bg_color=bg_color, padding=10
            )
        
        return frame
    
    def _draw_progress_bar(self, frame: np.ndarray, current_frame: int, total_frames: int) -> np.ndarray:
        """Draw progress bar at bottom of frame"""
        height, width = frame.shape[:2]
        
        # Progress bar dimensions
        bar_height = 10
        bar_y = height - 20
        bar_x_start = 50
        bar_width = width - 100
        
        # Calculate progress
        progress = current_frame / total_frames if total_frames > 0 else 0
        filled_width = int(bar_width * progress)
        
        # Draw background bar
        cv2.rectangle(frame, (bar_x_start, bar_y), 
                     (bar_x_start + bar_width, bar_y + bar_height),
                     (50, 50, 50), -1)
        
        # Draw filled portion
        if filled_width > 0:
            cv2.rectangle(frame, (bar_x_start, bar_y),
                         (bar_x_start + filled_width, bar_y + bar_height),
                         (0, 255, 0), -1)
        
        # Draw border
        cv2.rectangle(frame, (bar_x_start, bar_y),
                     (bar_x_start + bar_width, bar_y + bar_height),
                     (255, 255, 255), 2)
        
        return frame
    
    def _draw_text_with_background(
        self, 
        frame: np.ndarray, 
        text: str, 
        position: Tuple[int, int],
        font_scale: float,
        text_color: Tuple[int, int, int],
        bg_color: Tuple[int, int, int] = (0, 0, 0),
        padding: int = 10
    ) -> np.ndarray:
        """Draw text with background rectangle"""
        x, y = position
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(
            text, self.FONT, font_scale, self.FONT_THICKNESS_BOLD
        )
        
        # Draw background rectangle
        cv2.rectangle(
            frame,
            (x - padding, y - text_height - padding),
            (x + text_width + padding, y + baseline + padding),
            bg_color,
            -1
        )
        
        # Draw border
        cv2.rectangle(
            frame,
            (x - padding, y - text_height - padding),
            (x + text_width + padding, y + baseline + padding),
            (255, 255, 255),
            2
        )
        
        # Draw text
        cv2.putText(
            frame, text, (x, y),
            self.FONT, font_scale, text_color,
            self.FONT_THICKNESS_BOLD, cv2.LINE_AA
        )
        
        return frame
    
    async def _create_annotated_video_simple(
        self, 
        input_video_path: str, 
        output_video_path: str,
        exercise_name: str,
        session_id: str,
        progress_callback=None
    ) -> Dict:
        """
        Simpler video annotation method using raw frame writing
        """
        logger.info(f"Using simple annotation method for session {session_id}")
        
        try:
            import subprocess
            
            # Open input video
            cap = cv2.VideoCapture(input_video_path)
            if not cap.isOpened():
                raise Exception("Could not open input video")
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if fps <= 0:
                fps = 30
            
            # Create temporary directory for frames
            import tempfile
            temp_dir = tempfile.mkdtemp()
            frames_dir = os.path.join(temp_dir, "frames")
            os.makedirs(frames_dir, exist_ok=True)
            
            logger.info(f"Processing frames to {frames_dir}")
            
            # Process and save frames
            frame_count = 0
            correct_reps = 0
            incorrect_reps = 0
            current_feedback = []
            last_rep_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Process frame with MediaPipe
                analysis_result = mediapipe_service.process_frame(frame, exercise_name, session_id)
                
                if analysis_result:
                    if analysis_result.rep_count > last_rep_count:
                        if analysis_result.accuracy_score >= 0.7:
                            correct_reps += 1
                        else:
                            incorrect_reps += 1
                        last_rep_count = analysis_result.rep_count
                    
                    current_feedback = analysis_result.form_feedback[-3:] if analysis_result.form_feedback else []
                    frame = self._draw_skeleton(frame, analysis_result.landmarks)
                    frame = self._draw_angle_indicators(frame, analysis_result.angle_data, analysis_result.landmarks)
                
                frame = self._draw_rep_counters(frame, correct_reps, incorrect_reps)
                frame = self._draw_feedback(frame, current_feedback)
                frame = self._draw_progress_bar(frame, frame_count, total_frames)
                
                # Save frame as image
                frame_path = os.path.join(frames_dir, f"frame_{frame_count:06d}.jpg")
                cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                
                if progress_callback and frame_count % 30 == 0:
                    progress = int((frame_count / total_frames) * 100)
                    await progress_callback(progress, f"Processing frame {frame_count}/{total_frames}")
            
            cap.release()
            mediapipe_service.reset_session(session_id)
            
            logger.info(f"Processed {frame_count} frames, creating video with FFmpeg...")
            
            # Use FFmpeg to create video from frames
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',  # Overwrite output
                '-framerate', str(fps),
                '-i', os.path.join(frames_dir, 'frame_%06d.jpg'),
                '-c:v', 'libx264',  # H.264 codec
                '-preset', 'medium',  # Encoding speed/quality balance
                '-crf', '23',  # Quality (lower = better, 18-28 is good range)
                '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
                '-movflags', '+faststart',  # Enable streaming
                output_video_path
            ]
            
            try:
                logger.info(f"Running FFmpeg: {' '.join(ffmpeg_cmd)}")
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    logger.error(f"FFmpeg stderr: {result.stderr}")
                    raise Exception(f"FFmpeg failed with code {result.returncode}")
                
                logger.info("FFmpeg completed successfully")
                
            except subprocess.TimeoutExpired:
                logger.error("FFmpeg timed out after 5 minutes")
                raise Exception("FFmpeg processing timed out")
            except FileNotFoundError:
                logger.error("FFmpeg not found, trying OpenCV VideoWriter with different settings")
                
                # Last resort: use OpenCV with most compatible settings
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
                
                for i in range(1, frame_count + 1):
                    frame_path = os.path.join(frames_dir, f"frame_{i:06d}.jpg")
                    frame = cv2.imread(frame_path)
                    if frame is not None:
                        out.write(frame)
                
                out.release()
            
            # Clean up temporary frames
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            # Verify output
            if not os.path.exists(output_video_path):
                raise Exception("Output video was not created")
            
            file_size = os.path.getsize(output_video_path)
            logger.info(f"Video created: {file_size / (1024*1024):.2f} MB")
            
            stats = {
                "total_frames": total_frames,
                "processed_frames": frame_count,
                "correct_reps": correct_reps,
                "incorrect_reps": incorrect_reps,
                "total_reps": correct_reps + incorrect_reps,
                "output_path": output_video_path
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Simple annotation method failed: {e}")
            raise

# Global instance
video_annotator = VideoAnnotator()
