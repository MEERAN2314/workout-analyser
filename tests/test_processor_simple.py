#!/usr/bin/env python3
"""
Simple test to verify video processor works
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_processor():
    print("Testing Video Processor...")
    print("=" * 60)
    
    try:
        from app.services.video_processor_fixed import video_processor_fixed
        
        print("✅ Imported video_processor_fixed")
        
        # Test with a dummy URL (will fail but we'll see the logs)
        test_url = "https://example.com/test.mp4"
        
        print(f"\nTesting with URL: {test_url}")
        print("(This will fail but we'll see if the processor runs)\n")
        
        try:
            result = await video_processor_fixed.process_video_from_url(
                test_url,
                "push_ups",
                "test_session_123",
                generate_annotated=False
            )
            print(f"Result: {result}")
        except Exception as e:
            print(f"Expected error: {e}")
            print("\n✅ Processor is being called (error is expected)")
            return True
            
    except Exception as e:
        print(f"❌ Import or setup error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_processor())
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Video processor can be called")
        print("Now restart server and upload a video")
        print("Watch the logs for detailed processing output")
    else:
        print("\n" + "=" * 60)
        print("❌ Video processor has issues")
        print("Check the error above")
