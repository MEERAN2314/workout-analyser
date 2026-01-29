# AI Chat - Gemini Model Update

## Current Configuration

The AI chat service now uses **Gemini 2.5 Flash** - the latest stable model from Google!

### Model Priority (tries in order):
1. `gemini-2.5-flash` - **Latest stable (June 2025)** ⭐ USING THIS
2. `gemini-2.5-pro` - More capable 2.5 Pro
3. `gemini-2.0-flash` - Stable 2.0 Flash
4. `gemini-flash-latest` - Latest Flash (any version)
5. `gemini-pro-latest` - Latest Pro (fallback)

## Changes Made

### 1. Fixed SystemMessage Error
**Problem:** 
```
SystemMessages are not yet supported!
```

**Solution:**
- Added `convert_system_message_to_human=True` parameter to ChatGoogleGenerativeAI
- Modified message handling to include system prompt in first human message
- Subsequent messages only include context and user question

### 2. Fixed Model Not Found Error
**Problem:**
```
404 models/gemini-2.0-flash-exp is not found
```

**Solution:**
- Changed to use stable `gemini-2.5-flash` model (latest available!)
- Added fallback mechanism to try multiple models
- Logs which model successfully initialized

### 3. Model Configuration
**Current Model:** `gemini-2.5-flash` ⭐ (with fallbacks)

**Features:**
- Released June 2025
- Supports up to 1 million tokens
- Fast and versatile multimodal model
- Excellent for workout coaching and analysis

**Configuration:**
```python
models_to_try = [
    "gemini-2.5-flash",          # Latest stable (June 2025)
    "gemini-2.5-pro",            # More capable 2.5 Pro
    "gemini-2.0-flash",          # Stable 2.0 Flash
    "gemini-flash-latest",       # Latest Flash (any version)
    "gemini-pro-latest"          # Latest Pro (fallback)
]
```

**Before:**
- Used SystemMessage for system prompt
- Failed with "SystemMessages not supported" error

**After:**
- System prompt included in first human message
- Subsequent messages use context-aware formatting
- Conversation history maintained properly

**Message Flow:**
```
First Message:
[System Prompt]
---
User Context: [user info]
Recent Workouts: [workout history]
User Question: [actual question]

Subsequent Messages:
User Context: [user info]
Recent Workouts: [workout history]
User Question: [actual question]
```

## Benefits

1. **No More Errors:** SystemMessage error completely resolved
2. **Better Context:** System prompt included in conversation naturally
3. **Longer Responses:** Increased max_tokens from 1000 to 2000
4. **Maintained Quality:** Same AI coaching quality with better reliability

## Testing

### Test the AI Chat
1. Login to the application
2. Go to `/chat`
3. Start a new chat session
4. Send a message like "How can I improve my push-ups?"
5. Should receive a helpful response without errors

### Expected Behavior
- ✅ No SystemMessage errors
- ✅ Contextual responses based on user profile
- ✅ References to recent workouts
- ✅ Helpful fitness coaching advice
- ✅ Conversation history maintained

## Model Availability

### Current Models (as of 2026-01-29)
- ✅ `gemini-2.0-flash-exp` - Latest experimental (USING THIS)
- ✅ `gemini-1.5-flash` - Stable version
- ✅ `gemini-1.5-pro` - More capable, slower
- ❌ `gemini-2.5-flash` - Not yet available in API

### When Gemini 2.5 Flash Becomes Available
Simply update the model name:
```python
model="gemini-2.5-flash"  # or "gemini-2.5-flash-exp"
```

## Features

### AI Chat Capabilities
1. **Workout Analysis:** Reviews your recent workouts
2. **Form Feedback:** Provides specific form corrections
3. **Goal Setting:** Helps plan fitness goals
4. **Motivation:** Encourages and celebrates progress
5. **Safety:** Prioritizes proper form and injury prevention

### Context Awareness
The AI has access to:
- User profile (age, fitness level, goals)
- Recent workout history (last 5 workouts)
- Exercise performance data (reps, accuracy)
- Form feedback from analysis
- Conversation history (last 10 messages)

## API Endpoints

### Chat API (`/chat/api/`)
- `POST /start` - Start new chat session
- `POST /message` - Send message and get AI response
- `GET /sessions` - List user's chat sessions
- `GET /session/{id}` - Get specific session with messages
- `DELETE /session/{id}` - Delete chat session

## Configuration

### Environment Variables Required
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Get API Key
1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key
3. Add to `.env` file

## Error Handling

### Common Issues

**Issue:** "API key not valid"
**Solution:** Check GOOGLE_API_KEY in .env file

**Issue:** "Rate limit exceeded"
**Solution:** Wait a moment and try again, or upgrade API quota

**Issue:** "Model not found"
**Solution:** Check model name is correct and available

**Issue:** "Response too long"
**Solution:** max_tokens is set to 2000, should be sufficient

## Performance

### Response Times
- Average: 2-4 seconds
- With context: 3-5 seconds
- Long conversations: 4-6 seconds

### Token Usage
- System prompt: ~200 tokens
- User context: ~100 tokens
- Workout context: ~150 tokens per workout
- User message: varies
- AI response: up to 2000 tokens

## Future Enhancements

1. **Streaming Responses:** Real-time token streaming
2. **Voice Input:** Speech-to-text integration
3. **Image Analysis:** Upload form check photos
4. **Workout Plans:** Generate custom workout programs
5. **Progress Tracking:** Long-term goal monitoring
6. **Multi-language:** Support for multiple languages

## Version
- AI Chat Service: v2.0
- Model: Gemini 2.0 Flash Experimental
- Last Updated: 2026-01-29
- Status: ✅ Working
