from flask import Flask, jsonify, request
from app.config import Config
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global instances (will be set by main.py)
parser = None
worker_manager = None

@app.route('/api/status')
def status():
    """System status"""
    if not worker_manager:
        return jsonify({'error': 'System not initialized'}), 500
    
    return jsonify({
        'status': 'running',
        'total_channels': len(parser.channels) if parser else 0,
        'total_workers': len(worker_manager.workers),
        'running_workers': worker_manager.get_running_count(),
        'groups': parser.get_all_groups() if parser else []
    })

@app.route('/api/channels')
def get_channels():
    """Get all channels"""
    if not parser:
        return jsonify({'error': 'System not initialized'}), 500
    
    return jsonify({
        'total': len(parser.channels),
        'channels': parser.channels
    })

@app.route('/api/streams')
def get_streams():
    """Get all active streams"""
    if not worker_manager:
        return jsonify({'error': 'System not initialized'}), 500
    
    base_url = request.url_root.rstrip('/')
    
    streams = []
    for worker in worker_manager.workers.values():
        stream_id = worker.channel['stream_id']
        streams.append({
            'id': stream_id,
            'name': worker.channel['name'],
            'group': worker.channel['group_title'],
            'logo': worker.channel.get('tvg_logo', ''),
            'webrtc_url': f'/webrtc/{stream_id}',
            'hls_url': f'/hls/{stream_id}/index.m3u8',
            'running': worker.is_running()
        })
    
    return jsonify({
        'total': len(streams),
        'running': worker_manager.get_running_count(),
        'streams': streams
    })

@app.route('/api/streams/<stream_id>')
def get_stream(stream_id):
    """Get specific stream status"""
    if not worker_manager:
        return jsonify({'error': 'System not initialized'}), 500
    
    if stream_id not in worker_manager.workers:
        return jsonify({'error': 'Stream not found'}), 404
    
    worker = worker_manager.workers[stream_id]
    return jsonify(worker.get_status())

@app.route('/api/streams/<stream_id>/restart', methods=['POST'])
def restart_stream(stream_id):
    """Restart a specific stream"""
    if not worker_manager:
        return jsonify({'error': 'System not initialized'}), 500
    
    if stream_id not in worker_manager.workers:
        return jsonify({'error': 'Stream not found'}), 404
    
    success = worker_manager.restart_channel(stream_id)
    
    if success:
        return jsonify({'status': 'restarted', 'stream_id': stream_id})
    else:
        return jsonify({'error': 'Failed to restart'}), 500

@app.route('/api/playlist.m3u')
def playlist():
    """Generate output M3U playlist"""
    if not worker_manager:
        return "System not initialized", 500
    
    base_url = request.url_root.rstrip('/')
    
    lines = ['#EXTM3U']
    
    for worker in worker_manager.workers.values():
        channel = worker.channel
        stream_id = channel['stream_id']
        
        extinf = f"#EXTINF:-1"
        
        if channel.get('tvg_id'):
            extinf += f' tvg-id="{channel["tvg_id"]}"'
        if channel.get('tvg_logo'):
            extinf += f' tvg-logo="{channel["tvg_logo"]}"'
        if channel.get('group_title'):
            extinf += f' group-title="{channel["group_title"]}"'
        
        extinf += f',{channel["name"]}'
        lines.append(extinf)
        
        stream_url = f"{base_url}/hls/{stream_id}/index.m3u8"
        lines.append(stream_url)
    
    content = '\n'.join(lines)
    
    return content, 200, {
        'Content-Type': 'application/vnd.apple.mpegurl',
        'Content-Disposition': 'attachment; filename=playlist.m3u8'
    }

@app.route('/health')
def health():
    """Health check endpoint"""
    return 'OK', 200
