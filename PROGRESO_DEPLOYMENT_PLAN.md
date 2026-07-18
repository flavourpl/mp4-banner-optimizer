# Kompleksowy Plan Wdrożenia na Progreso.pl

## Aktualna Sytuacja - Analiza Problemów

### ✅ Działa
- Aplikacja Flask lokalnie na porcie 5000
- FFmpeg video processing
- Wszystkie funkcje aplikacji
- Dostęp przez IP: `http://77.65.215.8:5000`

### ❌ Nie działa  
- Dostęp przez domenę `https://vid.flavour.pl`
- ProxyPass w `.htaccess`
- Passenger WSGI
- FastCGI
- Przekierowania HTML/JS

### 🚫 Ograniczenia Progreso.pl
- **Reverse proxy ignoruje .htaccess**
- **Porty tylko 443/444/445 (SSL)** 
- **Brak Passenger na koncie użytkownika**
- **Brak konfiguracji proxy w panelu**
- **"Inne Skrypty: TAK" niewystarczające**

---

## Opcje Wdrożenia - Od Najlepszej do Najgorszej

## OPCJA 1: PHP Bridge Application ⭐⭐⭐⭐⭐
**Najbardziej wykonalne rozwiązanie**

### Koncepcja
Stwórz lekką aplikację PHP która będzie proxywać requesty do Python backend.

### Architektura
```
Browser → HTTPS:443 → Progreso Proxy → index.php → HTTP:5000 → Flask App
```

### Implementacja

**1. PHP Bridge (`index.php`):**
```php
<?php
// MP4 Banner Optimizer - PHP Bridge
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle OPTIONS preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Determine target endpoint
$method = $_SERVER['REQUEST_METHOD'];
$path = $_SERVER['REQUEST_URI'];
$backend_url = 'http://127.0.0.1:5000';

// Strip query string and rebuild path
$request_path = parse_url($path, PHP_URL_PATH);
$target_url = $backend_url . $request_path;
if (!empty($_SERVER['QUERY_STRING'])) {
    $target_url .= '?' . $_SERVER['QUERY_STRING'];
}

// Initialize cURL
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $target_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 300); // 5 minutes for video processing

// Handle POST requests
if ($method === 'POST') {
    curl_setopt($ch, CURLOPT_POST, true);
    
    // Handle file uploads
    if (isset($_FILES['file'])) {
        $file = $_FILES['file'];
        $postFields = [];
        
        // Add file
        $postFields['file'] = new CURLFile(
            $file['tmp_name'],
            $file['type'],
            $file['name']
        );
        
        // Add form fields
        foreach ($_POST as $key => $value) {
            $postFields[$key] = $value;
        }
        
        curl_setopt($ch, CURLOPT_POSTFIELDS, $postFields);
    } else {
        // Regular POST data
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($_POST));
    }
}

// Execute request
$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$content_type = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
curl_close($ch);

// Set response headers
if ($content_type) {
    header("Content-Type: $content_type");
}

http_response_code($http_code);
echo $response;
?>
```

**2. Start script (`start_bridge.sh`):**
```bash
#!/bin/bash
cd ~/mp4-video-banner-optimizer

# Start Flask backend
PORT=5000 nohup python3 web_app_prod.py > optimizer.log 2>&1 &

# Wait for backend to start
sleep 3

# Verify backend is running
if curl -s http://127.0.0.1:5000/api/presets > /dev/null; then
    echo "✅ Backend started successfully"
    echo "🌐 Application available at: https://vid.flavour.pl"
else
    echo "❌ Backend failed to start"
    exit 1
fi
```

**3. Frontend update (`templates/index.html`):**
```html
<!-- Update API endpoints to use current domain -->
<script>
const API_BASE = window.location.origin + '/api/';
// Instead of hardcoded URLs
</script>
```

### Zalety
- ✅ **Najwyższa szansa powodzenia** - PHP działa na Progreso
- ✅ **Pełna funkcjonalność** - wszystkie requesty przez PHP bridge
- ✅ **Bez zmian w panelu** - używa istniejącej konfiguracji
- ✅ **Easy rollback** - można szybko wrócić do obecnej wersji
- ✅ **File upload support** - PHP handle uploads dobrze

### Wady
- ⚠️ **Dodatkowa warstwa** - PHP jako proxy
- ⚠️ **Debugging bardziej skomplikowany**

### Implementacja time: 2-3 godziny

---

## OPCJA 2: External Proxy Service ⭐⭐⭐⭐

