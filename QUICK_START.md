# 🚀 SZYBKI START - DEPLOYMENT NA PROGRESO.PL

## 👈 CO MUSISZ ZROBIĆ (3 kroki):

### 1️⃣ WYBIERZ METODĘ

**OPCJA A: Automatyczna (najprostsza)** - 1 komenda
**OPCJA B: Manualna przez FTP** - kontrola nad każdym plikiem

---

## 🎯 OPCJA A: AUTOMATYCZNA DEPLOYMENT

### KROK 1: Edytuj jedną linijkę

Otwórz: `deployment/upload_to_server.sh`

Znajdź i zmień te 3 linie:

```bash
SERVER_USER="twoj_username"      # 👈 ZMIEŃ
SERVER_HOST="twoj_serwer.com"     # 👈 ZMIEŃ  
SERVER_PATH="/public_html"        # 👈 ZMIEŃ (jeśli inne)
```

**Przykład dla Twojego serwera:**
```bash
SERVER_USER="ars"                 # ✅ Twoj username
SERVER_HOST="p5001.progreso.pl"   # ✅ Twoj serwer
SERVER_PATH="/public_html"        # ✅ Główny katalog
```

### KROK 2: Uruchom jedną komendę

```bash
cd deployment
./upload_to_server.sh
```

### KROK 3: Gotowe!

Skrypt zrobi wszystko:
- ✅ Wgra wszystkie pliki
- ✅ Zainstaluje FFmpeg  
- ✅ Ustawi permissions
- ✅ Zainstaluje Python deps
- ✅ Uruchomi aplikację

**Otwórz w przeglądarce:** `http://twoja-domena.com:8080`

---

## 📁 OPCJA B: MANUALNY FTP

### KROK 1: Lista plików

Otwórz: `deployment/FILES_TO_UPLOAD.txt` - pełna lista plików do wgrania.

### KROK 2: Wgraj przez FTP

**Struktura:**
```
/public_html/
├── mp4_optimizer/          (cały folder)
├── templates/              (cały folder)  
├── deployment/             (3 pliki)
├── web_app_prod.py
├── requirements.txt
├── uploads/ (pusty)
├── outputs/ (pusty)
└── reports/ (pusty)
```

### KROK 3: SSH na serwer

```bash
ssh twoj_user@twoj_serwer.com
cd /public_html
```

### KROK 4: Uruchom check

```bash
bash deployment/check_deployment.sh
```

### KROK 5: Zainstaluj FFmpeg (jeśli potrzeba)

```bash
mkdir -p ~/bin
cd ~
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xf ffmpeg-release-amd64-static.tar.xz  
mv ffmpeg-*/ffmpeg ~/bin/ffmpeg
mv ffmpeg-*/ffprobe ~/bin/ffprobe
chmod +x ~/bin/ffmpeg ~/bin/ffprobe
```

### KROK 6: Uruchom

```bash
cd deployment
./start_progreso.sh
```

---

## 🔐 DANE KTÓRE POTRZEBUJESZ

### Od Progreso.pl:

1. **Username SSH** (np. `ars@p5001`)
2. **Server address** (np. `p5001.progreso.pl`)
3. **Main directory path** (np. `/public_html`)
4. **Domain** (np. `twoja-domena.com`)

### Jak znaleźć te dane?

1. **Zaloguj do panelu Progreso.pl**
2. **Wejdź w "Hosting" → "Twoje konto"**
3. **Znajdź sekcję "Dane SSH"**

---

## ⏱️ CZAS TRWANIA

### Automatyczna metoda: ~5-10 minut
- Upload: 2-3 minuty
- Instalacja FFmpeg: 3-5 minut
- Konfiguracja: 1 minuta

### Manualna metoda: ~15-20 minut  
- Upload przez FTP: 5-10 minut
- Konfiguracja SSH: 5-8 minut
- Instalacja dependencies: 2-3 minuty

---

## 🎯 PO DEPLOYMENT

### Testuj aplikację:

1. **Otwórz:** `http://twoja-domena.com:8080`
2. **Wgraj testowy plik MP4** (mały, < 100KB)
3. **Wybierz opcje** (400KB, no audio, crop)
4. **Kliknij "Optimize"**
5. **Poczekaj** 5-10 sekund
6. **Pobierz zoptymalizowany plik**

### Jeśli działa:

✅ **Gratulacje!** Aplikacja jest online!

### Jeśli nie działa:

**Sprawdź:**
1. **Czy FFmpeg działa:** `~/bin/ffmpeg -version`
2. **Czy Python działa:** `python3 --version`  
3. **Czy aplikacja działa:** `ps aux | grep web_app_prod`
4. **Logi:** `tail optimizer.log`

---

## 🆘 PROBLEMY?

### "Nie mogę się połączyć przez SSH"

**Rozwiązanie:**
- Sprawdź dane połączenia (username, host)
- Upewnij się że masz dostęp SSH (nie tylko FTP)
- Skontaktuj się z supportem Progreso.pl

### "FFmpeg nie działa"

**Rozwiązanie:**
```bash
~/bin/ffmpeg -version
# Jak wywali błąd, zainstaluj ponownie
cd ~ && mkdir -p bin
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xf ffmpeg-release-amd64-static.tar.xz
mv ffmpeg-*/ffmpeg ~/bin/ffmpeg && mv ffmpeg-*/ffprobe ~/bin/ffprobe
chmod +x ~/bin/ffmpeg ~/bin/ffprobe
```

### "Port 8080 zajęty"

**Rozwiązanie:**
```bash
# Użyj innego portu
export PORT=8081
cd deployment && ./start_progreso.sh
```

---

## 📞 KONTAKT

Jeśli coś nie działa:

1. **Uruchom check_deployment.sh** - powie co jest nie tak
2. **Sprawdź logi** - `tail optimizer.log`
3. **Skontaktuj z supportem Progreso.pl** - jak masz problemy z dostępem

---

## 🎉 JESTEŚ GOTOWY!

**Wybierz metodę i zaczynaj:**

### Automatyczna:
```bash
cd deployment
# Edytuj upload_to_server.sh
./upload_to_server.sh
```

### Manualna:
```bash
# Otwórz deployment/FILES_TO_UPLOAD.txt
# Wgraj pliki przez FTP
# Zaloguj przez SSH
bash deployment/check_deployment.sh
cd deployment && ./start_progreso.sh
```

---

**🚀 Powodzenia! Twoj MP4 Banner Optimizer czeka na deployment!**