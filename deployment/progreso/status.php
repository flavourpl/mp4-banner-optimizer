<?php
/**
 * status.php — health check NIEZALEŻNY od PHP bridge (index.php).
 *
 * Apache serwuje ten plik bezpośrednio (reguła rewrite w .htaccess ma warunek
 * %{REQUEST_FILENAME} !-f), więc odpowiada nawet wtedy, gdy proces Pythona
 * nie działa — w przeciwieństwie do /api/health, które przechodzi przez
 * bridge i pada razem z backendem.
 *
 * Użycie:
 *   curl -s https://vid.flavour.pl/status.php
 *   {"alive":true,"port_open":true,"http_code":200,"checks":{...},...}
 *
 * HTTP 200 = usługa żyje, HTTP 503 = proces nie działa lub health check się nie powiódł.
 * Nadaje się do monitoringu zewnętrznego (np. UptimeRobot — słowo kluczowe: "alive":true).
 */

header('Content-Type: application/json');
header('Cache-Control: no-store');

define('BACKEND_HOST', '127.0.0.1');
define('BACKEND_PORT', 5000);

$status = [
    'alive'   => false,
    'backend' => BACKEND_HOST . ':' . BACKEND_PORT,
    'time'    => date('c'),
];

// 1) Czy proces nasłuchuje na porcie?
$errno  = 0;
$errstr = '';
$conn = @fsockopen(BACKEND_HOST, BACKEND_PORT, $errno, $errstr, 2);
if (!$conn) {
    $status['error'] = "backend unreachable: $errstr ($errno)";
    http_response_code(503);
    echo json_encode($status);
    exit;
}
fclose($conn);
$status['port_open'] = true;

// 2) Czy /api/health zwraca "ok"? (ffmpeg, ffprobe, katalogi robocze)
$ch = curl_init('http://' . BACKEND_HOST . ':' . BACKEND_PORT . '/api/health');
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_CONNECTTIMEOUT => 2,
    CURLOPT_TIMEOUT        => 5,
]);
$body       = curl_exec($ch);
$http_code  = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curl_error = curl_error($ch);
curl_close($ch);

if ($body === false) {
    $status['error'] = "health check failed: $curl_error";
    http_response_code(503);
    echo json_encode($status);
    exit;
}

$data = json_decode($body, true);
$status['http_code'] = $http_code;
$status['checks']    = $data['checks'] ?? null;
$status['alive']     = ($http_code === 200 && ($data['status'] ?? '') === 'ok');

if (!$status['alive']) {
    $status['error'] = 'backend responded but health checks failed';
    http_response_code(503);
}

echo json_encode($status);
