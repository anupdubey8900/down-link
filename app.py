from flask import Flask, render_template, request, jsonify
import yt_dlp
import os
import subprocess

app = Flask(__name__)

# 🔥 FIX: Android ki main Gallery/Download folder ka rasta
# Termux mein 'termux-setup-storage' karne ke baad ye rasta banta hai
if os.path.exists('/sdcard/Download'):
    DOWNLOAD_FOLDER = '/sdcard/Download/StudioDownloader'
else:
    # PC ke liye purana rasta
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
    quality = data.get('quality', 'high')
    
    if not urls:
        return jsonify({'success': False, 'message': 'Koi link nahi mila!'})

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True
    }

    if quality == 'audio':
        ydl_opts['format'] = 'bestaudio/best' 
    elif quality == 'high':
        ydl_opts['format'] = 'best'
    elif quality == 'medium':
        ydl_opts['format'] = 'best[height<=720]/best'
    elif quality == 'low':
        ydl_opts['format'] = 'best[height<=360]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(urls)
        
        # 🔥 FIX: Android ko batana ki nayi file aayi hai taaki Gallery mein dikhe
        # Is command se Gallery refresh ho jati hai
        try:
            subprocess.run(["termux-media-scan", DOWNLOAD_FOLDER], check=False)
        except:
            pass

        return jsonify({'success': True, 'message': 'Successfully Downloaded to Gallery!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
