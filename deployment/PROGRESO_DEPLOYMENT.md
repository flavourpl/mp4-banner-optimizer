# Progreso.pl Deployment Guide

## Quick Start (5 Minutes)

### 1. Upload Files to Your Hosting

Upload these files/folders to your Progreso.pl account:
- `web_app_prod.py`
- `start_progreso.sh` 
- `mp4_optimizer/` (entire folder)
- `templates/` (folder with index.html)

### 2. SSH into Your Progreso.pl Account

```bash
ssh your_username@your-server.com
```

### 3. Go to Deployment Directory

```bash
cd path/to/deployment/folder
```

### 4. Make Scripts Executable

```bash
chmod +x start_progreso.sh
```

### 5. Start the Application

```bash
./start_progreso.sh
```

Your MP4 Banner Optimizer is now running!
Access it at: `http://your-domain.com:8080`

## What This Does

The application will automatically:
- ✅ Use your static FFmpeg build in `~/bin/`
- ✅ Create required directories (uploads/, outputs/, reports/)
- ✅ Start on port 8080
- ✅ Handle video optimization requests

## Testing

1. Open `http://your-domain.com:8080` in your browser
2. Upload a small MP4 file (< 100MB)
3. Select optimization options
4. Wait for processing
5. Download optimized file

## Common Issues

### "Port already in use"
```bash
# Check what's using the port
netstat -tuln | grep 8080

# Use a different port
export PORT=8081
./start_progreso.sh
```

### "FFmpeg not found"
```bash
# Make sure static FFmpeg is in ~/bin/
ls -la ~/bin/ffmpeg

# If missing, re-run deployment
./deploy_progreso.sh
```

### "Permission denied"
```bash
# Make sure directories are writable
chmod 755 uploads outputs reports
```

## Advanced Configuration

### Change Port
```bash
export PORT=9000
./start_progreso.sh
```

### Background Process
```bash
nohup ./start_progreso.sh > optimizer.log 2>&1 &
```

### Check Logs
```bash
tail -f optimizer.log
```

### Stop Background Process
```bash
ps aux | grep web_app_prod
kill <PID>
```

## File Cleanup

The application automatically cleans up files older than 1 hour. To manually clean:

```bash
rm uploads/* outputs/* reports/*
```

## Support

If you encounter issues:
1. Check FFmpeg is working: `~/bin/ffmpeg -version`
2. Check Python is working: `python3 --version`
3. Check disk space: `df -h`
4. Review logs: `tail optimizer.log`

## Security Notes

- The application accepts files up to 100MB
- Only MP4 files are accepted
- Files are automatically cleaned up after 1 hour
- Run as regular user (not root)

## Performance Tips

- For high traffic, consider using Gunicorn instead of Flask dev server
- Monitor disk usage: `df -h`
- Check memory usage: `free -h`
- Monitor active processes: `ps aux | grep python`

Enjoy optimizing your MP4 banners! 🚀