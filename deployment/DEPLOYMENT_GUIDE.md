# 🚀 DEPLOYMENT GUIDE - MP4 Banner Optimizer

## 📋 WYMAGANIA SERWERA

### Minimalne wymagania:
- **System operacyjny:** Linux (Ubuntu 20.04+, Debian 10+, CentOS 7+)
- **RAM:** 1-2 GB minimum
- **Dysk:** 10 GB minimum (na pliki tymczasowe + ffmpeg)
- **CPU:** 2 core minimum (lepie 4+ dla encodingu)

### Wymagane oprogramowanie:
- **Python:** 3.6+ 
- **FFmpeg:** 4.0+ (z x264 codec)
- **FFprobe:** (z pakietu ffmpeg)

---

## 🎯 **OPCJA 1: Tradycyjny VPS (Recommended for control)**
### Hosting providers:
- **DigitalOcean** ($5-10/miesiąc)
- **Linode** ($5-10/miesiąc) 
- **Vultr** ($3-5/miesiąc)
- **Hetzner** ($4-5/miesiąc)

### KROK PO KROKU:

#### **KROK 1: Zakup serwera VPS**
1. Zarejestruj konto u providera (np. DigitalOcean)
2. Utwórz nowy "Droplet" (VPS):
   - **Obraz:** Ubuntu 22.04 LTS
   - **Rozmiar:** 2GB RAM, 1 CPU, 40GB dysku ($6/miesiąc)
   - **Lokalizacja:** najbliżej Twoich klientów

#### **KROK 2: Połączenie przez SSH**
```bash
ssh root@twoje_ip_serwera
```

#### **KROK 3: Instalacja wymaganych pakietów**
```bash
# Aktualizacja systemu
apt update && apt upgrade -y

# Instalacja Pythona i zależności
apt install python3 python3-pip python3-venv -y

# Instalacja FFmpeg (CRUCZNE!)
apt install ffmpeg -y

# Weryfikacja instalacji
python3 --version
pip3 --version
ffmpeg -version
ffprobe -version
```

#### **KROK 4: Konfiguracja aplikacji**
```bash
# Dodaj użytkownika (opcjonalnie, lepsze niż root)
adduser mp4optimizer
usermod -aG sudo mp4optimizer

# Przełącz na użytkownika
su - mp4optimizer
cd ~

# Stwórz katalog projektu
mkdir -p mp4_optimizer
cd mp4_optimizer
```

#### **KROK 5: Upload plików na serwer**
**Opcja A: SCP (z lokalnego terminala)**
```bash
# Z Twojego lokalnego komputera:
cd /Users/arek/Desktop/KIMI-WORKSPACE/KIMI-DYNAMIC-ADS/KIMI-VIDEO-OPTIMIZER-400kb/deployment
scp -r * user@twoje_ip_serwera:/home/mp4optimizer/mp4_optimizer/
```

**Opcja B: SFTP (Cyberduck, FileZilla)**
- Połącz się z serwerem przez SFTP
- Prześlij pliki do `/home/mp4optimizer/mp4_optimizer/`

**Opcja C: Git (najlepsze dla przyszłości)**
```bash
# Na serwerze:
sudo apt install git -y
git clone https://github.com/twoje-repo/mp4-optimizer.git
cd mp4-optimizer
```

#### **KROK 6: Konfiguracja środowiska Python**
```bash
cd /home/mp4optimizer/mp4_optimizer

# Stwórz virtual environment
python3 -m venv venv
source venv/bin/activate

# Zainstaluj zależności
pip install Flask Werkzeug

# Stwórz foldery na pliki
mkdir -p uploads outputs reports
```

#### **KROK 7: Produkcja deployment (zamiast dev)**
Zmieniamy aplikację na produkcję:

```bash
# Wyedytuj web_app.py i zamień poniższe linie:
# Zmień port z 5001 na 8080 (bez roota):
# app.run(debug=False, host='0.0.0.0', port=8080)
```

Lub użyj Gunicorn (professionale):

```bash
pip install gunicorn

# Stwórz plik startowy:
cat > gunicorn_config.py << 'EOF'
import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
bind = "0.0.0.0:8080"
timeout = 300  # 5 minuty na encoding
EOF
```

#### **KROK 8: Testowanie lokalne**
```bash
# Testuj aplikację:
python3 web_app.py
# Otwórz http://twoje_ip:8080 w przeglądarce

# Lub z Gunicorn:
gunicorn -c gunicorn_config.py wsgi:app
```

#### **KROK 9: Systemd Service (autostart)**
```bash
sudo nano /etc/systemd/system/mp4-optimizer.service
```

