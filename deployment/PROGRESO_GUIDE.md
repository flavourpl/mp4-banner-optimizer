# 🚀 PROGRESO.PL DEPLOYMENT - INSTRUKCJA KROK PO KROKU

## 🎯 SZYBKI START (2 metody)

### METODA 1: AUTOMATYCZNA (NAJPROSTSZA) ⭐
### METODA 2: MANUALNA PRZEZ FTP

---

## 🚀 METODA 1: AUTOMATYCZNA DEPLOYMENT

### KROK 1: Przygotuj dane serwera

Potrzebujesz tych informacji od Progreso.pl:
- **Username:** (np. `ars@p5001`)
- **Server:** (np. `p5001.progreso.pl`)
- **Ścieżka do katalogu głównego:** (np. `/public_html`)

### KROK 2: Edytuj skrypt uploadu

Otwórz plik: `deployment/upload_to_server.sh`

Znajdź te linie i edytuj:

```bash
SERVER_USER="twoj_username"              # 👈 ZMIEŃ TO
SERVER_HOST="twoj_serwer.com"            # 👈 ZMIEŃ TO  
SERVER_PATH="/public_html"               # 👈 ZMIEŃ TO (jeśli inne)
```

**Przykład:**
```bash
SERVER_USER="ars"
SERVER_HOST="p5001.progreso.pl"
SERVER_PATH="/public_html"
```

### KROK 3: Uruchom automatyczny upload

```bash
cd deployment
./upload_to_server.sh
```

**To zrobi wszystko automatycznie:**
- ✅ Wgra pliki na serwer
- ✅ Utworzy katalogi
- ✅ Ustawi permissions
- ✅ Zainstaluje FFmpeg
- ✅ Zainstaluje Python dependencies
- ✅ Sprawdzi poprawność deploymentu

### KROK 4: Uruchom aplikację

Po zakończeniu uploadu, skrypt Cię zapyta czy chcesz uruchomić aplikację. Jeśli tak, to zrobi to automatycznie!

Lub ręcznie:
```bash
ssh twoj_user@twoj_serwer.com
cd /public_html/deployment
./start_progreso.sh
```

### KROK 5: Testuj w przeglądarce

Otwórz: `http://twoja-domena.com:8080`

---

## 📁 METODA 2: MANUALNY UPLOAD PRZEZ FTP

### KROK 1: Przygotuj listę plików

Otwórz plik: `deployment/FILES_TO_UPLOAD.txt` - masz tam pełną listę plików do wgrania.

### KROK 2: Zaloguj się przez FTP

Użyj klienta FTP (np. FileZilla):

```
Host: twoja_domena.com
User: twoj_username  
Password: twoje_hasło
Port: 21
```

### KROK 3: Wgraj pliki

Wgryj w tej strukturze:

```
/public_html/
├── mp4_optimizer/          (cały folder)
│   ├── __init__.py
│   ├── encoder.py
│   ├── probe.py  
│   ├── ladder.py
│   ├── report.py
│   ├── config.py
│   ├── ffmpeg_config.py
│   ├── bitrate_calc.py
│   └── cli.py
├── templates/              (cały folder)
│   └── index.html
├── deployment/             (tylko te pliki)
│   ├── start_progreso.sh
│   ├── verify_deployment.py
│   └── check_deployment.sh
├── web_app_prod.py        (główny plik)
├── requirements.txt
├── uploads/               (utwórz pusty katalog)
├── outputs/               (utwórz pusty katalog)
└── reports/               (utwórz pusty katalog)
```

### KROK 4: Ustaw permissions

W kliencie FTP:
1. Kliknij prawym na `deployment/start_progreso.sh`
2. File permissions → `755`
3. Powtórz dla `deployment/check_deployment.sh`

### KROK 5: Zaloguj się przez SSH

```bash
ssh twoj_username@twoja_domena.com
```

### KROK 6: Uruchom sprawdzenie

```bash
cd /public_html  # lub inny katalog główny
bash deployment/check_deployment.sh
```

To Ci powie co jest missing lub wrong.

### KROK 7: Zainstaluj FFmpeg (jeśli potrzeba)

```bash
mkdir -p ~/bin
cd ~
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xf ffmpeg-release-amd64-static.tar.xz
mv ffmpeg-*/ffmpeg ~/bin/ffmpeg
mv ffmpeg-*/ffprobe ~/bin/ffprobe
chmod +x ~/bin/ffmpeg ~/bin/ffprobe
rm -rf ffmpeg-*.tar.xz ffmpeg-*

# Test
~/bin/ffmpeg -version
```

### KROK 8: Zainstaluj Python dependencies

