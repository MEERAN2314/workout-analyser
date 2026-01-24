#!/usr/bin/env python3
"""
Test the hybrid processing system (Celery + Direct fallback)
"""
import asyncio
import aiohttp
import os

async def test_hybrid_upload():
    """Test the hybrid upload system"""
    base_url = "http://localhost:8000"
    
    print("🔄 Testing Hybrid Processing System...")
    print("-" * 50)
    
    # Create test video
    print("📹 Creating test video...")
    os.system("python create_test_video.py")
    
    try:
        async with aiohttp.ClientSession() as session:
            print("📤 Uploading video with hybrid processing...")
            
            with open("test_workout.mp4", "rb") as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='test_workout.mp4', content_type='video/mp4')
                data.add_field('exercise_name', 'push_ups')
                data.add_field('user_id', 'test_user')
                
                async with session.post(f"{base_url}/recording/upload", data=data) as resp:
                    print(f"📊 Response Status: {resp.status}")
                    
                    if resp.status == 200:
                        result = await resp.json()
                        
                        print("🎉 Upload Successful!")
                        print(f"   Session ID: {result.get('session_id')}")
                        print(f"   Status: {result.get('status')}")
                        print(f"   Message: {result.get('message')}")
                        
                        session_id = result.get('session_id')
                        
                        if result.get('status') == 'completed':
                            print("✅ Direct processing completed immediately!")
                            
                            # Get results
                            async with session.get(f"{base_url}/recording/results/{session_id}") as results_resp:
                                if results_resp.status == 200:
                                    analysis = await results_resp.json()
                                    print(f"📊 Results: {analysis.get('total_reps')} reps, {analysis.get('accuracy_score', 0)*100:.1f}% accuracy")
                        
                        elif result.get('status') == 'uploaded':
                            print("🔄 Celery processing started, monitoring...")
                            
                            # Monitor for a short time
                            for i in range(10):
                                await asyncio.sleep(2)
                                
                                async with session.get(f"{base_url}/recording/status/{session_id}") as status_resp:
                                    if status_resp.status == 200:
                                        status_data = await status_resp.json()
                                        print(f"   [{i*2:2d}s] {status_data.get('status')} - {status_data.get('progress')}% - {status_data.get('message')}")
                                        
                                        if status_data.get('status') == 'completed':
                                            print("✅ Celery processing completed!")
                                            break
                                    else:
                                        print(f"   Status check failed: {status_resp.status}")
                    
                    else:
                        error_text = await resp.text()
                        print(f"❌ Upload failed: {error_text}")
    
    finally:
        # Clean up
        if os.path.exists("test_workout.mp4"):
            os.remove("test_workout.mp4")

if __name__ == "__main__":
    print("Hybrid Processing System Test")
    print("=" * 50)
    
    try:
        asyncio.run(test_hybrid_upload())
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Hybrid system automatically chooses:")
    print("   - Celery processing if workers are available")
    print("   - Direct processing if Celery is unavailable")
    print("   - Always provides results!")