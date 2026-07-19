from flask import Flask, request, Response, stream_with_context, jsonify
import subprocess
import time
import threading
import queue
import os
import signal

app = Flask(__name__)

# ===== الإعدادات =====
SOURCE_URL = "http://arena940.xyz/live/018e49b001/4c0706010b/983525.ts"
STREAM_QUEUE = queue.Queue(maxsize=100)
ffmpeg_process = None
is_running = False
connected_clients = 0
clients_lock = threading.Lock()

# ===== تشغيل FFmpeg =====
def start_ffmpeg():
    global ffmpeg_process, is_running

    cmd = [
        'ffmpeg',
        '-re',                     # قراءة بسرعة البث الحقيقي
        '-i', SOURCE_URL,
        '-c', 'copy',              # نسخ بدون ترميز (سريع)
        '-f', 'mpegts',            # صيغة MPEG-TS
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
        is_running = True
        print("✅ FFmpeg started successfully")

        def read_stream():
            while is_running and ffmpeg_process:
                try:
                    data = ffmpeg_process.stdout.read(8192)
                    if data:
                        STREAM_QUEUE.put(data)
                    else:
                        break
                except:
                    break

        threading.Thread(target=read_stream, daemon=True).start()
        return True
    except Exception as e:
        print(f"❌ FFmpeg error: {e}")
        is_running = False
        return False

# ===== مسار البث (لجميع الأجهزة) =====
@app.route('/stream.ts')
def stream():
    global connected_clients

    if not is_running:
        start_ffmpeg()

    with clients_lock:
        connected_clients += 1
        client_id = connected_clients
        print(f"📱 Client #{client_id} connected. Total: {connected_clients}")

    def generate():
        timeout_counter = 0
        while True:
            try:
                data = STREAM_QUEUE.get(timeout=5)
                yield data
                timeout_counter = 0
            except queue.Empty:
                timeout_counter += 1
                if timeout_counter > 10:
                    print(f"⏳ Client #{client_id} timed out")
                    break
                yield b''

    try:
        response = Response(
            stream_with_context(generate()),
            content_type='video/MP2T',
            headers={
                'Cache-Control': 'no-cache, no-store',
                'Access-Control-Allow-Origin': '*',
                'Connection': 'keep-alive'
            }
        )
    finally:
        with clients_lock:
            connected_clients -= 1
            print(f"📱 Client #{client_id} disconnected. Total: {connected_clients}")

    return response

# ===== صفحة رئيسية تعرض حالة البث =====
@app.route('/')
def home():
    status = "🟢 Live" if is_running else "🔴 Offline"
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📡 Restream Proxy</title>
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            body {{
                background: #0a0a0a;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                font-family: -apple-system, 'Segoe UI', Roboto, sans-serif;
                padding: 20px;
            }}
            .container {{
                background: #111;
                padding: 30px;
                border-radius: 24px;
                max-width: 500px;
                width: 100%;
                border: 1px solid #222;
                text-align: center;
            }}
            h1 {{ color: #00ff88; font-size: 28px; }}
            .status {{
                display: inline-block;
                padding: 5px 20px;
                border-radius: 20px;
                background: #00ff88;
                color: #000;
                font-weight: bold;
                margin: 10px 0;
            }}
            .info {{
                background: #1a1a1a;
                padding: 15px;
                border-radius: 12px;
                margin: 15px 0;
                text-align: right;
            }}
            .info p {{ color: #aaa; font-size: 14px; margin: 5px 0; }}
            code {{
                display: block;
                background: #0a0a0a;
                padding: 10px;
                border-radius: 8px;
                color: #00ff88;
                word-break: break-all;
                font-size: 12px;
                border: 1px solid #222;
            }}
            .footer {{ color: #333; font-size: 11px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📡 Restream Proxy</h1>
            <div class="status">{status}</div>
            <p style="color:#666;font-size:13px;">يعمل كـ Proxy لتوزيع البث على عدة أجهزة</p>

            <div class="info">
                <p>📱 <strong>المتصفح / VLC:</strong></p>
                <code>{request.host_url}stream.ts</code>
                <p style="margin-top:10px;">📊 <strong>عدد الأجهزة المتصلة:</strong> {connected_clients}</p>
                <p>📦 <strong>حالة التخزين المؤقت:</strong> {STREAM_QUEUE.qsize()} حزمة</p>
            </div>

            <p style="color:#555;font-size:12px;">
                💡 افتح هذا الرابط على عدة أجهزة لمشاهدة البث معاً
            </p>
            <div class="footer">⚡ Restream Proxy | يعمل على جميع الأجهزة</div>
        </div>
    </body>
    </html>
    """

# ===== مسار لحالة النظام (API) =====
@app.route('/status')
def status():
    return jsonify({
        "stream": "live" if is_running else "offline",
        "clients": connected_clients,
        "queue_size": STREAM_QUEUE.qsize()
    })

# ===== إغلاق آمن عند التوقف =====
@app.route('/shutdown', methods=['POST'])
def shutdown():
    global is_running, ffmpeg_process
    is_running = False
    if ffmpeg_process:
        ffmpeg_process.terminate()
        ffmpeg_process = None
    return "🔴 Shutting down..."

if __name__ == '__main__':
    start_ffmpeg()
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)