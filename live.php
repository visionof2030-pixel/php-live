<?php

$url = "https://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/405509.M3U8";

$ch = curl_init($url);

curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_TIMEOUT => 30,
    CURLOPT_USERAGENT => $_SERVER['HTTP_USER_AGENT'] ?? 'Mozilla/5.0',
]);

$response = curl_exec($ch);

if ($response === false) {
    http_response_code(500);
    exit(curl_error($ch));
}

$contentType = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
if ($contentType) {
    header("Content-Type: $contentType");
} else {
    header("Content-Type: application/vnd.apple.mpegurl");
}

curl_close($ch);

echo $response;
