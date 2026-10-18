#!/usr/bin/env bash
# Build script for YouTube Streamer Android APK
# This script prepares and builds the Android application using Buildozer

set -e

echo "========================================"
echo " YouTube Streamer - Android APK Builder"
echo "========================================"
echo ""

# Configuration
APP_DIR="/home/antoniorm/youtube-streamer"
BUILD_DIR="${APP_DIR}/build"
APK_DIR="${BUILD_DIR}/outputs/apk"

echo "📁 Working directory: ${APP_DIR}"
echo ""

# Step 1: Verify dependencies
echo "🔍 Step 1: Verifying dependencies..."
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VER=$(python3 --version 2>&1)
    echo "✅ Python: ${PYTHON_VER}"
else
    echo "❌ Python 3 not found. Please install Python 3.11+."
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo "✅ pip installed"
else
    echo "❌ pip not found. Please install pip."
    exit 1
fi

# Check Java
if command -v java &> /dev/null; then
    JAVA_VER=$(java -version 2>&1 | head -1)
    echo "✅ Java: ${JAVA_VER}"
else
    echo "⚠️  Java not found. Required for Android build."
    echo "   Install with: sudo apt install openjdk-17-jdk"
fi

# Check javac
if command -v javac &> /dev/null; then
    echo "✅ javac installed"
else
    echo "⚠️  javac not found."
fi

# Check git
if command -v git &> /dev/null; then
    echo "✅ git installed"
else
    echo "⚠️  git not found."
fi

# Check SDK tools
if [ -d "$ANDROID_HOME" ] || [ -d "$ANDROID_SDK_ROOT" ]; then
    echo "✅ Android SDK found"
else
    echo "⚠️  Android SDK not found in environment variables."
    echo "   Set ANDROID_HOME or ANDROID_SDK_ROOT"
fi

echo ""

# Step 2: Setup virtual environment
echo "🔧 Step 2: Setting up Python environment..."
echo ""

cd "${APP_DIR}"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo "✅ Virtual environment activated"

# Install/update packages
echo "Installing Python packages..."
pip install --upgrade pip setuptools wheel 2>&1 | tail -3

# Install Kivy and dependencies
echo "Installing Kivy..."
pip install kivy 2>&1 | tail -3

# Install other dependencies
pip install requests yt-dlp pydantic 2>&1 | tail -3

echo "✅ Python environment ready"
echo ""

# Step 3: Verify application structure
echo "📂 Step 3: Verifying application structure..."
echo ""

REQUIRED_FILES=(
    "main.py"
    "android_app.py"
    "models.py"
    "ytdlp_layer.py"
    "player.py"
    "requirements.txt"
    "buildozer.spec"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "${APP_DIR}/${file}" ]; then
        echo "✅ ${file}"
    else
        echo "❌ Missing: ${file}"
        exit 1
    fi
done

echo ""

# Step 4: Python syntax check
echo "🔍 Step 4: Checking Python syntax..."
echo ""

python3 -m py_compile main.py 2>&1 && echo "✅ main.py syntax OK"
python3 -m py_compile android_app.py 2>&1 && echo "✅ android_app.py syntax OK"
python3 -m py_compile models.py 2>&1 && echo "✅ models.py syntax OK"
python3 -m py_compile ytdlp_layer.py 2>&1 && echo "✅ ytdlp_layer.py syntax OK"
python3 -m py_compile player.py 2>&1 && echo "✅ player.py syntax OK"

echo ""

# Step 5: Test imports
echo "🧪 Step 5: Testing Python imports..."
echo ""

python3 -c "
import sys
sys.path.insert(0, '.')
from models import VideoInfo, StreamInfo, PlaybackQueue
from ytdlp_layer import YouTubeDLWrapper
print('✅ All core modules import successfully')
" 2>&1

echo ""

# Step 6: Prepare build directory
echo "📦 Step 6: Preparing build directory..."
echo ""

mkdir -p "${BUILD_DIR}"
mkdir -p "${APK_DIR}"

echo "✅ Build directory created: ${BUILD_DIR}"
echo ""

# Step 7: Build APK with Buildozer
echo "🚀 Step 7: Building APK with Buildozer..."
echo ""
echo "⏱️  This step may take 10-30 minutes depending on your system..."
echo ""

if command -v buildozer &> /dev/null; then
    echo "✅ Buildozer installed"
    cd "${APP_DIR}"
    
    buildozer android debug 2>&1 | tee "${BUILD_DIR}/build.log"
    
    echo ""
    echo "Build log saved to: ${BUILD_DIR}/build.log"
else
    echo "⚠️  Buildozer not installed."
    echo "Installing Buildozer..."
    pip install buildozer cython 2>&1 | tail -3
    echo ""
    echo "Buildozer installed. Starting APK build..."
    
    cd "${APP_DIR}"
    
    buildozer android debug 2>&1 | tee "${BUILD_DIR}/build.log"
    
    echo ""
    echo "Build log saved to: ${BUILD_DIR}/build.log"
fi

echo ""

# Step 8: Verify APK output
echo "📦 Step 8: Verifying APK output..."
echo ""

APK_FILES=$(find "${APK_DIR}" -name "*.apk" 2>/dev/null)

if [ -n "${APK_FILES}" ]; then
    echo "✅ APK files found:"
    echo "${APK_FILES}" | while read apk; do
        SIZE=$(du -h "${apk}" 2>/dev/null | cut -f1)
        echo "   📱 ${apk} (${SIZE})"
    done
else
    # Try to find APK in buildozer default location
    FINAL_APK=$(find "${APP_DIR}" -name "*-debug.apk" 2>/dev/null | head -1)
    if [ -n "${FINAL_APK}" ]; then
        echo "✅ APK found at default location:"
        SIZE=$(du -h "${FINAL_APK}" 2>/dev/null | cut -f1)
        echo "   📱 ${FINAL_APK} (${SIZE})"
    else
        echo "⚠️  APK file not found."
        echo "   Check the build log for errors: ${BUILD_DIR}/build.log"
        echo "   Common issues:"
        echo "   - Android SDK/NDK not configured"
        echo "   - Java not installed"
        echo "   - Insufficient disk space"
    fi
fi

echo ""

# Step 9: Summary
echo "========================================"
echo " Build Summary"
echo "========================================"
echo ""
echo "Project: YouTube Streamer"
echo "Platform: Android"
echo "Output: ${APK_DIR}"
echo ""

if [ -n "${APK_FILES}" ]; then
    echo "✅ Build completed successfully!"
    echo ""
    echo "📱 To install the APK on your device:"
    echo "   1. Connect your Android device via USB"
    echo "   2. Enable USB debugging on your device"
    echo "   3. Run: adb install <path-to-apk>"
    echo ""
    echo "📦 To upload to Google Play Store (AAB):"
    echo "   Run: buildozer android release"
else
    echo "⚠️  Build completed with warnings."
    echo "   Check the build log for details."
fi

echo ""
echo "📄 Build log: ${BUILD_DIR}/build.log"
echo ""
echo "========================================"
