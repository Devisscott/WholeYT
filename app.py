from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import yt_dlp
import os
import json
import tempfile
import threading
import time
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)

# Global variables for download management
active_downloads = {}
download_history = []

class DownloadProgress:
    def __init__(self, download_id):
        self.download_id = download_id
        self.status = "starting"
        self.progress = 0
        self.speed = ""
        self.eta = ""
        self.filename = ""
        self.error = None
        self.completed = False

def progress_hook(d, download_id):
    """Progress hook for yt-dlp downloads"""
    if download_id in active_downloads:
        progress_obj = active_downloads[download_id]
        
        if d['status'] == 'downloading':
            progress_obj.status = "downloading"
            if 'downloaded_bytes' in d and 'total_bytes' in d:
                progress_obj.progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif '_percent_str' in d:
                progress_obj.progress = float(d['_percent_str'].replace('%', ''))
            
            progress_obj.speed = d.get('_speed_str', '')
            progress_obj.eta = d.get('_eta_str', '')
            progress_obj.filename = d.get('filename', '')
            
        elif d['status'] == 'finished':
            progress_obj.status = "completed"
            progress_obj.progress = 100
            progress_obj.completed = True
            progress_obj.filename = d.get('filename', '')
            
        elif d['status'] == 'error':
            progress_obj.status = "error"
            progress_obj.error = str(d.get('error', 'Unknown error'))

def get_video_info(url, cookies_file=None):
    """Extract video information without downloading"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'formats': [
                    {
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'quality': f.get('height', 'audio'),
                        'filesize': f.get('filesize', 0)
                    } for f in info.get('formats', [])
                ]
            }
    except Exception as e:
        return {'error': str(e)}

def download_video(url, format_selector, output_path, cookies_file=None, download_id=None):
    """Download video with yt-dlp"""
    ydl_opts = {
        'format': format_selector,
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'progress_hooks': [lambda d: progress_hook(d, download_id)] if download_id else [],
    }
    
    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        if download_id and download_id in active_downloads:
            active_downloads[download_id].error = str(e)
            active_downloads[download_id].status = "error"
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bulk')
def bulk():
    return render_template('bulk_download.html')

@app.route('/grabber')
def grabber():
    return render_template('link_grabber.html')

@app.route('/files')
def files():
    return render_template('files.html')

@app.route('/api/video-info', methods=['POST'])
def get_video_info_api():
    """Get video information"""
    data = request.json
    url = data.get('url')
    cookies_file = data.get('cookies_file')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    info = get_video_info(url, cookies_file)
    return jsonify(info)

@app.route('/api/download', methods=['POST'])
def download_api():
    """Start a download"""
    data = request.json
    url = data.get('url')
    format_selector = data.get('format', 'best')
    cookies_file = data.get('cookies_file')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Generate unique download ID
    download_id = str(uuid.uuid4())
    
    # Create progress tracker
    active_downloads[download_id] = DownloadProgress(download_id)
    
    # Create downloads directory
    downloads_dir = os.path.join(os.getcwd(), 'downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    
    # Start download in background thread
    def download_thread():
        success = download_video(url, format_selector, downloads_dir, cookies_file, download_id)
        if success:
            # Add to history
            download_history.append({
                'id': download_id,
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'status': 'completed'
            })
    
    thread = threading.Thread(target=download_thread)
    thread.daemon = True
    thread.start()
    
    return jsonify({'download_id': download_id})

@app.route('/api/download-progress/<download_id>')
def get_download_progress(download_id):
    """Get download progress"""
    if download_id not in active_downloads:
        return jsonify({'error': 'Download not found'}), 404
    
    progress = active_downloads[download_id]
    return jsonify({
        'status': progress.status,
        'progress': progress.progress,
        'speed': progress.speed,
        'eta': progress.eta,
        'filename': progress.filename,
        'error': progress.error,
        'completed': progress.completed
    })

@app.route('/api/bulk-download', methods=['POST'])
def bulk_download_api():
    """Start bulk downloads"""
    data = request.json
    urls = data.get('urls', [])
    format_selector = data.get('format', 'best')
    cookies_file = data.get('cookies_file')
    
    if not urls:
        return jsonify({'error': 'URLs are required'}), 400
    
    download_ids = []
    
    for url in urls:
        download_id = str(uuid.uuid4())
        active_downloads[download_id] = DownloadProgress(download_id)
        download_ids.append(download_id)
        
        # Create downloads directory
        downloads_dir = os.path.join(os.getcwd(), 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        # Start download in background thread
        def download_thread(url=url, download_id=download_id):
            success = download_video(url, format_selector, downloads_dir, cookies_file, download_id)
            if success:
                download_history.append({
                    'id': download_id,
                    'url': url,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'completed'
                })
        
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
        
        # Small delay between downloads to prevent overwhelming
        time.sleep(0.5)
    
    return jsonify({'download_ids': download_ids})

@app.route('/api/extract-links', methods=['POST'])
def extract_links_api():
    """Extract all media links from a page/playlist"""
    data = request.json
    url = data.get('url')
    cookies_file = data.get('cookies_file')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    
    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            links = []
            if 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        links.append({
                            'url': entry.get('url', ''),
                            'title': entry.get('title', 'Unknown'),
                            'duration': entry.get('duration', 0),
                            'thumbnail': entry.get('thumbnail', ''),
                            'id': entry.get('id', '')
                        })
            else:
                # Single video
                links.append({
                    'url': info.get('webpage_url', url),
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'id': info.get('id', '')
                })
            
            return jsonify({'links': links})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-history')
def get_download_history():
    """Get download history"""
    return jsonify({'history': download_history})

@app.route('/api/files')
def list_files():
    """List downloaded files"""
    downloads_dir = os.path.join(os.getcwd(), 'downloads')
    if not os.path.exists(downloads_dir):
        return jsonify({'files': []})
    
    files = []
    for filename in os.listdir(downloads_dir):
        file_path = os.path.join(downloads_dir, filename)
        if os.path.isfile(file_path):
            files.append({
                'name': filename,
                'size': os.path.getsize(file_path),
                'modified': os.path.getmtime(file_path)
            })
    
    return jsonify({'files': files})

@app.route('/api/download-file/<filename>')
def download_file(filename):
    """Download a specific file"""
    downloads_dir = os.path.join(os.getcwd(), 'downloads')
    file_path = os.path.join(downloads_dir, filename)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/upload-cookies', methods=['POST'])
def upload_cookies():
    """Handle cookies file upload"""
    if 'cookies' not in request.files:
        return jsonify({'error': 'No cookies file provided'}), 400
    
    file = request.files['cookies']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save cookies file
    cookies_dir = os.path.join(os.getcwd(), 'cookies')
    os.makedirs(cookies_dir, exist_ok=True)
    
    cookies_path = os.path.join(cookies_dir, 'cookies.txt')
    file.save(cookies_path)
    
    return jsonify({'message': 'Cookies uploaded successfully', 'path': cookies_path})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
