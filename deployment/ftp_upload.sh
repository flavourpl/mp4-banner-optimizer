#!/bin/bash

# UPLOAD NA PROGRESO.PL PRZEZ FTP + SSH (ROOT)
# ===============================================
#
# Ten skrypt automatycznie wgra wszystkie pliki na konto FTP
# i then użyje SSH roota do konfiguracji i uruchomienia
#
# ===============================================

echo "🚀 Upload MP4 Banner Optimizer na Progreso.pl"
echo "=============================================="
echo ""

# ===== KONFIGURACJA FTP =====
FTP_HOST="flavour.civ.pl"
FTP_USER="ars_mp4_video_opt"
# Hasło zostanie podane interaktywnie

# ===== KONFIGURACJA SSH ROOT =====
SSH_USER="root"
SSH_HOST="flavour.civ.pl"
# Zakładamy że SSH key jest skonfigurowany dla roota
# Jeśli nie, skrypt zapyta o hasło

echo "📋 Konfiguracja:"
echo "  FTP: $FTP_USER@$FTP_HOST"
echo "  SSH: $SSH_USER@$SSH_HOST"
echo ""

# Sprawdź czy mamy wszystkie pliki lokalnie
echo "📋 Sprawdzanie plików lokalnych..."
if [ ! -f "web_app_prod.py" ]; then
    echo "❌ Brak web_app_prod.py - czy jesteś w głównym katalogu projektu?"
    exit 1
fi

if [ ! -d "mp4_optimizer" ]; then
    echo "❌ Brak katalogu mp4_optimizer/ - czy jesteś w głównym katalogu projektu?"
    exit 1
fi

echo "   ✅ Wszystkie pliki lokalne są obecne"
echo ""

# Pobierz hasło FTP
echo "🔐 Podaj hasło FTP:"
read -s FTP_PASS
echo ""
echo "   ✅ Hasło pobrane"
echo ""

# Test połączenia FTP
echo "🔍 Test połączenia FTP..."
if ! ftp -n -v $FTP_HOST 2>&1 <<EOF | grep -q "Connected"
quote USER $FTP_USER
quote PASS $FTP_PASS
quit
EOF
then
    echo "❌ Nie można połączyć się z FTP!"
    echo "   Sprawdź:"
    echo "   - Host jest poprawny: $FTP_HOST"
    echo "   - Username jest poprawny: $FTP_USER"
    echo "   - Hasło jest poprawne"
    exit 1
fi

echo "   ✅ Połączenie FTP działa"
echo ""

# Tworzenie skryptu FTP do uploadu
echo "📤 Przygotowanie uploadu FTP..."
FTP_SCRIPT="/tmp/ftp_upload_$$.txt"

cat > $FTP_SCRIPT <<EOF
quote USER $FTP_USER
quote PASS $FTP_PASS
binary

# Tworzenie struktury katalogów
mkdir mp4_optimizer
mkdir templates
mkdir uploads
mkdir outputs
mkdir reports
mkdir deployment

# Upload mp4_optimizer/
cd mp4_optimizer
lcd mp4_optimizer
mput *
cd ..

# Upload templates/
cd templates
lcd templates
mput *
cd ..

# Upload plików głównych
put web_app_prod.py
put requirements.txt

# Upload deployment/
cd deployment
lcd deployment
put start_progreso.sh
put check_deployment.sh
put verify_deployment.py

# Powrót do roota
cd /
lcd

quit
EOF

echo "   ✅ Skrypt FTP przygotowany"
echo ""

# Upload przez FTP
echo "📤 Upload plików przez FTP (to może chwilę potrwać)..."
if ! ftp -n $FTP_HOST < $FTP_SCRIPT > /tmp/ftp_output_$$.txt 2>&1; then
    echo "❌ Błąd podczas uploadu FTP!"
    echo "Sprawdź log: /tmp/ftp_output_$$.txt"
    rm -f $FTP_SCRIPT
    exit 1
fi

rm -f $FTP_SCRIPT
echo "   ✅ Wszystkie pliki wgrane przez FTP"
echo ""

# Teraz użyj SSH roota do konfiguracji
echo "🔧 Konfiguracja przez SSH (jako root)..."
echo "   Ustawianie permissions..."

ssh $SSH_USER@$SSH_HOST << 'ENDSSH'
set -e

# Znajdź kalk użytkownika i ustaw permissions
USER_HOME=$(getent passwd ars_mp4_video_opt | cut -d: -f6)
if [ -z "$USER_HOME" ]; then
    echo "❌ Nie znaleziono użytkownika ars_mp4_video_opt"
    exit 1
fi

cd "$USER_HOME"

# Ustaw permissions
chmod +x deployment/start_progreso.sh deployment/check_deployment.sh
chmod 755 mp4_optimizer templates uploads outputs reports
chown -R ars_mp4_video_opt:ars_mp4_video_opt .

echo "   ✅ Permissions ustawione"

# Sprawdź FFmpeg
echo "🎬 Sprawdzanie FFmpeg..."
if [ ! -f ~/bin/ffmpeg ]; then
    echo "   Instalowanie FFmpeg..."
    mkdir -p ~/bin
    wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
    tar xf ffmpeg-release-amd64-static.tar.xz
    mv ffmpeg-*/ffmpeg ~/bin/ffmpeg
    mv ffmpeg-*/ffprobe ~/bin/ffprobe
    chmod +x ~/bin/ffmpeg ~/bin/ffprobe
    rm -rf ffmpeg-*.tar.xz ffmpeg-*
    echo "   ✅ FFmpeg zainstalowany"
else
    echo "   ✅ FFmpeg już istnieje"
fi

# Sprawdź Python dependencies
echo "📦 Sprawdzanie Python dependencies..."
pip3 install --user Flask Werkzeug 2>/dev/null || true
echo "   ✅ Dependencies sprawdzone"

echo ""
echo "🧪 Uruchamianie sprawdzenia deploymentu..."
cd "$USER_HOME"
bash deployment/check_deployment.sh

ENDSSH

echo ""
echo "========================================================"
echo "🎉 Upload i konfiguracja zakończone pomyślnie!"
echo "========================================================"
echo ""
echo "Co dalej?"
echo ""
echo "1. Zaloguj się przez SSH jako root:"
echo "   ssh root@$SSH_HOST"
echo ""
echo "2. Przełącz się na użytkownika:"
echo "   su - ars_mp4_video_opt"
echo ""
echo "3. Uruchom aplikację:"
echo "   cd deployment"
echo "   ./start_progreso.sh"
echo ""
echo "4. Aplikacja będzie dostępna na porcie 8080"
echo ""
echo "🚀 Twoja aplikacja powinna działać!"
echo ""

# Opcja: Natychmiastowe uruchomienie
read -p "Czy chcesz teraz uruchomić aplikację? (t/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Tt]$ ]]; then
    echo "🚀 Uruchamiam aplikację..."

    ssh $SSH_USER@$SSH_HOST << 'ENDSSH'
        USER_HOME=$(getent passwd ars_mp4_video_opt | cut -d: -f6)
        cd "$USER_HOME/deployment"

        # Uruchom jako użytkownik ars_mp4_video_opt
        su - ars_mp4_video_opt -c "cd $USER_HOME/deployment && nohup ./start_progreso.sh > ../optimizer.log 2>&1 &"

        echo "✅ Aplikacja uruchomiona!"
        echo "Sprawdź logi: tail -f $USER_HOME/optimizer.log"
ENDSSH
fi
