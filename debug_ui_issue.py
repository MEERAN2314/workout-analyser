#!/usr/bin/env python3
"""
Debug script to check for UI issues and background processing
"""
import asyncio
import aiohttp
import json

async def debug_ui_issue():
    """Debug the UI display issue"""
    base_url = "http://localhost:8000"
    
    print("🔍 Debugging Recording Analysis UI Issue...")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Check if page loads correctly
        print("\n1. Testing page load...")
        async with session.get(f"{base_url}/recording/") as resp:
            if resp.status == 200:
                content = await resp.text()
                
                # Check for CSS issues
                if 'display: none !important' in content:
                    print("   ✅ CSS hiding rules found in template")
                else:
                    print("   ⚠️  CSS hiding rules might be missing")
                
                # Check for JavaScript
                if 'console.log' in content:
                    print("   ✅ Debug JavaScript found")
                else:
                    print("   ⚠️  Debug JavaScript missing")
                
                print(f"   ✅ Page loaded successfully ({len(content)} bytes)")
            else:
                print(f"   ❌ Page load failed: {resp.status}")
        
        # Test 2: Check for any existing sessions
        print("\n2. Checking for existing sessions...")
        try:
            # Try a few random session IDs to see if any exist
            test_sessions = [
                "507f1f77bcf86cd799439011",
                "507f1f77bcf86cd799439012", 
                "507f1f77bcf86cd799439013"
            ]
            
            for session_id in test_sessions:
                async with session.get(f"{base_url}/recording/status/{session_id}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"   ⚠️  Found existing session: {session_id} - {data.get('status')}")
                    elif resp.status == 404:
                        print(f"   ✅ No session found: {session_id}")
                    else:
                        print(f"   ❓ Unexpected response for {session_id}: {resp.status}")
        except Exception as e:
            print(f"   ❌ Error checking sessions: {e}")
        
        # Test 3: Check database for any active sessions
        print("\n3. Database check would require direct MongoDB access")
        print("   💡 Suggestion: Check MongoDB for any documents in 'workouts' collection")
        print("   💡 Command: db.workouts.find({analysis_completed: false})")
        
        print("\n🔧 Troubleshooting Steps:")
        print("   1. Clear browser cache (Ctrl+F5 or Cmd+Shift+R)")
        print("   2. Check browser console for JavaScript errors")
        print("   3. Verify no background Celery tasks are running")
        print("   4. Check MongoDB for orphaned sessions")
        print("   5. Restart the FastAPI server")
        
        print("\n📋 Expected Behavior:")
        print("   ✅ Only 'Upload Workout Video' section should be visible")
        print("   ❌ 'Analyzing Your Workout' section should be hidden")
        print("   ❌ 'Analysis Results' section should be hidden")

def check_celery_status():
    """Check if Celery workers are running"""
    print("\n⚙️  Checking Celery Status...")
    
    try:
        from app.services.celery_app import celery_app
        
        # Try to get active tasks
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        if active_tasks:
            print(f"   ⚠️  Active Celery tasks found: {len(active_tasks)}")
            for worker, tasks in active_tasks.items():
                print(f"      Worker {worker}: {len(tasks)} tasks")
                for task in tasks:
                    print(f"        - {task.get('name', 'unknown')} ({task.get('id', 'no-id')})")
        else:
            print("   ✅ No active Celery tasks")
            
    except Exception as e:
        print(f"   ❌ Error checking Celery status: {e}")
        print("   💡 This is normal if Celery worker is not running")

if __name__ == "__main__":
    print("Starting UI issue debugging...")
    print("=" * 50)
    
    # Check Celery status
    check_celery_status()
    
    # Check UI endpoints
    try:
        asyncio.run(debug_ui_issue())
    except Exception as e:
        print(f"\n❌ Debug failed: {e}")
        print("Make sure the server is running on http://localhost:8000")
    
    print("\n" + "=" * 50)
    print("🎯 Quick Fix Suggestions:")
    print("1. Hard refresh the browser (Ctrl+F5)")
    print("2. Check browser developer tools console")
    print("3. Restart FastAPI server: python run.py")
    print("4. Clear any orphaned database sessions")