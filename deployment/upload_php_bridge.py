#!/usr/bin/env python3
"""
FTP Upload Script for PHP Bridge Deployment
Uploads all required files for PHP Bridge + Flask Backend
"""

import os
import sys
from ftplib import FTP, error_perm
from pathlib import Path

# Konfiguracja FTP
FTP_HOST = "flavour.civ.pl"
FTP_USER = "ars_mp4_video_opt"

def upload_file(ftp, local_path, remote_path):
    """Upload pojedynczego pliku"""
    try:
        with open(local_path, 'rb') as f:
            ftp.storbinary(f'STOR {remote_path}', f)
        print(f"   ✅ {remote_path}")
        return True
    except Exception as e:
        print(f"   ❌ {remote_path}: {e}")
        return False

def upload_directory(ftp, local_dir, remote_dir):
    """Upload całego katalogu"""
    local_path = Path(local_dir)
    if not local_path.exists():
        print(f"   ⚠️  Katalog {local_dir} nie istnieje - pomijam")
        return

    # Spróbuj stworzyć katalog
    try:
        ftp.mkd(remote_dir)
    except error_perm:
        pass  # Katalog może już istnieć

    # Uploaduj pliki
    for file in local_path.iterdir():
        if file.is_file() and not file.name.startswith('.'):
            remote_path = f"{remote_dir}/{file.name}"
            upload_file(ftp, str(file), remote_path)

def main():
    print("🚀 Upload PHP Bridge + Flask Backend")
    print("=" * 60)
    print()

    # Sprawdź czy jesteś w głównym katalogu
    if not Path("index.php").exists():
        print("❌ Brak index.php - czy jesteś w głównym katalogu projektu?")
        sys.exit(1)

    print(f"📋 Konfiguracja FTP:")
    print(f"  Host: {FTP_HOST}")
    print(f"  User: {FTP_USER}")
    print()

    # Pobierz hasło
    ftp_password = input("🔐 Podaj hasło FTP: ")

    try:
        # Połączenie FTP
        print("🔍 Łączenie z FTP...")
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, ftp_password)
        print("   ✅ Połączono")
        print()

        # Upload głównych plików PHP Bridge
        print("📤 Upload PHP Bridge files...")
        upload_file(ftp, "index.php", "index.php")
        upload_file(ftp, "start_bridge.sh", "start_bridge.sh")
        upload_file(ftp, "test_php_bridge.php", "test_php_bridge.php")
        upload_file(ftp, "web_app_prod.py", "web_app_prod.py")
        upload_file(ftp, "passenger_wsgi.py", "passenger_wsgi.py")
        upload_file(ftp, "requirements.txt", "requirements.txt")
        print()

        # Upload katalogów
        print("📤 Upload katalogów...")
        upload_directory(ftp, "mp4_optimizer", "mp4_optimizer")
        upload_directory(ftp, "templates", "templates")
        upload_directory(ftp, "deployment", "deployment")
        print()

        # Zamknij połączenie
        ftp.quit()
        print()
        print("=" * 60)
        print("🎉 Upload zakończony pomyślnie!")
        print("=" * 60)
        print()
        print("Co teraz?")
        print()
        print("1. Zaloguj się na konto:")
        print(f"   ssh {FTP_USER}@{FTP_HOST}")
        print()
        print("2. Uruchom PHP Bridge:")
        print("   cd ~/mp4-video-banner-optimizer")
        print("   chmod +x start_bridge.sh")
        print("   ./start_bridge.sh")
        print()
        print("3. Przetestuj działanie:")
        print("   curl -s https://vid.flavour.pl/api/presets")
        print()
        print("🚀 Aplikacja powinna być dostępna przez domenę!")

    except Exception as e:
        print(f"❌ Błąd: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()