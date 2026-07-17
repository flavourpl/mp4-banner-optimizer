#!/bin/bash

# Skrypt sprawdzający czy wszystko jest poprawnie wgrane na serwer
# Uruchom ten skrypt po wgraniu plików na serwer

echo "🔍 Sprawdzanie deploymentu na Progreso.pl"
echo "============================================"
echo ""

# Funkcje check
check_ok() {
    echo "   ✅ $1"
}

check_fail() {
    echo "   ❌ $1"
}

check_warn() {
    echo "   ⚠️  $1"
}

# 1. Sprawdź strukturę katalogów
echo "📁 Struktura katalogów:"
for dir in mp4_optimizer templates uploads outputs reports deployment; do
    if [ -d "$dir" ]; then
        check_ok "Katalog $dir/ istnieje"
    else
        check_fail "Brak katalogu $dir/"
    fi
done

echo ""

# 2. Sprawdź główne pliki
echo "📄 Główne pliki:"
for file in web_app_prod.py requirements.txt; do
    if [ -f "$file" ]; then
        check_ok "$file istnieje"
    else
        check_fail "Brak $file"
    fi
done

echo ""

# 3. Sprawdź mp4_optimizer pliki
echo "🔧 Moduły mp4_optimizer:"
for module in __init__.py encoder.py probe.py ladder.py report.py config.py ffmpeg_config.py bitrate_calc.py cli.py; do
    if [ -f "mp4_optimizer/$module" ]; then
        check_ok "mp4_optimizer/$module"
    else
        check_fail "Brak mp4_optimizer/$module"
    fi
done

echo ""

# 4. Sprawdź templates
echo "🌐 Templates:"
if [ -f "templates/index.html" ]; then
    check_ok "templates/index.html"
else
    check_fail "Brak templates/index.html"
fi

echo ""

# 5. Sprawdź deployment scripts
echo "🚀 Skrypty deployment:"
if [ -f "deployment/start_progreso.sh" ]; then
    check_ok "deployment/start_progreso.sh"
    if [ -x "deployment/start_progreso.sh" ]; then
        check_ok "start_progreso.sh jest executable"
    else
        check_warn "start_progreso.sh nie jest executable (uruchom: chmod +x deployment/start_progreso.sh)"
    fi
else
    check_fail "Brak deployment/start_progreso.sh"
fi

if [ -f "deployment/verify_deployment.py" ]; then
    check_ok "deployment/verify_deployment.py"
else
    check_fail "Brak deployment/verify_deployment.py"
fi

echo ""

# 6. Sprawdź Python
echo "🐍 Python:"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    check_ok "Python: $PYTHON_VERSION"
else
    check_fail "Python3 nie znaleziono"
fi

echo ""

# 7. Sprawdź FFmpeg
echo "🎬 FFmpeg:"
if [ -f ~/bin/ffmpeg ]; then
    FFMPEG_VERSION=$(~/bin/ffmpeg -version 2>&1 | head -1)
    check_ok "Static FFmpeg: $FFMPEG_VERSION"
else
    check_warn "Static FFmpeg nie znaleziony w ~/bin/"
    echo "   Zainstaluj:"
    echo "   mkdir -p ~/bin"
    echo "   cd ~"
    echo "   wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    echo "   tar xf ffmpeg-release-amd64-static.tar.xz"
    echo "   mv ffmpeg-*/ffmpeg ~/bin/ffmpeg"
    echo "   mv ffmpeg-*/ffprobe ~/bin/ffprobe"
    echo "   chmod +x ~/bin/ffmpeg ~/bin/ffprobe"
fi

echo ""

# 8. Sprawdź Python dependencies
echo "📦 Python dependencies:"
if python3 -c "import flask" 2>/dev/null; then
    check_ok "Flask zainstalowany"
else
    check_warn "Flask nie zainstalowany"
    echo "   Uruchom: pip3 install --user Flask Werkzeug"
fi

if python3 -c "import werkzeug" 2>/dev/null; then
    check_ok "Werkzeug zainstalowany"
else
    check_warn "Werkzeug nie zainstalowany"
fi

echo ""

# 9. Sprawdź permissions do zapisu
echo "💾 Permissions do zapisu:"
for dir in uploads outputs reports; do
    if [ -d "$dir" ]; then
        if [ -w "$dir" ]; then
            check_ok "$dir/ jest writable"
        else
            check_fail "$dir/ nie jest writable"
        fi
    fi
done

echo ""

# 10. Test importu
echo "🧪 Test importu modułów:"
if python3 -c "import sys; sys.path.insert(0, '.'); from mp4_optimizer import ffmpeg_config; print('OK')" 2>/dev/null; then
    check_ok "Moduły mp4_optimizer importują się poprawnie"
else
    check_fail "Błąd importu modułów"
fi

echo ""

# 11. Test FFmpeg config
echo "🎯 Test konfiguracji FFmpeg:"
if python3 -c "
import sys
sys.path.insert(0, '.')
from mp4_optimizer.ffmpeg_config import get_ffmpeg_paths, is_ffmpeg_working
ffmpeg, ffprobe = get_ffmpeg_paths()
working = is_ffmpeg_working()
print(f'FFmpeg: {ffmpeg}')
print(f'FFprobe: {ffprobe}')
print(f'Working: {working}')
" 2>/dev/null; then
    check_ok "FFmpeg config poprawny"
else
    check_fail "Problem z FFmpeg config"
fi

echo ""
echo "============================================"
echo "🏁 Sprawdzanie zakończone!"
echo "============================================"
echo ""
echo "Jeśli wszystko jest OK, uruchom:"
echo "  cd deployment"
echo "  ./start_progreso.sh"
echo ""
echo "Jeśli są błędy, napraw je wg instrukcji powyżej."