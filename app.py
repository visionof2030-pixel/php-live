from flask import Flask, request, Response, redirect
import requests
import re

app = Flask(__name__)

SOURCE_URL = "https://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/405509.M3U8"
BASE_URL = "https://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/"

# نفس الإعدادات التي يستخدمها VLC
HEADERS = {
    'User-Agent': 'VLC/3.0.18 LibVLC/3.0.18',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://mavpro.xyz/',
}

@app.route('/proxy.m3u8')
def proxy_m3u8():
    try:
        # محاكاة طلب VLC بالضبط
        resp = requests.get(SOURCE_URL, headers=HEADERS, timeout=15, verify=False)
        
        if resp.status_code == 200:
            content = resp.text
            # تصحيح روابط المقاطع
            content = re.sub(r'(https?://[^\s]+\.ts)', r'/proxy/\1', content)
            return Response(content, content_type='application/vnd.apple.mpegurl')
        else:
            return f"Error: {resp.status_code} - {resp.text[:200]}", resp.status_code
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/proxy/<path:segment_url>')
def proxy_segment(segment_url):
    try:
        # طلب المقطع بنفس الإعدادات
        resp = requests.get(segment_url, headers=HEADERS, stream=True, timeout=15, verify=False)
        return Response(resp.iter_content(chunk_size=1024), 
                       content_type='video/MP2T')
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/')
def home():
    return f"""
    <h2>M3U8 Proxy (VLC Mode)</h2>
    <p>Use this URL in VLC or IPTV Smarter:</p>
    <code>{request.host_url}proxy.m3u8</code>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)