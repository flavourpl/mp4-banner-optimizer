import sys
import os

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Set up paths
os.environ['FFMPEG_PATH'] = os.path.expanduser('~/bin/ffmpeg')
os.environ['FFPROBE_PATH'] = os.path.expanduser('~/bin/ffprobe')

# Import Flask app
from web_app_prod import app as application

# Passenger will use 'application' as the entry point
