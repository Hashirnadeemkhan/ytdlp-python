import os, time
from flask import Flask, request, send_file, abort, Response, stream_with_context
import yt_dlp

app = Flask(__name__)
DOWNLOAD_DIR = '/tmp/downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/')
def index():
    return open('templates/index.html').read()  # your HTML 

@app.route('/progress')
def progress():
    def gen():
        for i in range(0, 101, 10):
            yield f"data: {{\"percent\": {i}}}\n\n"
            time.sleep(0.1)
    return Response(stream_with_context(gen()), mimetype='text/event-stream')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    if not url:
        abort(400, 'No URL provided')

    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        app.logger.error(f"Download failed: {e}")
        abort(500, f"Download Error: {e}")

    file_path = ydl.prepare_filename(info)
    if not os.path.exists(file_path):
        abort(500, 'Downloaded file not found')

    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
