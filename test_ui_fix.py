#!/usr/bin/env python3
"""
Test script to verify the UI fix is working
"""
import asyncio
import aiohttp
import re

async def test_ui_fix():
    """Test that the UI sections are properly hidden"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing UI Fix...")
    
    async with aiohttp.ClientSession() as session:
        # Get the recording analysis page
        async with session.get(f"{base_url}/recording/") as resp:
            if resp.status == 200:
                content = await resp.text()
                
                # Check for cache buster
                if 'Fresh Load - v3.2' in content:
                    print("   ✅ Cache buster found - fresh version loaded")
                elif 'Fresh Load - v3.1' in content:
                    print("   ⚠️  Cache buster found - slightly older version")
                else:
                    print("   ❌ Cache buster missing - old version cached")
                
                # Check for proper CSS hiding
                if 'display: none !important' in content:
                    print("   ✅ CSS hiding rules found")
                else:
                    print("   ❌ CSS hiding rules missing")
                
                # Check for enhanced JavaScript
                if 'Recording Analysis v3.2' in content:
                    print("   ✅ Enhanced JavaScript v3.2 found")
                elif 'Recording Analysis v3.1' in content:
                    print("   ✅ Enhanced JavaScript v3.1 found")
                else:
                    print("   ❌ Enhanced JavaScript missing")
                
                # Check for proper section structure
                upload_section = 'id="upload-section" style="display: block;"' in content
                analysis_hidden = 'id="analysis-section" style="display: none !important;"' in content
                results_hidden = 'id="results-section" style="display: none !important;"' in content
                
                print(f"   Upload Section Visible: {'✅' if upload_section else '❌'}")
                print(f"   Analysis Section Hidden: {'✅' if analysis_hidden else '❌'}")
                print(f"   Results Section Hidden: {'✅' if results_hidden else '❌'}")
                
                if upload_section and analysis_hidden and results_hidden:
                    print("\n🎉 UI FIX IS WORKING CORRECTLY!")
                    print("   The page should now show only the upload section.")
                    
                    # Additional checks for completeness
                    if 'Fresh Load - v3.2' in content and 'Recording Analysis v3.2' in content:
                        print("   🚀 COMPLETE FIX ACTIVE - All enhancements loaded!")
                    else:
                        print("   ⚠️  Core fix working, but do a hard refresh for full enhancements")
                else:
                    print("\n⚠️  UI fix may not be complete.")
                    print("   Try a hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)")
                
            else:
                print(f"   ❌ Failed to load page: {resp.status}")

if __name__ == "__main__":
    print("Testing UI fix implementation...")
    print("=" * 50)
    
    try:
        asyncio.run(test_ui_fix())
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure the server is running on http://localhost:8000")
    
    print("\n" + "=" * 50)
    print("🔧 If sections are still showing:")
    print("1. Hard refresh browser: Ctrl+F5 or Cmd+Shift+R")
    print("2. Clear browser cache completely")
    print("3. Try incognito/private browsing mode")
    print("4. Check browser console for errors (F12)")
    print("5. Look for green 'Fresh Load - v3.1' indicator")