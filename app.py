from flask import Flask, request, Response, redirect
import requests
import re

app = Flask(__name__)
SOURCE_URL = "https://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/405509.M3U8"
BASE_URL = "https://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/"

@app.route('/proxy.m3u8')
def proxy_m3u8():
    try:
        resp = requests.get(SOURCE_URL, timeout=10)
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
        # إعادة توجيه طلب المقطع
        full_url = segment_url
        resp = requests.get(full_url, stream=True, timeout=10)
        return Response(resp.iter_content(chunk_size=1024), 
                       content_type='video/MP2T')
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/')
def home():
    return """
    <h2>M3U8 Proxy</h2>
    <p>Use this URL in VLC:</p>
    <code>{}/proxy.m3u8</code>
    """.format(request.host_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