Wklej zawartość:
```ini
[Unit]
Description=MP4 Banner Optimizer
After=network.target

[Service]
Type=notify
User=mp4optimizer
WorkingDirectory=/home/mp4optimizer/mp4_optimizer
Environment="PATH=/home/mp4optimizer/mp4_optimizer/venv/bin"
ExecStart=/home/mp4optimizer/mp4_optimizer/venv/bin/gunicorn \
          -c /home/mp4optimizer/mp4_optimizer/gunicorn_config.py \
          wsgi:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Stwórz wsgi entry point
cat > wsgi.py << 'EOF'
from web_app import app
if __name__ == "__main__":
    app.run()
EOF

# Włącz i uruchom service
sudo systemctl daemon-reload
sudo systemctl enable mp4-optimizer
sudo systemctl start mp4-optimizer

# Sprawdź status
sudo systemctl status mp4-optimizer
```

#### **KROK 10: Firewall**
```bash
# Otwórz port 8080
sudo ufw allow 8080
sudo ufw enable
sudo ufw status
```

---

## ☁️ **OPCJA 2: PaaS (Najprostsza dla początkujących)**
### Hosting providers:
- **Render** (free tier available)
- **Railway** (gdzie darmowe konto)
- **Fly.io** (konto z free trial)

### KROK PO KROKU (Render.com):

#### **KROK 1: Przygotowanie**
1. Stwórz konto na **render.com**
2. Zainstaluj **Render CLI**:
   ```bash
   npm install -g @render/cli
   ```

#### **KROK 2: Stwórz pliki deployment**
```bash
# Stwórz pliki w katalogu głównym:
cat > render.yaml << 'EOF'
services:
  - type: web
    name: mp4-optimizer
    env: python
    buildCommand: pip install Flask Werkzeug
    startCommand: python web_app.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.12
    disk:
      name: data
      size: 10GB  # Dla plików tymczasowych
EOF

cat > runtime.txt << 'EOF'
python-3.9.12
EOF
```

#### **KROK 3: Upload na GitHub**
```bash
git init
git add .
git commit -m "MP4 Banner Optimizer deployment"
git remote add origin https://github.com/twoje-repo/mp4-optimizer.git
git push -u origin main
```

#### **KROK 4: Deploy na Render**
```bash
# Połącz Render z GitHub
# Deploy aplikacji z dashboard
# Render automatycznie wykryje requirements.txt i web_app.py
```

#### **KROK 5: Konfiguracja FFmpeg na Render**
Render wymaga dodania **build script** dla FFmpeg:

```yaml
# Dodaj do render.yaml:
build:
  commands:
    - echo "Installing FFmpeg..."
    - apt-get update && apt-get install -y ffmpeg
    - pip install Flask Werkzeug
```

---

## 🐳 **OPCJA 3: Docker (Najbardziej profesjonalne)**

### KROK PO KROKU:

#### **KROK 1: Stwórz Dockerfile**
```dockerfile
FROM python:3.9-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY mp4_optimizer/ ./mp4_optimizer/
COPY templates/ ./templates/
COPY web_app.py .

# Create directories
RUN mkdir -p uploads outputs reports

# Expose port
EXPOSE 5001

# Run application
CMD ["python", "web_app.py"]
```

#### **KROK 2: Docker Compose**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5001:5001"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./reports:/app/reports
    environment:
      - FLASK_ENV=production
      - PORT=5001
    restart: unless-stopped
```

#### **KROK 3: Deploy**
```bash
# Lokalne testy:
docker-compose build
docker-compose up

# Na serwerze:
docker-compose up -d
```

---

## 🔧 **OPCJA 4: Hosting z Panelem (cPanel/Plesk)**
### Dostawcy:
- **Hostinger** (plan Professional)
- **A2 Hosting** (plan Turbo)
- **SiteGround** (plan GrowBig)

### KROK PO KROKU:

#### **KROK 1: Panel hostingowy**
1. Zaloguj się do cPanel
2. Wejdź w **"Setup Python App"**
3. Wybierz:
   - **Python Version:** 3.9+
   - **Application Root:** `/mp4_optimizer`
   - **Application URL:** `twoja-domena.com`

#### **KROK 2: Upload plików**
- Użyj **File Manager** w cPanel
- Upload pliki do katalogu `/mp4_optimizer`

#### **KROK 3: Instalacja FFmpeg**
W **Terminal** cPanel:
```bash
# Zależnie od hosta, może być dostępne:
apt install ffmpeg
# lub poproś support o instalację
```

#### **KROK 4: Konfiguracja**
- Ustaw **Application URL**
- Skonfiguruj **Start command**
- Dodaj **Environment variables**

---

## 🛡️ **OPCJA 5: Nginx Reverse Proxy (Production ready)**

### KROK PO KROKU:

#### **KROK 1: Instalacja Nginx**
```bash
sudo apt install nginx -y
```

#### **KROK 2: Konfiguracja Nginx**
```bash
sudo nano /etc/nginx/sites-available/mp4-optimizer
```

```nginx
upstream mp4_optimizer {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name twoja-domena.com;

    client_max_body_size 100M;
    client_body_timeout 300s;

    location / {
        proxy_pass http://mp4_optimizer;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias /home/mp4optimizer/mp4_optimizer/static/;
    }
}
```

#### **KROK 3: Włącz konfigurację**
```bash
sudo ln -s /etc/nginx/sites-available/mp4-optimizer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔐 **BEZPIECZEŃSTWO**

