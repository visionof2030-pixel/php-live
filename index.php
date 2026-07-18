<?php

// إظهار الأخطاء (احذف هذه الأسطر بعد الانتهاء من الاختبار)
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

// رابط البث
$url = "https://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/405509.M3U8";

// إنشاء اتصال cURL
$ch = curl_init($url);

curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_TIMEOUT => 30,
    CURLOPT_SSL_VERIFYPEER => false,
    CURLOPT_SSL_VERIFYHOST => false,
    CURLOPT_USERAGENT => $_SERVER['HTTP_USER_AGENT'] ?? 'Mozilla/5.0',
]);

$response = curl_exec($ch);

if ($response === false) {
    http_response_code(500);
    die("cURL Error: " . curl_error($ch));
}

// الحصول على نوع المحتوى
$contentType = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);

curl_close($ch);

// إرسال نوع المحتوى
header("Content-Type: " . ($contentType ?: "application/vnd.apple.mpegurl"));

echo $response;
