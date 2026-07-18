from flask import Flask, request, Response, stream_with_context
import requests
import time

app = Flask(__name__)

SOURCE_URL = "http://arena940.xyz/live/018e49b001/4c0706010b/983525.ts"

@app.route('/stream.ts')
def stream():
    """إعادة تمرير البث مباشرة"""
    try:
        # طلب البث من المصدر مع إعدادات مناسبة
        headers = {
            'User-Agent': 'VLC/3.0.18 LibVLC/3.0.18',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }
        
        resp = requests.get(
            SOURCE_URL, 
            headers=headers, 
            stream=True, 
            timeout=30
        )
        
        if resp.status_code != 200:
            return f"Error: {resp.status_code}", resp.status_code
        
        # إرجاع البث مباشرة للمتصفح
        def generate():
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        
        return Response(
            stream_with_context(generate()),
            content_type='video/MP2T',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'Access-Control-Allow-Origin': '*',
                'Content-Disposition': 'inline'
            }
        )
    
    except requests.exceptions.RequestException as e:
        return f"Connection error: {str(e)}", 500
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/')
def home():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>IPTV Live Proxy</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #0a0a0a;
                color: white;
                margin: 0;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
            }}
            .container {{
                max-width: 900px;
                width: 100%;
                background: #1a1a1a;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.8);
            }}
            h2 {{
                color: #00ff88;
                text-align: center;
                margin-bottom: 20px;
            }}
            video {{
                width: 100%;
                border-radius: 10px;
                background: #000;
                max-height: 600px;
            }}
            .info {{
                background: #222;
                padding: 15px;
                border-radius: 10px;
                margin-top: 15px;
            }}
            code {{
                background: #333;
                padding: 8px 12px;
                border-radius: 5px;
                color: #00ff88;
                word-break: break-all;
                display: block;
                margin: 10px 0;
            }}
            .status {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                background: #00ff88;
                color: #000;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 20px;
                text-align: center;
                color: #666;
                font-size: 14px;
            }}
            .btn {{
                background: #00ff88;
                color: #000;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                cursor: pointer;
                margin-top: 10px;
            }}
            .btn:hover {{
                background: #00cc66;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📡 IPTV Live Stream</h2>
            
            <video id="video" controls autoplay muted playsinline>
                <source src="/stream.ts" type="video/MP2T">
                <source src="/stream.ts" type="video/mp2t">
                Your browser doesn't support this stream.
            </video>
            
            <div class="info">
                <p><strong>Status:</strong> <span id="status" class="status">● LIVE</span></p>
                <p><strong>VLC / IPTV URL:</strong></p>
                <code>{request.host_url}stream.ts</code>
                <button class="btn" onclick="copyToClipboard()">📋 Copy URL</button>
            </div>
            
            <div class="footer">
                Powered by Flask Proxy | Stream from: arena940.xyz
            </div>
        </div>
        
        <script>
            const video = document.getElementById('video');
            const status = document.getElementById('status');
            
            // محاولة إعادة التشغيل تلقائياً إذا توقف
            video.addEventListener('error', function() {{
                status.textContent = '⚠️ Reconnecting...';
                status.style.background = '#ffaa00';
                status.style.color = '#000';
                setTimeout(() => {{
                    video.load();
                    video.play();
                    status.textContent = '● LIVE';
                    status.style.background = '#00ff88';
                    status.style.color = '#000';
                }}, 3000);
            }});
            
            video.addEventListener('playing', function() {{
                status.textContent = '● LIVE';
                status.style.background = '#00ff88';
                status.style.color = '#000';
            }});
            
            video.addEventListener('waiting', function() {{
                status.textContent = '⏳ Buffering...';
                status.style.background = '#ffaa00';
                status.style.color = '#000';
            }});
            
            // نسخ الرابط
            function copyToClipboard() {{
                const url = '{request.host_url}stream.ts';
                navigator.clipboard.writeText(url).then(() => {{
                    alert('URL copied to clipboard!');
                }});
            }}
            
            // إعادة المحاولة كل 10 ثوانٍ إذا توقف
            setInterval(() => {{
                if (video.paused && video.currentTime === 0 && !video.ended) {{
                    video.play();
                }}
            }}, 10000);
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)