```bash
pip3 install --user Flask Werkzeug
```

### KROK 9: Uruchom aplikację

```bash
cd deployment
./start_progreso.sh
```

### KROK 10: Testuj

Otwórz: `http://twoja-domena.com:8080`

---

## 🎛️ PO URUCHOMIENIU

### Aplikacja powinna:

1. **Startować na porcie 8080**
2. **Pokazywać interfejs webowy** 
3. **Przyjmować pliki MP4**
4. **Optymalizować do wybranych rozmiarów**
5. **Generować raporty JSON**

### Testuj aplikację:

1. **Upload testowy:**
   - Kliknij "Choose File"
   - Wybierz mały plik MP4 (< 100KB)
   - Kliknij "Upload & Optimize"

2. **Opcje:**
   - Target size: 400KB (default)
   - Keep audio: unchecked (default)
   - Fit mode: crop (default)

3. **Wynik:**
   - Pojawia się progress bar
   - Po zakończeniu można pobrać plik
   - Raport JSON dostępny

---

## 🛠️ TROUBLESHOOTING

### "Cannot connect to server"

```bash
# Sprawdź dane połączenia
ssh twoj_user@twoj_host.com

# Jeśli nie działa, sprawdź:
# - Username jest poprawny
# - Host/address jest poprawny  
# - Masz dostęp SSH (nie tylko FTP)
```

### "FFmpeg not found"

```bash
# Sprawdź czy jest zainstalowane
~/bin/ffmpeg -version

# Jeśli nie, zainstaluj ponownie
cd ~
mkdir -p bin
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xf ffmpeg-release-amd64-static.tar.xz
mv ffmpeg-*/ffmpeg ~/bin/ffmpeg
mv ffmpeg-*/ffprobe ~/bin/ffprobe
chmod +x ~/bin/ffmpeg ~/bin/ffprobe
```

### "Port 8080 already in use"

```bash
# Sprawdź co używa portu
netstat -tuln | grep 8080

# Użyj innego portu
export PORT=8081
cd deployment
./start_progreso.sh
```

### "Permission denied"

```bash
# Ustaw permissions
chmod 755 uploads outputs reports
chmod +x deployment/start_progreso.sh
```

### "Flask not installed"

```bash
pip3 install --user Flask Werkzeug
```

### Application not working in browser

```bash
# Sprawdź czy aplikacja działa
ps aux | grep web_app_prod

# Sprawdź logi
tail optimizer.log

# Restart
cd deployment
./start_progreso.sh
```

---

## 🔄 CZYSZCZENIE I MAINTENANCE

### Automaticzne czyszczenie:

Aplikacja automatycznie usuwa pliki starsze niż 1 godzinę.

### Manualne czyszczenie:

```bash
# Wyczyść stare pliki
rm uploads/* outputs/* reports/*

# Sprawdź miejsce na dysku
df -h
```

### Restart aplikacji:

```bash
# Znajdź proces
ps aux | grep web_app_prod

# Zatrzymaj
kill <PID>

# Uruchom ponownie
cd deployment
./start_progreso.sh
```

---

## 📊 MONITORING

### Sprawdź czy działa:

```bash
# Health check
curl http://localhost:8080/health

# Statystyki
curl http://localhost:8080/stats
```

### Logi aplikacji:

```bash
# Jeśli uruchomione w tle
tail -f optimizer.log

# Jeśli uruchomione bezpośrednio
# Output jest w terminalu
```

---

## 🎉 SUKCES!

Jeśli dotarłeś do tego momentu i aplikacja działa:

**🚀 Gratulacje! Twoj MP4 Banner Optimizer jest online!**

Możesz teraz:
- Optymalizować wideo dla reklam
- Redukować rozmiary plików
- Automatyzować workflow
- Integrować z innymi systemami

---

## 📞 POMOC

Jeśli coś nie działa:

1. **Uruchom check_deployment.sh:**
   ```bash
   bash deployment/check_deployment.sh
   ```

2. **Sprawdź logi:**
   ```bash
   tail optimizer.log
   ```

3. **Skontaktuj się z supportem Progreso.pl** jeśli:
   - Nie masz dostępu SSH
   - Nie możesz zainstalować FFmpeg
   - Port 8080 jest zablokowany

---

## 🔝 DALEJ OPCJE

### Uruchomienie w tle (production):

```bash
cd deployment
nohup ./start_progreso.sh > ../optimizer.log 2>&1 &
```

### Auto-start przy restarcie:

Dodaj do crontab:
```bash
crontab -e
```

Dodaj:
```
@reboot cd /public_html/deployment && ./start_progreso.sh
```

---

**Powodzenia! 🚀**