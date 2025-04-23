import os, time
from flask import Flask, request, jsonify, Response, stream_with_context, send_file, abort
import yt_dlp

app = Flask(__name__)

# Use a "downloads" folder in your project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/', methods=['GET'])
def home():
    return open('templates/index.html').read()

@app.route('/download', methods=['POST'])
def download():
    # 1. Read JSON body
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # 2. Configure yt-dlp to download into DOWNLOAD_DIR
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        return jsonify({"error": f"Download Error: {e}"}), 500

    # 3. Find the downloaded file path
    file_path = ydl.prepare_filename(info)
    if not os.path.exists(file_path):
        return jsonify({"error": "Downloaded file not found"}), 500

    # 4. Stream file back to the caller as an attachment
    return send_file(
        file_path,
        as_attachment=True,
        download_name=os.path.basename(file_path),
        mimetype='application/octet-stream'
    )

@app.route('/progress', methods=['GET'])
def progress():
    def gen():
        for i in range(0, 101, 10):
            yield f"data: {{\"percent\": {i}}}\n\n"
            time.sleep(0.1)
    return Response(stream_with_context(gen()), mimetype='text/event-stream')

if __name__ == '__main__':
    # Use the PORT env var that Railway provides, default to 5000 locally
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
