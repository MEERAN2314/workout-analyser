# API Documentation - Workout Analyzer

## Base URL
```
http://localhost:8000
```

## Authentication
All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### Authentication

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "age": 25,
  "height": 175.5,
  "weight": 70.0,
  "fitness_level": "intermediate",
  "goals": ["weight_loss", "muscle_gain"]
}
```

**Response:**
```json
{
  "message": "User created successfully",
  "user_id": "507f1f77bcf86cd799439011"
}
```

#### POST /auth/login
Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Home & Navigation

#### GET /
Home page with navigation options.

**Response:** HTML template

#### GET /dashboard
User dashboard with recent workouts and progress.

**Headers:** `Authorization: Bearer <token>`

**Response:** HTML template with user data

### Live Analysis

#### GET /live
Live analysis page with exercise selection.

**Headers:** `Authorization: Bearer <token>`

**Response:** HTML template

#### POST /live/start-session
Start a new live workout session.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "exercise_name": "push_ups"
}
```

**Response:**
```json
{
  "session_id": "507f1f77bcf86cd799439011",
  "exercise_name": "push_ups",
  "status": "started"
}
```

#### WebSocket /live/ws/{session_id}
Real-time communication for live analysis.

**Messages:**
- Client sends pose landmarks
- Server responds with rep count and feedback

### Recording Analysis

#### GET /recording
Recording analysis page with upload interface.

**Headers:** `Authorization: Bearer <token>`

**Response:** HTML template

#### POST /recording/upload
Upload video for analysis.

**Headers:** `Authorization: Bearer <token>`

**Request:** Multipart form data with video file

**Response:**
```json
{
  "session_id": "507f1f77bcf86cd799439011",
  "filename": "workout_video.mp4",
  "status": "uploaded",
  "message": "Video uploaded successfully. Analysis will begin shortly."
}
```

#### GET /recording/status/{session_id}
Check analysis status.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "session_id": "507f1f77bcf86cd799439011",
  "status": "processing",
  "progress": 45,
  "estimated_completion": "2024-01-15T10:30:00Z"
}
```

#### GET /recording/results/{session_id}
Get analysis results.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "session_id": "507f1f77bcf86cd799439011",
  "exercise_name": "squats",
  "total_reps": 15,
  "correct_reps": 12,
  "accuracy_score": 0.8,
  "form_feedback": [
    "Good depth on most reps",
    "Keep knees aligned with toes"
  ],
  "mistakes": [
    {
      "timestamp": 45.2,
      "description": "Knee valgus detected",
      "severity": "medium"
    }
  ],
  "calories_burned": 25.5,
  "video_url": "https://storage.googleapis.com/bucket/analyzed_video.mp4",
  "report_url": "/recording/report/507f1f77bcf86cd799439011"
}
```

### Exercise Library

#### GET /exercises
Get list of available exercises.

**Query Parameters:**
- `category` (optional): Filter by category
- `difficulty` (optional): Filter by difficulty level

**Response:**
```json
{
  "exercises": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "push_ups",
      "category": "upper_body",
      "description": "Classic upper body exercise",
      "difficulty_level": "beginner",
      "target_muscles": ["chest", "triceps", "shoulders"]
    }
  ]
}
```

#### GET /exercises/{exercise_id}
Get detailed exercise information.

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "push_ups",
  "category": "upper_body",
  "description": "Classic upper body exercise targeting chest, triceps, and shoulders",
  "instructions": [
    "Start in plank position",
    "Lower body until chest nearly touches ground",
    "Push back up to starting position"
  ],
  "target_muscles": ["chest", "triceps", "shoulders"],
  "difficulty_level": "beginner",
  "equipment_needed": [],
  "key_landmarks": ["left_shoulder", "right_shoulder", "left_elbow", "right_elbow"],
  "form_rules": {
    "min_depth": 0.7,
    "max_elbow_flare": 45
  }
}
```

### User Profile

#### GET /profile
Get user profile information.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "age": 25,
  "height": 175.5,
  "weight": 70.0,
  "fitness_level": "intermediate",
  "goals": ["weight_loss", "muscle_gain"],
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### PUT /profile
Update user profile.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "full_name": "John Smith",
  "age": 26,
  "weight": 68.0,
  "fitness_level": "advanced"
}
```

### Workout History

#### GET /workouts
Get user's workout history.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of results (default: 20)
- `offset` (optional): Pagination offset (default: 0)
- `exercise` (optional): Filter by exercise name

**Response:**
```json
{
  "workouts": [
    {
      "id": "507f1f77bcf86cd799439011",
      "exercise_name": "push_ups",
      "session_type": "live",
      "total_reps": 20,
      "correct_reps": 18,
      "accuracy_score": 0.9,
      "calories_burned": 15.2,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

### AI Chat

#### POST /chat/start
Start a new chat session.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "workout_id": "507f1f77bcf86cd799439011"
}
```

**Response:**
```json
{
  "chat_session_id": "507f1f77bcf86cd799439012",
  "message": "Hi! I've analyzed your recent workout. What would you like to know?"
}
```

#### POST /chat/{session_id}/message
Send message to AI consultant.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "message": "How can I improve my push-up form?"
}
```

**Response:**
```json
{
  "response": "Based on your recent workout analysis, I noticed you had some elbow flare. Try keeping your elbows closer to your body...",
  "suggestions": [
    "Focus on elbow positioning",
    "Practice with modified push-ups first"
  ]
}
```

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid input data",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limits

- Authentication endpoints: 5 requests per minute
- File upload endpoints: 3 requests per minute
- Other endpoints: 100 requests per minute

## File Upload Specifications

### Video Upload
- **Max file size**: 100MB
- **Supported formats**: MP4, AVI, MOV, MKV
- **Max duration**: 10 minutes
- **Resolution**: Up to 1080p recommended