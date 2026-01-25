#!/bin/bash

echo "=========================================="
echo "Installing Video Processing Fixes"
echo "=========================================="
echo ""

# Check if FFmpeg is installed
echo "1. Checking FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "   ✅ FFmpeg is already installed"
    ffmpeg -version | head -n 1
else
    echo "   ❌ FFmpeg not found"
    echo "   Installing FFmpeg..."
    
    # Detect OS and install
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
        sudo apt-get install -y ffmpeg
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ffmpeg
    else
        echo "   ⚠️  Please install FFmpeg manually"
        echo "   Visit: https://ffmpeg.org/download.html"
        exit 1
    fi
    
    # Verify installation
    if command -v ffmpeg &> /dev/null; then
        echo "   ✅ FFmpeg installed successfully"
    else
        echo "   ❌ FFmpeg installation failed"
        exit 1
    fi
fi

echo ""
echo "2. Installing Python dependencies..."
pip install ffmpeg-python aiofiles aiohttp

echo ""
echo "3. Verifying installations..."

# Test FFmpeg
if ffmpeg -version &> /dev/null; then
    echo "   ✅ FFmpeg: Working"
else
    echo "   ❌ FFmpeg: Not working"
fi

# Test Python packages
python -c "import ffmpeg; print('   ✅ ffmpeg-python: Installed')" 2>/dev/null || echo "   ❌ ffmpeg-python: Failed"
python -c "import aiofiles; print('   ✅ aiofiles: Installed')" 2>/dev/null || echo "   ❌ aiofiles: Failed"
python -c "import aiohttp; print('   ✅ aiohttp: Installed')" 2>/dev/null || echo "   ❌ aiohttp: Failed"
python -c "import mediapipe; print('   ✅ mediapipe: Installed')" 2>/dev/null || echo "   ❌ mediapipe: Failed"
python -c "import cv2; print('   ✅ opencv: Installed')" 2>/dev/null || echo "   ❌ opencv: Failed"

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Restart your server: python run.py"
echo "2. Upload a new video (don't reuse old uploads)"
echo "3. Check logs for progress"
echo "4. Verify results show actual rep counts"
echo ""
echo "For detailed instructions, see: COMPLETE_FIX_GUIDE.md"
echo ""
