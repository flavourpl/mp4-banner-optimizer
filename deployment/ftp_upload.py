#!/usr/bin/env python3
"""
FTP Upload Script for Progreso.pl
Uploads the deployment/progreso/ package (MP4 Banner Optimizer).

Run from the PROJECT ROOT:
    python3 deployment/ftp_upload.py           # sam upload
    python3 deployment/ftp_upload.py --clean   # najpierw wyczyść zdalny katalog aplikacji
"""

import os
import sys
from ftplib import FTP, error_perm
from pathlib import Path

# Konfiguracja FTP
FTP_HOST = "flavour.civ.pl"
FTP_USER = "ars_mp4_video_opt"

# Pakiet do wysłania (względem katalogu głównego projektu)
PACKAGE_DIR = Path("deployment/progreso")

# Nazwa katalogu aplikacji na serwerze (jeśli FTP ląduje w katalogu domowym)
APP_DIR_NAME = "mp4-video-banner-optimizer"

# Czego nie wysyłamy
SKIP_NAMES = {".DS_Store", "Thumbs.db"}
SKIP_DIRS = {"__pycache__"}

# Czego NIGDY nie usuwamy po stronie serwera (~/bin/ffmpeg!)
PROTECTED_NAMES = {"bin"}


# ---------------------------------------------------------------- lokalne

