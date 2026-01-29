#!/usr/bin/env python3
"""
Check available Gemini models
"""
import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

def main():
    """List available Gemini models"""
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in .env file")
        return
    
    print("🔑 API Key found")
    print(f"   Key: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    try:
        # Configure API
        genai.configure(api_key=api_key)
        
        print("📋 Available Gemini Models:")
        print("=" * 80)
        
        # List all models
        models = genai.list_models()
        
        gemini_models = []
        for model in models:
            if 'gemini' in model.name.lower():
                gemini_models.append(model)
                print(f"\n✅ {model.name}")
                print(f"   Display Name: {model.display_name}")
                print(f"   Description: {model.description}")
                
                # Check supported methods
                if hasattr(model, 'supported_generation_methods'):
                    methods = model.supported_generation_methods
                    print(f"   Supported Methods: {', '.join(methods)}")
                
                # Check if it supports generateContent
                supports_chat = 'generateContent' in getattr(model, 'supported_generation_methods', [])
                print(f"   Supports Chat: {'✅ Yes' if supports_chat else '❌ No'}")
        
        print("\n" + "=" * 80)
        print(f"\n📊 Total Gemini models found: {len(gemini_models)}")
        
        # Recommend models for chat
        print("\n💡 Recommended models for AI Chat:")
        recommended = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-latest", 
            "models/gemini-1.5-pro",
            "models/gemini-2.0-flash-exp",
            "models/gemini-exp-1206"
        ]
        
        for rec in recommended:
            found = any(rec in m.name for m in gemini_models)
            status = "✅ Available" if found else "❌ Not available"
            print(f"   {rec}: {status}")
        
        # Show how to use in code
        print("\n📝 To use in code (ai_chat_service.py):")
        if gemini_models:
            # Get the first flash model
            flash_models = [m for m in gemini_models if 'flash' in m.name.lower()]
            if flash_models:
                model_name = flash_models[0].name.replace('models/', '')
                print(f'   model="{model_name}"')
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your API key is valid")
        print("2. Ensure you have internet connection")
        print("3. Visit https://makersuite.google.com/app/apikey to verify your key")

if __name__ == "__main__":
    main()
