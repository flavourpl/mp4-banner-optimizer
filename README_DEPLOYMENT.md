# MP4 Banner Optimizer - Deployment Status

## ✅ WORKING: Local Application
**URL**: `http://77.65.215.8:5000`  
**Status**: Fully operational  
**Access**: Direct IP access only

## ❌ NOT WORKING: Domain Access  
**URL**: `https://vid.flavour.pl`  
**Status**: Returns default Flavour page  
**Reason**: Progreso.pl reverse proxy ignores `.htaccess`

## Quick Start (After Server Reset)

### 1. Upload Files
```bash
python3 deployment/ftp_upload.py
```

### 2. Start Application
```bash
ssh ars_mp4_video_opt@flavour.civ.pl
cd ~/mp4-video-banner-optimizer
PORT=5000 nohup python3 web_app_prod.py > optimizer.log 2>&1 &
```

### 3. Verify
```bash
curl http://127.0.0.1:5000/api/presets
# Should return: {"high": 500, "low": 400, "med": 450}
```

## Current Limitations

**Progreso.pl Hosting Issues:**
- External reverse proxy ignores `.htaccess` files
- Panel ports limited to 443/444/445 (SSL only)
- No proxy configuration options available
- "Inne Skrypty: TAK" enabled but insufficient

**Workarounds Attempted:**
- ❌ ProxyPass in .htaccess
- ❌ Passenger WSGI  
- ❌ FastCGI
- ❌ HTML redirects
- ❌ iframe embeds

## Current Solution

**Application runs locally on port 5000**
- Direct access: `http://77.65.215.8:5000`
- Not accessible via domain
- All features working (upload, optimize, download)

## Technical Details

**Application:** Flask + FFmpeg video optimizer  
**Server:** ars_mp4_video_opt@flavour.civ.pl  
**Directory:** ~/mp4-video-banner-optimizer  
**Dependencies:** Flask, Werkzeug, FFmpeg static build  
**Ports:** 5000 (working), 443/444/445 (blocked by SSL)

## For Domain Access

**Options to investigate:**
1. Contact Progreso.pl support for proxy configuration
2. Use different hosting with proper .htaccess support
3. Configure Cloudflare/Squid proxy in front of domain
4. Use subdomain with different DNS configuration

---

**Status**: Application working, domain access pending hosting solution  
**Last Updated**: 2024-07-17  
**Documentation**: See AGENTS.md for detailed recovery procedures