# Phase 4 - AI Integration Plan

## 🎯 Phase 4 Overview

**Goal:** Integrate AI-powered workout consultation using LangChain + Gemini 2.0 Flash

**Duration:** 2 weeks

**Status:** 🚀 Starting Now

---

## 📋 Phase 4 Objectives

### Primary Goals
1. **AI Chatbot Integration** - LangChain + Gemini 2.0 Flash for workout consultation
2. **User Authentication** - JWT-based authentication system
3. **User Profiles** - Profile management and workout history
4. **Progress Tracking** - Historical data analysis and trends

### Secondary Goals
5. **Enhanced Dashboard** - User-specific workout history and stats
6. **Chat History** - Persistent conversation storage
7. **Context-Aware AI** - AI that understands user's workout history

---

## 🏗️ Architecture

### New Components

```
Phase 4 Architecture:
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│  - Login/Register Pages                         │
│  - User Dashboard                               │
│  - AI Chat Interface                            │
│  - Profile Management                           │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│                  FastAPI Backend                 │
│  - Auth Routes (JWT)                            │
│  - Chat Routes (AI)                             │
│  - Profile Routes                               │
│  - Protected Endpoints                          │
└─────────────────────────────────────────────────┘
                      ↓
┌──────────────────┬──────────────────────────────┐
│   LangChain      │      MongoDB Atlas           │
│   + Gemini       │   - users                    │
│                  │   - workouts                 │
│   - Chat Agent   │   - chat_sessions            │
│   - Context      │   - chat_messages            │
│   - Memory       │                              │
└──────────────────┴──────────────────────────────┘
```

---

## 📦 Implementation Tasks

### Week 1: Authentication & User Management

#### Task 1.1: User Authentication System ✅
**Files to Create:**
- `app/models/user.py` (enhance existing)
- `app/services/auth_service.py`
- `app/api/routes/auth.py` (enhance existing)

**Features:**
- User registration with validation
- Login with JWT token generation
- Password hashing (bcrypt)
- Token verification middleware
- Refresh token support

#### Task 1.2: User Profile Management ✅
**Files to Create:**
- `app/api/routes/profile.py`
- `app/services/user_service.py`

**Features:**
- Get user profile
- Update profile (name, age, weight, goals)
- View workout history
- Delete account

#### Task 1.3: Protected Routes ✅
**Files to Modify:**
- `app/api/routes/live_analysis.py`
- `app/api/routes/recording_analysis_new.py`
- `app/main.py`

**Changes:**
- Add authentication dependency
- Link workouts to user accounts
- Filter data by user

#### Task 1.4: Frontend Authentication ✅
**Files to Create:**
- `app/templates/auth/login.html` (enhance existing)
- `app/templates/auth/register.html` (enhance existing)
- `app/templates/profile.html`
- `app/static/js/auth.js`

**Features:**
- Login/register forms
- Token storage (localStorage)
- Auto-redirect on auth failure
- Profile editing interface

---

### Week 2: AI Chatbot Integration

#### Task 2.1: LangChain + Gemini Setup ✅
**Files to Create:**
- `app/services/ai_chat_service.py`
- `app/models/chat.py`

**Features:**
- Gemini 2.0 Flash integration
- LangChain conversation chain
- Memory management
- Context injection

#### Task 2.2: Chat API Endpoints ✅
**Files to Create:**
- `app/api/routes/chat.py`

**Endpoints:**
- `POST /chat/start` - Start new chat session
- `POST /chat/{session_id}/message` - Send message
- `GET /chat/{session_id}/history` - Get chat history
- `GET /chat/sessions` - List user's chat sessions
- `DELETE /chat/{session_id}` - Delete chat session

#### Task 2.3: Workout Context Integration ✅
**Files to Modify:**
- `app/services/ai_chat_service.py`

**Features:**
- Fetch user's recent workouts
- Include workout stats in context
- Analyze performance trends
- Generate personalized recommendations

