#!/usr/bin/env python3
"""
FTP Upload Script for Progreso.pl
Uploads all required files for MP4 Banner Optimizer
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
    print("🚀 Upload plików MP4 Banner Optimizer na Progreso.pl")
    print("=" * 60)
    print()

    # Sprawdź czy jesteś w głównym katalogu
    if not Path("web_app_prod.py").exists():
        print("❌ Brak web_app_prod.py - czy jesteś w głównym katalogu projektu?")
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

        # Upload głównych plików
        print("📤 Upload głównych plików...")
        upload_file(ftp, "web_app_prod.py", "web_app_prod.py")
        upload_file(ftp, "requirements.txt", "requirements.txt")
        upload_file(ftp, "passenger_wsgi.py", "passenger_wsgi.py")
        upload_file(ftp, ".htaccess", ".htaccess")
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
        print("2. Uruchom aplikację:")
        print("   cd deployment")
        print("   ./start_progreso.sh")
        print()
        print("🚀 Aplikacja powinna wystartować na porcie 8080")
        print()

    except Exception as e:
        print(f"❌ Błąd: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
