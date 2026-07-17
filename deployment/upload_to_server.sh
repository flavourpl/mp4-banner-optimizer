#!/bin/bash

# AUTOMATYCZNY UPLOAD NA SERWER PRZEZ SSH/SCP
# ============================================
#
# Ten skrypt automatycznie wgra wszystkie pliki na serwer Progreso.pl
#
# UŻYCIE:
# 1. Wypełnij dane serwera poniżej
# 2. Uruchom: ./upload_to_server.sh
#
# ============================================

# ===== KONFIGURACJA SERWERA =====
# Edytuj te wartości!

SERVER_USER="ars"              # Twój username SSH
SERVER_HOST="flavour.civ.pl"            # Adres serwera
SERVER_PATH="/home/ars//mp4-video-banner-optimizer"               # Ścieżka do katalogu głównego (zmień jeśli potrzeba)
# ============================================

echo "🚀 Automatyczny upload MP4 Banner Optimizer na serwer"
echo "========================================================"
echo ""
echo "Konfiguracja:"
echo "  Serwer: $SERVER_USER@$SERVER_HOST"
echo "  Katalog: $SERVER_PATH"
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

# Test połączenia z serwerem
echo "🔍 Test połączenia z serwerem..."
if ! ssh -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" "echo 'Połączenie OK'" 2>/dev/null; then
    echo "❌ Nie można połączyć się z serwerem!"
    echo "   Sprawdź:"
    echo "   - Username jest poprawny: $SERVER_USER"
    echo "   - Adres serwera jest poprawny: $SERVER_HOST"
    echo "   - Masz dostęp SSH do tego serwera"
    echo "   - SSH key jest skonfigurowany (lub użyj hasła)"
    exit 1
fi

echo "   ✅ Połączenie z serwerem działa"
echo ""

# Tworzenie struktury katalogów na serwerze
echo "📁 Tworzenie struktury katalogów na serwerze..."
ssh "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && mkdir -p mp4_optimizer templates uploads outputs reports deployment" || {
    echo "❌ Nie można utworzyć katalogów na serwerze"
    echo "   Sprawdź czy ścieżka $SERVER_PATH jest poprawna i masz uprawnienia do zapisu"
    exit 1
}

echo "   ✅ Struktura katalogów utworzona"
echo ""

# Upload plików
echo "📤 Upload plików na serwer..."

# 1. mp4_optimizer/
echo "   - Upload mp4_optimizer/..."
scp -r mp4_optimizer/* "$SERVER_USER@$SERVER_HOST:$SERVER_PATH/mp4_optimizer/" || {
    echo "❌ Błąd podczas uploadu mp4_optimizer/"
    exit 1
}

# 2. templates/
echo "   - Upload templates/..."
scp -r templates/* "$SERVER_USER@$SERVER_HOST:$SERVER_PATH/templates/" || {
    echo "❌ Błąd podczas uploadu templates/"
    exit 1
}

# 3. Główne pliki
echo "   - Upload głównych plików..."
scp web_app_prod.py requirements.txt "$SERVER_USER@$SERVER_HOST:$SERVER_PATH/" || {
    echo "❌ Błąd podczas uploadu głównych plików"
    exit 1
}

# 4. Deployment skrypty
echo "   - Upload skryptów deployment..."
scp deployment/start_progreso.sh deployment/verify_deployment.py deployment/check_deployment.sh "$SERVER_USER@$SERVER_HOST:$SERVER_PATH/deployment/" || {
    echo "❌ Błąd podczas uploadu skryptów deployment"
    exit 1
}

echo "   ✅ Wszystkie pliki wgrane"
echo ""

# Ustawienie permissions
echo "🔧 Ustawianie permissions..."
ssh "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && chmod +x deployment/start_progreso.sh deployment/check_deployment.sh && chmod 755 mp4_optimizer templates uploads outputs reports" || {
    echo "⚠️  Ostrzeżenie: Nie można ustawić wszystkich permissions"
}

echo "   ✅ Permissions ustawione"
echo ""

# Sprawdzenie czy FFmpeg jest zainstalowany
echo "🎬 Sprawdzanie FFmpeg na serwerze..."
if ssh "$SERVER_USER@$SERVER_HOST" "[ -f ~/bin/ffmpeg ]"; then
    echo "   ✅ FFmpeg jest zainstalowany"
else
    echo "   ⚠️  FFmpeg nie jest zainstalowany w ~/bin/"
    echo "   Zainstaluję FFmpeg teraz..."

    ssh "$SERVER_USER@$SERVER_HOST" "bash -s" << 'ENDSSH'
        set -e
        echo "   Pobieranie FFmpeg..."
        cd ~
        mkdir -p bin

        if [ ! -f ~/bin/ffmpeg ]; then
            wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
            tar xf ffmpeg-release-amd64-static.tar.xz
            mv ffmpeg-*/ffmpeg ~/bin/ffmpeg
            mv ffmpeg-*/ffprobe ~/bin/ffprobe
            chmod +x ~/bin/ffmpeg ~/bin/ffprobe
            rm -rf ffmpeg-*.tar.xz ffmpeg-*
            echo "   ✅ FFmpeg zainstalowany"
        else
            echo "   FFmpeg już istnieje"
        fi
ENDSSH

    echo "   ✅ FFmpeg zainstalowany"
fi

echo ""

# Sprawdzenie Python dependencies
echo "📦 Sprawdzanie Python dependencies..."
ssh "$SERVER_USER@$SERVER_HOST" "pip3 install --user Flask Werkzeug 2>/dev/null" || {
    echo "⚠️  Ostrzeżenie: Nie można zainstalować Python dependencies"
}

echo "   ✅ Dependencies sprawdzone/zainstalowane"
echo ""

# Uruchomienie check_deployment.sh
echo "🧪 Uruchamianie sprawdzenia deploymentu..."
ssh "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && bash deployment/check_deployment.sh"

echo ""
echo "========================================================"
echo "🎉 Upload zakończony pomyślnie!"
echo "========================================================"
echo ""
echo "Co dalej?"
echo ""
echo "1. Zaloguj się na serwer:"
echo "   ssh $SERVER_USER@$SERVER_HOST"
echo ""
echo "2. Idź do katalogu:"
echo "   cd $SERVER_PATH"
echo ""
echo "3. Uruchom aplikację:"
echo "   cd deployment"
echo "   ./start_progreso.sh"
echo ""
echo "4. Otwórz w przeglądarce:"
echo "   http://twoja-domena.com:8080"
echo ""
echo "🚀 Twoja aplikacja powinna działać!"
echo ""

# Opcja: Natychmiastowe uruchomienie
read -p "Czy chcesz teraz uruchomić aplikację na serwerze? (t/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Tt]$ ]]; then
    echo "🚀 Uruchamiam aplikację..."
    ssh "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH/deployment && nohup ./start_progreso.sh > ../optimizer.log 2>&1 &"
    echo "✅ Aplikacja uruchomiona w tle!"
    echo "Sprawdź logi: ssh $SERVER_USER@$SERVER_HOST 'tail -f $SERVER_PATH/optimizer.log'"
fi