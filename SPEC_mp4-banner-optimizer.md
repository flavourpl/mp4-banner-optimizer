# SPEC: mp4-banner-optimizer

## 1. Cel projektu

Narzędzie CLI (Python), które przyjmuje plik `.mp4` (krótki klip 3–5s przeznaczony do wklejenia w baner HTML5) i **iteracyjnie optymalizuje go**, aż osiągnie zadany limit wagi pliku, przy jak najlepszej możliwej jakości wizualnej w ramach tego limitu.

Kontekst użycia: kreacje HTML5 (AppLovin, Google Ads/GDN, Meta, TikTok/Pangle) gdzie wideo jest jednym z assetów bannera i musi zmieścić się w twardym limicie wagi całego pakietu. Tool ma być wołany z poziomu istniejących skryptów generatorów (`generator_*.py`) albo osobno, ręcznie.

## 2. Wymagania funkcjonalne — skrót

- Input: dowolny `.mp4` (różne rozdzielczości, fps, obecność/brak audio)
- Output: `.mp4` który **na pewno** mieści się pod limitem wagi (chyba że nawet przy najniższej jakości/rozdzielczości się nie da — patrz sekcja 8, "best effort")
- Docelowa rozdzielczość: **300×400px** (podstawowa)
- Fallback rozdzielczości (gdy nie da się zmieścić w limicie przy 300×400 nawet przy sensownej jakości): **300×300px**, a w ostateczności **150×150px**
- Limit wagi: konfigurowalny preset **LOW / MED / HIGH**
- Tool ma logować każdą próbę (iterację) i finalny raport

## 3. Presety wagi (konfigurowalne)

Domyślne wartości — mają być zdefiniowane jako stałe/config, łatwe do zmiany:

| Preset | Limit wagi |
|--------|-----------|
| LOW    | 400 KB    |
| MED    | 450 KB (default) |
| HIGH   | 500 KB    |

Uwaga: "KB" = kilobajty binarne w rozumieniu praktyki branżowej ad-tech, czyli `1 KB = 1024 B`. To trzeba trzymać konsekwentnie w całym narzędziu (limit i pomiar finalnego pliku tą samą jednostką).

Parametr wybierany flagą CLI, np.:
```
--preset low|med|high
```
lub bezpośrednio wagą w KB:
```
--max-kb 420
```
(`--max-kb` nadpisuje `--preset` jeśli podane oba).

## 4. Drabinka rozdzielczości

```
300x400  (primary, target aspect 3:4)
  ↓ jeśli nie da się zmieścić w limicie przy akceptowalnej jakości
300x300  (aspect 1:1)
  ↓ jeśli nadal nie da się zmieścić
150x150  (aspect 1:1, ostateczność)
```

Konfigurowalne jako lista w configu (żeby łatwo dodać np. `160x600` w przyszłości):
```python
RESOLUTION_LADDER = ["300x400", "300x300", "150x150"]
```

### Obsługa aspect ratio źródła
Źródłowe wideo może mieć inny stosunek boków niż target. Strategia:
- Domyślnie: **crop-to-fill** (scale + center crop), żeby wypełnić cały kadr bez czarnych pasów — to standard dla bannerów reklamowych.
- Flaga `--fit pad` jako opcja alternatywna: scale + letterbox/pillarbox (zachowuje całą treść, dodaje tło — kolor tła konfigurowalny, domyślnie czarny).
- Flaga `--fit stretch` (nie zalecane, ale dostępne) — proste rozciągnięcie bez zachowania proporcji.

## 5. Dźwignie optymalizacji (kolejność od najtańszej jakościowo do najdroższej)

Agent ma implementować to jako **uporządkowaną sekwencję kroków**, testując po każdym kroku czy plik mieści się w limicie. Jeśli tak — stop, zwróć wynik. Jeśli nie — przejdź do kolejnego kroku.

1. **Strip metadata + faststart** (zawsze, na starcie, bez wpływu na jakość)
   - `-map_metadata -1`
   - `-movflags +faststart`
2. **Strip audio** (chyba że użytkownik poda `--keep-audio`)
   - Sprawdź czy source ma ścieżkę audio (`ffprobe`)
   - Jeśli tak: policz ile KB zajmuje sama ścieżka audio (估算), usuń (`-an`), sprawdź czy to wystarcza
   - Jeśli `--keep-audio`: zamiast usuwać, kompresuj audio do niskiego bitrate AAC (np. 48kbps mono) jako osobna, mniej agresywna dźwignia
3. **Redukcja fps**
   - Drabinka: source_fps → 24 → 20 → 15 (nie schodzić poniżej 15 — zbyt "szarpane" dla reklamy)
   - `-r <fps>`
