import sys
import os
import re
import subprocess
import threading
from PIL import Image, ImageDraw, ImageFont

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QProgressBar, QFileDialog, QHBoxLayout
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSignal


class YouTubeDownloader(QWidget):
    append_log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.download_location = os.path.expanduser("~/Downloads")
        self.is_playlist = False

        self.typing_timer = QTimer()
        self.typing_timer.setSingleShot(True)
        self.typing_timer.timeout.connect(self.check_if_playlist)

        self.initUI()

        self.append_log_signal.connect(self.append_log_message)

    def initUI(self):
        self.setWindowTitle('ayglø playlist downloader')

        layout = QVBoxLayout()

        self.url_label = QLabel('YouTube Playlist URL:')
        layout.addWidget(self.url_label)

        self.url_input = QLineEdit(self)
        self.url_input.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.url_input)

        output_layout = QHBoxLayout()
        self.output_label = QLabel(f'Output Folder: {self.download_location}')
        output_layout.addWidget(self.output_label)

        choose_folder_btn = QPushButton('Choose Folder')
        choose_folder_btn.clicked.connect(self.choose_output_folder)
        output_layout.addWidget(choose_folder_btn)

        layout.addLayout(output_layout)

        # Display placeholder
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setFixedSize(320, 180)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.thumbnail_label, alignment=Qt.AlignCenter)

        self.display_placeholder_thumbnail()

        self.download_button = QPushButton('Download', self)
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setEnabled(False)
        layout.addWidget(self.download_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_output = QTextEdit(self)
        self.status_output.setReadOnly(True)
        layout.addWidget(self.status_output)

        self.setLayout(layout)

    def choose_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Download Folder', self.download_location)
        if folder:
            self.download_location = folder
            self.output_label.setText(f'Output Folder: {self.download_location}')

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

        text = "ayglø playlist downloader"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_x = (img.width - (text_bbox[2] - text_bbox[0])) // 2
        text_y = (img.height - (text_bbox[3] - text_bbox[1])) // 2
        draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))
        img.save(path)

    def on_text_changed(self):
        self.typing_timer.start(1000)

    def check_if_playlist(self):
        youtube_url = self.url_input.text().strip()
        if "&list=" in youtube_url:
            self.is_playlist = True
            self.download_button.setEnabled(True)
            self.append_log_message("Detected a playlist URL.")
        else:
            self.is_playlist = False
            self.download_button.setEnabled(False)
            self.append_log_message("Not a playlist URL. Please provide a valid playlist URL.")

    def start_download(self):
        youtube_url = self.url_input.text().strip()
        if not youtube_url or not self.is_playlist:
            self.append_log_message("Not a valid playlist URL.")
            return

        self.append_log_message("\n------------\nStarting playlist download...")
        self.download_button.setEnabled(False)

        thread = threading.Thread(target=self.download_playlist, args=(youtube_url,))
        thread.start()

    def download_playlist(self, youtube_url):
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
            self.append_log_signal.emit("Executing command: " + " ".join(command))
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            for line in process.stdout:
                stripped_line = line.strip()
                self.append_log_signal.emit("yt-dlp: " + stripped_line)

            process.wait()

            if process.returncode == 0:
                self.append_log_signal.emit("All downloads completed successfully!")
            else:
                self.append_log_signal.emit(f"yt-dlp failed with code {process.returncode}")
        except Exception as e:
            self.append_log_signal.emit(f"Error during playlist download: {e}")
        finally:
            self.download_button.setEnabled(True)

    def append_log_message(self, message):
        self.status_output.append(message)
        self.status_output.ensureCursorVisible()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    downloader = YouTubeDownloader()
    downloader.show()
    sys.exit(app.exec_())
