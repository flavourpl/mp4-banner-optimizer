# Admin Panel - Upload History

## 🎯 Dostęp do Panelu Admin

### Lokalny dostęp:
```
http://127.0.0.1:8888/admin/uploads
```

### Dostęp po deployment:
```
https://vid.flavour.pl/admin/uploads
```

## 🔐 Autoryzacja

**Login:** `admin`
**Hasło:** `admin123`

*(Można zmienić w `index.php` linia 12: `define('ADMIN_PASSWORD', 'twoje_haslo');`)*

## 📊 Funkcje Panelu Admin

### 1. Przeglądanie Historii Uploadów
- Kompletna historia wszystkich wgranych plików
- Czas uploadu, rozmiary, status przetwarzania
- Stopa kompresji dla każdego pliku

### 2. Statystyki
- **Total Uploads:** Liczba wszystkich uploadów
- **Processed Successfully:** Liczba ukończonych procesów
- **Pending/Failed:** Liczba oczekujących lub nieudanych
- **Reports Generated:** Liczba wygenerowanych raportów

### 3. Akcje na Plikach
- **📥 Download** - Pobierz zoptymalizowany plik
- **📊 Report** - Pobierz raport techniczny
- **🔍 Details** - Szczegóły procesu optymalizacji

### 4. API Endpoint
```bash
# Pobierz listę wszystkich plików jako JSON
curl -u admin:admin123 https://vid.flavour.pl/admin/files
```

## 🌐 Struktura URL

```
/ (Portal)           → Wybór aplikacji
/app (Main App)      → Główna aplikacja upload
/admin/uploads        → Panel admin z historią
/admin/files         → API endpoint (JSON)
/api/*               → API endpoints dla główniej aplikacji
```

## 🔄 Automatyczne Odświeżanie

Panel admin odświeża się automatycznie co 30 sekund aby pokazać najnowsze statusy przetwarzania.

## 📱 Mobilny Dostęp

Panel admin jest w pełni responsywny i działa na urządzeniach mobilnych.

## 🔧 Konfiguracja

### Zmiana hasła admin:
```php
// W index.php linia 12:
define('ADMIN_PASSWORD', 'twoje_nowe_haslo');
```

### Wyłączenie autoryzacji (niezalecane):
```php
// W index.php zakomentuj sekcję autoryzacji:
/*
if (strpos($_SERVER['REQUEST_URI'], '/admin') === 0) {
    // ... kod autoryzacji ...
}
*/
```

## 🚀 Bezpieczeństwo

1. **Hasło:** Domyślne hasło `admin123` - zmień je przy pierwszym uruchomieniu
2. **HTTPS:** Na produkcji używaj HTTPS dla bezpiecznego transferu
3. **IP Restriction:** Opcjonalnie możesz dodać ograniczenie IP w PHP

### Ograniczenie IP (opcjonalne):
```php
// W index.php dodaj po autoryzacji:
$allowed_ips = ['127.0.0.1', 'YOUR_IP_ADDRESS'];
if (!in_array($_SERVER['REMOTE_ADDR'], $allowed_ips)) {
    http_response_code(403);
    echo json_encode(['error' => 'Access denied']);
    exit();
}
```

## 📋 Przykład Użycia

### 1. Przeglądanie historii:
1. Otwórz: `http://127.0.0.1:8888/admin/uploads`
2. Zaloguj się: `admin` / `admin123`
3. Przeglądaj tabelę z historią uploadów
4. Kliknij przyciski aby pobierać pliki lub raporty

### 2. Pobranie raportu API:
```bash
curl -u admin:admin123 https://vid.flavour.pl/admin/files
```

### 3. Monitorowanie w czasie rzeczywistym:
- Panel odświeża się automatycznie co 30 sekund
- Ręczne odświeżenie: przycisk "🔄 Refresh"

## 🛠️ Rozwiązywanie Problemów

### Nie można zalogować:
- Sprawdź login: `admin`
- Sprawdź hasło: `admin123` (domyślne)
- Sprawdź czy przeglądarka wspiera HTTP Basic Auth

### Pusta tabela uploadów:
- To normalne jeśli jeszcze nie było żadnych uploadów
- Wróć do głównej aplikacji i wgraj plik testowy

### Błędy autoryzacji:
- Sprawdź czy hasło zostało zmienione w `index.php`
- Wyczyść cache przeglądarki i spróbuj ponownie

---

**Panel admin jest gotowy do użycia!** 🎯