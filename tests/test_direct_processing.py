#!/usr/bin/env python3
"""
Test direct video processing (bypasses Celery)
"""
import asyncio
import aiohttp
import os

async def test_direct_processing():
    """Test direct video processing"""
    base_url = "http://localhost:8000"
    
    print("🚀 Testing Direct Video Processing...")
    print("-" * 50)
    
    # Create a test video first
    print("📹 Creating test video...")
    os.system("python create_test_video.py")
    
    if not os.path.exists("test_workout.mp4"):
        print("❌ Test video not found. Creating a simple one...")
        # Create a minimal test file
        with open("test_workout.mp4", "wb") as f:
            # Write a minimal MP4 header
            f.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom')
            f.write(b'\x00' * 1000)
    
    try:
        async with aiohttp.ClientSession() as session:
            print("📤 Uploading video for direct processing...")
            
            with open("test_workout.mp4", "rb") as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='test_workout.mp4', content_type='video/mp4')
                data.add_field('exercise_name', 'push_ups')
                data.add_field('user_id', 'test_user')
                
                print("⏳ Processing... (this may take a minute)")
                
                async with session.post(f"{base_url}/recording/upload-direct", data=data) as resp:
                    print(f"📊 Response Status: {resp.status}")
                    
                    if resp.status == 200:
                        result = await resp.json()
                        
                        print("🎉 Direct Processing Successful!")
                        print(f"   Session ID: {result.get('session_id')}")
                        print(f"   Status: {result.get('status')}")
                        print(f"   Message: {result.get('message')}")
                        print(f"   Duration: {result.get('duration', 0):.1f}s")
                        
                        # Get detailed results
                        session_id = result.get('session_id')
                        if session_id:
                            print("\n📈 Getting detailed analysis results...")
                            
                            async with session.get(f"{base_url}/recording/results/{session_id}") as results_resp:
                                if results_resp.status == 200:
                                    analysis = await results_resp.json()
                                    
                                    print("📊 Analysis Results:")
                                    print(f"   Exercise: {analysis.get('exercise_name')}")
                                    print(f"   Total Reps: {analysis.get('total_reps')}")
                                    print(f"   Correct Reps: {analysis.get('correct_reps')}")
                                    print(f"   Accuracy: {analysis.get('accuracy_score', 0)*100:.1f}%")
                                    print(f"   Calories Burned: {analysis.get('calories_burned', 0):.1f}")
                                    
                                    feedback = analysis.get('form_feedback', [])
                                    if feedback:
                                        print(f"   Form Feedback ({len(feedback)} items):")
                                        for i, fb in enumerate(feedback[:5], 1):
                                            print(f"     {i}. {fb}")
                                    
                                    mistakes = analysis.get('mistakes', [])
                                    if mistakes:
                                        print(f"   Mistakes Identified ({len(mistakes)} items):")
                                        for i, mistake in enumerate(mistakes[:3], 1):
                                            print(f"     {i}. At {mistake.get('timestamp', 0):.1f}s: {mistake.get('description')}")
                                    
                                    timeline = analysis.get('analysis_timeline', [])
                                    if timeline:
                                        print(f"   Timeline Events: {len(timeline)} recorded")
                                
                                else:
                                    print(f"   ⚠️ Could not get detailed results: {results_resp.status}")
                    
                    else:
                        error_text = await resp.text()
                        print(f"❌ Direct processing failed!")
                        print(f"   Error: {error_text}")
    
    finally:
        # Clean up test file
        if os.path.exists("test_workout.mp4"):
            os.remove("test_workout.mp4")

if __name__ == "__main__":
    print("Direct Video Processing Test")
    print("=" * 50)
    
    try:
        asyncio.run(test_direct_processing())
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure the server is running on http://localhost:8000")
    
    print("\n" + "=" * 50)
    print("🎯 Direct processing bypasses Celery for immediate results!")
    print("💡 Use /recording/upload-direct endpoint for instant processing")