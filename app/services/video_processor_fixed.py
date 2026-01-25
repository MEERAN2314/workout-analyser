"""
Fixed Video Processor - Ensures proper MP4 format and reliable processing
"""
import cv2
import numpy as np
from typing import Dict, List, Optional, Any
import logging
import asyncio
import tempfile
import os
import subprocess
from datetime import datetime
import aiohttp
import aiofiles

from app.services.mediapipe_service import mediapipe_service
from app.core.config import settings
from app.core.database import get_database

logger = logging.getLogger(__name__)

class VideoAnalysisResult:
    def __init__(self):
        self.total_frames = 0
        self.processed_frames = 0
        self.total_reps = 0
        self.correct_reps = 0
        self.accuracy_scores = []
        self.form_feedback = []
        self.mistakes = []
        self.timeline_data = []
        self.exercise_name = ""
        self.duration = 0.0
        self.fps = 30.0
        self.calories_burned = 0.0
        self.video_url = None
        
    def get_average_accuracy(self) -> float:
        if not self.accuracy_scores:
            return 0.5  # Default
        return sum(self.accuracy_scores) / len(self.accuracy_scores)
    
    def add_timeline_entry(self, timestamp: float, rep_count: int, phase: str, accuracy: float, feedback: List[str]):
        self.timeline_data.append({
            "timestamp": timestamp,
            "rep_count": rep_count,
            "phase": phase,
            "accuracy_score": accuracy,
            "feedback": feedback,
            "frame_number": int(timestamp * self.fps)
        })
    
    def add_mistake(self, timestamp: float, description: str, severity: str = "medium"):
        self.mistakes.append({
            "timestamp": timestamp,
            "description": description,
            "severity": severity,
            "frame_number": int(timestamp * self.fps)
        })
    
    def calculate_calories(self) -> float:
        calories_per_rep = {
            "push_ups": 0.5,
            "squats": 0.8,
            "bicep_curls": 0.3,
            "lunges": 0.7,
            "planks": 0.1
        }
        
        base_calories = calories_per_rep.get(self.exercise_name.lower(), 0.5)
        
        if self.exercise_name.lower() == "planks":
            self.calories_burned = base_calories * self.duration
        else:
            self.calories_burned = base_calories * self.total_reps
        
        return self.calories_burned
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_frames": self.total_frames,
            "processed_frames": self.processed_frames,
            "total_reps": self.total_reps,
            "correct_reps": self.correct_reps,
            "accuracy_score": self.get_average_accuracy(),
            "form_feedback": list(set(self.form_feedback)),
            "mistakes": self.mistakes,
            "timeline_data": self.timeline_data,
            "exercise_name": self.exercise_name,
            "duration": self.duration,
            "fps": self.fps,
            "calories_burned": self.calculate_calories(),
            "analysis_completed": True,
            "completed_at": datetime.utcnow(),
            "video_url": self.video_url
        }

