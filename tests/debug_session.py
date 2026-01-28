#!/usr/bin/env python3
"""
Debug a specific session to see what's happening
"""
import asyncio
import aiohttp
import json

async def debug_session(session_id):
    """Debug a specific session"""
    base_url = "http://localhost:8000"
    
    print(f"🔍 Debugging session: {session_id}")
    print("-" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Check debug endpoint
        async with session.get(f"{base_url}/recording/debug-session/{session_id}") as resp:
            if resp.status == 200:
                debug_data = await resp.json()
                
                print("📊 Session Debug Info:")
                print(json.dumps(debug_data, indent=2))
                
                # Analyze the data
                session_data = debug_data.get('session_data', {})
                task_info = debug_data.get('task_info', {})
                
                print("\n🔍 Analysis:")
                print(f"   Exercise: {session_data.get('exercise_name')}")
                print(f"   Video URL: {'✅ Present' if session_data.get('video_url') else '❌ Missing'}")
                print(f"   Processing Started: {session_data.get('processing_started')}")
                print(f"   Analysis Completed: {session_data.get('analysis_completed')}")
                
                if task_info:
                    print(f"   Task ID: {task_info.get('task_id')}")
                    print(f"   Task State: {task_info.get('state')}")
                    print(f"   Task Ready: {task_info.get('ready')}")
                    print(f"   Task Info: {task_info.get('info')}")
                else:
                    print("   ❌ No Celery task found")
                
            else:
                print(f"❌ Debug endpoint failed: {resp.status}")
                error_text = await resp.text()
                print(f"   Error: {error_text}")

if __name__ == "__main__":
    session_id = input("Enter session ID to debug: ").strip()
    
    if session_id:
        try:
            asyncio.run(debug_session(session_id))
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("No session ID provided")