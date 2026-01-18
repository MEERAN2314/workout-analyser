# Workout Analyzer Project Plan

## Project Overview
A comprehensive workout analysis application with live video analysis and recording analysis capabilities. Users can get real-time feedback during workouts or upload recorded videos for detailed analysis and AI-powered consultation.

## Updated Tech Stack

### Backend
- **FastAPI** - Main web framework
- **Jinja2** - Server-side templating
- **MediaPipe** - Pose estimation and workout analysis
- **OpenCV** - Video processing and manipulation
- **MongoDB Atlas** - Primary database (user data, workout sessions, analysis results, chat history)
- **Google Drive** - Video file storage only
- **Redis** - Caching and session management
- **Celery** - Background task processing for video analysis
- **LangChain + Gemini 2.0 Flash** - AI chatbot for workout consultation

### Frontend
- **Vanilla JavaScript** - Interactive features and real-time functionality
- **WebSockets** - Real-time communication for live analysis
- **HTML5 Canvas** - Skeleton overlay rendering
- **Web APIs** - Camera access, speech synthesis, file handling

### Additional Tools
- **google-api-python-client** - Google Drive API client
- **Pydantic** - Data validation and serialization
- **Pillow** - Image processing
- **ReportLab** - PDF generation for workout reports
- **python-multipart** - File upload handling
- **Motor** - Async MongoDB driver for FastAPI

## Clean Feature Implementation Plan

### 1. Home Page & Navigation
- **Landing page** with live/recording analysis options
- **Exercise library** browser with thumbnails
- **User authentication** and profile management
- **Dashboard** with recent workouts and progress

### 2. Live Analysis Module
- **Exercise selection** from predefined library
- **Camera setup** with positioning guidelines
- **Real-time pose detection** and rep counting
- **Live feedback overlay** with form corrections
- **Audio coaching** (optional)
- **Session data** stored in MongoDB (no video storage)
- **Instant results** with performance summary

### 3. Recording Analysis Module
- **Video upload** to Google Cloud Storage
- **Background processing** with Celery workers
- **Exercise detection** or manual selection
- **Comprehensive analysis**:
  - Frame-by-frame pose analysis
  - Rep counting with accuracy scoring
  - Form assessment and mistake detection
  - Skeleton visualization generation
- **Results storage** in MongoDB with GCS video references
- **Interactive playback** with analysis overlay
- **PDF report** generation and download

### 4. AI Workout Consultant
- **Contextual chat** using workout history from MongoDB
- **Exercise recommendations** based on performance data
- **Form improvement** suggestions
- **Progress insights** and goal setting
- **Chat history** persistence in MongoDB

### 5. Data Management
- **MongoDB Collections**:
  - Users (profiles, preferences, goals)
  - Workouts (sessions, metrics, analysis results)
  - Exercises (library, instructions, form guidelines)
  - Chat_sessions (AI conversations, context)
- **Google Drive Integration**:
  - Video upload with shareable links
  - Free 15GB storage for testing
  - Easy authentication with Google account

### 6. Analytics & Reporting
- **Progress tracking** with MongoDB aggregation
- **Performance metrics** calculation and storage
- **PDF reports** with charts and recommendations
- **Data export** capabilities

## Development Phases

### Phase 1: Foundation (Weeks 1-2)
- FastAPI project setup with MongoDB Atlas connection
- Google Drive integration
- Basic Jinja2 templates and routing
- User authentication system
- Exercise library setup in MongoDB

### Phase 2: Live Analysis MVP (Weeks 3-4)
- MediaPipe integration for pose detection
- Real-time camera feed processing
- Basic rep counting for 2-3 exercises (push-ups, squats)
- WebSocket implementation for live feedback
- Session data storage in MongoDB

### Phase 3: Recording Analysis Core (Weeks 5-6)
- Video upload to Google Drive
- Celery setup for background processing
- Video analysis pipeline with MediaPipe
- Results storage and retrieval from MongoDB
- Basic analysis results display

### Phase 4: Enhanced Analysis (Weeks 7-8)
- Advanced form validation algorithms
- Skeleton overlay generation
- PDF report creation with ReportLab
- Interactive video playback with analysis
- Performance metrics calculation

### Phase 5: AI Integration (Weeks 9-10)
- LangChain + Gemini 2.0 Flash setup
- Chat interface development
- Context integration with workout data
- Conversation persistence in MongoDB

### Phase 6: Polish & Optimization (Weeks 11-12)
- UI/UX improvements
- Performance optimization
- Error handling and edge cases
- Testing and bug fixes
- Deployment preparation

## Key Features Summary

### Live Analysis
- Real-time pose detection and rep counting
- Live feedback with form corrections
- Audio coaching capabilities
- Instant session summaries

### Recording Analysis
- Video upload and background processing
- Comprehensive form analysis with timestamps
- Interactive skeleton overlay visualization
- Detailed PDF reports with recommendations
- Calorie estimation and performance metrics

### AI Consultation
- Context-aware workout discussions
- Personalized exercise recommendations
- Progress tracking and goal setting
- Form improvement suggestions

## Storage Strategy
- **Videos**: Google Drive for free storage and easy testing
- **All other data**: MongoDB Atlas for flexibility and document-based storage
- **Caching**: Redis for session management and temporary data
- **Background jobs**: Celery with Redis as message broker

## Timeline
**Total Duration**: 12 weeks
**Delivery**: Incremental with working features at each phase
**Testing**: Continuous throughout development
**Deployment**: Prepared in final phase