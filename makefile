# Variables
APP_NAME = ayglø_beat_downloader
MAIN_FILE = ./download_youtube_to_wav_APP.py
ICON_FILE = ./icon.png
ICONSET_DIR = ./MyIcon.iconset
ICON_ICNS = ./icon.icns
DIST_DIR = dist
BUILD_DIR = build
FONT_FILE = ./resources/OldLondon.ttf
VENV_DIR = venv
PYTHON_PATH = /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

.PHONY: build unbuild

build: $(ICON_ICNS)
	@echo "Removing old venv if any..."
	rm -rf $(VENV_DIR)
	@echo "Creating new venv with python from python.org..."
	$(PYTHON_PATH) -m venv $(VENV_DIR)
	@echo "Installing dependencies in venv..."
	# Using a single shell invocation for simplicity:
	. $(VENV_DIR)/bin/activate && \
	$(PIP) install --upgrade pip && \
	$(PIP) install -r requirements.txt && \
	$(PIP) install yt-dlp pyinstaller && \
	$(PYTHON) -c "import tkinter; print('tkinter is available')"
	@echo "Building the app with PyInstaller..."
	. $(VENV_DIR)/bin/activate && \
	$(PYTHON) -m PyInstaller --onefile --windowed --name "$(APP_NAME)" \
		--icon="$(ICON_ICNS)" \
		--hidden-import=yt_dlp \
		--add-binary "$$(which yt-dlp):yt-dlp" \
		--add-data "$(FONT_FILE):." \
		$(MAIN_FILE)

$(ICON_ICNS): $(ICONSET_DIR)
	@echo "Creating $(ICON_ICNS) from $(ICONSET_DIR)..."
	iconutil -c icns "$(ICONSET_DIR)" -o "$(ICON_ICNS)"

$(ICONSET_DIR): $(ICON_FILE)
	@echo "Creating $(ICONSET_DIR) and generating PNG files..."
	mkdir -p $(ICONSET_DIR)
	magick $(ICON_FILE) -resize 16x16 $(ICONSET_DIR)/icon_16x16.png
	magick $(ICON_FILE) -resize 32x32 $(ICONSET_DIR)/icon_32x32.png
	magick $(ICON_FILE) -resize 128x128 $(ICONSET_DIR)/icon_128x128.png
	magick $(ICON_FILE) -resize 256x256 $(ICONSET_DIR)/icon_256x256.png
	magick $(ICON_FILE) -resize 512x512 $(ICONSET_DIR)/icon_512x512.png

unbuild:
	@echo "Removing all build artifacts and venv..."
	rm -rf $(DIST_DIR) $(BUILD_DIR) $(APP_NAME).spec $(ICON_ICNS) $(ICONSET_DIR) $(VENV_DIR)
