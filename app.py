from flask import Flask, render_template, request, jsonify
import yt_dlp
import os
import subprocess

app = Flask(__name__)

# Storage Path for Gallery
if os.path.exists('/sdcard/Download'):
    DOWNLOAD_FOLDER = '/sdcard/Download/StudioDownloader'
else:
    DOWNLOAD_FOLDER = 'downloads'

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_video_info', methods=['POST'])
def get_video_info():
    data = request.get_json()
    url = data.get('url')
    if '.m3u8' in url:
        return jsonify({'success': True, 'title': 'HLS_Stream_Video', 'size_mb': 'Unknown', 'url': url})
    
    ydl_opts = {'quiet': True, 'no_warnings': True} 
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            size_bytes = info.get('filesize') or info.get('filesize_approx') or 0
            size_mb = round(size_bytes / (1024 * 1024), 2)
            title = info.get('title', 'Unknown Title')
            return jsonify({'success': True, 'title': title, 'size_mb': size_mb, 'url': url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download_videos', methods=['POST'])
def download_videos():
    data = request.get_json()
    urls = data.get('urls', [])
    quality = data.get('quality', '720') # Default 720p
    
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': True,
    }

    # Resolution Logic (with Fallback)
    if quality == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
    elif quality == '4k':
        ydl_opts['format'] = 'bestvideo[height<=2160]+bestaudio/best'
    else:
        # For 1080, 720, 480, 240
        ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(urls)
        
        try: subprocess.run(["termux-media-scan", DOWNLOAD_FOLDER], check=False)
        except: pass

        return jsonify({'success': True, 'message': f'Downloaded in {quality}p quality!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