4. **Redukcja bitrate wideo (2-pass encode)** — główna dźwignia
   - Oblicz target bitrate z wagi docelowej i długości klipu (patrz sekcja 6)
   - 2-pass H.264 encode do tego bitrate
   - To jest krok, w którym faktycznie "mierzymy i trafiamy" w limit — nie zgadywanie przez CRF, tylko liczony bitrate
5. **Redukcja rozdzielczości** (dopiero gdy 1–4 wyczerpane przy obecnej rozdzielczości i nadal nie mieści się w limicie przy akceptowalnym bitrate — patrz "quality floor" niżej)
   - Przejdź do kolejnej pozycji w `RESOLUTION_LADDER`
   - Po zmianie rozdzielczości: wróć do kroku 4 (przelicz target bitrate dla nowej rozdzielczości, spróbuj ponownie)

### Quality floor (żeby nie zjechać do mazi)
Zdefiniuj minimalny akceptowalny bitrate wideo dla danej rozdzielczości (żeby tool nie próbował encodować 300×400 przy 20kbps i nazywać to sukcesem, jeśli limit i tak się nie mieści). Przykładowe wartości startowe (agent może je stroić empirycznie na realnych plikach testowych):

| Rozdzielczość | Minimalny sensowny bitrate wideo |
|---|---|
| 300×400 | ~180 kbps |
| 300×300 | ~140 kbps |
| 150×150 | ~80 kbps |

Jeśli policzony target bitrate (sekcja 6) spadnie poniżej tego floora dla danej rozdzielczości — **nie próbuj encodować przy tak niskim bitrate**, tylko od razu przejdź do niższej rozdzielczości w drabince.

## 6. Kalkulacja target bitrate

```
target_bitrate_kbps = (max_kb * 8 / duration_seconds - audio_bitrate_kbps) * safety_margin
```

Uwaga: `1 KB = 8 kilobits`, więc `max_kb * 8` konwertuje kilobajty na kilobity.

- `max_kb` — limit z presetu/flagi
- `duration_seconds` — z ffprobe źródła
- `audio_bitrate_kbps` — 0 jeśli audio strippowane, inaczej wybrany niski bitrate audio (np. 48)
- `safety_margin` — współczynnik bezpieczeństwa **0.92** (nie 1.0), bo:
  - kontener mp4 (moov atom, muxing overhead) zjada trochę wagi
  - 2-pass encoding nie trafia w bitrate co do bajta, ma wariancję

Po encodzie: **zawsze sprawdź faktyczny rozmiar pliku na dysku** (nie ufaj obliczonemu bitrate). Jeśli mimo safety margin plik i tak przekracza limit — zmniejsz target_bitrate o 10% i powtórz 2-pass (max 3 dodatkowe iteracje na tym samym kroku, zanim przejdziesz do kolejnej dźwigni/rozdzielczości).

## 7. Parametry kodowania (ffmpeg)

Stałe (nie zmieniają się między iteracjami):
```
Codec video: libx264
Profile: baseline (max kompatybilność) lub main jeśli baseline nie wspiera potrzebnych ficzerów — main jako fallback
Pixel format: yuv420p (wymagane dla kompatybilności z odtwarzaczami w WebView/MRAID)
Keyframe interval: co 1s (-g <fps>, żeby seek/loop działał płynnie w krótkich klipach reklamowych)
Preset x264: slower (bo optymalizujemy pod jakość-przy-danym-bitrate, nie pod szybkość encodu — to narzędzie developerskie, nie real-time)
Audio codec (jeśli keep-audio): AAC-LC
Container: mp4, faststart
```

## 8. "Best effort" / brak możliwości zmieszczenia w limicie

Jeśli po przejściu całej drabinki (wszystkie 3 rozdzielczości × wszystkie dźwignie) plik nadal przekracza limit wagi:
- Zwróć **najlepszy osiągnięty wynik** (najmniejszy plik z całej sesji optymalizacji, niekoniecznie ostatni)
- Zakończ z kodem wyjścia innym niż 0 (np. `exit code 2`) i jasnym komunikatem w logu/raporcie: `WARNING: could not fit under {limit}KB. Best result: {actual}KB at {resolution}.`
- Nie failuj cicho — to musi być widoczne w output.

## 9. CLI interface

