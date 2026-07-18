from flask import Flask, request, Response, stream_with_context
import subprocess
import time
import threading
import queue
import signal
import os

app = Flask(__name__)

SOURCE_URL = "http://arena940.xyz/live/018e49b001/4c0706010b/983525.ts"

# قائمة لتخزين بيانات البث
stream_queue = queue.Queue(maxsize=100)
ffmpeg_process = None
stream_active = False

def start_ffmpeg():
    """تشغيل FFmpeg في الخلفية لسحب البث"""
    global ffmpeg_process, stream_active
    
    cmd = [
        'ffmpeg',
        '-re',                  # قراءة بسرعة البث الحقيقي
        '-i', SOURCE_URL,
        '-c', 'copy',           # نسخ بدون ترميز
        '-f', 'mpegts',         # صيغة MPEG-TS
        '-mpegts_flags', 'resend_headers',
        '-'
    ]
    
    try:
        ffmpeg_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0
        )
        stream_active = True
        print("✅ FFmpeg started successfully")
        
        # بدء قراءة البيانات في خيط منفصل
        def read_stream():
            while stream_active and ffmpeg_process:
                try:
                    data = ffmpeg_process.stdout.read(8192)
                    if data:
                        stream_queue.put(data)
                    else:
                        break
                except:
                    break
        
        threading.Thread(target=read_stream, daemon=True).start()
        return True
        
    except Exception as e:
        print(f"❌ FFmpeg error: {e}")
        stream_active = False
        return False

@app.route('/stream.ts')
def stream():
    """إرجاع البث من قائمة الانتظار"""
    global stream_active
    
    # تأكد من تشغيل FFmpeg
    if not stream_active or ffmpeg_process is None:
        if not start_ffmpeg():
            return "Failed to start stream", 500
    
    def generate():
        """توليد البيانات من قائمة الانتظار"""
        timeout_counter = 0
        while stream_active:
            try:
                # جلب البيانات من القائمة مع مهلة
                data = stream_queue.get(timeout=10)
                yield data
                timeout_counter = 0
            except queue.Empty:
                timeout_counter += 1
                # إذا لم تأتِ بيانات لمدة 30 ثانية، حاول إعادة التشغيل
                if timeout_counter > 3:
                    print("⏳ No data, restarting...")
                    restart_stream()
                    timeout_counter = 0
                yield b''  # أرسل بيانات فارغة لإبقاء الاتصال مفتوحاً
            except Exception as e:
                print(f"⚠️ Stream error: {e}")
                break
    
    return Response(
        stream_with_context(generate()),
        content_type='video/MP2T',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'Access-Control-Allow-Origin': '*',
            'Content-Disposition': 'inline',
            'Connection': 'keep-alive'
        }
    )

def restart_stream():
    """إعادة تشغيل البث"""
    global ffmpeg_process, stream_active
    if ffmpeg_process:
        ffmpeg_process.terminate()
        ffmpeg_process = None
    stream_active = False
    time.sleep(2)
    start_ffmpeg()

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
                background: #ffaa00;
                color: #000;
                font-weight: bold;
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
                Your browser doesn't support this stream.
            </video>
            
            <div class="info">
                <p><strong>Status:</strong> <span id="status" class="status">⏳ Connecting...</span></p>
                <p><strong>VLC / IPTV URL:</strong></p>
                <code>{request.host_url}stream.ts</code>
                <button class="btn" onclick="copyToClipboard()">📋 Copy URL</button>
            </div>
        </div>
        
        <script>
            const video = document.getElementById('video');
            const status = document.getElementById('status');
            
            function updateStatus(text, color='#ffaa00') {{
                status.textContent = text;
                status.style.background = color;
                status.style.color = '#000';
            }}
            
            video.addEventListener('playing', function() {{
                updateStatus('● LIVE', '#00ff88');
            }});
            
            video.addEventListener('waiting', function() {{
                updateStatus('⏳ Buffering...', '#ffaa00');
            }});
            
            video.addEventListener('error', function(e) {{
                updateStatus('⚠️ Reconnecting...', '#ff4444');
                setTimeout(() => {{
                    video.load();
                    video.play();
                }}, 3000);
            }});
            
            // محاولة التشغيل التلقائي
            setTimeout(() => {{
                video.play().catch(() => {{
                    updateStatus('▶️ Click play to start', '#8888ff');
                }});
            }}, 1000);
            
            function copyToClipboard() {{
                const url = '{request.host_url}stream.ts';
                navigator.clipboard.writeText(url).then(() => {{
                    alert('URL copied to clipboard!');
                }});
            }}
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    # بدء البث عند تشغيل السيرفر
    start_ffmpeg()
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)