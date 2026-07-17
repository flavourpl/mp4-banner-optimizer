# MP4 Banner Optimizer - Web Interface

Nowy webowy interfejs dla mp4-banner-optimizer! 🎉

## 🚀 Szybki Start

### 1. Zainstaluj zależności

```bash
pip install Flask Werkzeug
```

Lub z requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Uruchom aplikację

```bash
python web_app.py
```

### 3. Otwórz przeglądarkę

```
http://localhost:5000
```

## ✨ Funkcje

### 📁 Upload
- **Drag & Drop** plików MP4
- Wsparcie dla plików do 100MB
- Walidacja formatu
- Podgląd wybranego pliku

### ⚙️ Opcje optymalizacji
- **Presety**: LOW (400KB), MED (450KB), HIGH (500KB)
- **Custom size**: własny limit w KB
- **Aspect ratio**: Crop, Pad, Stretch
- **Audio**: usuń lub zachowaj ścieżkę audio

### 📊 Podgląd na żywo
- **Progress bar** z procentami
- **Aktualny krok** optymalizacji
- **Podgląd wideo**: przed i po
- **Statystyki**: redukcja rozmiaru, rozdzielczość

### 📥 Download
- **Pobierz wideo**: zoptymalizowany plik MP4
- **Pobierz raport**: szczegółowy JSON z historią kroków
- **Historia iteracji**: pełna ścieżka optymalizacji

## 🎯 Użycie

### Podstawowe użycie

1. **Wybierz plik** - kliknij lub drag & drop
2. **Wybierz preset** - LOW/MED/HIGH lub własny rozmiar
3. **Konfiguruj opcje** - tryb dopasowania, audio
4. **Start** - kliknij "Start Optimization"
5. **Obserwuj postęp** - progress bar i aktualne kroki
6. **Pobierz wynik** - zoptymalizowane wideo + raport

### Przykłady

#### Baner HTML5 (standardowy)
```
Preset: MED (450 KB)
Fit mode: Crop
Audio: Usuń
```

#### Baner z dźwiękiem
```
Preset: HIGH (500 KB)
Fit mode: Crop
Audio: Zachowaj
```

#### Minimalny rozmiar
```
Custom size: 350 KB
Fit mode: Pad (zachowaj zawartość)
Audio: Usuń
```

## 🏗️ Architektura

### Backend (Flask)
- **`web_app.py`** - główna aplikacja Flask
- **`templates/index.html`** - frontend UI
- **Background threads** - optymalizacja asynchroniczna
- **In-memory jobs** - śledzenie statusu

### Endpointy API

#### `GET /`
Główna strona aplikacji

#### `GET /api/presets`
Pobierz dostępne presety

#### `GET /api/resolutions`
Pobierz dostepne rozdzielczości

#### `POST /api/upload`
Upload pliku i start optymalizacji
- **Form data**: file, preset, max_kb, fit_mode, keep_audio, resolution_ladder
- **Returns**: job_id

#### `GET /api/status/<job_id>`
Sprawdź status optymalizacji
- **Returns**: status, progress, current_step, source_info, result

#### `GET /api/download/<job_id>`
Pobierz zoptymalizowane wideo

#### `GET /api/report/<job_id>`
Pobierz raport JSON

## 🎨 UI Features

### Drag & Drop Upload
- Wizualne wsparcie drag & drop
- Podświetlenie podczas przeciągania
- Walidacja formatu MP4

### Progress Tracking
- **Pasek postępu** - animowany progress bar
- **Procenty** - dokładny procent ukończenia
- **Aktualny krok** - co dzieje się teraz
- **Aktualizacja co 1s** - real-time status

### Results Display
- **Sukces** - zielona sekcja z wynikami
- **Ostrzeżenie** - żółta sekcja (best effort)
- **Błąd** - czerwona sekcja z komunikatem

### Video Preview
- **Original vs Optimized** - porównanie side-by-side
- **Autoplay** - automatyczne odtwarzanie
- **Controls** - pełna kontrola odtwarzania
- **Muted** - wyciszone (dla autoplay)

### Iterations History
- **Lista kroków** - pełna historia
- **Rozmiary** - rozmiar po każdym kroku
- **Target bitrate** - planowany bitrate
- **Scrollable** - dla długich historii

## 🔧 Konfiguracja

### Backend options (w `web_app.py`)

```python
# Maksymalny rozmiar uploadu
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Foldery
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['REPORT_FOLDER'] = 'reports'
```

### Port i host

```python
# Domyślne: localhost:5000
app.run(debug=True, host='0.0.0.0', port=5000)

# Production (bez debug mode)
app.run(debug=False, host='0.0.0.0', port=80)
```

## 📝 Statusy Job

### pending
Job utworzony, czeka na processing

### running
Optymalizacja w toku
- Progress bar aktywny
- Aktualizacje co 1s

### completed
Optymalizacja zakończona
- Wyniki dostępne
- Pliki gotowe do download

### failed
Błąd optymalizacji
- Komunikat błędu
- Szczegóły w logach

## 🐛 Troubleshooting

### "Failed to upload"
- Sprawdź rozmiar pliku (max 100MB)
- Upewnij się że to MP4
- Sprawdź uprawnienia folderów

### "Optimization failed"
- Sprawdź czy ffmpeg jest zainstalowany
- Upewnij się że plik źródłowy jest poprawny
- Sprawdź logi serwera

### "Progress stuck"
- Odśwież stronę
- Sprawdź czy backend działa
- Sprawdź console w przeglądarce

### "Video not playing"
- Upewnij się że optymalizacja się zakończyła
- Sprawdź czy plik wyjściowy istnieje
- Spróbuj innej przeglądarki

## 🚀 Production Deployment

### Gunicorn (recommended)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

### Docker

```dockerfile
FROM python:3.9-slim
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "web_app:app"]
```

### Nginx reverse proxy

```nginx
location / {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    client_max_body_size 100M;
}
```

## 🔒 Security

### Input validation
- Walidacja typu pliku (MP4 only)
- Limit rozmiaru uploadu
- Secure filenames
- Path traversal protection

### Rate limiting (recommended)
```bash
pip install flask-limiter
```

### HTTPS (production)
- Użyj reverse proxy z SSL
-lub Flask z certbot

## 📊 Monitoring

### Logs
```python
# Logowanie statusów
app.logger.info(f'Job {job_id}: {status}')
```

### Metrics
- Liczba jobów
- Średni czas optymalizacji
- Success/failure rate
- Rozmiary plików

## 🎯 Next Steps

- [ ] User authentication
- [ ] Batch processing
- [ ] Job history
- [ ] Custom configurations
- [ ] API documentation (Swagger)
- [ ] Docker deployment
- [ ] Database storage

---

**Enjoy optimizing your banners through the web! 🚀**