class VideoProcessorFixed:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        
    async def process_video_from_url(
        self, 
        video_url: str, 
        exercise_name: str, 
        session_id: str,
        generate_annotated: bool = False
    ) -> VideoAnalysisResult:
        """
        Process video from URL with proper MP4 format handling
        """
        logger.info(f"🎬 Starting video processing for session {session_id}")
        logger.info(f"   Exercise: {exercise_name}")
        logger.info(f"   Video URL: {video_url}")
        
        result = VideoAnalysisResult()
        result.exercise_name = exercise_name
        result.video_url = video_url
        
        temp_video_path = None
        converted_video_path = None
        
        try:
            # Step 1: Download video
            logger.info("📥 Step 1: Downloading video...")
            temp_video_path = await self._download_video_robust(video_url, session_id)
            
            if not temp_video_path or not os.path.exists(temp_video_path):
                raise Exception("Failed to download video")
            
            file_size = os.path.getsize(temp_video_path)
            logger.info(f"✅ Video downloaded: {file_size / (1024*1024):.2f} MB")
            
            # Step 2: Convert to proper MP4 format using FFmpeg
            logger.info("🔄 Step 2: Converting to proper MP4 format...")
            converted_video_path = await self._convert_to_mp4(temp_video_path, session_id)
            
            if not converted_video_path or not os.path.exists(converted_video_path):
                logger.warning("Conversion failed, using original video")
                converted_video_path = temp_video_path
            else:
                logger.info("✅ Video converted to MP4")
            
            # Step 3: Process video frames
            logger.info("🎯 Step 3: Analyzing video frames...")
            result = await self._process_video_frames(converted_video_path, exercise_name, session_id, result)
            
            logger.info(f"✅ Processing complete: {result.total_reps} reps detected")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing video: {e}")
            import traceback
            traceback.print_exc()
            raise
            
        finally:
            # Cleanup
            for path in [temp_video_path, converted_video_path]:
                if path and os.path.exists(path) and path != temp_video_path:
                    try:
                        os.remove(path)
                    except:
                        pass
    
    async def _download_video_robust(self, video_url: str, session_id: str) -> Optional[str]:
        """Download video with robust error handling"""
        try:
            temp_path = os.path.join(self.temp_dir, f"download_{session_id}.mp4")
            
            logger.info(f"Downloading from: {video_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                    if response.status != 200:
                        logger.error(f"Download failed with status: {response.status}")
                        return None
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    async with aiofiles.open(temp_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size > 0 and downloaded % (1024 * 1024) == 0:  # Log every MB
                                progress = (downloaded / total_size) * 100
                                logger.info(f"Download progress: {progress:.1f}%")
            
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                logger.info(f"✅ Download complete: {temp_path}")
                return temp_path
            else:
                logger.error("Downloaded file is empty or doesn't exist")
                return None
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    async def _convert_to_mp4(self, input_path: str, session_id: str) -> Optional[str]:
        """Convert video to proper MP4 format using FFmpeg"""
        try:
            output_path = os.path.join(self.temp_dir, f"converted_{session_id}.mp4")
            
            # FFmpeg command for reliable MP4 conversion
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', 'libx264',  # H.264 video codec
                '-preset', 'fast',  # Faster encoding
                '-crf', '23',  # Quality
                '-c:a', 'aac',  # AAC audio codec
                '-b:a', '128k',  # Audio bitrate
                '-movflags', '+faststart',  # Enable streaming
                '-y',  # Overwrite output
                output_path
            ]
            
            logger.info(f"Running FFmpeg conversion...")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            
            if process.returncode == 0 and os.path.exists(output_path):
                logger.info(f"✅ Conversion successful: {output_path}")
                return output_path
            else:
                logger.error(f"FFmpeg failed: {stderr.decode()}")
                return None
                
        except asyncio.TimeoutError:
            logger.error("FFmpeg conversion timed out")
            return None
        except FileNotFoundError:
            logger.warning("FFmpeg not found, skipping conversion")
            return None
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            return None
    
    async def _process_video_frames(
        self, 
        video_path: str, 
        exercise_name: str, 
        session_id: str,
        result: VideoAnalysisResult
    ) -> VideoAnalysisResult:
        """Process video frames for exercise analysis"""
        
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise Exception("Cannot open video file")
            
            # Get video properties
            result.fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            result.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            result.duration = result.total_frames / result.fps
            
            logger.info(f"Video: {result.total_frames} frames, {result.fps} FPS, {result.duration:.1f}s")
            
            # Process frames
            frame_count = 0
            last_rep_count = 0
            process_every = max(1, int(result.fps / 10))  # Process 10 frames per second
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Process every nth frame
                if frame_count % process_every == 0:
                    timestamp = frame_count / result.fps
                    
                    try:
                        # Analyze frame with MediaPipe
                        analysis = mediapipe_service.process_frame(frame, exercise_name, session_id)
                        
                        if analysis:
                            result.processed_frames += 1
                            
                            # Update rep count
                            if analysis.rep_count > last_rep_count:
                                result.total_reps = analysis.rep_count
                                last_rep_count = analysis.rep_count
                                logger.info(f"🏋️ Rep {analysis.rep_count} at {timestamp:.1f}s")
                                
                                if analysis.accuracy_score > 0.7:
                                    result.correct_reps += 1
                            
                            # Store accuracy
                            if analysis.accuracy_score > 0:
                                result.accuracy_scores.append(analysis.accuracy_score)
                            
                            # Store feedback
                            if analysis.form_feedback:
                                result.form_feedback.extend(analysis.form_feedback)
                            
                            # Add timeline entry
                            result.add_timeline_entry(
                                timestamp,
                                analysis.rep_count,
                                analysis.current_phase,
                                analysis.accuracy_score,
                                analysis.form_feedback
                            )
                            
                            # Detect mistakes
                            if analysis.accuracy_score < 0.5 and analysis.form_feedback:
                                for feedback in analysis.form_feedback:
                                    if any(word in feedback.lower() for word in ['keep', 'maintain', 'avoid']):
                                        result.add_mistake(timestamp, feedback, "medium")
                    
                    except Exception as e:
                        logger.warning(f"Frame {frame_count} error: {e}")
                        continue
                
                # Progress logging
                if frame_count % (result.total_frames // 10) == 0:
                    progress = (frame_count / result.total_frames) * 100
                    logger.info(f"Progress: {progress:.0f}% ({frame_count}/{result.total_frames})")
                
                # Safety limit
                if frame_count > result.fps * 600:  # 10 minutes max
                    logger.warning("Video too long, stopping at 10 minutes")
                    break
            
            result.total_reps = max(result.total_reps, last_rep_count)
            
            logger.info(f"✅ Analysis complete: {result.total_reps} reps, {result.processed_frames} frames processed")
            
            return result
            
        except Exception as e:
            logger.error(f"Frame processing error: {e}")
            raise
            
        finally:
            if cap:
                cap.release()
            mediapipe_service.reset_session(session_id)
    
    async def generate_analysis_summary(self, result: VideoAnalysisResult) -> Dict[str, Any]:
        """Generate analysis summary"""
        accuracy_percentage = result.get_average_accuracy() * 100
        rep_accuracy = (result.correct_reps / result.total_reps * 100) if result.total_reps > 0 else 0
        
        suggestions = []
        if accuracy_percentage < 70:
            suggestions.append("Focus on maintaining proper form")
        if rep_accuracy < 80:
            suggestions.append("Slow down and concentrate on quality")
        
        rating = "Excellent" if accuracy_percentage >= 90 else \
                 "Good" if accuracy_percentage >= 80 else \
                 "Fair" if accuracy_percentage >= 70 else "Needs Improvement"
        
        return {
            "performance_rating": rating,
            "accuracy_percentage": round(accuracy_percentage, 1),
            "rep_accuracy_percentage": round(rep_accuracy, 1),
            "improvement_suggestions": suggestions,
            "total_mistakes": len(result.mistakes),
            "exercise_duration": round(result.duration, 1),
            "calories_burned": round(result.calories_burned, 1),
            "frames_analyzed": result.processed_frames
        }

# Global instance
video_processor_fixed = VideoProcessorFixed()
