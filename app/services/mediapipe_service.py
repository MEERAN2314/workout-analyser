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
    angle_data: Dict[str, float]

class MediaPipeService:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize MediaPipe Pose with optimized settings
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,  # Balance between accuracy and performance
            enable_segmentation=False,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )
        
        # Exercise state tracking with improved structure
        self.exercise_states = {}
        
        # Pose connections for skeleton drawing
        self.pose_connections = [
            # Torso
            (11, 12), (11, 23), (12, 24), (23, 24),
            # Left arm
            (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
            # Right arm  
            (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
            # Left leg
            (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
            # Right leg
            (24, 26), (26, 28), (28, 30), (28, 32), (30, 32)
        ]
    
    def process_frame(self, frame: np.ndarray, exercise_name: str, session_id: str) -> Optional[ExerciseResult]:
        """
        Process a single frame for pose detection and exercise analysis
        """
        try:
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame
            results = self.pose.process(rgb_frame)
            
            if not results.pose_landmarks:
                logger.debug(f"No pose landmarks detected for session {session_id}")
                return None
                
            # Extract landmarks with improved mapping
            landmarks = self._extract_landmarks_improved(results.pose_landmarks)
            
            # Initialize session state if needed
            if session_id not in self.exercise_states:
                self.exercise_states[session_id] = {
                    'rep_count': 0,
                    'current_phase': 'ready',
                    'last_angles': {},
                    'movement_direction': 'none',
                    'frame_count': 0,
                    'stable_frames': 0,
                    'last_rep_frame': 0,
                    'last_angle': 0,
                    'exercise_name': exercise_name.lower()
                }
                logger.info(f"Initialized exercise state for session {session_id} - {exercise_name}")
            
            state = self.exercise_states[session_id]
            state['frame_count'] += 1
            
            # Analyze exercise based on type with improved algorithms
            exercise_lower = exercise_name.lower()
            
            if exercise_lower == 'push_ups':
                result = self._analyze_push_ups_improved(landmarks, session_id)
            elif exercise_lower == 'squats':
                result = self._analyze_squats_improved(landmarks, session_id)
            elif exercise_lower == 'bicep_curls':
                result = self._analyze_bicep_curls_improved(landmarks, session_id)
            else:
                result = self._generic_analysis(landmarks, session_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing frame for session {session_id}: {e}")
            return None
    
    def _extract_landmarks_improved(self, pose_landmarks) -> Dict[str, PoseLandmark]:
        """Extract key landmarks with improved mapping"""
        landmarks = {}
        
        # MediaPipe landmark indices
        landmark_indices = {
            'nose': 0,
            'left_eye_inner': 1, 'left_eye': 2, 'left_eye_outer': 3,
            'right_eye_inner': 4, 'right_eye': 5, 'right_eye_outer': 6,
            'left_ear': 7, 'right_ear': 8,
            'mouth_left': 9, 'mouth_right': 10,
            'left_shoulder': 11, 'right_shoulder': 12,
            'left_elbow': 13, 'right_elbow': 14,
            'left_wrist': 15, 'right_wrist': 16,
            'left_pinky': 17, 'right_pinky': 18,
            'left_index': 19, 'right_index': 20,
            'left_thumb': 21, 'right_thumb': 22,
            'left_hip': 23, 'right_hip': 24,
            'left_knee': 25, 'right_knee': 26,
            'left_ankle': 27, 'right_ankle': 28,
            'left_heel': 29, 'right_heel': 30,
            'left_foot_index': 31, 'right_foot_index': 32
        }
        
        for name, idx in landmark_indices.items():
            if idx < len(pose_landmarks.landmark):
                landmark = pose_landmarks.landmark[idx]
                landmarks[name] = PoseLandmark(
                    x=landmark.x,
                    y=landmark.y,
                    z=landmark.z,
                    visibility=landmark.visibility
                )
        
        return landmarks
    
    def _calculate_angle_3d(self, point1: PoseLandmark, point2: PoseLandmark, point3: PoseLandmark) -> float:
        """Calculate 3D angle between three points for better accuracy"""
        # Convert to numpy arrays with 3D coordinates
        a = np.array([point1.x, point1.y, point1.z])
        b = np.array([point2.x, point2.y, point2.z])
        c = np.array([point3.x, point3.y, point3.z])
        
        # Calculate vectors
        ba = a - b
        bc = c - b
        
        # Calculate angle using dot product
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
        angle = np.arccos(cosine_angle)
        
        return np.degrees(angle)
    
    def _calculate_distance(self, point1: PoseLandmark, point2: PoseLandmark) -> float:
        """Calculate distance between two landmarks"""
        return np.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2 + (point1.z - point2.z)**2)
    
    def _analyze_push_ups_improved(self, landmarks: Dict[str, PoseLandmark], session_id: str) -> ExerciseResult:
        """Improved push-up analysis with better accuracy and form checking"""
        state = self.exercise_states[session_id]
        feedback = []
        angle_data = {}
        
        # Calculate key angles
        left_elbow_angle = self._calculate_angle_3d(
            landmarks['left_shoulder'],
            landmarks['left_elbow'],
            landmarks['left_wrist']
        )
        
        right_elbow_angle = self._calculate_angle_3d(
            landmarks['right_shoulder'],
            landmarks['right_elbow'],
            landmarks['right_wrist']
        )
        
        # Average elbow angle for rep counting
        avg_elbow_angle = (left_elbow_angle + right_elbow_angle) / 2
        angle_data['elbow_angle'] = avg_elbow_angle
        
        # Body alignment angle (shoulder to hip)
        body_angle = self._calculate_angle_3d(
            landmarks['left_shoulder'],
            landmarks['left_hip'],
            landmarks['left_ankle']
        )
        angle_data['body_angle'] = body_angle
        
        # IMPROVED push-up phase detection with better thresholds
        current_phase = state['current_phase']
        rep_detected = False
        
        # More accurate phase thresholds
        UP_THRESHOLD = 140    # Arms mostly extended
        DOWN_THRESHOLD = 80   # Arms bent at bottom
        HYSTERESIS = 10       # Prevent oscillation
        
        # State machine for rep counting
        if current_phase == 'ready':
            if avg_elbow_angle > UP_THRESHOLD:
                state['current_phase'] = 'up'
                state['stable_frames'] = 0
                feedback.append("Starting position detected")
        
        elif current_phase == 'up':
            if avg_elbow_angle < DOWN_THRESHOLD:
                state['current_phase'] = 'down'
                state['stable_frames'] = 0
                feedback.append("Going down")
        
        elif current_phase == 'down':
            # Require stable frames in down position before counting up
            if avg_elbow_angle < DOWN_THRESHOLD + HYSTERESIS:
                state['stable_frames'] += 1
            
            if avg_elbow_angle > UP_THRESHOLD and state['stable_frames'] >= 3:
                # Check minimum time between reps (prevent double counting)
                frames_since_last_rep = state['frame_count'] - state['last_rep_frame']
                if frames_since_last_rep > 20:  # Minimum 2 seconds at 10 FPS
                    state['current_phase'] = 'up'
                    state['rep_count'] += 1
                    state['last_rep_frame'] = state['frame_count']
                    state['stable_frames'] = 0
                    rep_detected = True
                    feedback.append(f"Push-up {state['rep_count']} completed!")
        
        # Form analysis with detailed feedback
        accuracy_score = 1.0
        
        # 1. Check elbow flare
        shoulder_width = self._calculate_distance(landmarks['left_shoulder'], landmarks['right_shoulder'])
        elbow_width = self._calculate_distance(landmarks['left_elbow'], landmarks['right_elbow'])
        
        elbow_flare_ratio = elbow_width / shoulder_width if shoulder_width > 0 else 0
        if elbow_flare_ratio > 1.6:
            feedback.append("Keep elbows closer to your body")
            accuracy_score -= 0.15
        elif elbow_flare_ratio < 1.3:
            feedback.append("Good elbow position!")
        
        # 2. Check body alignment (plank position)
        if body_angle < 150 or body_angle > 210:
            feedback.append("Keep your body in a straight line")
            accuracy_score -= 0.2
        else:
            feedback.append("Excellent body alignment!")
        
        # 3. Check depth based on current phase
        if current_phase == 'down':
            if avg_elbow_angle > 100:
                feedback.append("Go deeper - lower your chest more")
                accuracy_score -= 0.15
            elif avg_elbow_angle < 60:
                feedback.append("Perfect depth!")
                accuracy_score += 0.05
            else:
                feedback.append("Good depth!")
        
        # 4. Check hand position relative to shoulders
        left_hand_shoulder_dist = abs(landmarks['left_wrist'].y - landmarks['left_shoulder'].y)
        right_hand_shoulder_dist = abs(landmarks['right_wrist'].y - landmarks['right_shoulder'].y)
        
        if left_hand_shoulder_dist > 0.15 or right_hand_shoulder_dist > 0.15:
            feedback.append("Align hands with shoulders")
            accuracy_score -= 0.1
        
        return ExerciseResult(
            rep_count=state['rep_count'],
            current_phase=state['current_phase'],
            form_feedback=feedback,
            accuracy_score=max(0.0, min(1.0, accuracy_score)),
            landmarks=landmarks,
            angle_data=angle_data
        )
    
    def _analyze_squats_improved(self, landmarks: Dict[str, PoseLandmark], session_id: str) -> ExerciseResult:
        """Improved squat analysis with better form checking"""
        state = self.exercise_states[session_id]
        feedback = []
        angle_data = {}
        
        # Calculate key angles
        left_knee_angle = self._calculate_angle_3d(
            landmarks['left_hip'],
            landmarks['left_knee'],
            landmarks['left_ankle']
        )
        
        right_knee_angle = self._calculate_angle_3d(
            landmarks['right_hip'],
            landmarks['right_knee'],
            landmarks['right_ankle']
        )
        
        avg_knee_angle = (left_knee_angle + right_knee_angle) / 2
        angle_data['knee_angle'] = avg_knee_angle
        
        # Hip angle for depth analysis
        left_hip_angle = self._calculate_angle_3d(
            landmarks['left_shoulder'],
            landmarks['left_hip'],
            landmarks['left_knee']
        )
        angle_data['hip_angle'] = left_hip_angle
        
        # IMPROVED squat phase detection with better thresholds
        current_phase = state['current_phase']
        rep_detected = False
        
        # More accurate phase thresholds for squats
        STANDING_THRESHOLD = 150  # Knees mostly straight
        SQUAT_THRESHOLD = 90      # Deep squat position
        HYSTERESIS = 15           # Prevent oscillation
        
        # State machine for rep counting
        if current_phase == 'ready':
            if avg_knee_angle > STANDING_THRESHOLD:
                state['current_phase'] = 'up'
                state['stable_frames'] = 0
                feedback.append("Standing position detected")
        
        elif current_phase == 'up':
            if avg_knee_angle < SQUAT_THRESHOLD:
                state['current_phase'] = 'down'
                state['stable_frames'] = 0
                feedback.append("Squatting down")
        
        elif current_phase == 'down':
            # Require stable frames in squat position
            if avg_knee_angle < SQUAT_THRESHOLD + HYSTERESIS:
                state['stable_frames'] += 1
            
            if avg_knee_angle > STANDING_THRESHOLD and state['stable_frames'] >= 5:
                # Check minimum time between reps
                frames_since_last_rep = state['frame_count'] - state['last_rep_frame']
                if frames_since_last_rep > 25:  # Minimum 2.5 seconds at 10 FPS
                    state['current_phase'] = 'up'
                    state['rep_count'] += 1
                    state['last_rep_frame'] = state['frame_count']
                    state['stable_frames'] = 0
                    rep_detected = True
                    feedback.append(f"Squat {state['rep_count']} completed!")
        
        # Form analysis
        accuracy_score = 1.0
        
        # 1. Check knee alignment (knees over toes)
        left_knee_ankle_dist = abs(landmarks['left_knee'].x - landmarks['left_ankle'].x)
        right_knee_ankle_dist = abs(landmarks['right_knee'].x - landmarks['right_ankle'].x)
        
        if left_knee_ankle_dist > 0.08 or right_knee_ankle_dist > 0.08:
            feedback.append("Keep knees aligned over your toes")
            accuracy_score -= 0.2
        else:
            feedback.append("Great knee alignment!")
        
        # 2. Check squat depth
        if current_phase == 'down':
            if avg_knee_angle > 110:
                feedback.append("Go deeper - squat until thighs are parallel")
                accuracy_score -= 0.15
            elif avg_knee_angle < 70:
                feedback.append("Excellent depth!")
                accuracy_score += 0.05
            else:
                feedback.append("Good squat depth!")
        
        # 3. Check back posture using torso angle
        torso_angle = self._calculate_angle_3d(
            landmarks['left_shoulder'],
            landmarks['left_hip'],
            landmarks['left_knee']
        )
        
        if torso_angle < 60 or torso_angle > 120:
            feedback.append("Keep your chest up and back straight")
            accuracy_score -= 0.15
        else:
            feedback.append("Good posture!")
        
        # 4. Check foot stability
        left_ankle_y = landmarks['left_ankle'].y
        right_ankle_y = landmarks['right_ankle'].y
        
        if abs(left_ankle_y - right_ankle_y) > 0.03:
            feedback.append("Keep both feet planted evenly")
            accuracy_score -= 0.1
        
        return ExerciseResult(
            rep_count=state['rep_count'],
            current_phase=state['current_phase'],
            form_feedback=feedback,
            accuracy_score=max(0.0, min(1.0, accuracy_score)),
            landmarks=landmarks,
            angle_data=angle_data
        )
    
    def _analyze_bicep_curls_improved(self, landmarks: Dict[str, PoseLandmark], session_id: str) -> ExerciseResult:
        """Improved bicep curl analysis with better rep counting"""
        state = self.exercise_states[session_id]
        feedback = []
        angle_data = {}
        
        # Calculate both arms for better accuracy
        left_elbow_angle = self._calculate_angle_3d(
            landmarks['left_shoulder'],
            landmarks['left_elbow'],
            landmarks['left_wrist']
        )
        
        right_elbow_angle = self._calculate_angle_3d(
            landmarks['right_shoulder'],
            landmarks['right_elbow'],
            landmarks['right_wrist']
        )
        
        # Use the arm with better visibility or average both
        left_visibility = landmarks['left_elbow'].visibility
        right_visibility = landmarks['right_elbow'].visibility
        
        if left_visibility > right_visibility:
            primary_elbow_angle = left_elbow_angle
            primary_arm = 'left'
        else:
            primary_elbow_angle = right_elbow_angle
            primary_arm = 'right'
        
        angle_data['elbow_angle'] = primary_elbow_angle
        angle_data['primary_arm'] = primary_arm
        
        # IMPROVED bicep curl phase detection
        current_phase = state['current_phase']
        rep_detected = False
        
        # More accurate thresholds for bicep curls
        EXTENDED_THRESHOLD = 150   # Arm mostly straight
        CURLED_THRESHOLD = 45      # Arm fully curled
        HYSTERESIS = 10            # Prevent oscillation
        
        # State machine for rep counting
        if current_phase == 'ready':
            if primary_elbow_angle > EXTENDED_THRESHOLD:
                state['current_phase'] = 'extended'
                state['stable_frames'] = 0
                feedback.append("Starting position detected")
        
        elif current_phase == 'extended':
            if primary_elbow_angle < CURLED_THRESHOLD:
                state['current_phase'] = 'curled'
                state['stable_frames'] = 0
                feedback.append("Curling up")
        
        elif current_phase == 'curled':
            # Require stable frames in curled position
            if primary_elbow_angle < CURLED_THRESHOLD + HYSTERESIS:
                state['stable_frames'] += 1
            
            if primary_elbow_angle > EXTENDED_THRESHOLD and state['stable_frames'] >= 3:
                # Check minimum time between reps
                frames_since_last_rep = state['frame_count'] - state['last_rep_frame']
                if frames_since_last_rep > 15:  # Minimum 1.5 seconds at 10 FPS
                    state['current_phase'] = 'extended'
                    state['rep_count'] += 1
                    state['last_rep_frame'] = state['frame_count']
                    state['stable_frames'] = 0
                    rep_detected = True
                    feedback.append(f"Bicep curl {state['rep_count']} completed!")
        
        # Form analysis
        accuracy_score = 1.0
        
        # Check elbow stability for primary arm
        if primary_arm == 'left':
            elbow_shoulder_dist = abs(landmarks['left_elbow'].x - landmarks['left_shoulder'].x)
            elbow_y_movement = abs(landmarks['left_elbow'].y - landmarks['left_shoulder'].y)
        else:
            elbow_shoulder_dist = abs(landmarks['right_elbow'].x - landmarks['right_shoulder'].x)
            elbow_y_movement = abs(landmarks['right_elbow'].y - landmarks['right_shoulder'].y)
        
        # 1. Check elbow stability (should stay close to body)
        if elbow_shoulder_dist > 0.12:
            feedback.append("Keep your elbow stable at your side")
            accuracy_score -= 0.2
        else:
            feedback.append("Good elbow stability!")
        
        # 2. Check for elbow dropping (elbow should stay at shoulder level)
        if elbow_y_movement > 0.1:
            feedback.append("Keep your elbow up at shoulder level")
            accuracy_score -= 0.15
        
        # 3. Check range of motion
        if current_phase == 'curled':
            if primary_elbow_angle > 60:
                feedback.append("Curl higher for full range of motion")
                accuracy_score -= 0.1
            elif primary_elbow_angle < 30:
                feedback.append("Perfect curl!")
                accuracy_score += 0.05
        
        # 4. Check for controlled movement (not too fast)
        if 'last_angle' in state:
            angle_change = abs(primary_elbow_angle - state['last_angle'])
            if angle_change > 30:  # Too fast movement
                feedback.append("Control the movement - slower is better")
                accuracy_score -= 0.1
        
        state['last_angle'] = primary_elbow_angle
        
        return ExerciseResult(
            rep_count=state['rep_count'],
            current_phase=state['current_phase'],
            form_feedback=feedback,
            accuracy_score=max(0.0, min(1.0, accuracy_score)),
            landmarks=landmarks,
            angle_data=angle_data
        )
    
    def _generic_analysis(self, landmarks: Dict[str, PoseLandmark], session_id: str) -> ExerciseResult:
        """Generic analysis for unknown exercises"""
        state = self.exercise_states[session_id]
        
        return ExerciseResult(
            rep_count=state['rep_count'],
            current_phase=state['current_phase'],
            form_feedback=["Exercise analysis not yet implemented"],
            accuracy_score=0.5,
            landmarks=landmarks,
            angle_data={}
        )
    
    def draw_landmarks_on_frame(self, frame: np.ndarray, landmarks: Dict[str, PoseLandmark]) -> np.ndarray:
        """Draw pose landmarks and skeleton on frame for visualization"""
        if not landmarks:
            return frame
        
        height, width = frame.shape[:2]
        
        # Draw skeleton connections
        for connection in self.pose_connections:
            start_idx, end_idx = connection
            
            # Map MediaPipe indices to our landmark names
            landmark_names = list(landmarks.keys())
            if start_idx < len(landmark_names) and end_idx < len(landmark_names):
                start_name = landmark_names[start_idx] if start_idx < len(landmark_names) else None
                end_name = landmark_names[end_idx] if end_idx < len(landmark_names) else None
                
                if start_name in landmarks and end_name in landmarks:
                    start_landmark = landmarks[start_name]
                    end_landmark = landmarks[end_name]
                    
                    if start_landmark.visibility > 0.5 and end_landmark.visibility > 0.5:
                        start_point = (int(start_landmark.x * width), int(start_landmark.y * height))
                        end_point = (int(end_landmark.x * width), int(end_landmark.y * height))
                        
                        cv2.line(frame, start_point, end_point, (0, 255, 0), 2)
        
        # Draw landmark points
        for name, landmark in landmarks.items():
            if landmark.visibility > 0.5:
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                
                # Different colors for different body parts
                if 'shoulder' in name or 'elbow' in name or 'wrist' in name:
                    color = (255, 0, 0)  # Blue for arms
                elif 'hip' in name or 'knee' in name or 'ankle' in name:
                    color = (0, 0, 255)  # Red for legs
                else:
                    color = (255, 255, 0)  # Cyan for other points
                
                cv2.circle(frame, (x, y), 5, color, -1)
                cv2.circle(frame, (x, y), 7, (255, 255, 255), 2)  # White border
        
        return frame
    
    def get_skeleton_data(self, landmarks: Dict[str, PoseLandmark]) -> List[Dict]:
        """Get skeleton connection data for frontend visualization"""
        if not landmarks:
            return []
        
        connections = []
        
        # Define key connections for visualization
        key_connections = [
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_elbow'),
            ('left_elbow', 'left_wrist'),
            ('right_shoulder', 'right_elbow'),
            ('right_elbow', 'right_wrist'),
            ('left_shoulder', 'left_hip'),
            ('right_shoulder', 'right_hip'),
            ('left_hip', 'right_hip'),
            ('left_hip', 'left_knee'),
            ('left_knee', 'left_ankle'),
            ('right_hip', 'right_knee'),
            ('right_knee', 'right_ankle')
        ]
        
        for start_name, end_name in key_connections:
            if start_name in landmarks and end_name in landmarks:
                start_landmark = landmarks[start_name]
                end_landmark = landmarks[end_name]
                
                if start_landmark.visibility > 0.5 and end_landmark.visibility > 0.5:
                    connections.append({
                        'start': {
                            'x': start_landmark.x,
                            'y': start_landmark.y,
                            'name': start_name
                        },
                        'end': {
                            'x': end_landmark.x,
                            'y': end_landmark.y,
                            'name': end_name
                        }
                    })
        
        return connections
    
    def reset_session(self, session_id: str):
        """Reset exercise state for a session"""
        if session_id in self.exercise_states:
            del self.exercise_states[session_id]
            logger.info(f"Reset session state for {session_id}")
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get current session statistics"""
        if session_id not in self.exercise_states:
            return {'rep_count': 0, 'current_phase': 'ready'}
        
        return self.exercise_states[session_id].copy()

# Global instance
mediapipe_service = MediaPipeService()