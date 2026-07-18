from flask import Flask, request, Response
import requests
import re

app = Flask(__name__)

SOURCE_URL = "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/405509.M3U8"
BASE_URL = "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/"

# ⬇️⬇️⬇️ هنا نضيف الـ Headers ⬇️⬇️⬇️
HEADERS = {
    'User-Agent': 'VLC/3.0.18 LibVLC/3.0.18',  # محاكاة هوية VLC
    'Accept': '*/*',                             # نقبل أي نوع محتوى
    'Accept-Encoding': 'gzip, deflate, br',     # دعم الضغط
    'Connection': 'keep-alive',                 # ابق الاتصال مفتوحاً
    'Referer': 'https://mavpro.xyz/',           # نوهم الخادم أن الطلب من موقعه
    'Origin': 'https://mavpro.xyz',             # أصل الطلب
}
# ⬆️⬆️⬆️ انتهى الجزء المضافة ⬆️⬆️⬆️

@app.route('/proxy.m3u8')
def proxy_m3u8():
    try:
        # ⬇️⬇️⬇️ هنا نستخدم الـ Headers ⬇️⬇️⬇️
        resp = requests.get(
            SOURCE_URL, 
            headers=HEADERS,      # <---- نمرر الـ Headers هنا
            timeout=15, 
            verify=False          # <---- تجاهل مشاكل SSL (مثل -k في curl)
        )
        # ⬆️⬆️⬆️ انتهى ⬆️⬆️⬆️
        
        if resp.status_code == 200:
            content = resp.text
            # تعديل روابط المقاطع لتوجيهها عبر الوكيل
            content = re.sub(r'(https?://[^\s]+\.ts)', r'/proxy/\1', content)
            return Response(content, content_type='application/vnd.apple.mpegurl')
        else:
            return f"Error: {resp.status_code}", resp.status_code
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/proxy/<path:segment_url>')
def proxy_segment(segment_url):
    try:
        # ⬇️⬇️⬇️ هنا أيضاً نستخدم الـ Headers للمقاطع ⬇️⬇️⬇️
        resp = requests.get(
            segment_url, 
            headers=HEADERS,      # <---- نفس الـ Headers للمقاطع
            stream=True, 
            timeout=15, 
            verify=False          # <---- تجاهل SSL أيضاً
        )
        # ⬆️⬆️⬆️ انتهى ⬆️⬆️⬆️
        
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
    <br><br>
    <p>Or test with curl:</p>
    <code>curl -k "{request.host_url}proxy.m3u8"</code>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)