from setuptools import setup

APP = ['download_youtube_to_wav_UI.py']
DATA_FILES = ['icon.icns', 'resources/OldLondon.ttf']
OPTIONS = {
    'iconfile': 'icon.icns',
    'packages': ['yt_dlp', 'requests', 'Pillow', 'librosa'],
    'includes': ['PIL', 'Pillow', 'PyQt5', 'requests', 'yt_dlp'],
}


setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

