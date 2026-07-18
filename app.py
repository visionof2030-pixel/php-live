from flask import Flask, request, Response, stream_with_context
import subprocess
import time
import threading
import queue

app = Flask(__name__)

SOURCE_URL = "http://arena940.xyz/live/018e49b001/4c0706010b/983525.ts"

# قائمة انتظار للبث
stream_queue = queue.Queue(maxsize=50)
ffmpeg_process = None
is_running = False

def start_stream():
    """تشغيل FFmpeg لسحب البث"""
    global ffmpeg_process, is_running
    
    if is_running:
        return
    
    cmd = [
        'ffmpeg',
        '-re',
        '-i', SOURCE_URL,
        '-c', 'copy',
        '-f', 'mpegts',
        '-mpegts_flags', '+resend_headers',
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
        
        def read_stream():
            while is_running:
                data = ffmpeg_process.stdout.read(8192)
                if data:
                    stream_queue.put(data)
                else:
                    break
        
        threading.Thread(target=read_stream, daemon=True).start()
        print("✅ FFmpeg started")
        
    except Exception as e:
        print(f"❌ Error: {e}")

@app.route('/stream.ts')
def stream():
    global is_running
    
    if not is_running:
        start_stream()
    
    def generate():
        while is_running:
            try:
                data = stream_queue.get(timeout=5)
                yield data
            except queue.Empty:
                yield b''
    
    return Response(
        stream_with_context(generate()),
        content_type='video/MP2T',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'
        }
    )

@app.route('/')
def home():
    return '''
    <h2>📡 IPTV Stream</h2>
    <video controls autoplay width="100%">
        <source src="/stream.ts" type="video/MP2T">
    </video>
    <p>VLC: <code>/stream.ts</code></p>
    '''

if __name__ == '__main__':
    start_stream()
    app.run(host='0.0.0.0', port=8080)