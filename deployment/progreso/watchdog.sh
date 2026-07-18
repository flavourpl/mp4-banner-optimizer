#!/bin/bash
# Watchdog — restartuje aplikację, gdy proces nie działa.
# Rozwiązuje problem "usługa padła i nikt nie zauważył": zamiast tylko
# sprawdzać stan, cron co minutę sam podnosi proces.
#
# Instalacja na serwerze (raz):
#   chmod +x watchdog.sh
#   crontab -e
#   * * * * * cd ~/mp4-video-banner-optimizer && ./watchdog.sh >> watchdog.log 2>&1
#
# Jeśli cron nie jest dostępny w panelu Progreso, alternatywa: zewnętrzny
# monitoring (np. UptimeRobot) odpytujący https://vid.flavour.pl/status.php
# i restart ręczny przez ./start.sh po alercie.

cd "$(dirname "$0")"

if pgrep -f web_app_prod.py > /dev/null; then
    exit 0   # działa — nic nie rób
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] proces nie działa — restart"
./start.sh
