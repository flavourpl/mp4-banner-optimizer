# Progreso.pl — Full Developer Specification

> Complete reference for building server-side-only applications on Progreso.pl hosting.
> Last verified: July 2026.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Hosting Plans & Hardware](#2-hosting-plans--hardware)
3. [SSH / Shell Access](#3-ssh--shell-access)
4. [PHP Stack](#4-php-stack)
5. [Python Stack](#5-python-stack)
6. [Database (MySQL)](#6-database-mysql)
7. [FFmpeg & Media Processing](#7-ffmpeg--media-processing)
8. [Cron / Scheduled Tasks](#8-cron--scheduled-tasks)
9. [SSL / TLS](#9-ssl--tls)
10. [DNS & Domains](#10-dns--domains)
11. [Email](#11-email)
12. [Security: Separation Mode](#12-security-separation-mode)
13. [PHP Bridge Pattern (for Python apps)](#13-php-bridge-pattern-for-python-apps)
14. [Server-Side Only Architecture](#14-server-side-only-architecture)
15. [Limits Cheat Sheet](#15-limits-cheat-sheet)
16. [Known Gotchas & Workarounds](#16-known-gotchas--workarounds)
17. [Deployment Checklist](#17-deployment-checklist)
18. [What You CANNOT Do](#18-what-you-cannot-do)
19. [Recommended Patterns](#19-recommended-patterns)
20. [Contact & Infrastructure](#20-contact--infrastructure)

---

## 1. Architecture Overview

### What Progreso.pl Is

- **Shared hosting** (Hybrid plans) or **virtual server** (VPS plans)
- Managed panel called **Extranet** (custom, not cPanel)
- Apache web server with PHP-FPM
- SSH access (port 22, requires one-time helpdesk request)
- No root access on shared hosting
- No Docker, no systemd, no Passenger, no systemd services

### What Progreso.pl Is NOT

- NOT a VPS (you don't get root)
- NOT a container platform
- NOT a serverless platform
- NOT a PaaS (no Heroku-style deploys)

### Core Constraint

**You are a user on a shared Linux server.** You can:
- Run background processes via `nohup` / `&`
- Install Python packages via `pip3 install --user`
- Download static binaries to `~/bin/`
- Use cron for scheduling
- Access MySQL databases
- Run PHP scripts via Apache

You cannot:
- Install system packages (`apt`, `yum`)
- Bind to ports < 1024
- Run Passenger / uWSGI / Gunicorn as a service
- Modify Apache config
- Access Docker / Kubernetes

---

## 2. Hosting Plans & Hardware

### Hybrid Plans (NVMe — Recommended)

| Plan | Price/mo | Disk | CPU (avail/guar) | RAM (avail/guar) | Ramdisk | Bandwidth | Autoscaler |
|------|----------|------|-------------------|-------------------|---------|-----------|------------|
| Hybrid 1 | 60 PLN | 250 GB NVMe | 1 / 0.5 cores | 4 / 2 GB | 256 MB | 250 Mbit | up to 400% |
| Hybrid 2 | 120 PLN | 500 GB NVMe | 2 / 1 cores | 8 / 4 GB | 512 MB | 500 Mbit | up to 400% |
| Hybrid 4 | 240 PLN | 1000 GB NVMe | 4 / 2 cores | 16 / 8 GB | 1 GB | 1 Gbit | up to 400% |
| Hybrid 8 | 480 PLN | 2000 GB NVMe | 8 / 4 cores | 32 / 16 GB | 2 GB | 1 Gbit | up to 400% |

### Virtual Server Plans (SSD — Shared)

| Plan | Price/yr | Disk | Backup |
|------|----------|------|--------|
| Biznes | 360 PLN | 100 GB SSD | 24h / 14 days |
| Biznes Plus | 720 PLN | 200 GB SSD | 24h / 14 days |

### Key Numbers

- **CPU**: > 2.5 GHz per core
- **Autoscaler**: up to 400% boost on demand
- **Backup**: 24h cycle, 30 days retention (Hybrid) / 14 days (Virtual)
- **Data redundancy**: 6x duplication (RAID10 + 2x backup + offsite)
- **Location**: Poland (Polkomtel datacenter)
- **Infrastructure**: 4 independent power lines, UPS 200kVA, generators 1000kVA
- **Network**: 200+ domestic, 140+ international operators

---

## 3. SSH / Shell Access

| Parameter | Value |
|-----------|-------|
| Port | 22 |
| Host | Your domain (e.g. `flavour.civ.pl`) |
| Auth | Extranet credentials (username + password) |
| Activation | One-time helpdesk request |
| Shell | bash (limited) |

### Available Shell Tools

- `joe`, `vi` (editors)
- `chmod`, `chown`
- `crontab`
- `wget`, `curl`
- `tar`, `gzip`, `xz`
- `python3` (system installed)
- `pip3 install --user` (user-space packages)
- `ffmpeg` (must be installed manually — see Section 7)

### File Permissions

- Server **auto-corrects permissions every 24 hours**
- Use `chmod 755` for directories, `chmod 644` for files
- Avoid `chmod 777` — it will be reset and may cause issues

---

## 4. PHP Stack

### Available Versions

| Version | Binary Path |
|---------|-------------|
| PHP 7.3 | `/usr/local/php73/bin/php` |
| PHP 7.4 | `/usr/local/php74/bin/php` |
| PHP 8.0 | `/usr/local/php80/bin/php` |

- Version switching: via Extranet panel
- Mode: **PHP-FPM** (FastCGI Process Manager)

### PHP Limits (configurable via `.user.ini`)

| Directive | Default | Hard Cap | Notes |
|-----------|---------|----------|-------|
| `memory_limit` | 256 MB | **1024 MB** | Cannot exceed even with `.user.ini` |
| `max_execution_time` | 30 | **300 seconds** | Hard cap; for longer tasks use cron/shell |
| `upload_max_filesize` | configurable | via `.user.ini` | |
| `post_max_size` | configurable | via `.user.ini` | |
| `max_input_time` | default | configurable | |
| `max_file_uploads` | 20 | configurable | |

### `.user.ini` Usage

Place in the domain's document root (usually `public_html/`). Changes propagate within seconds.

```ini
memory_limit = 1024M
max_execution_time = 300
upload_max_filesize = 256M
post_max_size = 256M
max_file_uploads = 50
```

### Available PHP Libraries

| Library | Status |
|---------|--------|
| GD | Available (all PHP versions) |
| ImageMagick | Available |
| PDO MySQL | Available |
| cURL | Available |
| JSON | Available (built-in) |
| mbstring | Available |
| OpenSSL | Available |
| Phalcon | Available |

### PHP Extensions (likely available)

- `mysqli`, `pdo_mysql`
- `curl`, `openssl`
- `gd`, `imagick`
- `json` (built-in since 7.x)
- `mbstring`
- `xml`, `xmlrpc`
- `zip`
- `soap`
- `bcmath`
- `gmp`

> **Verify any extension before relying on it**: `php -m | grep <extension>`

---

## 5. Python Stack

### System Python

- Python 3 is available via SSH
- Install packages: `pip3 install --user <package>`
- Packages install to `~/.local/lib/python3.x/site-packages/`

### Running Python Apps

**Method 1: Background process (recommended for web apps)**
```bash
nohup python3 app.py > app.log 2>&1 &
```

**Method 2: Cron job (for scheduled tasks)**
```bash
# crontab entry
*/5 * * * * /usr/bin/python3 /home/user/app/script.py >> /home/user/app/cron.log 2>&1
```

**Method 3: SSH one-off execution**
```bash
ssh user@domain "python3 /path/to/script.py"
```

### Python Libraries Known to Work

- Flask
- Werkzeug
- requests
- sqlite3 (built-in)
- subprocess (built-in)
- os, sys, json, re, etc. (built-in)
- Most pure-Python packages via pip

### Python Libraries That May NOT Work

- Libraries requiring C extensions compiled at install time (may fail without gcc)
- Libraries requiring system-level dependencies (libxml2, libssl-dev, etc.)
- Libraries that need `sudo` or root access

> **Rule of thumb**: If `pip3 install --user <package>` succeeds, it works. Test before relying on it.

---

## 6. Database (MySQL)

| Parameter | Value |
|-----------|-------|
| Engine | MySQL 8.0 |
| Host | `localhost` |
| Limit on databases | None (unlimited count and size) |
| Management | Extranet panel |
| Backup | Included in plan backup cycle |
| SQL dump | Available via shell (`mysqldump`) |

### Connection Example (PHP)

```php
$pdo = new PDO('mysql:host=localhost;dbname=mydb', 'user', 'password');
```

### Connection Example (Python)

```python
import pymysql
conn = pymysql.connect(host='localhost', user='user', password='pass', database='mydb')
```

### Connection Example (CLI)

```bash
mysql -u user -p -h localhost mydb
```

---

## 7. FFmpeg & Media Processing

### Native Availability

FFmpeg is **NOT pre-installed** on Progreso hosting. The help pages for FFmpeg return 404 (removed or never existed).

### Installation (Manual)

```bash
mkdir -p ~/bin
cd ~/bin
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xvf ffmpeg-release-amd64-static.tar.xz
cp ffmpeg-*/ffmpeg ffmpeg-*/ffprobe .
chmod +x ffmpeg ffprobe
```

### Verification

```bash
~/bin/ffmpeg -version
~/bin/ffprobe -version
```

### Limitations

- Static binary only (no hardware acceleration)
- CPU-bound processing (no GPU)
- 300-second PHP execution time limit (if called from PHP)
- No limit when called from Python/shell background process
- Shared CPU — may be throttled under load

### Media Processing Recommendations

1. Run FFmpeg from Python/shell, not from PHP
2. Use background processes (`nohup`) for long-running jobs
3. Process files asynchronously (queue system)
4. Set reasonable timeouts in your application
5. Clean up processed files regularly

---

## 8. Cron / Scheduled Tasks

### Access

- Via SSH: `crontab -e`
- Via Extranet: Aplikacje → Zadania cron

### PHP Binary Paths (for cron)

```bash
/usr/local/php73/bin/php
/usr/local/php74/bin/php
/usr/local/php80/bin/php
```

### Cron Syntax

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-7, 0=7=Sunday)
│ │ │ │ │
* * * * * command
```

### Examples

```bash
# Run Python script every 5 minutes
*/5 * * * * /usr/bin/python3 /home/user/app/task.py >> /home/user/app/cron.log 2>&1

# Run PHP script every hour
0 * * * * /usr/local/php80/bin/php /home/user/app/cron.php >> /home/user/app/cron.log 2>&1

# Run shell script daily at 2 AM
0 2 * * * /bin/bash /home/user/app/daily.sh >> /home/user/app/cron.log 2>&1

# Restart Python app every minute (watchdog)
* * * * * cd /home/user/app && ./watchdog.sh >> watchdog.log 2>&1
```

### Cron Commands

```bash
crontab -l          # List current crontab
crontab -r          # Remove all cron jobs
crontab -e          # Edit crontab
crontab ./cron.txt  # Import from file
```

---

## 9. SSL / TLS

| Feature | Status |
|---------|--------|
| TLS 1.2 | Supported |
| Free Let's Encrypt | Available, unlimited |
| Wildcard SSL | Supported (requires Progreso DNS) |
| Auto-renewal | Automatic in last week of validity |
| Rate limit | 2 certificates per user per 24 hours |
| SSL Labs rating | A |

### SSL Setup

- Auto-generated in ~60 seconds via Extranet
- Wildcard requires DNS on Progreso: `d.ns1.pl` / `d.ns2.pl`
- Standard SSL works with external DNS (Cloudflare, etc.)

---

## 10. DNS & Domains

| Feature | Status |
|---------|--------|
| Virtual domains | Supported (multiple per account) |
| Subdomains | Supported |
| Sub-subdomains | Supported |
| Wildcard subdomains | Supported (requires SSL) |
| DNS management | Extranet panel (DNS editor) |
| External DNS | Supported (for standard SSL) |
| Wildcard DNS | Requires Progreso DNS |

### Cloudflare Integration

- API token configuration available
- Standard SSL with Cloudflare works
- Wildcard does NOT work with Cloudflare (requires Progreso DNS)

---

## 11. Email

| Feature | Status |
|---------|--------|
| IMAP | Available (SSL) |
| POP3 | Available (SSL) |
| SMTP | Available (SSL) |
| SpamAssassin | Active |
| SPF/DKIM/DMARC | Full support |
| Webmail | Available |
| Mail groups | Supported |

### SMTP Configuration

```
Host: smtp.progreso.pl (or your domain)
Port: 465 (SSL) or 587 (STARTTLS)
Auth: Yes
Username: full email address
```

---

## 12. Security: Separation Mode

### What It Does

When enabled in Extranet (one click), **all** sites on the account are isolated:

1. Each site runs in its own directory
2. PHP can only access explicitly allowed directories
3. **CGI scripts (Perl, Ruby, Python) are DISABLED**
4. Dangerous PHP functions are disabled:
   - `exec`, `passthru`, `shell_exec`, `system`
   - `popen`, `proc_open`, `pcntl_exec`
   - `chroot`, `chdir`, `symlink`, `link`, `rename`, `putenv`

### Configuration After Enabling

In Extranet → Strony WWW → edit assignment:

- **Katalogi dostępne dla PHP** — directories PHP can access (colon-separated)
  - Example: `/www/progreso.pl:/www/upload`
- **Dostęp do katalogu tymczasowego** — access to `/tmp` (recommended: ON)

### Impact on Our Apps

**Separation does NOT affect:**
- Background Python processes (`nohup python3 app.py`)
- FFmpeg called from shell
- Cron jobs (run as shell commands)
- SSH access
- MySQL databases

**Separation DOES affect:**
- PHP scripts called via CGI (disabled entirely)
- PHP `exec()` / `shell_exec()` / `system()` calls (disabled)
- PHP access to other site directories

### Recommendation

**Enable separation.** Our Flask app runs as a background process, not CGI. Separation improves security without affecting our architecture.

---

## 13. PHP Bridge Pattern (for Python Apps)

### The Problem

Progreso.pl does NOT support:
- Passenger WSGI
- Reverse ProxyPass via .htaccess
- FastCGI for Python
- Custom port forwarding from the panel

### The Solution: PHP Bridge

A PHP script proxies HTTP requests to a Python Flask/Django app running on `127.0.0.1:<port>`.

### Architecture

```
Internet
    ↓ HTTPS (port 443)
Apache (Progreso)
    ↓ serves PHP
index.php (bridge)
    ↓ HTTP proxy (127.0.0.1:5000)
Python Flask app (nohup background process)
    ↓ subprocess calls
FFmpeg / ImageMagick / Custom binaries
```

### Bridge Code (index.php)

```php
<?php
$target = 'http://127.0.0.1:5000';
$path = $_SERVER['REQUEST_URI'];

$ch = curl_init($target . $path);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HEADER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, false);
curl_setopt($ch, CURLOPT_TIMEOUT, 300);
curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);

// Forward headers
$headers = [];
foreach ($_SERVER as $key => $value) {
    if (strpos($key, 'HTTP_') === 0) {
        $headerName = str_replace('_', '-', substr($key, 5));
        $headers[] = $headerName . ': ' . $value;
    }
}
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

// Forward body for POST/PUT
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, file_get_contents('php://input'));
}

$response = curl_exec($ch);
$headerSize = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
curl_close($ch);

// Split headers and body
$httpHeaders = substr($response, 0, $headerSize);
$httpBody = substr($response, $headerSize);

// Forward response headers
header_remove();
$headerLines = explode("\r\n", trim($httpHeaders));
foreach ($headerLines as $header) {
    if (strpos($header, ':') !== false) {
        $parts = explode(':', $header, 2);
        $name = trim($parts[0]);
        $value = trim($parts[1]);
        // Skip problematic headers
        if (!in_array(strtolower($name), ['transfer-encoding', 'content-length'])) {
            header($name . ': ' . $value);
        }
    }
}

echo $httpBody;
```

### .htaccess for Bridge

```apache
Options -Indexes
DirectoryIndex index.php index.html
```

### Why This Works

- PHP is executed by Apache (allowed on Progreso)
- PHP `curl` can reach `127.0.0.1:5000` (local loopback)
- Python app runs as a background process (no CGI involved)
- SSL termination happens at Apache level
- Client never sees Python code or server structure

---

## 14. Server-Side Only Architecture

### Principle

**Zero code, logic, or algorithms exposed to the client.** Everything runs server-side.

### What the Client Sees

- HTML pages (rendered server-side)
- CSS (styling only)
- Minimal JavaScript (UI interactions only — no business logic)
- API responses (JSON/XML)

### What Runs Server-Side

- All business logic (PHP or Python)
- All data processing
- All file processing (FFmpeg, ImageMagick)
- All database queries
- All authentication/authorization
- All validation
- All calculations

### Recommended Stack

```
Client (Browser)
    ↓ HTTP/HTTPS
Apache (SSL termination)
    ↓ PHP
PHP Bridge (index.php)
    ↓ HTTP localhost
Python Flask App (nohup)
    ├── Business Logic
    ├── Database (MySQL via pymysql/MySQLdb)
    ├── File Processing (FFmpeg, ImageMagick)
    └── Subprocess Calls (shell commands)
```

### API Design (Server-Side Rendering)

```
GET  /                  → HTML page (rendered in PHP/Python)
POST /api/process       → JSON response (processing result)
GET  /api/status/:id    → JSON response (job status)
GET  /download/:id      → File download (processed output)
```

### What NOT to Put in Client Code

- API keys
- Database credentials
- Business logic
- Algorithm implementations
- File paths
- Server structure
- Internal URLs

### Minimal Client JavaScript (Example)

```javascript
// ONLY UI interactions — no business logic
document.getElementById('upload-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    fetch('/api/upload', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
            document.getElementById('result').innerText = data.message;
        });
});
```

---

## 15. Limits Cheat Sheet

### PHP Limits

| Limit | Value | Configurable |
|-------|-------|--------------|
| `memory_limit` | 1024 MB hard cap | Via `.user.ini` (up to cap) |
| `max_execution_time` | 300 seconds hard cap | Via `.user.ini` (up to cap) |
| `upload_max_filesize` | Via `.user.ini` | Yes |
| `post_max_size` | Via `.user.ini` | Yes |
| `max_file_uploads` | 20 default | Via `.user.ini` |

### System Limits

| Limit | Value |
|-------|-------|
| SSH port | 22 |
| Allowed ports (binding) | > 1024 |
| Panel ports (SSL) | 443, 444, 445 |
| Cron resolution | 1 minute |
| File permission reset | Every 24 hours |
| Backup retention | 30 days (Hybrid) / 14 days (Virtual) |

### Resource Limits (Hybrid 2 example)

| Resource | Available | Guaranteed |
|----------|-----------|------------|
| CPU | 2 cores @ >2.5 GHz | 1 core |
| RAM | 8 GB | 4 GB |
| Disk | 500 GB NVMe | — |
| Bandwidth | 500 Mbit | — |
| Ramdisk | 512 MB | — |
| Autoscaler | up to 400% | — |

---

## 16. Known Gotchas & Workarounds

### Gotcha 1: No Reverse Proxy

**Problem**: `.htaccess` ProxyPass directives are **ignored** on Progreso.
**Workaround**: Use PHP bridge (index.php → curl → localhost:port).

### Gotcha 2: No Passenger/WSGI

**Problem**: Passenger WSGI is not supported.
**Workaround**: Run Python as `nohup` background process, use PHP bridge.

### Gotcha 3: Port Restrictions

**Problem**: Cannot bind to ports < 1024 (requires root). Panel only exposes 443/444/445 (SSL).
**Workaround**: Run Python on port 5000 (or any port > 1024), use PHP bridge for HTTPS.

### Gotcha 4: Separation Disables CGI

**Problem**: Enabling "Separacja serwisów" disables Perl/Ruby/Python CGI.
**Workaround**: Not a problem for our architecture — we run Python as background process, not CGI.

### Gotcha 5: Separation Disables PHP exec()

**Problem**: When separation is enabled, PHP cannot call `exec()`, `shell_exec()`, `system()`.
**Workaround**: Run FFmpeg/shell commands from Python, not from PHP.

### Gotcha 6: PHP Memory Cap

**Problem**: `memory_limit` cannot exceed 1024 MB.
**Workaround**: For heavier processing, use Python (no memory cap from PHP).

### Gotcha 7: PHP Execution Time

**Problem**: PHP scripts cannot run longer than 300 seconds.
**Workaround**: Use cron + shell for long-running tasks, or run from Python background process.

### Gotcha 8: File Permissions Reset

**Problem**: Server auto-corrects file permissions every 24 hours.
**Workaround**: Don't rely on restrictive permissions. Use `.htaccess` for access control.

### Gotcha 9: FFmpeg Not Pre-installed

**Problem**: FFmpeg is not available by default.
**Workaround**: Install static binary to `~/bin/ffmpeg`.

### Gotcha 10: Wildcard SSL Requires Progreso DNS

**Problem**: Wildcard certificates only work if DNS is on Progreso nameservers.
**Workaround**: Use standard SSL (one domain), or switch DNS to Progreso for wildcard.

### Gotcha 11: SSH Activation

**Problem**: SSH is not enabled by default.
**Workaround**: Request activation via helpdesk (one-time).

### Gotcha 12: No System Package Manager

**Problem**: Cannot install system packages (apt, yum).
**Workaround**: Use `pip3 install --user` for Python, download static binaries for tools.

---

## 17. Deployment Checklist

### Initial Setup

- [ ] SSH access activated (helpdesk request)
- [ ] Python 3 available (`python3 --version`)
- [ ] pip3 available (`pip3 --version`)
- [ ] MySQL database created (Extranet panel)
- [ ] SSL certificate generated (Extranet panel)
- [ ] Domain DNS pointing to Progreso
- [ ] "Inne Skrypty: TAK" enabled in panel (for Python)

### Application Deployment

- [ ] Upload files via FTP/SFTP
- [ ] Install Python dependencies (`pip3 install --user -r requirements.txt`)
- [ ] Install FFmpeg static binary (`~/bin/ffmpeg`)
- [ ] Create working directories (`uploads/`, `outputs/`, `reports/`)
- [ ] Set directory permissions (`chmod 755`)
- [ ] Configure `.user.ini` (memory, execution time, upload limits)
- [ ] Create `index.php` bridge
- [ ] Configure `.htaccess` (DirectoryIndex, Options)
- [ ] Start Python app (`nohup python3 app.py > app.log 2>&1 &`)
- [ ] Verify app is running (`curl http://127.0.0.1:5000/`)
- [ ] Test via HTTPS domain (`curl https://domain/api/health`)
- [ ] Set up cron watchdog for auto-restart
- [ ] Set up log rotation / cleanup cron

### Security

- [ ] Enable Separacja serwisów (Extranet)
- [ ] Configure "Katalogi dostępne dla PHP" if needed
- [ ] Set Basic Auth on admin pages (`.htaccess`)
- [ ] Verify no business logic in client JavaScript
- [ ] Verify API keys not exposed in client code
- [ ] Test that processed files are not publicly accessible

---

## 18. What You CANNOT Do

| Task | Why | Alternative |
|------|-----|-------------|
| Run Docker containers | No root, no container runtime | Use background processes |
| Install system packages | No apt/yum | Use pip3 --user, static binaries |
| Bind to port 80/443 directly | Requires root | Use PHP bridge |
| Run Passenger/WSGI | Not supported | Use nohup + PHP bridge |
| Use Reverse ProxyPass | Ignored by Apache | Use PHP bridge |
| Call PHP exec() with separation | Disabled | Run from Python |
| Run long PHP scripts (>300s) | Hard cap | Use cron/shell/Python |
| Use GPU processing | No GPU available | CPU only |
| Run WebSocket servers | No persistent connections from Apache | Use long-polling or Server-Sent Events |
| Access other users' files | Shared hosting isolation | N/A |

---

## 19. Recommended Patterns

### Pattern 1: Web Application (Flask/Django)

```
Architecture:
  Apache (HTTPS) → index.php (bridge) → Python Flask (localhost:5000)

Components:
  - index.php: HTTP proxy to Python
  - app.py: Flask application
  - templates/: HTML templates (Jinja2)
  - static/: CSS, images (no JS business logic)
  - uploads/: User uploads
  - outputs/: Processed files
  - watchdog.sh: Auto-restart script
  - .htaccess: DirectoryIndex, auth
  - .user.ini: PHP limits
```

### Pattern 2: Background Processing Service

```
Architecture:
  Upload (HTTP) → Python saves to queue → Cron processes → Output available

Components:
  - Flask API for uploads
  - queue/ directory for pending jobs
  - Cron script processes queue every N minutes
  - outputs/ for completed files
  - status.php for monitoring
```

### Pattern 3: API-Only Service

```
Architecture:
  Client → Apache → index.php → Python Flask API → JSON responses

Components:
  - Flask app with JSON endpoints only
  - No HTML templates
  - No client-side business logic
  - All processing server-side
```

### Pattern 4: Scheduled Data Processing

```
Architecture:
  Cron triggers Python script → processes data → stores results in MySQL

Components:
  - Python script for data processing
  - MySQL for storage
  - Cron for scheduling
  - Optional: Flask dashboard for viewing results
```

---

## 20. Contact & Infrastructure

### Server Access

- **SSH**: `ars@flavour.civ.pl` (port 22)
- **FTP**: Same credentials as SSH
- **Panel**: https://panel.progreso.pl/login/

### Domain

- **Production**: `vid.flavour.pl`
- **Direct IP**: `http://77.65.215.8:5000`

### Progreso.pl Support

- **Helpdesk**: https://panel.progreso.pl (Extranet)
- **Phone**: +48 500 450 100
- **Email**: info@progreso.pl
- **Availability**: 24/7

### Documentation

- **Help Center**: https://progreso.pl/pl/pomoc
- **Hosting Plans**: https://progreso.pl/pl/hosting-hybrydowy
- **Separacja**: https://progreso.pl/pl/pomoc/separacja-stron-www

---

## Quick Reference for AI Agents

### When building an app on Progreso.pl:

1. **Is it a web app?** → Use Flask + PHP bridge pattern
2. **Does it need FFmpeg?** → Install static binary, call from Python
3. **Does it need a database?** → Use MySQL (localhost, unlimited)
4. **Does it need scheduling?** → Use cron (1-minute resolution)
5. **Does it need HTTPS?** → Use Let's Encrypt (free, auto-renewal)
6. **Does it need file uploads?** → Configure `.user.ini` limits
7. **Does it need long processing?** → Use background process, not PHP
8. **Does it need separation?** → Enable it, use Python for shell calls
9. **Client code?** → Minimal JS for UI only, NO business logic
10. **Server-side only?** → Everything in Python/PHP, nothing in browser

### Golden Rule

**If it involves business logic, algorithms, data processing, or secrets — it runs server-side. The client is a dumb terminal that displays results.**
