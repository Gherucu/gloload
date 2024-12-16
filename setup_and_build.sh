#!/usr/bin/env bash

# Variables (Adjust these as needed)
APP_NAME="ayglø_beat_downloader"
MAIN_FILE="./download_youtube_to_wav_APP.py"
ICON_FILE="./icon.png"
FONT_FILE="./resources/OldLondon.ttf"
VENV_DIR="venv"
DIST_DIR="dist"
BUILD_DIR="build"
ICONSET_DIR="./MyIcon.iconset"
ICON_ICNS="./icon.icns"
PYTHON_PATH="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
REQUIREMENTS_FILE="requirements.txt"

# Step 1: Cleanup old artifacts
echo "Cleaning up old build artifacts..."
rm -rf "${DIST_DIR}" "${BUILD_DIR}" "${APP_NAME}.spec" "${ICON_ICNS}" "${ICONSET_DIR}" "${VENV_DIR}"
echo "Cleanup done."

# Step 2: Create new venv with python.org Python
echo "Creating new virtual environment with Python from python.org..."
${PYTHON_PATH} -m venv ${VENV_DIR}
if [ $? -ne 0 ]; then
    echo "Failed to create virtual environment. Check your PYTHON_PATH."
    exit 1
fi

# Activate venv
source ${VENV_DIR}/bin/activate

# Step 3: Check tkinter availability
echo "Checking tkinter availability..."
python -c "import tkinter; print('tkinter is available')"
if [ $? -ne 0 ]; then
    echo "tkinter is not available in this Python environment."
    echo "Please install a Python that has tkinter support, e.g. from python.org."
    deactivate
    exit 1
fi

# Step 4: Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
if [ -f "${REQUIREMENTS_FILE}" ]; then
    pip install -r "${REQUIREMENTS_FILE}"
fi
pip install yt-dlp pyinstaller
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies."
    deactivate
    exit 1
fi

# Step 5: Create icon if needed
if [ ! -f "${ICON_ICNS}" ]; then
    echo "Creating .icns icon from ${ICON_FILE}..."
    mkdir -p "${ICONSET_DIR}"
    magick ${ICON_FILE} -resize 16x16 ${ICONSET_DIR}/icon_16x16.png
    magick ${ICON_FILE} -resize 32x32 ${ICONSET_DIR}/icon_32x32.png
    magick ${ICON_FILE} -resize 128x128 ${ICONSET_DIR}/icon_128x128.png
    magick ${ICON_FILE} -resize 256x256 ${ICONSET_DIR}/icon_256x256.png
    magick ${ICON_FILE} -resize 512x512 ${ICONSET_DIR}/icon_512x512.png
    iconutil -c icns "${ICONSET_DIR}" -o "${ICON_ICNS}"
fi

# Step 6: Build the app with PyInstaller
echo "Building the app..."
pyinstaller --onefile --windowed --name "${APP_NAME}" \
    --icon="${ICON_ICNS}" \
    --hidden-import=yt_dlp \
    --add-binary "$(which yt-dlp):yt-dlp" \
    --add-data "${FONT_FILE}:." \
    ${MAIN_FILE}

if [ $? -ne 0 ]; then
    echo "Build failed. Check the logs above for errors."
    deactivate
    exit 1
fi

echo "Build completed successfully!"
deactivate

#########################################
# How to run this script:
#
# 1. Make it executable:
#    chmod +x setup_and_build.sh
#
# 2. Run it from your project directory:
#    ./setup_and_build.sh
#
# This script will:
# - Remove old artifacts and venv
# - Create a new venv using python.org Python
# - Check tkinter availability
# - Install all dependencies, PyInstaller, yt-dlp
# - Build your app into the dist/ directory
#
# After completion, check dist/ayglø_beat_downloader (or dist/ayglø_beat_downloader.app on macOS)
# to run your application.
#
# If you still encounter issues, verify your PYTHON_PATH, dependencies, and that tkinter is indeed available.
#########################################

