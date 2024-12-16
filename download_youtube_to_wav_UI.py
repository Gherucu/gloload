import sys
import os
import re
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QProgressBar, QFileDialog, QHBoxLayout
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, Qt
from PIL import Image, ImageDraw, ImageFont
import subprocess
import threading
import librosa
import numpy as np


class ThumbnailFetcher(QObject):
    # Signals to update the UI
    update_thumbnail = pyqtSignal(str)
    log_message = pyqtSignal(str)

    def fetch_thumbnail(self, youtube_url):
        try:
            self.log_message.emit("Fetching...")
            command = [
                "yt-dlp",
                "--skip-download",
                "--get-thumbnail",
                youtube_url,
            ]
            thumbnail_url = subprocess.check_output(command, text=True).strip()

            # Verify the thumbnail URL
            response = requests.get(thumbnail_url)
            if response.status_code == 200:
                self.update_thumbnail.emit(thumbnail_url)
            else:
                self.log_message.emit("Failed to fetch thumbnail.")
                self.update_thumbnail.emit("")
        except Exception as e:
            self.log_message.emit(f"Error fetching thumbnail: {e}")
            self.update_thumbnail.emit("")


class YouTubeDownloader(QWidget):
    log_signal = pyqtSignal(str)
    update_bpm_signal = pyqtSignal(str)
    update_key_signal = pyqtSignal(str)
    update_progress_signal = pyqtSignal(int)  # For updating progress bar on main thread
    append_log_signal = pyqtSignal(str)       # For appending text to status_output on main thread

    def __init__(self):
        super().__init__()
        self.download_location = os.path.expanduser("~/Downloads")  # Default to Downloads folder
        self.thumbnail_path = None

        self.thumbnail_fetcher = ThumbnailFetcher()
        self.thumbnail_fetcher.update_thumbnail.connect(self.display_thumbnail)
        self.thumbnail_fetcher.log_message.connect(self.append_log_message)

        self.log_signal.connect(self.append_log_message)
        self.update_bpm_signal.connect(self.update_bpm_label)
        self.update_key_signal.connect(self.update_key_label)
        self.update_progress_signal.connect(self.set_progress_value)
        self.append_log_signal.connect(self.append_log_message)

        self.typing_timer = QTimer()
        self.typing_timer.setSingleShot(True)
        self.typing_timer.timeout.connect(self.start_thumbnail_fetch)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('YouTube to WAV Downloader')

        layout = QVBoxLayout()

        self.url_label = QLabel('YouTube URL:')
        layout.addWidget(self.url_label)

        self.url_input = QLineEdit(self)
        self.url_input.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.url_input)

        output_layout = QHBoxLayout()
        self.output_label = QLabel(f'Output Folder: {self.download_location}')
        output_layout.addWidget(self.output_label)

        self.choose_folder_button = QPushButton('Choose Folder')
        self.choose_folder_button.clicked.connect(self.choose_output_folder)
        output_layout.addWidget(self.choose_folder_button)

        layout.addLayout(output_layout)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setPixmap(QPixmap())
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setFixedSize(320, 180)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.thumbnail_label, alignment=Qt.AlignCenter)

        self.display_placeholder_thumbnail()

        self.download_button = QPushButton('Download', self)
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)
        # Disable until thumbnail fetch completes or fails
        self.download_button.setEnabled(False)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # BPM and Key labels
        self.bpm_label = QLabel("BPM: Not detected")
        layout.addWidget(self.bpm_label)

        self.key_label = QLabel("Key: Not detected")
        layout.addWidget(self.key_label)

        self.status_output = QTextEdit(self)
        self.status_output.setReadOnly(True)
        layout.addWidget(self.status_output)

        self.setLayout(layout)

    def display_placeholder_thumbnail(self):
        placeholder_path = os.path.join(self.download_location, "placeholder.jpg")
        self.generate_placeholder_image(placeholder_path)
        pixmap = QPixmap(placeholder_path)
        self.thumbnail_label.setPixmap(pixmap)

    def generate_placeholder_image(self, path):
        img = Image.new('RGB', (320, 180), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/Library/Fonts/OldLondon.ttf", 24)
        except IOError:
            font = ImageFont.load_default()

        text = "ayglø beat downloader"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_x = (img.width - (text_bbox[2] - text_bbox[0])) // 2
        text_y = (img.height - (text_bbox[3] - text_bbox[1])) // 2
        draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))
        img.save(path)

    def choose_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Download Folder', self.download_location)
        if folder:
            self.download_location = folder
            self.output_label.setText(f'Output Folder: {self.download_location}')

    def on_text_changed(self):
        self.typing_timer.start(1000)

    def start_thumbnail_fetch(self):
        youtube_url = self.url_input.text().strip()
        if "youtube.com" in youtube_url or "youtu.be" in youtube_url:
            # Disable download button during fetch
            self.download_button.setEnabled(False)
            thread = threading.Thread(target=self.thumbnail_fetcher.fetch_thumbnail, args=(youtube_url,))
            thread.start()
        else:
            self.download_button.setEnabled(True)

    def display_thumbnail(self, thumbnail_url):
        # Re-enable download button after fetch completes
        self.download_button.setEnabled(True)

        if thumbnail_url:
            response = requests.get(thumbnail_url)
            if response.status_code == 200:
                self.thumbnail_path = os.path.join(self.download_location, "thumbnail.jpg")
                with open(self.thumbnail_path, "wb") as file:
                    file.write(response.content)
                pixmap = QPixmap(self.thumbnail_path)
                self.thumbnail_label.setPixmap(pixmap)
            else:
                self.display_placeholder_thumbnail()
        else:
            self.display_placeholder_thumbnail()

    def start_download(self):
        youtube_url = self.url_input.text().strip()
        if not youtube_url:
            self.append_log_message("Please enter a valid YouTube URL.")
            return

        self.append_log_message("\n------------\n")
        self.progress_bar.setValue(0)
        self.status_output.clear()

        self.download_button.setEnabled(False)
        self.append_log_message("Starting download...")

        # Run download in background
        thread = threading.Thread(target=self.download_video_as_wav, args=(youtube_url,))
        thread.start()

    def download_video_as_wav(self, youtube_url):
        try:
            output_template = os.path.join(self.download_location, "%(title)s.%(ext)s")
            command = [
                "yt-dlp",
                "--newline",
                "-f", "bestaudio",
                "--extract-audio",
                "--audio-format", "wav",
                "-o", output_template,
                youtube_url,
            ]

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            downloaded_file = None

            percent_regex = re.compile(r'(\d+(?:\.\d+)?)%')
            last_percent = -1

            for line in process.stdout:
                # Emit log signal so it's appended on the main thread
                self.log_signal.emit(line.strip())

                if '[download]' in line:
                    match = percent_regex.search(line)
                    if match:
                        percent_str = match.group(1)
                        try:
                            current_percent = int(float(percent_str))
                            if current_percent != last_percent:
                                # Update the progress bar via a signal to the main thread
                                self.update_progress_signal.emit(current_percent)
                                last_percent = current_percent
                        except ValueError:
                            pass

                if "Destination:" in line:
                    downloaded_file = line.split("Destination:")[-1].strip()

            process.wait()

            if process.returncode == 0:
                self.log_signal.emit("Download completed successfully!")
                if downloaded_file:
                    self.analyze_audio(downloaded_file)
                else:
                    self.log_signal.emit("Error: Could not determine the downloaded file path.")
            else:
                self.log_signal.emit(f"yt-dlp failed with code {process.returncode}")
        except Exception as e:
            self.log_signal.emit(f"Error: {e}")
        finally:
            # Re-enable download button after process finishes
            self.download_button.setEnabled(True)

    def analyze_audio(self, wav_file):
        try:
            self.log_signal.emit("Analyzing audio...")
            y, sr = librosa.load(wav_file, sr=None)

            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            if isinstance(tempo, np.ndarray):
                tempo = tempo[0]
            bpm_val = int(tempo)
            self.update_bpm_signal.emit(f"BPM: {bpm_val}")

            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            key_val = self.detect_key(chroma)
            self.update_key_signal.emit(f"Key: {key_val}")

            # After analysis is done, print values and say Complete
            self.log_signal.emit(f"BPM: {bpm_val}, Key: {key_val}. \nComplete")
        except Exception as e:
            self.log_signal.emit(f"Error analyzing audio: {e}")

    def detect_key(self, chroma):
        key_profiles = [
            'C Major', 'C# Major', 'D Major', 'D# Major', 'E Major', 'F Major',
            'F# Major', 'G Major', 'G# Major', 'A Major', 'A# Major', 'B Major',
            'C Minor', 'C# Minor', 'D Minor', 'D# Minor', 'E Minor', 'F Minor',
            'F# Minor', 'G Minor', 'G# Minor', 'A Minor', 'A# Minor', 'B Minor'
        ]
        chroma_vector = chroma.mean(axis=1)
        return key_profiles[chroma_vector.argmax()]

    def set_progress_value(self, value):
        self.progress_bar.setValue(value)

    def update_bpm_label(self, bpm_text):
        self.bpm_label.setText(bpm_text)

    def update_key_label(self, key_text):
        self.key_label.setText(key_text)

    def append_log_message(self, message):
        self.status_output.append(message)
        self.status_output.ensureCursorVisible()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    downloader = YouTubeDownloader()
    downloader.show()
    sys.exit(app.exec_())
