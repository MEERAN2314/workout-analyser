import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
import asyncio
import tempfile
import os
from datetime import datetime, timedelta
import json

from app.services.mediapipe_service import mediapipe_service, ExerciseResult
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
        
    def get_average_accuracy(self) -> float:
        """Calculate average accuracy score"""
        if not self.accuracy_scores:
            return 0.0
        return sum(self.accuracy_scores) / len(self.accuracy_scores)
    
    def add_timeline_entry(self, timestamp: float, rep_count: int, phase: str, accuracy: float, feedback: List[str]):
        """Add entry to analysis timeline"""
        self.timeline_data.append({
            "timestamp": timestamp,
            "rep_count": rep_count,
            "phase": phase,
            "accuracy_score": accuracy,
            "feedback": feedback,
            "frame_number": int(timestamp * self.fps)
        })
    
    def add_mistake(self, timestamp: float, description: str, severity: str = "medium"):
        """Add mistake to the analysis"""
        self.mistakes.append({
            "timestamp": timestamp,
            "description": description,
            "severity": severity,
            "frame_number": int(timestamp * self.fps)
        })
    
    def calculate_calories(self) -> float:
        """Estimate calories burned based on exercise and reps"""
        # Basic calorie estimation - can be enhanced with user data
        calories_per_rep = {
            "push_ups": 0.5,
            "squats": 0.8,
            "bicep_curls": 0.3,
            "lunges": 0.7,
            "planks": 0.1  # per second for planks
        }
        
        base_calories = calories_per_rep.get(self.exercise_name.lower(), 0.5)
        
        if self.exercise_name.lower() == "planks":
            # For planks, calculate based on duration
            self.calories_burned = base_calories * self.duration
        else:
            # For other exercises, calculate based on reps
            self.calories_burned = base_calories * self.total_reps
        
        return self.calories_burned
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis result to dictionary"""
        return {
            "total_frames": self.total_frames,
            "processed_frames": self.processed_frames,
            "total_reps": self.total_reps,
            "correct_reps": self.correct_reps,
            "accuracy_score": self.get_average_accuracy(),
            "form_feedback": list(set(self.form_feedback)),  # Remove duplicates
            "mistakes": self.mistakes,
            "timeline_data": self.timeline_data,
            "exercise_name": self.exercise_name,
            "duration": self.duration,
            "fps": self.fps,
            "calories_burned": self.calculate_calories(),
            "analysis_completed": True,
            "completed_at": datetime.utcnow()
        }

class VideoProcessor:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        
    async def process_video_from_url(self, video_url: str, exercise_name: str, session_id: str) -> VideoAnalysisResult:
        """
        Process video from URL with comprehensive analysis
        
        Args:
            video_url: URL to the video file
            exercise_name: Type of exercise to analyze
            session_id: Session identifier for tracking
            
        Returns:
            VideoAnalysisResult with comprehensive analysis data
        """
        logger.info(f"Starting video processing for session {session_id}: {exercise_name}")
        
        try:
            # Download video to temporary file
            temp_video_path = await self._download_video(video_url, session_id)
            
            if not temp_video_path:
                raise Exception("Failed to download video")
            
            # Process video file
            result = await self._process_video_file(temp_video_path, exercise_name, session_id)
            
            # Clean up temporary file
            try:
                os.remove(temp_video_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing video for session {session_id}: {e}")
            raise
    
    async def _download_video(self, video_url: str, session_id: str) -> Optional[str]:
        """Download video from URL to temporary file"""
        try:
            import aiohttp
            import aiofiles
            
            temp_path = os.path.join(self.temp_dir, f"video_{session_id}.mp4")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status == 200:
                        async with aiofiles.open(temp_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        logger.info(f"Video downloaded to {temp_path}")
                        return temp_path
                    else:
                        logger.error(f"Failed to download video: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None
    
    async def _process_video_file(self, video_path: str, exercise_name: str, session_id: str) -> VideoAnalysisResult:
        """Process video file frame by frame with progress updates"""
        result = VideoAnalysisResult()
        result.exercise_name = exercise_name
        
        try:
            # Open video file
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            # Get video properties
            result.fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            result.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            result.duration = result.total_frames / result.fps
            
            logger.info(f"Video properties: {result.total_frames} frames, {result.fps} FPS, {result.duration:.2f}s")
            
            # Process frames with progress tracking
            frame_count = 0
            last_rep_count = 0
            processing_interval = max(1, int(result.fps / 5))  # Process every ~0.2 seconds (reduced frequency)
            progress_interval = max(1, result.total_frames // 20)  # Update progress every 5%
            
            logger.info(f"🎬 Starting frame-by-frame analysis (processing every {processing_interval} frames)")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Update progress periodically
                if frame_count % progress_interval == 0:
                    progress_percent = int((frame_count / result.total_frames) * 70) + 10  # 10-80% range
                    logger.info(f"📊 Processing progress: {frame_count}/{result.total_frames} frames ({progress_percent}%)")
                
                # Process every nth frame to optimize performance
                if frame_count % processing_interval == 0:
                    timestamp = frame_count / result.fps
                    
                    try:
                        # Process frame with MediaPipe (with timeout protection)
                        analysis_result = mediapipe_service.process_frame(frame, exercise_name, session_id)
                        
                        if analysis_result:
                            result.processed_frames += 1
                            
                            # Update rep count
                            if analysis_result.rep_count > last_rep_count:
                                result.total_reps = analysis_result.rep_count
                                last_rep_count = analysis_result.rep_count
                                logger.info(f"🏋️ Rep {analysis_result.rep_count} detected at {timestamp:.1f}s")
                                
                                # Check if rep was performed correctly
                                if analysis_result.accuracy_score > 0.7:  # Threshold for "correct" rep
                                    result.correct_reps += 1
                            
                            # Store accuracy score
                            if analysis_result.accuracy_score > 0:
                                result.accuracy_scores.append(analysis_result.accuracy_score)
                            
                            # Add feedback
                            if analysis_result.form_feedback:
                                result.form_feedback.extend(analysis_result.form_feedback)
                            
                            # Add timeline entry
                            result.add_timeline_entry(
                                timestamp,
                                analysis_result.rep_count,
                                analysis_result.current_phase,
                                analysis_result.accuracy_score,
                                analysis_result.form_feedback
                            )
                            
                            # Detect mistakes based on low accuracy
                            if analysis_result.accuracy_score < 0.5 and analysis_result.form_feedback:
                                for feedback in analysis_result.form_feedback:
                                    if any(word in feedback.lower() for word in ['keep', 'maintain', 'avoid', 'fix']):
                                        result.add_mistake(timestamp, feedback, "medium")
                    
                    except Exception as e:
                        logger.warning(f"⚠️ Error processing frame {frame_count}: {e}")
                        # Continue processing other frames
                        continue
                
                # Safety check - don't process videos longer than 10 minutes
                if frame_count > result.fps * 600:  # 10 minutes max
                    logger.warning("⏰ Video too long, stopping processing at 10 minutes")
                    break
            
            cap.release()
            
            # Final processing
            result.total_reps = max(result.total_reps, last_rep_count)
            
            # Clean up MediaPipe session
            mediapipe_service.reset_session(session_id)
            
            logger.info(f"✅ Video processing completed: {result.total_reps} reps, {result.get_average_accuracy():.2f} avg accuracy")
            logger.info(f"📊 Processed {result.processed_frames} frames out of {result.total_frames} total frames")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing video file: {e}")
            raise
        finally:
            try:
                cap.release()
            except:
                pass
    
    async def _update_processing_progress(self, session_id: str, progress: int):
        """Update processing progress in database"""
        try:
            db = get_database()
            if db is not None:
                from bson import ObjectId
                await db.workouts.update_one(
                    {"_id": ObjectId(session_id.replace('-', '')[:24])},
                    {"$set": {"processing_progress": progress}}
                )
        except Exception as e:
            logger.warning(f"Failed to update progress: {e}")
    
    async def generate_analysis_summary(self, result: VideoAnalysisResult) -> Dict[str, Any]:
        """Generate comprehensive analysis summary"""
        try:
            # Calculate performance metrics
            accuracy_percentage = result.get_average_accuracy() * 100
            rep_accuracy = (result.correct_reps / result.total_reps * 100) if result.total_reps > 0 else 0
            
            # Generate improvement suggestions
            suggestions = []
            
            if accuracy_percentage < 70:
                suggestions.append("Focus on maintaining proper form throughout the exercise")
            
            if rep_accuracy < 80:
                suggestions.append("Slow down and concentrate on quality over quantity")
            
            if result.mistakes:
                common_mistakes = {}
                for mistake in result.mistakes:
                    desc = mistake["description"]
                    common_mistakes[desc] = common_mistakes.get(desc, 0) + 1
                
                most_common = max(common_mistakes.items(), key=lambda x: x[1])
                suggestions.append(f"Work on: {most_common[0]}")
            
            # Performance rating
            if accuracy_percentage >= 90:
                rating = "Excellent"
            elif accuracy_percentage >= 80:
                rating = "Good"
            elif accuracy_percentage >= 70:
                rating = "Fair"
            else:
                rating = "Needs Improvement"
            
            return {
                "performance_rating": rating,
                "accuracy_percentage": round(accuracy_percentage, 1),
                "rep_accuracy_percentage": round(rep_accuracy, 1),
                "improvement_suggestions": suggestions,
                "total_mistakes": len(result.mistakes),
                "exercise_duration": round(result.duration, 1),
                "calories_burned": round(result.calories_burned, 1),
                "frames_analyzed": result.processed_frames,
                "analysis_quality": "High" if result.processed_frames > 100 else "Medium"
            }
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {e}")
            return {"error": "Failed to generate summary"}

# Global instance
video_processor = VideoProcessor()