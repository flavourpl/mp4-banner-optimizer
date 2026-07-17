# MP4 Banner Optimizer

🎬 **Intelligent MP4 video optimization for web banners and advertising**

Optimize MP4 videos to strict file size limits while maintaining quality. Perfect for advertising platforms with file size restrictions.

## ✨ Features

- **Smart Size Targeting**: Automatically optimize to exact file sizes (100KB, 400KB, custom)
- **Quality Preservation**: Advanced 2-pass encoding with H.264 codec
- **Resolution Ladder**: Intelligent step-down optimization (original → 85% → 70% → 50%)
- **Web Interface**: Easy-to-use web interface for batch processing
- **Production Ready**: Docker support, VPS deployment, shared hosting compatible
- **FFmpeg Agnostic**: Works with system FFmpeg or static builds
- **Background Processing**: Async job processing with progress tracking

## 🚀 Quick Start

### Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the web interface
python deployment/web_app_prod.py

# Access at http://localhost:8080
```

### Docker Deployment

```bash
cd deployment
docker-compose up -d

# Access at http://localhost:8080
```

### Progreso.pl/Shared Hosting

```bash
# Upload files to hosting
ssh your-host.com
cd path/to/deployment
chmod +x start_progreso.sh
./start_progreso.sh
```

See [deployment/PROGRESO_DEPLOYMENT.md](deployment/PROGRESO_DEPLOYMENT.md) for details.

## 📖 Usage

### Command Line

```bash
# Basic optimization to 400KB
python mp4_optimizer.py input.mp4 -t 400

# With custom settings
python mp4_optimizer.py input.mp4 -t 100 --keep-audio --fit-mode pad

# Using presets
python mp4_optimizer.py input.mp4 --preset tiny
```

### Web Interface

1. Open `http://localhost:8080`
2. Upload MP4 file
3. Select target size/preset
4. Choose options (keep audio, fit mode)
5. Download optimized file

### Python API

```python
from mp4_optimizer.ladder import OptimizationLadder
from mp4_optimizer.encoder import FFmpegEncoder

encoder = FFmpegEncoder()
ladder = OptimizationLadder(encoder)

result = ladder.optimize(
    input_path="input.mp4",
    output_path="output.mp4",
    max_kb=400,
    keep_audio=False,
    fit_mode="crop"
)

print(f"Final size: {result['final_size_kb']} KB")
print(f"Status: {result['status']}")
```

## 🎯 Presets

- **tiny**: 50KB (Ultra-compact banners)
- **small**: 100KB (Small ads)
- **med**: 400KB (Medium banners - **default**)
- **large**: 1MB (Large formats)
- **max**: 2MB (Maximum quality)

## ⚙️ Configuration

### FFmpeg Configuration

The tool automatically detects FFmpeg in this order:
1. Static build in `~/bin/ffmpeg` (for shared hosting)
2. System FFmpeg from PATH
3. Environment variables `FFMPEG_PATH`/`FFPROBE_PATH`

### Resolution Ladder

Default optimization steps: `100% → 85% → 70% → 50%`

Customize via `mp4_optimizer/config.py`:
```python
RESOLUTION_LADDER = [
    "1.0x",    # 100% - try original first
    "0.85x",   # 85% - first reduction
    "0.7x",    # 70% - medium reduction
    "0.5x"     # 50% - aggressive reduction
]
```

## 📁 Project Structure