#### Task 2.4: Chat Interface ✅
**Files to Create:**
- `app/templates/chat.html`
- `app/static/js/chat.js`
- `app/static/css/chat.css`

**Features:**
- Modern chat UI
- Real-time message updates
- Typing indicators
- Message history
- Context display (recent workouts)

#### Task 2.5: Enhanced Dashboard ✅
**Files to Modify:**
- `app/templates/dashboard.html`
- `app/api/routes/home.py`

**Features:**
- User-specific workout history
- Progress charts
- Quick stats (total reps, calories, accuracy)
- Recent chat sessions
- Quick access to AI chat

---

## 🗄️ Database Schema

### New Collections

#### users
```javascript
{
  _id: ObjectId,
  username: String (unique),
  email: String (unique),
  password_hash: String,
  full_name: String,
  age: Number,
  height: Number,  // cm
  weight: Number,  // kg
  fitness_level: String,  // beginner, intermediate, advanced
  goals: [String],  // weight_loss, muscle_gain, endurance, etc.
  created_at: DateTime,
  updated_at: DateTime,
  last_login: DateTime
}
```

#### chat_sessions
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  title: String,  // Auto-generated or user-defined
  created_at: DateTime,
  updated_at: DateTime,
  message_count: Number,
  context_workouts: [ObjectId]  // Referenced workouts
}
```

#### chat_messages
```javascript
{
  _id: ObjectId,
  session_id: ObjectId,
  user_id: ObjectId,
  role: String,  // "user" or "assistant"
  content: String,
  timestamp: DateTime,
  context_used: Object  // Workout data used for this response
}
```

#### workouts (enhance existing)
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,  // NEW: Link to user
  session_type: String,  // "live" or "recording"
  exercise_name: String,
  // ... existing fields ...
  created_at: DateTime
}
```

---

## 🔐 Security

### JWT Configuration
```python
SECRET_KEY: str  # Already in .env
ALGORITHM: "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: 30
REFRESH_TOKEN_EXPIRE_DAYS: 7
```

### Password Security
- Bcrypt hashing with salt
- Minimum 8 characters
- Complexity requirements (optional)

### API Security
- JWT token validation on protected routes
- Rate limiting on auth endpoints
- CORS configuration
- Input validation with Pydantic

---

## 🤖 AI Chat Features

### Conversation Capabilities

1. **Workout Analysis**
   - "How did I do on my last workout?"
   - "What mistakes did I make?"
   - "Show me my progress"

2. **Form Improvement**
   - "How can I improve my push-up form?"
   - "Why do I keep getting incorrect reps?"
   - "What should I focus on?"

3. **Exercise Recommendations**
   - "What exercise should I do next?"
   - "Suggest a workout routine"
   - "What's good for building chest?"

4. **Progress Tracking**
   - "Am I improving?"
   - "Compare my last 5 workouts"
   - "How many calories have I burned this week?"

5. **Goal Setting**
   - "Help me set a fitness goal"
   - "How can I reach 50 push-ups?"
   - "Create a training plan"

### Context Integration

The AI will have access to:
- User profile (age, weight, fitness level, goals)
- Recent workout history (last 10 sessions)
- Performance trends (accuracy, reps, calories)
- Common mistakes and feedback
- Exercise preferences

---

## 📊 Progress Tracking

### Metrics to Track

1. **Performance Metrics**
   - Total workouts completed
   - Total reps performed
   - Average accuracy score
   - Total calories burned
   - Workout frequency

2. **Improvement Metrics**
   - Accuracy trend over time
   - Rep count progression
   - Form improvement rate
   - Consistency score

3. **Exercise-Specific**
   - Best performance per exercise
   - Most improved exercise
   - Favorite exercises
   - Exercises needing work

---

## 🎨 UI/UX Enhancements

### New Pages

1. **Login Page** (`/auth/login`)
   - Clean, modern design
   - Email/username + password
   - "Remember me" option
   - Link to register

2. **Register Page** (`/auth/register`)
   - Multi-step form
   - Profile information
   - Fitness goals selection
   - Terms acceptance

