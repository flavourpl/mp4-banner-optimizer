<?php
define('BACKEND_URL', 'http://127.0.0.1:6000');
echo "Proxying to: " . BACKEND_URL . "\n";

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, BACKEND_URL . '/api/presets');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

header('Content-Type: application/json');
http_response_code($http_code);
echo $response;
?>