```
mp4-banner-optimizer/
├── mp4_optimizer/           # Core optimization engine
│   ├── encoder.py           # FFmpeg operations
│   ├── probe.py             # Video analysis
│   ├── ladder.py            # Optimization logic
│   ├── report.py            # Reporting & metrics
│   ├── config.py            # Configuration & presets
│   └── ffmpeg_config.py     # FFmpeg detection
├── deployment/               # Deployment scripts
│   ├── web_app_prod.py      # Production web server
│   ├── deploy_vps.sh        # VPS deployment
│   ├── deploy_progreso.sh   # Progreso.pl deployment
│   ├── start_progreso.sh    # Quick start script
│   ├── docker-compose.yml   # Docker setup
│   └── PROGRESO_DEPLOYMENT.md
├── templates/                # Web interface templates
│   └── index.html
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🛠️ Requirements

- Python 3.6+
- FFmpeg (with libx264 codec)
- Flask (for web interface)
- Werkzeug

### Installing FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Static Build (Shared Hosting):**
```bash
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xf ffmpeg-release-amd64-static.tar.xz
mv ffmpeg-*/ffmpeg ~/bin/ffmpeg
chmod +x ~/bin/ffmpeg
```

## 🌐 Web Interface

### Features
- Drag-and-drop file upload
- Real-time progress tracking
- Batch processing support
- JSON report generation
- Automatic file cleanup

### Endpoints
- `GET /` - Web interface
- `POST /api/upload` - Upload video for optimization
- `GET /api/status/<job_id>` - Check job status
- `GET /api/download/<job_id>` - Download optimized file
- `GET /api/report/<job_id>` - Download JSON report
- `GET /health` - Health check
- `GET /stats` - Server statistics

## 📊 Optimization Reports

Each optimization generates a detailed JSON report:

```json
{
  "source_info": {
    "size_kb": 1200,
    "resolution": "1920x1080",
    "duration_s": 15.0,
    "fps": 30.0
  },
  "target_max_kb": 400,
  "result": {
    "final_size_kb": 398,
    "final_resolution": "960x540",
    "iterations": [...],
    "status": "success"
  }
}
```

## 🔧 Advanced Options

### Fit Modes
- **crop**: Center crop to exact dimensions (default)
- **pad**: Letterbox/pillarbox to fit dimensions
- **stretch**: Stretch to exact dimensions

### Audio Options
- `--keep-audio`: Preserve audio track (adds ~48KB)
- `--audio-bitrate`: Custom audio bitrate (default: 48kbps)

### Performance Tuning
- `--preset fast`: Faster encoding (lower quality)
- `--preset slow`: Slower encoding (higher quality)
- Custom resolution ladder for specific needs

## 🐳 Docker Deployment

```bash
# Build and run
docker-compose up -d

# Scale for high traffic
docker-compose up -d --scale web=3

# View logs
docker-compose logs -f
```

## 🚢 Production Deployment

### VPS Deployment
```bash
cd deployment
./deploy_vps.sh your-server-ip
```

### Shared Hosting (Progreso.pl)
```bash
cd deployment
./deploy_progreso.sh
```

### Systemd Service
```bash
sudo systemctl start mp4-optimizer
sudo systemctl enable mp4-optimizer
```

## 🧪 Testing

```bash
# Test basic functionality
python mp4_optimizer.py test_video.mp4 -t 100

# Test web interface
python deployment/verify_deployment.py

# Test FFmpeg detection
python -c "from mp4_optimizer.ffmpeg_config import get_ffmpeg_paths; print(get_ffmpeg_paths())"
```

## 📈 Performance

- **Processing Speed**: ~1-3 seconds per MB of source video
- **Memory Usage**: ~50-200MB per encoding job
- **CPU Usage**: 1-2 cores during active encoding
- **File Cleanup**: Automatic cleanup after 1 hour

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📝 License

MIT License - feel free to use in commercial projects

## 🆘 Support

For issues and questions:
- Check [deployment/PROGRESO_DEPLOYMENT.md](deployment/PROGRESO_DEPLOYMENT.md)
- Run `deployment/verify_deployment.py`
- Check FFmpeg: `ffmpeg -version`
- Check Python: `python3 --version`

## 🎯 Use Cases

- **Advertising Agencies**: Optimize client videos for ad platforms
- **Web Developers**: Reduce video file sizes for web
- **Marketing Teams**: Batch process campaign videos
- **E-commerce**: Product video optimization
- **Social Media**: Platform-specific video optimization

---

**Made with ❤️ for the advertising community**

Optimize your banners, reduce your load times, increase your conversions! 🚀