3. **Profile Page** (`/profile`)
   - View/edit profile
   - Change password
   - Workout statistics
   - Account settings

4. **Chat Page** (`/chat`)
   - Modern chat interface
   - Message history
   - Context sidebar (recent workouts)
   - Quick actions

5. **Enhanced Dashboard** (`/dashboard`)
   - Welcome message with user name
   - Quick stats cards
   - Recent workouts list
   - Progress charts
   - Quick access to chat

### Navigation Updates
- Add user menu (profile, logout)
- Show username in navbar
- Protected route indicators
- Login/register buttons for guests

---

## 🧪 Testing Plan

### Unit Tests
- Auth service (registration, login, token validation)
- AI chat service (message handling, context injection)
- User service (profile CRUD)

### Integration Tests
- End-to-end auth flow
- Chat with workout context
- Protected route access
- User workout history

### Manual Testing
- Register new user
- Login and receive token
- Create workout session
- Chat with AI about workout
- View progress on dashboard
- Update profile
- Logout and login again

---

## 📝 API Endpoints Summary

### Authentication
```
POST   /auth/register          - Register new user
POST   /auth/login             - Login and get JWT
POST   /auth/refresh           - Refresh access token
POST   /auth/logout            - Logout (optional)
GET    /auth/me                - Get current user
```

### Profile
```
GET    /profile                - Get user profile
PUT    /profile                - Update profile
DELETE /profile                - Delete account
GET    /profile/workouts       - Get workout history
GET    /profile/stats          - Get user statistics
```

### Chat
```
POST   /chat/start             - Start new chat session
POST   /chat/{id}/message      - Send message
GET    /chat/{id}/history      - Get chat history
GET    /chat/sessions          - List chat sessions
DELETE /chat/{id}              - Delete chat session
```

### Protected Routes (require auth)
```
POST   /live/start-session     - Start live workout
POST   /recording/upload       - Upload video
GET    /recording/results/{id} - Get results
```

---

## 🚀 Deployment Checklist

### Environment Variables
```bash
# Add to .env
GOOGLE_API_KEY=your_gemini_api_key
SECRET_KEY=your_jwt_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Dependencies
```bash
# Already in requirements.txt
langchain==0.1.0
langchain-google-genai==0.0.6
google-generativeai==0.3.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### Database Indexes
```python
# Create indexes for performance
users.username (unique)
users.email (unique)
workouts.user_id
chat_sessions.user_id
chat_messages.session_id
```

---

## 📈 Success Criteria

### Week 1 Complete When:
- ✅ Users can register and login
- ✅ JWT authentication working
- ✅ Profile management functional
- ✅ Workouts linked to users
- ✅ Protected routes enforced

### Week 2 Complete When:
- ✅ AI chat responding to messages
- ✅ Chat using workout context
- ✅ Conversation history saved
- ✅ Dashboard shows user data
- ✅ Progress tracking visible

### Phase 4 Complete When:
- ✅ All authentication flows working
- ✅ AI providing helpful workout advice
- ✅ Users can track their progress
- ✅ Chat history persisted
- ✅ UI polished and responsive
- ✅ All tests passing

---

## 🎯 Next Steps After Phase 4

### Phase 5: Polish & Optimization
- Performance optimization
- Advanced analytics
- Social features (optional)
- Mobile responsiveness
- Exercise library expansion

### Phase 6: Deployment
- Production environment setup
- CI/CD pipeline
- Monitoring and logging
- Backup strategy
- Documentation

---

## 📚 Resources

### Documentation
- [LangChain Docs](https://python.langchain.com/)
- [Gemini API Docs](https://ai.google.dev/docs)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://jwt.io/introduction)

### Code Examples
- LangChain conversation chains
- FastAPI JWT authentication
- MongoDB user management
- WebSocket chat implementation

---

**Phase 4 Start Date:** January 29, 2026
**Expected Completion:** February 12, 2026
**Status:** 🚀 Ready to Begin

Let's build an intelligent workout assistant! 💪🤖