### **Zabezpiecz aplikację:**

#### **1. Limit wielkości upload**
```python
# W web_app.py już masz:
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
```

#### **2. Rate limiting**
```bash
pip install flask-limiter
```

```python
# W web_app.py dodaj:
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/upload', methods=['POST'])
@limiter.limit("10 per hour")
def upload_file():
    # existing code
```

#### **3. Clean temporary files**
```bash
# Dodaj cron job:
0 */6 * * * find /home/mp4optimizer/mp4_optimizer/uploads -mtime +1 -delete
0 */6 * * * find /home/mp4optimizer/mp4_optimizer/outputs -mtime +1 -delete
```

#### **4. Monitorowanie**
```bash
# Logi aplikacji
journalctl -u mp4-optimizer -f

# Logi Nginx
tail -f /var/log/nginx/error.log
```

---

## 🧪 **OPCJA 6: Testowanie przed użyciem**

### **Test lokalny:**
```bash
# Uruchom testowe encoding
python mp4_optimizer.py test_video.mp4 --preset med
```

### **Test przez web interface:**
1. Otwórz `http://twoje_ip:8080`
2. Upload małego pliku testowego
3. Sprawdź czy działa optymalizacja
4. Sprawdź console logi

### **Test wydajności:**
```bash
# Upload duży plik i sprawdź:
# - CPU usage
# - Memory usage  
# - Time to process
```

---

## 🚨 **TROUBLESHOOTING**

### **Problem: "FFmpeg not found"**
```bash
# Sprawdź instalację:
which ffmpeg
which ffprobe

# Zainstaluj jeśli brakuje:
apt install ffmpeg -y
```

### **Problem: "Permission denied"**
```bash
# Sprawdź uprawnienia do katalogów:
ls -la uploads/ outputs/ reports/

# Napraw uprawnienia:
chmod 755 uploads/ outputs/ reports/
```

### **Problem: "Service not starting"**
```bash
# Sprawdź logi:
sudo journalctl -u mp4-optimizer -n 50

# Sprawdź port:
netstat -tulpn | grep 8080
```

### **Problem: "Encoding too slow"**
```bash
# Zwiększ timeout w gunicorn_config.py:
timeout = 600  # 10 minut
```

---

## 📊 **MONITORING**

### **Podstawowe monitorowanie:**
```bash
# Status service
sudo systemctl status mp4-optimizer

# Zasoby systemowe
htop
df -h

# Logi aplikacji
tail -f /var/log/syslog
```

### **Zaawansowane monitorowanie:**
```bash
# Zainstaluj monitoring tools
pip install prometheus_flask_exporter
```

---

## 🎯 **REKOMENDACJA DLA CIEBIE**

**Najlepsza opcja dla początkującego:**
→ **Render.com** (PaaS, łatwy deployment, auto-scaling)

**Najlepsza opcja dla zaawansowanych:**
→ **VPS + Docker** (pełna kontrola, łatwy rollback)

**Najprostsza opcja:**
→ **cPanel hosting** (wszystko w panelu)

---

## 📝 **CHECKLISTA PRZED DEPLOYMENT**

### **Serwer:**
- [ ] VPS zakupiony i działa
- [ ] Dostęp przez SSH
- [ ] FFmpeg zainstalowany (`ffmpeg -version`)
- [ ] Python 3.6+ zainstalowany (`python3 --version`)

### **Aplikacja:**
- [ ] Pliki uploadowane na serwer
- [ ] Virtual environment utworzony
- [   ] Zależności zainstalowane (`pip list`)
- [ ] Foldery tworzone (`uploads/`, `outputs/`, `reports/`)
- [ ] Test lokalny działa

### **Konfiguracja:**
- [ ] Port otwarty w firewall
- [ ] Service działa (`systemctl status`)
- [ ] Autostart włączony
- [ ] Logi działają

### **Testy:**
- [ ] Web interface dostępny
- [ ] Upload działa
- [ ] Optymalizacja działa
- [ ] Download działa

---

**Jaki rodzaj hostingu preferujesz? Mogę Cię przeprowadzić przez konkretny opcję szczegółowo!**