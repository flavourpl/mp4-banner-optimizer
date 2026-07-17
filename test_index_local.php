<?php
/**
 * MP4 Banner Optimizer - PHP Bridge
 * Proxies requests between frontend and Python Flask backend
 */

// Error reporting for debugging
error_reporting(E_ALL);
ini_set('display_errors', 0); // Don't show errors in output
ini_set('log_errors', 1);
ini_set('error_log', __DIR__ . '/php_bridge.log');

// Backend configuration
define("BACKEND_URL", "http://127.0.0.1:6000");;
define('REQUEST_TIMEOUT', 300); // 5 minutes for video processing

// CORS headers
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// Handle OPTIONS preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

/**
 * Log debug information
 */
function debug_log($message) {
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents(__DIR__ . '/php_bridge.log', "[$timestamp] $message\n", FILE_APPEND);
}

/**
 * Determine target URL for backend
 */
function get_target_url() {
    $request_path = $_SERVER['REQUEST_URI'];

    // Remove query string for path processing
    $path_parts = parse_url($request_path);
    $path = $path_parts['path'] ?? '/';

    // Rebuild with query string if present
    $target_url = BACKEND_URL . $path;
    if (!empty($_SERVER['QUERY_STRING'])) {
        $target_url .= '?' . $_SERVER['QUERY_STRING'];
    }

    debug_log("Request: {$_SERVER['REQUEST_METHOD']} $request_path -> $target_url");
    return $target_url;
}

/**
 * Execute cURL request to backend
 */
function proxy_request($target_url, $method = 'GET', $post_data = null, $files = null) {
    $ch = curl_init();

    curl_setopt($ch, CURLOPT_URL, $target_url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, REQUEST_TIMEOUT);
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);

    // Handle different request methods
    switch ($method) {
        case 'POST':
            curl_setopt($ch, CURLOPT_POST, true);

            if ($files) {
                // Handle file uploads
                $post_fields = [];

                // Add uploaded file
                if (isset($files['file'])) {
                    $file = $files['file'];
                    if (is_uploaded_file($file['tmp_name'])) {
                        $post_fields['file'] = new CURLFile(
                            $file['tmp_name'],
                            $file['type'],
                            $file['name']
                        );
                        debug_log("File upload: {$file['name']} ({$file['size']} bytes)");
                    }
                }

                // Add form fields
                if ($post_data && is_array($post_data)) {
                    foreach ($post_data as $key => $value) {
                        $post_fields[$key] = $value;
                    }
                }

                curl_setopt($ch, CURLOPT_POSTFIELDS, $post_fields);
            } elseif ($post_data) {
                // Regular POST data
                if (is_array($post_data)) {
                    curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($post_data));
                } else {
                    curl_setopt($ch, CURLOPT_POSTFIELDS, $post_data);
                }
            }
            break;

        case 'GET':
        default:
            // GET request - no special handling needed
            break;
    }

    // Capture response headers
    $response_headers = [];
    curl_setopt($ch, CURLOPT_HEADERFUNCTION, function($curl, $header) use (&$response_headers) {
        $len = strlen($header);
        $header = trim($header);
        if (!empty($header)) {
            if (strpos($header, ':') !== false) {
                list($key, $value) = explode(':', $header, 2);
                $response_headers[trim($key)] = trim($value);
            }
        }
        return $len;
    });

    // Execute request
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $content_type = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
    $error = curl_error($ch);
    curl_close($ch);

    if ($error) {
        debug_log("cURL Error: $error");
    }

    debug_log("Response: HTTP $http_code, Content-Type: $content_type");

    return [
        'body' => $response,
        'code' => $http_code,
        'content_type' => $content_type,
        'headers' => $response_headers
    ];
}

/**
 * Main request handling
 */
try {
    $target_url = get_target_url();
    $method = $_SERVER['REQUEST_METHOD'];

    // Prepare POST data
    $post_data = null;
    $files = null;

    if ($method === 'POST') {
        // Check for file uploads
        if (!empty($_FILES)) {
            $files = $_FILES;
            $post_data = $_POST; // Form fields
        } else {
            // Regular POST data
            $post_data = file_get_contents('php://input');

            // Try to decode as JSON
            $json_data = json_decode($post_data, true);
            if ($json_data !== null) {
                $post_data = $json_data;
            }
        }
    }

    // Execute proxy request
    $result = proxy_request($target_url, $method, $post_data, $files);

    // Set response headers
    if (!empty($result['content_type'])) {
        header("Content-Type: {$result['content_type']}");
    }

    // Forward important headers
    if (isset($result['headers']['Content-Disposition'])) {
        header("Content-Disposition: {$result['headers']['Content-Disposition']}");
    }

    // Set HTTP status code
    http_response_code($result['code']);

    // Output response body
    echo $result['body'];

    debug_log("Request completed successfully");

} catch (Exception $e) {
    debug_log("Exception: " . $e->getMessage());
    http_response_code(500);
    header('Content-Type: application/json');
    echo json_encode([
        'error' => 'PHP Bridge Error',
        'message' => 'An error occurred processing your request'
    ]);
}
?>