```
mp4-banner-optimizer INPUT.mp4 [opcje]

Opcje:
  --preset {low,med,high}      domyślnie: med
  --max-kb N                   nadpisuje --preset, limit w KB
  --output PATH                domyślnie: <input>_optimized.mp4
  --fit {crop,pad,stretch}     domyślnie: crop
  --keep-audio                 domyślnie: audio usuwane
  --resolution-ladder "300x400,300x300,150x150"   nadpisuje domyślną drabinkę
  --min-fps N                  domyślnie: 15
  --report PATH                zapisz raport JSON z historią iteracji (domyślnie: <output>.report.json)
  --dry-run                    pokaż plan iteracji bez faktycznego encodowania
```

Przykład:
```bash
python mp4_optimizer.py clip.mp4 --preset high --output clip_450kb.mp4
```

## 10. Struktura raportu (JSON)

Dla każdego finalnego przebiegu — pełna historia prób, przydatna do debugowania i do tuningu quality-floora w przyszłości:

```json
{
  "input_file": "clip.mp4",
  "input_size_kb": 2140,
  "input_resolution": "1080x1350",
  "input_duration_s": 4.2,
  "target_max_kb": 450,
  "final_size_kb": 438,
  "final_resolution": "300x400",
  "status": "success",
  "iterations": [
    {"step": "strip_metadata_faststart", "size_kb": 2138},
    {"step": "strip_audio", "size_kb": 1980},
    {"step": "fps_24", "size_kb": 1750},
    {"step": "bitrate_2pass", "target_kbps": 762, "actual_size_kb": 438}
  ]
}
```

`status` ∈ `success` | `best_effort_failed`

## 11. Architektura kodu (sugerowana)

```
mp4_optimizer/
  __init__.py
  cli.py              # parsowanie argumentów, entry point
  probe.py            # wrapper na ffprobe (duration, res, fps, audio presence, source bitrate)
  encoder.py           # wrapper na ffmpeg 2-pass, strip audio, fps change, scale/crop
  ladder.py             # logika drabinki: sekwencja dźwigni + resolution fallback + quality floor
  bitrate_calc.py       # kalkulacja target bitrate (sekcja 6)
  report.py             # budowanie i zapis raportu JSON
  config.py             # presety LOW/MED/HIGH, RESOLUTION_LADDER, quality floors — wszystko w jednym miejscu do łatwej edycji
```

Zależności: `ffmpeg` + `ffprobe` muszą być dostępne w PATH (albo ścieżka podawana configiem). Reszta — czysty Python (subprocess), bez ciężkich bibliotek wideo.

## 12. Kryteria akceptacji (do testów agenta)

1. Plik wejściowy 1080p, 5s, z audio → output ≤ limitu, rozdzielczość 300×400, bez audio, odtwarza się poprawnie w przeglądarce (`<video>` tag, autoplay muted loop).
2. Plik wejściowy już mniejszy niż limit → tool nie "psuje" pliku bez potrzeby: nadal normalizuje do target rozdzielczości/faststart, ale nie kompresuje bardziej niż trzeba (krok 4 powinien wykryć że już się mieści i nie schodzić z bitrate bez potrzeby — czyli test na każdym kroku, nie tylko na końcu).
3. Plik wejściowy bardzo "ciężki" contentowo (dużo ruchu/szumu) → tool poprawnie zjeżdża przez całą drabinkę rozdzielczości i zwraca `best_effort_failed` z sensownym najlepszym wynikiem, zamiast zawieszać się w nieskończonej pętli.
4. `--preset low/med/high` faktycznie zmienia finalny limit i wynik.
5. Raport JSON zawiera pełną, czytelną historię iteracji.
6. Czas przetwarzania pojedynczego 3–5s klipu: rozsądny (2-pass × kilka iteracji × kilka rozdzielczości nie powinno przekraczać ~30–60s na klip na typowym CPU — jeśli przekracza, rozważyć ograniczenie liczby iteracji bitrate na krok, patrz sekcja 6).

## 13. Otwarte pytania / do decyzji przy developmencie

- Czy narzędzie ma też wspierać output w formacie WebM/VP9 jako alternatywę (część ad-networków akceptuje, ale MP4/H.264 jest najbezpieczniejszy wybór na start — **rekomendacja: zostać przy MP4 w v1**, WebM jako możliwe rozszerzenie).
- Czy potrzebny tryb batch (folder klipów naraz) — łatwe do dodania na bazie tej architektury, ale nie ma w v1 scope.
- Czy limit 450KB dotyczy samego pliku wideo, czy wideo jako część większego pakietu bannera (czy generator_*.py ma odejmować już zużytą wagę innych assetów przed wywołaniem tego toola) — jeśli tak, dodać `--max-kb` liczone dynamicznie z zewnątrz (już wspierane przez istniejącą flagę, tylko trzeba to spiąć w pipeline).