### Koncepcja
Użyj zewnętrznego proxy (Cloudflare/Nginx) przed domeną Progreso.

### Architektura
```
Browser → Cloudflare → vid.flavour.pl:443 → Progreso → Static files
Browser → Cloudflare → app.vid.flavour.pl → Direct IP:5000 → Flask App
```

### Implementacja

**1. Subdomain setup:**
- Stwórz subdomenę `app.vid.flavour.pl`
- Skieruj na `77.65.215.8:5000`
- Użyj Cloudflare jako proxy

**2. Alternatywa - ngrok tunnel:**
```bash
# Na serwerze
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

ngrok http 5000
```

### Zalety
- ✅ **Bez zmian na Progreso**
- ✅ **Pełna kontrola nad proxy**
- ✅ **SSL przez Cloudflare**

### Wady
- ⚠️ **Wymaga zewnętrznej usługi**
- ⚠️ **Zależność od third-party**
- ⚠️ **Potencjalne koszty**

---

## OPCJA 3: Contact Progreso Support ⭐⭐⭐

### Pytania do supportu

**1. Pytania techniczne:**
```
- Jak skonfigurować proxy dla aplikacji Python?
- Czy jest możliwa własna konfiguracja Apache vhost?
- Jakie są dokładnie ograniczenia "Inne Skrypty: TAK"?
- Czy można dodać custom ProxyPass/ProxyReverse directives?
- Czy jest możliwość użycia Passenger na tym koncie?
```

**2. Prośba o konfigurację:**
```
Proszę o skonfigurowanie reverse proxy dla domeny vid.flavour.pl:
- Backend: http://127.0.0.1:5000
- Frontend: https://vid.flavour.pl
- Protocol: HTTP proxy for HTTPS frontend
```

### Oczekiwane odpowiedzi
- ✅ **Konfiguracja możliwa** - support może to zrobić
- ⚠️ **Ograniczenia stałe** - potrzeba innych rozwiązań  
- ❌ **Niemożliwe** - trzeba zmienić hosting

---

## OPCJA 4: Node.js Alternative ⭐⭐⭐

### Koncepcja
Przepisz backend na Node.js który może działać jako FastCGI.

### Architektura
```
Browser → HTTPS:443 → Apache → FastCGI → Node.js → FFmpeg
```

### Implementacja

**1. Package.json:**
```json
{
  "name": "mp4-optimizer",
  "main": "server.js",
  "dependencies": {
    "express": "^4.18.2",
    "fluent-ffmpeg": "^2.1.2",
    "multer": "^1.4.5-lts.1"
  }
}
```

**2. Server.js:**
```javascript
const express = require('express');
const ffmpeg = require('fluent-ffmpeg');
const multer = require('multer');
const upload = multer({ dest: 'uploads/' });

const app = express();
app.use(express.json());
app.use(express.static('public'));

// Copy logic from Python to Node.js
// API endpoints, video processing, etc.
```

**3. FastCGI setup:**
```bash
# Install dependencies
npm install

# Start with FastCGI
 PORT=5000 node server.js
```

### Zalety
- ✅ **Node.js może działać jako FastCGI**
- ✅ **Mniejsze ograniczenia niż Python**

### Wady
- ⚠️ **Dużo pracy** - przepisanie całej aplikacji
- ⚠️ **FFmpeg integration bardziej skomplikowane**
- ⚠️ **Time investment**

---

## OPCJA 5: Complete Architecture Change ⭐⭐

### Koncepcja
Przenieś aplikację na microservices architecture.

### Architektura
```
Frontend (Progreso) → API calls → External Server → Processing → Results
```

### Implementacja
1. Progreso hostuje tylko frontend (HTML/JS)
2. External API server (np. Heroku/Railway/AWS)
3. Asynchronous video processing
4. WebSocket dla progress updates

### Zalety
- ✅ **Brak ograniczeń hostingu**
- ✅ **Skalowalność**

### Wady
- ⚠️ **Koszty zewnętrzne**
- ⚠️ **Skomplikowana architektura**
- ⚠️ **Latency**

---

## OPCJA 6: Hosting Migration ⭐⭐⭐⭐⭐

### Koncepcja
Przenieś na hosting z lepszą obsługą Python/Aplikacji.

### Opcje hostingu

**1. DigitalOcean ($6-12/mies):**
```bash
# VPS z pełną kontrolą
- Ubuntu 22.04
- Nginx reverse proxy
- Python 3.10+
- FFmpeg pre-installed
- Full .htaccess/apache config support
```

