# Workout Analyzer 🏋️

AI-powered workout analysis with real-time feedback and personalized coaching.

## 🚀 Current Status: Phase 4 - AI Integration (In Progress)

**Latest Update:** January 29, 2026  
**Phase 4 Progress:** 30% Complete

### ✅ Completed Phases
- **Phase 1:** Foundation & Setup ✅
- **Phase 2:** Live Analysis with MediaPipe ✅
- **Phase 3:** Recording Analysis & Annotated Videos ✅
- **Phase 4:** User Authentication & AI Chat (Week 1 - 60% Complete) 🔄

---

## 🎯 Features

### Live Workout Analysis
- ✅ Real-time pose detection with MediaPipe
- ✅ Rep counting for push-ups, squats, bicep curls
- ✅ Form validation with accuracy scoring (90%+ accuracy)
- ✅ Voice feedback and coaching
- ✅ Perfect skeleton overlay alignment
- ✅ WebSocket-based real-time communication

### Recording Analysis
- ✅ Video upload (MP4, AVI, MOV, MKV)
- ✅ Background processing with Celery
- ✅ Frame-by-frame analysis
- ✅ Professional annotated videos with:
  - Color-coded skeleton overlay
  - Rep counters (correct/incorrect)
  - Real-time form feedback
  - H.264 MP4 encoding
- ✅ PDF report generation
- ✅ Interactive results visualization

### User Management (NEW - Phase 4)
- ✅ User registration and authentication (JWT)
- ✅ User profiles with fitness goals
- ✅ Workout history tracking
- ✅ Progress analytics and statistics
- ✅ Personal dashboard
- 🔄 AI chatbot for workout advice (Week 2)

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Web framework
- **MediaPipe** - Pose detection
- **OpenCV** - Video processing
- **MongoDB Atlas** - Database
- **Google Drive** - Video storage
- **Celery + Redis** - Background tasks
- **LangChain + Gemini 2.0 Flash** - AI chatbot (Phase 4)

### Frontend
- **Vanilla JavaScript** - Interactive features
- **WebSockets** - Real-time communication
- **Bootstrap** - UI framework
- **HTML5 Canvas** - Skeleton overlay

---

## 📦 Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd workout-analyzer
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install FFmpeg (Required)
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
```bash
# MongoDB
MONGODB_URL=mongodb+srv://...
DATABASE_NAME=workout_analyzer

# Google Drive
GOOGLE_DRIVE_CREDENTIALS_FILE=credentials.json
GOOGLE_DRIVE_TOKEN_FILE=google_drive_token.pickle

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Security (Phase 4)
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI (Phase 4 - Week 2)
GOOGLE_API_KEY=your-gemini-api-key
```

### 5. Run the Application
```bash
python run.py
```

Access at: http://localhost:8000

---

## 🎮 Quick Start

### For Users

#### 1. Register Account (NEW)
```
http://localhost:8000/auth/register
```

#### 2. Login
```
http://localhost:8000/auth/login
```

#### 3. Live Analysis
```
http://localhost:8000/live/
```
- Select exercise
- Start camera
- Get real-time feedback

#### 4. Recording Analysis
```
http://localhost:8000/recording/
```
- Upload workout video
- Wait for processing (2-4 minutes)
- View annotated video and results
- Download PDF report

#### 5. View Profile & Stats (NEW)
```
http://localhost:8000/profile/
```
- View workout history
- Track progress
- See statistics

### For Developers

#### Test Authentication API
```bash
# Register
curl -X POST http://localhost:8000/auth/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepass123",
    "fitness_level": "intermediate"
  }'

# Login
curl -X POST http://localhost:8000/auth/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepass123"
  }'

# Get user info (with token)
curl -X GET http://localhost:8000/auth/api/me \
  -H "Authorization: Bearer <your_token>"
```

---

## 📊 API Documentation

### Interactive API Docs
```
http://localhost:8000/docs
```

### Authentication Endpoints (NEW)
```
POST   /auth/api/register       - Register new user
POST   /auth/api/login          - Login and get JWT token
GET    /auth/api/me             - Get current user
PUT    /auth/api/me             - Update profile
POST   /auth/api/change-password - Change password
DELETE /auth/api/me             - Delete account
```

### Profile Endpoints (NEW)
```
GET    /profile/api/workouts    - Get workout history
GET    /profile/api/stats       - Get user statistics
GET    /profile/api/progress    - Get progress data
GET    /profile/api/recent-workouts - Get recent workouts
```

### Workout Endpoints
```
POST   /live/start-session      - Start live workout
POST   /recording/upload        - Upload video
GET    /recording/results/{id}  - Get analysis results
GET    /recording/report/{id}   - Download PDF report
```

---

## 🎯 Supported Exercises

1. **Push-ups** - Elbow angle tracking, body alignment, depth validation (90%+ accuracy)
2. **Squats** - Knee angle tracking, depth validation, alignment checking (90%+ accuracy)
3. **Bicep Curls** - Dual-arm detection, ROM tracking, elbow stability (85%+ accuracy)

---

## 📚 Documentation

### User Guides
- `docs/QUICK_START_PROFESSIONAL.md` - Quick start guide
- `docs/PHASE4_QUICKSTART.md` - Authentication guide (NEW)

### Technical Documentation
- `docs/PROJECT_PLAN.md` - Complete project plan
- `docs/API_DOCUMENTATION.md` - API reference
- `docs/PHASE4_PLAN.md` - Phase 4 implementation plan (NEW)
- `docs/PHASE4_SUMMARY.md` - Phase 4 summary (NEW)

---

## 🚀 Roadmap

### Phase 4: AI Integration (Current - 30% Complete)
- ✅ User authentication (JWT)
- ✅ User profiles and statistics
- 🔄 Protected routes (In Progress)
- 🔄 Frontend UI (In Progress)
- ⏳ AI chatbot (Week 2)

### Phase 5: Polish & Optimization (Planned)
- Performance optimization
- Advanced analytics
- Exercise library expansion

---

**Built with ❤️ using FastAPI, MediaPipe, and AI**

**Status:** Production-Ready (Phases 1-3) + Active Development (Phase 4) 🚀
