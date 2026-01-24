#!/usr/bin/env python3
"""
Monitor video processing status
"""
import asyncio
import aiohttp
import time

async def monitor_session(session_id, max_wait_minutes=5):
    """Monitor a processing session"""
    base_url = "http://localhost:8000"
    max_checks = max_wait_minutes * 30  # Check every 2 seconds
    
    print(f"🔍 Monitoring session: {session_id}")
    print(f"⏱️  Max wait time: {max_wait_minutes} minutes")
    print("-" * 50)
    
    async with aiohttp.ClientSession() as session:
        for check_num in range(max_checks):
            try:
                async with session.get(f"{base_url}/recording/status/{session_id}") as resp:
                    if resp.status == 200:
                        status_data = await resp.json()
                        
                        status = status_data.get('status', 'unknown')
                        progress = status_data.get('progress', 0)
                        message = status_data.get('message', 'No message')
                        
                        print(f"[{check_num*2:3d}s] Status: {status:12} | Progress: {progress:3d}% | {message}")
                        
                        if status == 'completed':
                            print("\n🎉 Processing completed successfully!")
                            
                            # Get results
                            async with session.get(f"{base_url}/recording/results/{session_id}") as results_resp:
                                if results_resp.status == 200:
                                    results = await results_resp.json()
                                    print(f"📊 Results:")
                                    print(f"   Exercise: {results.get('exercise_name')}")
                                    print(f"   Total Reps: {results.get('total_reps')}")
                                    print(f"   Correct Reps: {results.get('correct_reps')}")
                                    print(f"   Accuracy: {results.get('accuracy_score', 0)*100:.1f}%")
                                    print(f"   Calories: {results.get('calories_burned', 0):.1f}")
                                    print(f"   Feedback: {len(results.get('form_feedback', []))} items")
                                    print(f"   Mistakes: {len(results.get('mistakes', []))} identified")
                                else:
                                    print("⚠️  Could not fetch results")
                            return True
                            
                        elif status == 'failed':
                            print(f"\n❌ Processing failed: {message}")
                            return False
                            
                    elif resp.status == 404:
                        print(f"❌ Session not found: {session_id}")
                        return False
                    else:
                        print(f"⚠️  HTTP {resp.status}: {await resp.text()}")
                        
            except Exception as e:
                print(f"❌ Error checking status: {e}")
            
            # Wait before next check
            await asyncio.sleep(2)
    
    print(f"\n⏰ Timeout after {max_wait_minutes} minutes")
    return False

async def test_with_session_id():
    """Test monitoring with a specific session ID"""
    session_id = input("Enter session ID to monitor (or press Enter to skip): ").strip()
    
    if session_id:
        await monitor_session(session_id)
    else:
        print("No session ID provided. Upload a video first to get a session ID.")

if __name__ == "__main__":
    print("Video Processing Monitor")
    print("=" * 50)
    
    try:
        asyncio.run(test_with_session_id())
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n💡 Tips:")
    print("1. Upload a video at http://localhost:8000/recording/")
    print("2. Copy the session ID from the browser console")
    print("3. Run this script to monitor processing")
    print("4. Make sure Celery worker is running: python celery_worker.py")