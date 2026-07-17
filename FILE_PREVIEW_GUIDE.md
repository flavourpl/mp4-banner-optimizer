# File Preview Functionality - User Guide

## 🎬 Nowa Funkcjonalność: Podgląd Plików

Panel admin teraz zawiera pełną funkcjonalność podglądu i porównywania plików wideo!

## 📊 Dostęp

**URL:** `http://127.0.0.1:8888/admin/uploads`
**Login:** `admin` / `admin123`

## ✨ Nowe Funkcje

### 1. Miniatury Wideo 📸
- Automatycznie generowane miniaturki (320x180px)
- Podgląd zoptymalizowanego wideo przed pobraniem
- Interaktywne hover effects

### 2. Modal Video Player 🎥
- Kliknij miniaturę aby otworzyć modal
- Odtwarzanie wideo bezpośrednio w panelu
- HTML5 video player z kontrolkami
- Pełny ekran dostępny

### 3. Porównianie Plików 🔄
- **Przycisk "Compare"** dla każdego zoptymalizowanego pliku
- Porównanie rozmiarów: Original vs Optimized
- Stopa kompresji z dokładnymi procentami
- Porównanie rozdzielczości i jakości

### 4. Szczegółowe Statystyki 📈
- **Original Size:** Rozmiar oryginalnego pliku
- **Optimized Size:** Rozmiar po kompresji
- **Compression Ratio:** Procent oszczędności
- **Saved KB:** Zaoszczędzone kilobajty
- **Resolution:** Rozdzielczość wideo
- **Duration:** Długość wideo

## 🎯 Przykład Użycia

### Test Case: Rzeczywisty Upload
Z panelu pokazuje prawdziwe dane z wcześniejszych testów:

**Job ID:** `5e2e4472-a587-469f-af05-f307217ba6e6`

**Wyniki Optymalizacji:**
- ✅ **Original:** 4,837 KB (784x1168, 24fps)
- ✅ **Optimized:** 378 KB (300x400, 24fps)
- ✅ **Compression:** 92.19% oszczędności!
- ✅ **Saved:** 4,459 KB

## 🔧 Funkcje Techniczne

### Generowanie Miniatur
```bash
# FFmpeg automatycznie generuje miniaturki
ffmpeg -i video.mp4 -ss 00:00:01 -vframes 1 -vf scale=320:180 thumbnail.jpg
```

### API Endpointy
```bash
# Podgląd metadanych
curl -u admin:admin123 http://127.0.0.1:8888/admin/preview/<job_id>

# Porównanie plików
curl -u admin:admin123 http://127.0.0.1:8888/admin/compare/<job_id>

# Pobieranie miniatury
curl -u admin:admin123 http://127.0.0.1:8888/admin/thumbnail/<job_id>
```

## 💡 Jak Używać

### 1. Przeglądanie Historii
1. Otwórz panel admin: `http://127.0.0.1:8888/admin/uploads`
2. Zaloguj się: `admin` / `admin123`
3. Przeglądaj tabelę z miniaturami

### 2. Podgląd Wideo
1. Kliknij miniaturę w kolumnie "Preview"
2. Otworzy się modal z odtwarzaczem wideo
3. Oglądaj zoptymalizowane wideo bezpośrednio

### 3. Porównanie Plików
1. Kliknij przycisk "🔄 Compare" w kolumnie "Actions"
2. Zobaczysz szczegółowe porównanie:
   - Rozmiary plików
   - Stopa kompresji
   - Rozdzielczości
   - Zaoszczędzone miejsce

### 4. Pobieranie
1. **📥 Download** - pobierz zoptymalizowany plik
2. **📊 Report** - pobierz techniczny raport
3. **🔄 Compare** - porównaj oryginał z optymalizacją

## 🎨 Interface

### Kolory Statusów:
- 🟢 **Zielony** - Kompletna optymalizacja
- 🟡 **Żółty** - Przetwarzanie w toku
- 🔴 **Czerwony** - Błąd przetwarzania

### Przyciski:
- **📥 Download** - Pobierz plik
- **📊 Report** - Raport techniczny
- **🔄 Compare** - Porównanie
- **🔍 Details** - Szczegóły procesu

## 📱 Responsywność

Panel admin jest w pełni responsywny:
- ✅ Desktop - Pełna funkcjonalność
- ✅ Tablet - Dostosowany layout
- ✅ Mobile - Zoptymalizowany widok

## 🔒 Bezpieczeństwo

- ✅ Hasło chronione (HTTP Basic Auth)
- ✅ Tylko uprawnieni użytkownicy
- ✅ Miniatury generowane lokalnie
- ✅ Bez dostępu do zewnętrznych serwerów

## 🚀 Performance

- Miniatury generowane jednorazowo
- Cache'owane w folderze `reports/thumbnails/`
- Auto-refresh co 30 sekund
- Fast loading z lazy loading

---

## 🎯 Przykładowy Workflow

1. **Upload:** Wgraj plik w głównej aplikacji
2. **Process:** Czekaj na zakończenie optymalizacji
3. **Preview:** Otwórz panel admin
4. **Compare:** Kliknij "Compare" aby zobaczyć wyniki
5. **Download:** Pobierz zoptymalizowany plik

**Panel admin teraz jest kompletnym narzędziem do zarządzania historią uploadów!** 🎊