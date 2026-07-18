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
ls -la ~/bin/ffmpeg ~/bin/ffprobe   # sprawdź czy OBA istnieją

# jeśli brak:
mkdir -p ~/bin && cd ~/bin
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xvf ffmpeg-release-amd64-static.tar.xz
cp ffmpeg-*/ffmpeg ffmpeg-*/ffprobe .   # OBOWIĄZKOWO oba binarki
chmod +x ffmpeg ffprobe
```

Brakuje tylko `ffprobe`? (typowe przypadki: `/api/health` pokazuje `ffprobe: false`
albo błąd optymalizacji `ffprobe: error while loading shared libraries: ...` —
to znak, że aplikacja trafiła na zepsuty systemowy ffprobe; aplikacja preferuje
`~/bin` przed binariami systemowymi, więc wystarczy dołożyć statyczny build):

```bash
cd /tmp
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xvf ffmpeg-release-amd64-static.tar.xz
cp ffmpeg-*/ffprobe ~/bin/ && chmod +x ~/bin/ffprobe
~/bin/ffprobe -version | head -1   # weryfikacja
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

## 6. Dostęp przez domenę (PHP bridge)

Pakiet zawiera `index.php` — mostek, który przekazuje ruch z domeny do aplikacji:

```
Przeglądarka → https://vid.flavour.pl → index.php → http://127.0.0.1:5000 → Flask
```

- Aplikacja MUSI chodzić na porcie **5000** (w `index.php`: `BACKEND_URL = http://127.0.0.1:5000`).
- `.htaccess` z pakietu ma `DirectoryIndex index.php index.html` ORAZ rewrite
  nieistniejących ścieżek do `index.php` — bez tego drugiego działa tylko `/`,
  a `/api/*`, `/app`, `/admin/uploads` zwracają 404 prosto z Apache.
  Mostek wygrywa też z ewentualnym starym `index.html` w docroocie
  (wcześniej domena "fallbackowała" do cudzej strony, bo mostka tam nie było).
- Panelowe porty 443/444/445 NIE są potrzebne (SSL, wymagają roota).

Test po uploadzie:

```bash
curl -s https://vid.flavour.pl/api/health
curl -s https://vid.flavour.pl/api/presets
```

Jeśli domena dalej pokazuje cudzy HTML: sprawdź, czy `index.php` jest
w katalogu aplikacji (`ls -la index.php`) i zajrzyj do `php_bridge.log`.

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
