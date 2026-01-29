# Phase 4 - Quick Start Guide

## 🚀 What's New in Phase 4

Phase 4 adds **User Authentication** and **AI-Powered Workout Consultation** to the Workout Analyzer.

### New Features
- ✅ User registration and login (JWT-based)
- ✅ User profiles with fitness goals
- ✅ Workout history tracking per user
- ✅ Progress analytics and statistics
- 🔄 AI chatbot for workout advice (Week 2)
- 🔄 Personalized recommendations (Week 2)

---

## 📦 Installation

### 1. Dependencies Already Installed
All required packages are already in `requirements.txt`:
```bash
# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# AI (for Week 2)
langchain==0.1.0
langchain-google-genai==0.0.6
google-generativeai==0.3.2
```

### 2. Environment Variables
Make sure your `.env` file has:
```bash
# Existing
MONGODB_URL=your_mongodb_url
SECRET_KEY=your_secret_key_here

# For Week 2 (AI Chat)
GOOGLE_API_KEY=your_gemini_api_key

# JWT Settings (optional, has defaults)
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
```

### 3. Database Indexes
The app will automatically create indexes on startup, but you can manually create them:
```javascript
// In MongoDB
db.users.createIndex({ "username": 1 }, { unique: true })
db.users.createIndex({ "email": 1 }, { unique: true })
db.workouts.createIndex({ "user_id": 1 })
```

---

## 🎯 Testing the New Features

### 1. Start the Server
```bash
python run.py
```

### 2. Test Authentication API

#### Register a New User
```bash
curl -X POST http://localhost:8000/auth/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepass123",
    "full_name": "John Doe",
    "age": 25,
    "height": 175.5,
    "weight": 70.0,
    "fitness_level": "intermediate",
    "goals": ["weight_loss", "muscle_gain"]
  }'
```

**Expected Response:**
```json
{
  "message": "User registered successfully",
  "user_id": "507f1f77bcf86cd799439011",
  "username": "john_doe",
  "email": "john@example.com"
}
```

#### Login
```bash
curl -X POST http://localhost:8000/auth/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepass123"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "_id": "507f1f77bcf86cd799439011",
    "username": "john_doe",
    "email": "john@example.com",
    ...
  }
}
```

#### Get Current User (Protected Route)
```bash
# Save the token from login response
TOKEN="your_access_token_here"

curl -X GET http://localhost:8000/auth/api/me \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Test Profile API

#### Get User Statistics
```bash
curl -X GET http://localhost:8000/profile/api/stats \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "total_workouts": 10,
  "total_reps": 150,
  "total_calories": 125.5,
  "average_accuracy": 87.3,
  "workout_frequency": 3.5,
  "exercise_breakdown": {
    "push_ups": {
      "count": 5,
      "total_reps": 75,
      "average_accuracy": 0.89,
      "total_calories": 37.5
    }
  },
  "recent_trend": "improving",
  "days_active": 20
}
```

#### Get Workout History
```bash
curl -X GET "http://localhost:8000/profile/api/workouts?limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

#### Get Progress Data (for charts)
```bash
curl -X GET "http://localhost:8000/profile/api/progress?days=30" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔐 Authentication Flow

### For Frontend Developers

#### 1. Register User
```javascript
const response = await fetch('/auth/api/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'john_doe',
    email: 'john@example.com',
    password: 'securepass123',
    full_name: 'John Doe',
    age: 25,
    fitness_level: 'intermediate',
    goals: ['weight_loss', 'muscle_gain']
  })
});

const data = await response.json();
console.log('User registered:', data.user_id);
```

#### 2. Login
```javascript
const response = await fetch('/auth/api/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'john_doe',
    password: 'securepass123'
  })
});

const data = await response.json();

// Store token in localStorage
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('user', JSON.stringify(data.user));
```

#### 3. Make Authenticated Requests
```javascript
const token = localStorage.getItem('access_token');

const response = await fetch('/profile/api/stats', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const stats = await response.json();
console.log('User stats:', stats);
```

#### 4. Handle Token Expiration
```javascript
async function makeAuthRequest(url, options = {}) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.status === 401) {
    // Token expired, redirect to login
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/auth/login';
    return;
  }
  
  return response;
}
```

#### 5. Logout
```javascript
function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  window.location.href = '/auth/login';
}
```

---

## 📊 API Endpoints Reference

### Authentication Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/auth/login` | No | Login page (HTML) |
| GET | `/auth/register` | No | Register page (HTML) |
| POST | `/auth/api/register` | No | Register new user |
| POST | `/auth/api/login` | No | Login and get token |
| GET | `/auth/api/me` | Yes | Get current user |
| PUT | `/auth/api/me` | Yes | Update profile |
| POST | `/auth/api/change-password` | Yes | Change password |
| DELETE | `/auth/api/me` | Yes | Delete account |
| POST | `/auth/api/logout` | Yes | Logout |

### Profile Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/profile/` | Yes | Profile page (HTML) |
| GET | `/profile/api/workouts` | Yes | Get workout history |
| GET | `/profile/api/stats` | Yes | Get user statistics |
| GET | `/profile/api/progress` | Yes | Get progress data |
| GET | `/profile/api/recent-workouts` | Yes | Get recent workouts |

---

## 🎨 Frontend Integration (Coming Soon)

### Pages to Create
1. **Enhanced Login Page** - Modern login form with validation
2. **Enhanced Register Page** - Multi-step registration with goals
3. **Profile Page** - View/edit profile, workout history, stats
4. **Enhanced Dashboard** - User-specific data and quick actions

### JavaScript Files to Create
1. **auth.js** - Authentication utilities and token management
2. **profile.js** - Profile page functionality
3. **dashboard.js** - Enhanced dashboard with user data

---

## 🧪 Testing Checklist

### Manual Testing
- [ ] Register new user
- [ ] Login with correct credentials
- [ ] Login with wrong credentials (should fail)
- [ ] Access protected route without token (should fail)
- [ ] Access protected route with token (should work)
- [ ] Update user profile
- [ ] Change password
- [ ] Get user statistics
- [ ] Get workout history
- [ ] Token expiration (wait 30 minutes)

### API Testing with Postman/Insomnia
1. Import the API endpoints
2. Create environment variable for token
3. Test all endpoints
4. Verify error responses

---

## 🐛 Troubleshooting

### Issue: "Database not available"
**Solution:** Check MongoDB connection in `.env`

### Issue: "Could not validate credentials"
**Solution:** Token expired or invalid, login again

### Issue: "Email already registered"
**Solution:** Use different email or login with existing account

### Issue: "Username already taken"
**Solution:** Choose different username

### Issue: Token not working
**Solution:** 
1. Check token format: `Bearer <token>`
2. Verify token hasn't expired (30 min default)
3. Check SECRET_KEY in .env matches

---

## 📈 What's Next

### Week 2: AI Chatbot Integration
- LangChain + Gemini 2.0 Flash setup
- Chat API endpoints
- Workout context integration
- Chat UI
- Enhanced dashboard

### Coming Features
- AI workout recommendations
- Form improvement suggestions
- Progress insights
- Goal tracking
- Personalized training plans

---

## 📚 Additional Resources

### Documentation
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/) - JWT debugger
- [Pydantic Validation](https://docs.pydantic.dev/)

### Code Examples
- See `app/services/auth_service.py` for implementation
- See `app/api/routes/auth.py` for API examples
- See `app/core/dependencies.py` for auth middleware

---

**Phase 4 Status:** Week 1 - 60% Complete ✅  
**Next Milestone:** Complete frontend UI and protect workout routes  
**ETA:** End of Week 1

Happy coding! 🚀