def collect_files(package_dir):
    """Zbierz wszystkie pliki pakietu (rekurencyjnie), ze ścieżkami względnymi."""
    files = []
    for path in sorted(package_dir.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.name not in SKIP_NAMES:
            files.append(path.relative_to(package_dir))
    return files


def ensure_remote_dir(ftp, remote_dir):
    """Utwórz zdalny katalog (i rodziców), ignoruj 'już istnieje'."""
    parts = remote_dir.replace("\\", "/").strip("/").split("/")
    current = ""
    for part in parts:
        current = f"{current}/{part}" if current else part
        try:
            ftp.mkd(current)
        except error_perm:
            pass  # katalog już istnieje


def upload_file(ftp, local_path, remote_path):
    """Upload pojedynczego pliku."""
    try:
        with open(local_path, "rb") as f:
            ftp.storbinary(f"STOR {remote_path}", f)
        print(f"   ✅ {remote_path}")
        return True
    except Exception as e:
        print(f"   ❌ {remote_path}: {e}")
        return False


def chmod_remote(ftp, remote_path, mode):
    """Spróbuj nadać uprawnienia (np. 755 dla *.sh). Ignoruj brak wsparcia."""
    try:
        ftp.sendcmd(f"SITE CHMOD {mode} {remote_path}")
    except Exception:
        pass


# ---------------------------------------------------------------- czyszczenie zdalne

def remote_entries(ftp, path):
    """Lista (name, is_dir) dla zdalnego katalogu. MLSD, fallback NLST."""
    try:
        out = []
        for name, facts in ftp.mlsd(path, facts=["type"]):
            if name in (".", ".."):
                continue
            out.append((name, facts.get("type") == "dir"))
        return out
    except Exception:
        pass

    # Fallback: NLST + sonda katalogowa przez cwd
    out = []
    try:
        names = ftp.nlst(path)
    except error_perm:
        return out
    for name in names:
        if name.rsplit("/", 1)[-1] in (".", ".."):
            continue
        is_dir = False
        try:
            current = ftp.pwd()
            ftp.cwd(name)
            ftp.cwd(current)
            is_dir = True
        except error_perm:
            pass
        # NLST potrafi zwracać ścieżki z prefiksem katalogu
        short = name[len(path):].lstrip("/") if name.startswith(path + "/") else name
        out.append((short, is_dir))
    return out


def remote_walk(ftp, path):
    """Rekurencyjny listing: zwraca (files, dirs) ze ścieżkami względnymi."""
    files, dirs = [], []
    for name, is_dir in remote_entries(ftp, path):
        full = f"{path}/{name}" if path != "." else name
        if full.split("/")[0] in PROTECTED_NAMES:
            continue
        if is_dir:
            dirs.append(full)
            sub_files, sub_dirs = remote_walk(ftp, full)
            files.extend(sub_files)
            dirs.extend(sub_dirs)
        else:
            files.append(full)
    return files, dirs


def clean_remote(ftp):
    """Wyczyść zdalny katalog aplikacji (z podglądem i potwierdzeniem)."""
    top_names = [name for name, _ in remote_entries(ftp, ".")]
    target = APP_DIR_NAME if APP_DIR_NAME in top_names else "."

    print(f"🧹 Tryb --clean: czyszczę zdalny katalog: {target!r}")
    if target == ".":
        print("   (FTP ląduje bezpośrednio w katalogu aplikacji)")
    print(f"   Pomijam na wszelki wypadek: {', '.join(sorted(PROTECTED_NAMES))}")
    print()

    files, dirs = remote_walk(ftp, target)
    if not files and not dirs:
        print("   Katalog jest już pusty.")
        return

    print(f"   Do usunięcia: {len(files)} plików, {len(dirs)} katalogów")
    preview = files[:15]
    for f in preview:
        print(f"     - {f}")
    if len(files) > len(preview):
        print(f"     ... i {len(files) - len(preview)} więcej")
    print()

    answer = input("❓ Potwierdź usunięcie wpisując 'yes': ").strip()
    if answer != "yes":
        print("❌ Przerwano - nic nie usunięto.")
        sys.exit(1)

    removed = 0
    for f in files:
        try:
            ftp.delete(f)
            removed += 1
        except error_perm as e:
            print(f"   ⚠️  nie mogę usunąć {f}: {e}")
    for d in reversed(dirs):
        try:
            ftp.rmd(d)
        except error_perm as e:
            print(f"   ⚠️  nie mogę usunąć {d}: {e}")
    print(f"   ✅ Usunięto {removed}/{len(files)} plików i katalogi")
    print()


# ---------------------------------------------------------------- main

def main():
    clean_mode = "--clean" in sys.argv

    print("🚀 Upload MP4 Banner Optimizer na Progreso.pl")
    print("=" * 60)

    if not PACKAGE_DIR.is_dir():
        print(f"❌ Brak pakietu {PACKAGE_DIR} - uruchom z katalogu głównego projektu")
        sys.exit(1)

    files = collect_files(PACKAGE_DIR)
    if not files:
        print(f"❌ Pakiet {PACKAGE_DIR} jest pusty")
        sys.exit(1)

    print(f"📦 Pakiet: {PACKAGE_DIR} ({len(files)} plików)")
    print(f"📋 FTP: {FTP_USER}@{FTP_HOST}")
    if clean_mode:
        print("🧹 Tryb: --clean (najpierw czyszczenie zdalnego katalogu)")
    print()

    ftp_password = input("🔐 Podaj hasło FTP: ")

    try:
        print("🔍 Łączenie z FTP...")
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, ftp_password)
        print("   ✅ Połączono")
        print()

        if clean_mode:
            clean_remote(ftp)

        print("📤 Upload...")
        failed = 0
        for rel in files:
            remote_path = rel.as_posix()
            parent = os.path.dirname(remote_path)
            if parent:
                ensure_remote_dir(ftp, parent)
            if not upload_file(ftp, PACKAGE_DIR / rel, remote_path):
                failed += 1
            elif remote_path.endswith(".sh"):
                chmod_remote(ftp, remote_path, "755")

        ftp.quit()
        print()
        print("=" * 60)
        if failed:
            print(f"⚠️  Upload zakończony z błędami ({failed}/{len(files)} nie powiodło się)")
            sys.exit(1)
        print(f"🎉 Upload zakończony ({len(files)} plików)")
        print("=" * 60)
        print()
        print("Co teraz? (szczegóły: deployment/progreso/INSTALL.md)")
        print()
        print(f"  ssh {FTP_USER}@{FTP_HOST}")
        print("  cd ~/mp4-video-banner-optimizer")
        print("  pip3 install --user flask werkzeug   # raz")
        print("  chmod +x start.sh verify.sh")
        print("  ./start.sh                            # start na porcie 5000")
        print("  ./verify.sh                           # sprawdzenie /api/health")
        print()

    except Exception as e:
        print(f"❌ Błąd: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
