import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import math

from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class PoseLandmark:
    x: float
    y: float
    z: float
    visibility: float

@dataclass
class ExerciseResult:
    rep_count: int
    current_phase: str
    form_feedback: List[str]
    accuracy_score: float
    landmarks: Dict[str, PoseLandmark]

class MediaPipeService:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=settings.DETECTION_CONFIDENCE,
            min_tracking_confidence=settings.TRACKING_CONFIDENCE
        )
        
        # Exercise state tracking
        self.exercise_states = {}
        
    def process_frame(self, frame: np.ndarray, exercise_name: str, session_id: str) -> Optional[ExerciseResult]:
        """
        Process a single frame for pose detection and exercise analysis
        
        Args:
            frame: Input video frame
            exercise_name: Name of exercise being performed
            session_id: Unique session identifier
            
        Returns:
            ExerciseResult with analysis data or None if no pose detected
        """
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame
            results = self.pose.process(rgb_frame)
            
            if not results.pose_landmarks:
                return None
                
            # Extract landmarks
            landmarks = self._extract_landmarks(results.pose_landmarks)
            
            # Initialize session state if needed
            if session_id not in self.exercise_states:
                self.exercise_states[session_id] = {
                    'rep_count': 0,
                    'current_phase': 'ready',
                    'last_angle': 0,
                    'movement_direction': 'none'
                }
            
            # Analyze exercise based on type
            if exercise_name.lower() == 'push_ups':
                result = self._analyze_push_ups(landmarks, session_id)
            elif exercise_name.lower() == 'squats':
                result = self._analyze_squats(landmarks, session_id)
            elif exercise_name.lower() == 'bicep_curls':
                result = self._analyze_bicep_curls(landmarks, session_id)
            else:
                # Generic analysis
                result = self._generic_analysis(landmarks, session_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return None
    
    def draw_landmarks(self, frame: np.ndarray, landmarks: Optional[any]) -> np.ndarray:
        """Draw pose landmarks on frame"""
        if landmarks:
            self.mp_drawing.draw_landmarks(
                frame, landmarks, self.mp_pose.POSE_CONNECTIONS
            )
        return frame
    
    def _extract_landmarks(self, pose_landmarks) -> Dict[str, PoseLandmark]:
        """Extract key landmarks from MediaPipe results"""
        landmarks = {}
        
        # Key landmarks for exercises
        key_points = {
            'left_shoulder': self.mp_pose.PoseLandmark.LEFT_SHOULDER,
            'right_shoulder': self.mp_pose.PoseLandmark.RIGHT_SHOULDER,
            'left_elbow': self.mp_pose.PoseLandmark.LEFT_ELBOW,
            'right_elbow': self.mp_pose.PoseLandmark.RIGHT_ELBOW,
            'left_wrist': self.mp_pose.PoseLandmark.LEFT_WRIST,
            'right_wrist': self.mp_pose.PoseLandmark.RIGHT_WRIST,
            'left_hip': self.mp_pose.PoseLandmark.LEFT_HIP,
            'right_hip': self.mp_pose.PoseLandmark.RIGHT_HIP,
            'left_knee': self.mp_pose.PoseLandmark.LEFT_KNEE,
            'right_knee': self.mp_pose.PoseLandmark.RIGHT_KNEE,
            'left_ankle': self.mp_pose.PoseLandmark.LEFT_ANKLE,
            'right_ankle': self.mp_pose.PoseLandmark.RIGHT_ANKLE,
            'nose': self.mp_pose.PoseLandmark.NOSE
        }
        
        for name, landmark_id in key_points.items():
            landmark = pose_landmarks.landmark[landmark_id]
            landmarks[name] = PoseLandmark(
                x=landmark.x,
                y=landmark.y,
                z=landmark.z,
                visibility=landmark.visibility
            )
        
        return landmarks
    
    def _calculate_angle(self, point1: PoseLandmark, point2: PoseLandmark, point3: PoseLandmark) -> float:
        """Calculate angle between three points"""
        # Convert to numpy arrays
        a = np.array([point1.x, point1.y])
        b = np.array([point2.x, point2.y])
        c = np.array([point3.x, point3.y])
        
        # Calculate vectors
        ba = a - b
        bc = c - b
        
        # Calculate angle
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        
        return np.degrees(angle)
    
    def _analyze_push_ups(self, landmarks: Dict[str, PoseLandmark], session_id: str) -> ExerciseResult:
        """Analyze push-up exercise"""
        state = self.exercise_states[session_id]
        feedback = []
        
        # Calculate elbow angle (key metric for push-ups)
        left_elbow_angle = self._calculate_angle(
            landmarks['left_shoulder'],
            landmarks['left_elbow'],
            landmarks['left_wrist']
        )
        
        right_elbow_angle = self._calculate_angle(
            landmarks['right_shoulder'],
            landmarks['right_elbow'],
            landmarks['right_wrist']
        )
        
        avg_elbow_angle = (left_elbow_angle + right_elbow_angle) / 2
        
        # Push-up phase detection
        if avg_elbow_angle > 160 and state['current_phase'] != 'up':
            state['current_phase'] = 'up'
        elif avg_elbow_angle < 90 and state['current_phase'] == 'up':
            state['current_phase'] = 'down'
            state['rep_count'] += 1
        
        # Form analysis
        accuracy_score = 1.0
        
        # Check elbow flare
        shoulder_width = abs(landmarks['left_shoulder'].x - landmarks['right_shoulder'].x)
        elbow_width = abs(landmarks['left_elbow'].x - landmarks['right_elbow'].x)
        
        if elbow_width > shoulder_width * 1.3:
            feedback.append("Keep elbows closer to your body")
            accuracy_score -= 0.2
        
        # Check body alignment
        hip_y = (landmarks['left_hip'].y + landmarks['right_hip'].y) / 2
        shoulder_y = (landmarks['left_shoulder'].y + landmarks['right_shoulder'].y) / 2
        
        if abs(hip_y - shoulder_y) > 0.1:
            feedback.append("Keep your body in a straight line")
            accuracy_score -= 0.1
        
        # Check depth
        if state['current_phase'] == 'down' and avg_elbow_angle > 100:
            feedback.append("Go deeper - lower your chest more")
            accuracy_score -= 0.1
        
        return ExerciseResult(
            rep_count=state['rep_count'],
            current_phase=state['current_phase'],
            form_feedback=feedback,
            accuracy_score=max(0.0, accuracy_score),
            landmarks=landmarks
        )
    
    def _analyze_squats(self, landmarks: Dict[str, PoseLandmark], session_id: str) -> ExerciseResult:
        """Analyze squat exercise"""
        state = self.exercise_states[session_id]
        feedback = []
        
        # Calculate knee angle
        left_knee_angle = self._calculate_angle(
            landmarks['left_hip'],
            landmarks['left_knee'],
            landmarks['left_ankle']
        )
        
        right_knee_angle = self._calculate_angle(
            landmarks['right_hip'],
            landmarks['right_knee'],
            landmarks['right_ankle']
        )
        
        avg_knee_angle = (left_knee_angle + right_knee_angle) / 2
        
        # Squat phase detection
        if avg_knee_angle > 160 and state['current_phase'] != 'up':
            state['current_phase'] = 'up'
        elif avg_knee_angle < 90 and state['current_phase'] == 'up':
            state['current_phase'] = 'down'
            state['rep_count'] += 1
        
        # Form analysis
        accuracy_score = 1.0
        
        # Check knee alignment
        left_knee_x = landmarks['left_knee'].x
        left_ankle_x = landmarks['left_ankle'].x
        right_knee_x = landmarks['right_knee'].x
        right_ankle_x = landmarks['right_ankle'].x
        
        if abs(left_knee_x - left_ankle_x) > 0.05 or abs(right_knee_x - right_ankle_x) > 0.05:
            feedback.append("Keep knees aligned over your toes")
            accuracy_score -= 0.2
        
        # Check depth
        if state['current_phase'] == 'down' and avg_knee_angle > 100:
            feedback.append("Go deeper - squat until thighs are parallel to ground")
            accuracy_score -= 0.1
        
        # Check back posture
        hip_y = (landmarks['left_hip'].y + landmarks['right_hip'].y) / 2
        shoulder_y = (landmarks['left_shoulder'].y + landmarks['right_shoulder'].y) / 2
        
        if shoulder_y > hip_y + 0.2:
            feedback.append("Keep your chest up and back straight")
            accuracy_score -= 0.1
        
        return ExerciseResult(
            rep_count=state['rep_count'],
            current_phase=state['current_phase'],
            form_feedback=feedback,
            accuracy_score=max(0.0, accuracy_score),
            landmarks=landmarks
        )
    
    def _analyze_bicep_curls(self, landmarks: Dict[str, PoseLandmark], session_id: str) -> ExerciseResult:
        """Analyze bicep curl exercise"""
        state = self.exercise_states[session_id]
        feedback = []
        
        # Calculate elbow angle for dominant arm (right arm)
        elbow_angle = self._calculate_angle(
            landmarks['right_shoulder'],
            landmarks['right_elbow'],
            landmarks['right_wrist']
        )
        
        # Bicep curl phase detection
        if elbow_angle > 160 and state['current_phase'] != 'down':
            state['current_phase'] = 'down'
        elif elbow_angle < 45 and state['current_phase'] == 'down':
            state['current_phase'] = 'up'
            state['rep_count'] += 1
        
        # Form analysis
        accuracy_score = 1.0
        
        # Check elbow stability
        elbow_x = landmarks['right_elbow'].x
        shoulder_x = landmarks['right_shoulder'].x
        
        if abs(elbow_x - shoulder_x) > 0.1:
            feedback.append("Keep your elbow stable at your side")
            accuracy_score -= 0.2
        
        # Check full range of motion
        if state['current_phase'] == 'up' and elbow_angle > 60:
            feedback.append("Curl higher for full range of motion")
            accuracy_score -= 0.1
        
        return ExerciseResult(
            rep_count=state['rep_count'],
            current_phase=state['current_phase'],
            form_feedback=feedback,
            accuracy_score=max(0.0, accuracy_score),
            landmarks=landmarks
        )
    
    def _generic_analysis(self, landmarks: Dict[str, PoseLandmark], session_id: str) -> ExerciseResult:
        """Generic analysis for unknown exercises"""
        state = self.exercise_states[session_id]
        
        return ExerciseResult(
            rep_count=state['rep_count'],
            current_phase=state['current_phase'],
            form_feedback=["Exercise analysis not yet implemented"],
            accuracy_score=0.5,
            landmarks=landmarks
        )
    
    def reset_session(self, session_id: str):
        """Reset exercise state for a session"""
        if session_id in self.exercise_states:
            del self.exercise_states[session_id]
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get current session statistics"""
        if session_id not in self.exercise_states:
            return {'rep_count': 0, 'current_phase': 'ready'}
        
        return self.exercise_states[session_id].copy()

# Global instance
mediapipe_service = MediaPipeService()