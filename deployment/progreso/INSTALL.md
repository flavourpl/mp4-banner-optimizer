# Instalacja na Progreso.pl — MP4 Banner Optimizer

Serwer: `ars_mp4_video_opt@flavour.civ.pl` · katalog docelowy: `~/mp4-video-banner-optimizer/` · port: **5000**

## 1. Upload plików

Z katalogu głównego projektu:

```bash
python3 deployment/ftp_upload.py
```

Skrypt wysyła zawartość `deployment/progreso/` na serwer (spyta o hasło FTP).

**Świeża instalacja / porządek na FTP:**

```bash
python3 deployment/ftp_upload.py --clean
```

Tryb `--clean` najpierw czyści zdalny katalog aplikacji (pokazuje listę plików
i wymaga potwierdzenia wpisując `yes`), a potem wgrywa pakiet. Katalog `bin`
(z FFmpeg) jest zawsze pomijany — nie trzeba nic usuwać ręcznie przez klienta FTP.

Alternatywnie ręcznie (scp/rsync) — wgraj CAŁĄ zawartość `deployment/progreso/`
do `~/mp4-video-banner-optimizer/`, zachowując strukturę katalogów.

## 2. Zależności Pythona (raz, po SSH)

```bash
ssh ars_mp4_video_opt@flavour.civ.pl
pip3 install --user flask werkzeug
```

## 3. FFmpeg (raz)

```bash
ls -la ~/bin/ffmpeg   # sprawdź czy istnieje

# jeśli brak:
mkdir -p ~/bin && cd ~/bin
wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-release-64bit-static.tar.xz
tar xvf ffmpeg-release-64bit-static.tar.xz
cp ffmpeg-*/ffmpeg ffmpeg-*/ffprobe .
chmod +x ffmpeg ffprobe
```

## 4. Start

```bash
cd ~/mp4-video-banner-optimizer
chmod +x start.sh verify.sh
./start.sh          # domyślnie port 5000
```

Skrypt sam: tworzy `uploads/ outputs/ reports/`, zabija stare instancje,
startuje przez `nohup` (log: `optimizer.log`) i sprawdza `/api/health`.

## 5. Weryfikacja

```bash
./verify.sh
# lub ręcznie:
curl -s http://127.0.0.1:5000/api/health
curl -s http://127.0.0.1:5000/api/presets
```

`status: "ok"` = ffmpeg, ffprobe i katalogi działają. Od strony www:
`http://77.65.215.8:5000/` (panel pokaże zielony badge LIVE).

## Utrzymanie

```bash
tail -f optimizer.log                      # logi
pkill -f web_app_prod.py && ./start.sh     # restart
find uploads/ outputs/ -mtime +7 -delete   # sprzątanie starych plików
```

## Znane ograniczenia Progreso.pl

- Domena `vid.flavour.pl` NIE przekierowuje na aplikację (zewnętrzny reverse proxy
  ignoruje `.htaccess` / ProxyPass; panel daje tylko porty SSL 443/444/445 wymagające roota).
- Działające rozwiązanie: aplikacja na porcie 5000, dostęp po `http://77.65.215.8:5000`.
- W panelu Progreso "Inne Skrypty: TAK" musi być włączone (wymagane dla Pythona).
