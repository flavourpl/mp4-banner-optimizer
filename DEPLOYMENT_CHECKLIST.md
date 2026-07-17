# ✅ DEPLOYMENT CHECKLIST - PROGRESO.PL

## 🎋 USEJ TEJ LISTY KROK PO KROKU

---

## 📋 PRZED DEPLOYMENTEM

### Dane które potrzebujesz:

- [ ] **SSH Username:** `______________________`
- [ ] **Server address:** `______________________`  
- [ ] **Main directory:** `______________________`
- [ ] **Domain name:** `______________________`
- [ ] **SSH working?** (test: `ssh user@server`)

### Gdzie znaleźć te dane?

1. Zaloguj do panelu Progreso.pl
2. Wejdź w "Hosting" → "Twoje konto"
3. Znajdź sekcję "Dane SSH" lub "FTP"

---

## 🚀 DEPLOYMENT - AUTOMATYCZNA METODA

### Krok 1: Przygotowanie

- [ ] Otwórz `deployment/upload_to_server.sh`
- [ ] Edytuj linie 12-14:
  ```bash
  SERVER_USER="twoj_username"      
  SERVER_HOST="twoj_serwer.com"     
  SERVER_PATH="/public_html"        
  ```
- [ ] Zapisz plik

### Krok 2: Uruchomienie

- [ ] Otwórz terminal
- [ ] Idź do deployment: `cd deployment`
- [ ] Uruchom: `./upload_to_server.sh`
- [ ] Czekaj na zakończenie (~5-10 min)

### Krok 3: Weryfikacja

- [ ] Czy nie było błędów podczas uploadu?
- [ ] Czy FFmpeg został zainstalowany?
- [ ] Czy Python dependencies zostały zainstalowane?

---

## 📁 DEPLOYMENT - MANUALNA METODA

### Krok 1: Przygotowanie plików

- [ ] Otwórz `deployment/FILES_TO_UPLOAD.txt`
- [ ] Przejrzyj listę plików do wgrania
- [ ] Przygotuj klienta FTP (FileZilla, Cyberduck)

### Krok 2: Upload przez FTP

- [ ] Zaloguj się przez FTP
- [ ] Wgraj katalog `mp4_optimizer/`
- [ ] Wgraj katalog `templates/`
- [ ] Wgraj pliki z `deployment/`:
  - [ ] `start_progreso.sh`
  - [ ] `verify_deployment.py`
  - [ ] `check_deployment.sh`
- [ ] Wgraj `web_app_prod.py`
- [ ] Wgraj `requirements.txt`
- [ ] Utwórz puste katalogi: `uploads/`, `outputs/`, `reports/`

### Krok 3: Permissions

- [ ] Ustaw `755` dla `deployment/start_progreso.sh`
- [ ] Ustaw `755` dla `deployment/check_deployment.sh`

---

## 🔧 KONFIGURACJA NA SERWERZE

### Krok 1: Połączenie

- [ ] Zaloguj się przez SSH: `ssh user@server`
- [ ] Idź do katalogu: `cd /public_html`

### Krok 2: Sprawdzenie

- [ ] Uruchom: `bash deployment/check_deployment.sh`
- [ ] Przejrzyj wyniki
- [ ] Napraw ewentualne błędy

### Krok 3: FFmpeg

- [ ] Sprawdź czy FFmpeg działa: `~/bin/ffmpeg -version`
- [ ] Jak nie, zainstaluj:
  ```bash
  mkdir -p ~/bin
  cd ~
  wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
  tar xf ffmpeg-release-amd64-static.tar.xz
  mv ffmpeg-*/ffmpeg ~/bin/ffmpeg
  mv ffmpeg-*/ffprobe ~/bin/ffprobe
  chmod +x ~/bin/ffmpeg ~/bin/ffprobe
  ```

### Krok 4: Python dependencies

- [ ] Sprawdź Python: `python3 --version`
- [ ] Zainstaluj dependencies: `pip3 install --user Flask Werkzeug`

---

## 🚀 URUCHAMIANIE

### Start aplikacji:

- [ ] Idź do deployment: `cd deployment`
- [ ] Uruchom: `./start_progreso.sh`
- [ ] Czekaj na komunikat "Starting MP4 Banner Optimizer"
- [ ] Sprawdź czy nie ma błędów

### Alternatywne uruchomienie:

- [ ] W tle: `nohup ./start_progreso.sh > ../optimizer.log 2>&1 &`
- [ ] Z innym portem: `export PORT=8081 && ./start_progreso.sh`

---

## 🧪 TESTOWANIE

### Test 1: Health check

- [ ] Otwórz przeglądarkę
- [ ] Wejdź: `http://twoja-domena.com:8080/health`
- [ ] Powinieneś zobaczyć: `{"status": "healthy"}`

### Test 2: Web interface

- [ ] Otwórz: `http://twoja-domena.com:8080`
- [ ] Powinieneś zobaczyć interfejs MP4 Banner Optimizer
- [ ] Sprawdź czy są pola: upload, target size, options

### Test 3: Upload testowy

- [ ] Przygotuj mały plik MP4 (< 100KB)
- [ ] Kliknij "Choose File"
- [ ] Wybierz testowy plik
- [ ] Kliknij "Upload & Optimize"
- [ ] Czekaj na progress bar
- [ ] Sprawdź czy plik został pobrany

### Test 4: Pełna optymalizacja

- [ ] Wgraj większy plik MP4 (~500KB)
- [ ] Ustaw target size: 400KB
- [ ] Kliknij "Optimize"
- [ ] Czekaj na zakończenie
- [ ] Pobierz zoptymalizowany plik
- [ ] Sprawdź rozmiar (czy ~400KB)

---

## 🔍 TROUBLESHOOTING

### Jak coś nie działa:

- [ ] **Sprawdź logi:** `tail optimizer.log`
- [ ] **Sprawdź proces:** `ps aux | grep web_app_prod`
- [ ] **Sprawdź port:** `netstat -tuln | grep 8080`
- [ ] **Sprawdź FFmpeg:** `~/bin/ffmpeg -version`
- [ ] **Sprawdź Python:** `python3 --version`
- [ ] **Uruchom check:** `bash deployment/check_deployment.sh`

---

## 🎉 PO DEPLOYMENT

### Aplikacja działa gdy:

- [ ] Web interface jest dostępny
- [ ] Upload plików działa
- [ ] Optymalizacja działa
- [ ] Download plików działa
- [ ] Raporty JSON generują się

### Maintenance:

- [ ] **Sprawdzaj miejsce:** `df -h`
- [ ] **Czyść foldery:** `rm uploads/* outputs/* reports/*`
- [ ] **Monitoruj logi:** `tail -f optimizer.log`
- [ ] **Restart jak potrzeba:** `cd deployment && ./start_progreso.sh`

---

## 📞 SUPPORT

### Jak potrzebujesz pomocy:

1. **Sprawdź logi:** `tail optimizer.log`
2. **Uruchom check:** `bash deployment/check_deployment.sh`
3. **Przeczytaj guides:**
   - `QUICK_START.md`
   - `deployment/PROGRESO_GUIDE.md`
4. **Skontaktuj z supportem Progreso.pl** (jak problemy z serwerem)

---

## 🏁 KONIEC

### Jak wszystkie checkboxy są checked:

**🎉 GRATULACJE! Twoj MP4 Banner Optimizer jest online!**

### Co dalej:

- [ ] Przetestuj z prawdziwymi plikami
- [ ] Zintegruj z workflow
- [ ] Monitoruj performance
- [ ] Optymalizuj ustawienia

---

**🚀 Powodzenia w deployment!**