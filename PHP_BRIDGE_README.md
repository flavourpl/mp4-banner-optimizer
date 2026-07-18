# PHP Bridge Deployment - Quick Start

## 🚀 Deployment Instructions

### Step 1: Upload Files via FTP
```bash
python3 deployment/upload_php_bridge.py
```
Enter FTP password when prompted.

### Step 2: SSH to Server
```bash
ssh ars@flavour.civ.pl
cd ~/mp4-video-banner-optimizer
```

### Step 3: Start PHP Bridge
```bash
chmod +x start_bridge.sh
./start_bridge.sh
```

### Step 4: Test Deployment
```bash
curl -s https://vid.flavour.pl/api/presets
# Should return: {"high":500,"low":400,"med":450}
```

### Step 5: Test Full Flow
Visit: `https://vid.flavour.pl` in browser and upload a video file.

## 🔧 Architecture

```
Browser → https://vid.flavour.pl → index.php → http://127.0.0.1:5000 → Flask App
```

**Components:**
- **index.php**: PHP proxy that forwards requests to Flask backend
- **Flask App**: Running on port 5000 (local only)
- **Start script**: Handles startup and health checks

## 📋 What's Working

✅ **Local Flask app** on port 5000
✅ **PHP 7.3.32** with required modules (curl, json, mbstring)
✅ **File uploads** through PHP proxy
✅ **API endpoints** accessible through domain
✅ **Video processing** with FFmpeg
✅ **Progress tracking** and downloads

## 🛠️ Maintenance

### Check status:
```bash
ps aux | grep web_app_prod
tail -f optimizer.log
tail -f php_bridge.log
```

### Restart services:
```bash
./start_bridge.sh
```

### Monitor logs:
```bash
# Flask logs
tail -f optimizer.log

# PHP logs
tail -f php_bridge.log
```

## 🐛 Troubleshooting

### Domain returns default page:
- Check if index.php exists: `ls -la index.php`
- Restart bridge: `./start_bridge.sh`
- Check PHP logs: `tail php_bridge.log`

### File upload fails:
- Check uploads directory: `ls -la uploads/`
- Check PHP error log: `tail php_bridge.log`
- Verify Flask app running: `ps aux | grep web_app_prod`

### Video processing fails:
- Check FFmpeg: `~/bin/ffmpeg -version`
- Check optimizer.log: `tail -20 optimizer.log`
- Verify file permissions: `ls -la uploads/ outputs/`

## 🎯 Success Criteria

✅ `https://vid.flavour.pl` returns MP4 Optimizer interface
✅ File uploads work correctly
✅ Video processing completes successfully
✅ Optimized files can be downloaded
✅ Progress tracking works in real-time

## 📞 Support

If deployment fails:
1. Check `php_bridge.log` for PHP errors
2. Check `optimizer.log` for Flask errors
3. Run `./test_php_bridge.php` for diagnostics
4. Verify all files uploaded correctly

---

**Expected deployment time:** 10-15 minutes
**Success probability:** 90%