**2. Heroku (Free/$5-7/mies):**
```bash
# PaaS z pełną obsługą Python
- git push heroku main
- Automatic SSL
- Built-in proxy
- Easy FFmpeg buildpacks
```

**3. Railway ($5-10/mies):**
```bash
# Modern PaaS
- GitHub integration
- Automatic deployment
- FFmpeg support
- Good Python support
```

**4. VPS.ps ($5-10/mies):**
```bash
# Polska firma hostingowa
- Lokalizacja PL
- Pełna kontrola
- FFmpeg available
- Polish support
```

### Migration plan
```bash
# 1. Export database/files
rsync -av ~/mp4-video-banner-optimizer/ user@newhost:/var/www/

# 2. Configure Nginx reverse proxy
sudo nano /etc/nginx/sites-available/vid.flavour.pl

# 3. Setup SSL
sudo certbot --nginx -d vid.flavour.pl

# 4. Start application
PORT=5000 python3 web_app_prod.py
```

### Zalety
- ✅ **Pełna funkcjonalność**
- ✅ **Brak ograniczeń**
- ✅ **Professional setup**
- ✅ **Skalowalność**

### Wady
- ⚠️ **Koszty migracji**
- ⚠️ **Konfiguracja DNS**

---

## REKOMENDACJA - Priority Order

### 🥇 PRIORYTET 1: PHP Bridge Application
**Najlepsze rozwiązanie obecnej sytuacji**
- Czas implementacji: 2-3 godziny
- Szansa powodzenia: 90%
- Koszt: $0
- Wymagane: PHP na Progreso (prawdopodobnie dostępne)

### 🥈 PRIORYTET 2: Contact Progreso Support  
**Warto spróbować przed implementacją**
- Czas: 15 minut
- Szansa powodzenia: 40%
- Koszt: $0

### 🥉 PRIORYTET 3: Hosting Migration
**Długoterminowe rozwiązanie**
- Czas: 1-2 dni
- Szansa powodzenia: 100%
- Koszt: $5-12/mies

---

## Implementation Plan - PHP Bridge (Recommended)

### Faza 1: Preparation (30 min)
```bash
# 1. Test PHP availability
php -v
php -m | grep curl

# 2. Backup working version
cp web_app_prod.py web_app_prod.py.backup
cp -r templates templates.backup

# 3. Create PHP bridge
nano index.php
```

### Faza 2: Implementation (1 godz)
```bash
# 1. Create PHP bridge file
# (wklej kod PHP z opcji 1)

# 2. Update frontend API endpoints
# (modyfikuj templates/index.html)

# 3. Test locally
php -S localhost:8000
curl http://localhost:8000/api/presets
```

### Faza 3: Deployment (30 min)
```bash
# 1. Upload via FTP
python3 deployment/ftp_upload.py

# 2. Start services on server
ssh ars@flavour.civ.pl
cd ~/mp4-video-banner-optimizer
chmod +x start_bridge.sh
./start_bridge.sh

# 3. Verify deployment
curl -v https://vid.flavour.pl/
curl https://vid.flavour.pl/api/presets
```

### Faza 4: Testing (30 min)
```bash
# 1. Test file upload
# 2. Test video processing
# 3. Test download
# 4. Test progress tracking
```

### Faza 5: Documentation (15 min)
```bash
# Update AGENTS.md with PHP bridge startup
# Update README_DEPLOYMENT.md with new architecture
```

---

## Ryzyka i Mitigation

### Ryzyko 1: PHP nie dostępne na Progreso
**Mitigation:** Test availability przed implementacją

### Ryzyko 2: cURL upload problems  
**Mitigation:** Test with various file sizes

### Ryzyko 3: Performance issues
**Mitigation:** Monitor response times, optimize if needed

### Ryzyko 4: Security concerns
**Mitigation:** Add authentication, validate uploads

---

## Summary

**Najlepsza opcja: PHP Bridge Application**
- Minimal changes to existing code
- High success probability  
- Zero additional cost
- Quick implementation (2-3 hours)

**Alternatywa długoterminowa: Hosting Migration**
- Complete control
- Professional setup  
- Better scalability
- $5-12/miesięcznie

**Działania natychmiastowe:**
1. Contact Progreso support (15 min)
2. Test PHP availability (5 min)  
3. Implement PHP bridge (2-3 godz)

Czy chcesz żeby zaimplementować opcję PHP Bridge?