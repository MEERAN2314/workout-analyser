# Gemini Model Setup Guide

## Current Configuration

The AI chat service now tries multiple Gemini models in priority order:

1. `gemini-1.5-flash-latest` - Latest 1.5 Flash (recommended)
2. `gemini-1.5-flash` - Stable 1.5 Flash
3. `gemini-1.5-pro` - More capable Pro model
4. `gemini-pro` - Fallback basic Pro

## Check Available Models

Run this script to see which models are available with your API key:

```bash
python check_gemini_models.py
```

This will show:
- All available Gemini models
- Which models support chat (generateContent)
- Recommended model name to use

## Update Model Manually

If you want to use a specific model, edit `app/services/ai_chat_service.py`:

```python
self.llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",  # Change this to your preferred model
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.7,
    max_tokens=2000,
    convert_system_message_to_human=True
)
```

## Common Model Names

### Available Models (as of 2026-01-29)

| Model Name | Description | Speed | Quality | Cost |
|------------|-------------|-------|---------|------|
| `gemini-1.5-flash` | Fast, efficient | ⚡⚡⚡ | ⭐⭐⭐ | 💰 |
| `gemini-1.5-flash-latest` | Latest Flash | ⚡⚡⚡ | ⭐⭐⭐⭐ | 💰 |
| `gemini-1.5-pro` | More capable | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰 |
| `gemini-pro` | Basic Pro | ⚡⚡ | ⭐⭐⭐ | 💰 |

### Experimental Models (may not be available)

| Model Name | Status |
|------------|--------|
| `gemini-2.0-flash-exp` | ❌ Not available in v1beta API |
| `gemini-2.5-flash` | ❌ Not yet released |
| `gemini-exp-1206` | ⚠️ May require special access |

## Troubleshooting

### Error: "404 model not found"

**Solution 1:** Run the check script
```bash
python check_gemini_models.py
```

**Solution 2:** Use a stable model
```python
model="gemini-1.5-flash"  # Most reliable
```

**Solution 3:** Check your API key
- Visit https://makersuite.google.com/app/apikey
- Verify your key is active
- Check if you have API access enabled

### Error: "API key not valid"

1. Check `.env` file has `GOOGLE_API_KEY=your_key_here`
2. Restart the application after updating .env
3. Verify key at https://makersuite.google.com/app/apikey

### Error: "Rate limit exceeded"

1. Wait a few minutes
2. Check your API quota at https://console.cloud.google.com/
3. Consider upgrading your API plan

### Error: "SystemMessages not supported"

This is already fixed with `convert_system_message_to_human=True`

## API Key Setup

### Get a Free API Key

1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key
4. Add to `.env` file:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

### Free Tier Limits

- 60 requests per minute
- 1,500 requests per day
- Sufficient for testing and small deployments

### Paid Tier

For production use, consider:
- Higher rate limits
- More requests per day
- Priority support
- Access to newer models

Visit: https://ai.google.dev/pricing

## Model Selection Guide

### For Development/Testing
Use: `gemini-1.5-flash`
- Fast responses
- Good quality
- Free tier friendly

### For Production
Use: `gemini-1.5-flash-latest`
- Latest improvements
- Better quality
- Still fast

### For Complex Queries
Use: `gemini-1.5-pro`
- Best quality
- More context understanding
- Slower but more accurate

## Configuration Parameters

```python
ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",           # Model name
    google_api_key=settings.GOOGLE_API_KEY,  # Your API key
    temperature=0.7,                     # Creativity (0.0-1.0)
    max_tokens=2000,                     # Max response length
    convert_system_message_to_human=True # Fix for system messages
)
```

### Temperature Guide
- `0.0-0.3`: Focused, deterministic (good for facts)
- `0.4-0.7`: Balanced (good for coaching)
- `0.8-1.0`: Creative, varied (good for brainstorming)

### Max Tokens Guide
- `500-1000`: Short responses
- `1000-2000`: Medium responses (current)
- `2000-4000`: Long, detailed responses

## Testing

After updating the model, test the AI chat:

```bash
# 1. Restart the application
# 2. Login to the app
# 3. Go to /chat
# 4. Send a test message
# 5. Check server logs for model initialization
```

Expected log output:
```
INFO - Attempting to initialize with model: gemini-1.5-flash-latest
INFO - ✅ Successfully initialized with model: gemini-1.5-flash-latest
```

## Version
- Last Updated: 2026-01-29
- Current Model: gemini-1.5-flash (with fallbacks)
- Status: ✅ Working
