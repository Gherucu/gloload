#!/usr/bin/env bash

set -e  # Exit on error

# 1. Clean up old environment and build artifacts
rm -rf venv build dist *.spec

# 2. Create a new virtual environment using python3 (python.org version)
python3 -m venv venv
source venv/bin/activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install all dependencies from requirements.txt
pip install -r requirements.txt

# 5. Run py2app to build the app
python setup.py py2app

echo "Build complete. The .app is in the dist/ directory."

