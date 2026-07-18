from flask import Flask, request, Response, send_file
import requests
import os
import time
import threading
import subprocess
import tempfile

app = Flask(__name__)

SOURCE_URL = "http://arena940.xyz/live/018e49b001/4c0706010b/983525.ts"

# استخدام FFmpeg لتحويل البث إلى HLS
@app.route('/playlist.m3u8')
def playlist():
    try:
        # تشغيل FFmpeg لإنشاء HLS
        temp_dir = tempfile.mkdtemp()
        playlist_path = os.path.join(temp_dir, 'stream.m3u8')
        
        cmd = [
            'ffmpeg',
            '-i', SOURCE_URL,
            '-c', 'copy',
            '-f', 'hls',
            '-hls_time', '5',
            '-hls_list_size', '5',
            '-hls_flags', 'delete_segments+append_list',
            '-hls_segment_filename', os.path.join(temp_dir, 'segment_%03d.ts'),
            playlist_path
        ]
        
        # تشغيل FFmpeg في الخلفية
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # انتظر قليلاً حتى يتم إنشاء الملف
        time.sleep(2)
        
        # اقرأ ملف الـ M3U8 وأعدله ليستخدم مساراتنا
        with open(playlist_path, 'r') as f:
            content = f.read()
        
        # استبدل مسارات المقاطع بمسارات محلية
        content = content.replace('segment_', '/segment_')
        
        return Response(content, content_type='application/vnd.apple.mpegurl')
    
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/segment_<int:num>.ts')
def serve_segment(num):
    try:
        # ابحث عن المقطع في المجلد المؤقت
        for temp_dir in ['/tmp', '/var/tmp']:
            segment_path = os.path.join(temp_dir, f'segment_{num:03d}.ts')
            if os.path.exists(segment_path):
                return send_file(segment_path, mimetype='video/MP2T')
        
        # إذا لم يوجد، حاول جلب المقطع من المصدر مباشرة
        resp = requests.get(SOURCE_URL, stream=True)
        return Response(resp.iter_content(chunk_size=1024), 
                       content_type='video/MP2T')
    except Exception as e:
        return f"Error: {str(e)}", 404

@app.route('/')
def home():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>IPTV Proxy</title>
    </head>
    <body>
        <h2>📡 IPTV Proxy</h2>
        <p>Use this URL in VLC or any player:</p>
        <code style="background:#f0f0f0;padding:10px;display:block;margin:10px 0;">
            {request.host_url}playlist.m3u8
        </code>
        
        <h3>🌐 Watch in Browser:</h3>
        <video id="video" controls width="800" style="max-width:100%;">
            <source src="{request.host_url}playlist.m3u8" type="application/vnd.apple.mpegurl">
            Your browser doesn't support HLS.
        </video>
        
        <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
        <script>
            const video = document.getElementById('video');
            if (Hls.isSupported()) {{
                const hls = new Hls();
                hls.loadSource('{request.host_url}playlist.m3u8');
                hls.attachMedia(video);
                hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                    video.play();
                }});
            }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                video.src = '{request.host_url}playlist.m3u8';
            }}
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)