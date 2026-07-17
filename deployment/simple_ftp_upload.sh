#!/bin/bash

# PROSTY UPLOAD FTP NA PROGRESO.PL
# ================================
#
# Upload plików przez FTP do konta ars_mp4_video_opt
# Reszta deploymentu już zrobiona
#
# ================================

echo "🚀 Upload plików MP4 Banner Optimizer na Progreso.pl"
echo "======================================================"
echo ""

# ===== KONFIGURACJA FTP =====
FTP_HOST="flavour.civ.pl"
FTP_USER="ars_mp4_video_opt"

echo "📋 Konfiguracja FTP:"
echo "  Host: $FTP_HOST"
echo "  User: $FTP_USER"
echo ""

# Sprawdź czy jesteś w głównym katalogu
if [ ! -f "web_app_prod.py" ]; then
    echo "❌ Brak web_app_prod.py - czy jesteś w głównym katalogu projektu?"
    exit 1
fi

echo "✅ Wszystkie pliki lokalne są obecne"
echo ""

# Pobierz hasło FTP
echo "🔐 Podaj hasło FTP dla $FTP_USER:"
read -s FTP_PASS
echo ""

# Tworzenie skryptu FTP
echo "📤 Przygotowanie uploadu..."
FTP_SCRIPT="/tmp/ftp_upload_$$.txt"

cat > $FTP_SCRIPT <<EOF
user $FTP_USER $FTP_PASS
binary

# Upload głównych plików
put web_app_prod.py
put requirements.txt

# Upload katalogów
cd mp4_optimizer
lcd mp4_optimizer
mput *
cd ..
lcd ..

cd templates
lcd templates
mput *
cd ..
lcd ..

cd deployment
lcd deployment
put start_progreso.sh
put check_deployment.sh
put verify_deployment.py
cd ..
lcd ..

quit
EOF

echo "   ✅ Skrypt FTP przygotowany"
echo ""

# Upload przez FTP
echo "📤 Upload plików przez FTP..."
if ftp -n $FTP_HOST < $FTP_SCRIPT > /tmp/ftp_output_$$.txt 2>&1; then
    echo "   ✅ Upload zakończony pomyślnie!"
else
    echo "❌ Błąd podczas uploadu FTP!"
    echo "Sprawdź log: cat /tmp/ftp_output_$$.txt"
    rm -f $FTP_SCRIPT
    exit 1
fi

rm -f $FTP_SCRIPT

echo ""
echo "======================================================"
echo "🎉 Upload zakończony pomyślnie!"
echo "======================================================"
echo ""
echo "Co teraz?"
echo ""
echo "1. Zaloguj się na konto:"
echo "   ssh ars_mp4_video_opt@$FTP_HOST"
echo ""
echo "2. Uruchom aplikację:"
echo "   cd deployment"
echo "   ./start_progreso.sh"
echo ""
echo "🚀 Aplikacja powinna wystartować na porcie 8080"
echo ""
