# MP4 Banner Optimizer - Agent Deployment Guide

## Emergency Recovery After Server Reset

### Prerequisites
- SSH access: `ars_mp4_video_opt@flavour.civ.pl`
- FTP access for file uploads
- Domain: `vid.flavour.pl` → `/home/ars/mp4-video-banner-optimizer/`
- Working directory: `~/mp4-video-banner-optimizer/`

## Step 1 - Upload Files via FTP

```bash
# Locally execute FTP upload
cd /Users/arek/Desktop/KIMI-WORKSPACE/KIMI-DYNAMIC-ADS/KIMI-VIDEO-OPTIMIZER-400kb
python3 deployment/ftp_upload.py
```

The script uploads the canonical package `deployment/progreso/` (see its
`INSTALL.md` for the full install walkthrough):
- `web_app_prod.py` - Main Flask application (incl. `/api/health`)
- `requirements.txt` - Python dependencies
- `.htaccess` - Apache configuration (`Options -Indexes`)
- `mp4_optimizer/` - Core optimization modules (9 files)
- `templates/` - HTML templates (index, admin_uploads, portal)
- `start.sh`, `verify.sh` - start/restart and health-check helpers

Note: stale legacy copies elsewhere in `deployment/` (old `web_app_prod.py`,
`web_app.py`, nested `mp4_optimizer/`, `templates/`) are NOT the package —
do not upload them.

## Step 2 - Install Dependencies

```bash
# Install Python packages
pip3 install --user flask werkzeug
pip3 install --user -r requirements.txt
```

## Step 3 - Verify FFmpeg

```bash
# Check FFmpeg availability
ls -la ~/bin/ffmpeg
~/bin/ffmpeg -version | head -3

# If missing, download static build:
mkdir -p ~/bin
cd ~/bin
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xvf ffmpeg-release-amd64-static.tar.xz
cp ffmpeg-*/ffmpeg ffmpeg-*/ffprobe .
chmod +x ffmpeg ffprobe
```

## Step 4 - Create Working Directories

```bash
cd ~/mp4-video-banner-optimizer
mkdir -p uploads outputs reports
chmod 755 uploads outputs reports
```

## Step 5 - Configuration Files

### .htaccess (main directory)
```apache
Options -Indexes
```

Note: `passenger_wsgi.py` was removed — Passenger is not supported on
Progreso.pl (see Step 8). The app runs as a plain `nohup` process.

### web_app_prod.py (port configuration)
```python
# Line ~312
port = int(os.environ.get('PORT', 5000))
```

## Step 6 - Start Application

Preferred: use the packaged helper (creates dirs, kills old instances, starts
with nohup, checks `/api/health`):

```bash
cd ~/mp4-video-banner-optimizer
chmod +x start.sh verify.sh
./start.sh          # default port 5000
```

Manual equivalent:

```bash
cd ~/mp4-video-banner-optimizer

# Kill existing processes
pkill -f web_app_prod.py

# Start on port 5000
PORT=5000 nohup python3 web_app_prod.py > optimizer.log 2>&1 &

# Verify startup
sleep 3
ps aux | grep web_app_prod
tail -20 optimizer.log
```

Expected output:
```
Server running at: http://0.0.0.0:5000
Upload folder: uploads
Output folder: outputs
FFmpeg: ~/bin/ffmpeg
```

## Step 7 - Verify Local Operation

```bash
# Test locally
curl -s http://127.0.0.1:5000/ | head -10
curl -s http://127.0.0.1:5000/api/presets
curl -s http://127.0.0.1:5000/api/health
```

Should return HTML interface, JSON presets, and `{"status":"ok", ...}` health.

## Step 8 - Progreso.pl Panel Configuration

### Current Limitations
- Domain `vid.flavour.pl` uses external reverse proxy
- `.htaccess` ProxyPass directives are **ignored**
- Only ports 443/444/445 available in panel (SSL ports)
- Ports < 1024 require root permissions
- ProxyPass in panel cannot be configured to custom ports

### Panel Settings
- **Domain**: vid.flavour.pl
- **Document Root**: /mp4-video-banner-optimizer
- **Inne Skrypty**: TAK (enabled - required for Python)
- **Port**: 444 (or 445)
- **SSL**: Enabled

### Current Status
✅ **DOMAIN ACCESS WORKS via PHP bridge**
- `index.php` (in the package) proxies all requests to `http://127.0.0.1:5000`
- Package `.htaccess` has `DirectoryIndex index.php index.html`, so the bridge
  wins over any stray `index.html` in the docroot
- Requires: app running on port **5000** + "Inne Skrypty: TAK" (PHP) in panel
- Verify: `curl -s https://vid.flavour.pl/api/health`
- Troubleshooting: `php_bridge.log` in the app dir on the server

### Why direct proxying is NOT used
- Reverse proxy ignores `.htaccess` ProxyPass
- Panel proxy cannot forward to custom ports
- Panel ports 443/444/445 are SSL-only and require root

### Workarounds Attempted (before the bridge)
❌ ProxyPass in .htaccess (ignored)
❌ Passenger WSGI (not supported)
❌ FastCGI (not working)
❌ HTML redirect (ignored)
❌ iframe embed (ignored)

### Fallback Access
- Application also accessible directly via: `http://77.65.215.8:5000`

## Step 9 - Maintenance Commands

### Check status
```bash
ps aux | grep web_app_prod
netstat -tlnp | grep 5000
tail -f optimizer.log
```

### Restart application
```bash
pkill -f web_app_prod.py
PORT=5000 nohup python3 web_app_prod.py > optimizer.log 2>&1 &
```

### Check logs
```bash
tail -50 optimizer.log
ls -la uploads/ outputs/ reports/
```

### Clean up old files
```bash
find uploads/ -mtime +7 -delete
find outputs/ -mtime +7 -delete
find reports/ -mtime +30 -delete
```

## Troubleshooting

### Permission denied on ports 443/444/445
```bash
# These are SSL ports requiring root permissions
# Solution: Use port 5000 instead
PORT=5000 python3 web_app_prod.py
```

### Application not starting
```bash
# Check FFmpeg
~/bin/ffmpeg -version

# Check directories
ls -la uploads/ outputs/ reports/

# Check imports
python3 -c "from web_app_prod import app; print('OK')"
```

### Port already in use
```bash
fuser -k 5000/tcp
pkill -f web_app_prod.py
```

### Module not found
```bash
pip3 install --user flask werkzeug
pip3 install --user -r requirements.txt
```

## Important Notes

1. **Domain access currently NOT working** - use local IP:port
2. **Progreso.pl proxy limitations** - external reverse proxy ignores `.htaccess`
3. **Port restrictions** - only 443/444/445 available, but require SSL/root
4. **Current workaround** - app runs on port 5000, accessible via IP only
5. **Panel configuration** - "Inne Skrypty: TAK" required but not sufficient

## Contact & Support

- **Server**: ars_mp4_video_opt@flavour.civ.pl
- **Domain**: vid.flavour.pl
- **Local URL**: http://77.65.215.8:5000
- **Project**: MP4 Banner Optimizer with FFmpeg video processing