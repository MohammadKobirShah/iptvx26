import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # M3U Source
    M3U_URL = os.getenv('M3U_URL', '')
    M3U_CONTENT = os.getenv('M3U_CONTENT', '')
    
    # Performance
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 100))
    WORKER_START_DELAY = float(os.getenv('WORKER_START_DELAY', 0.5))
    
    # Authentication
    ENABLE_AUTH = os.getenv('ENABLE_AUTH', 'false').lower() == 'true'
    API_KEY = os.getenv('API_KEY', '')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'info')
    
    # Server
    PORT = int(os.getenv('PORT', 8080))
    HOST = '127.0.0.1'
    
    # Proxy
    ENABLE_PROXY = os.getenv('ENABLE_PROXY', 'false').lower() == 'true'
    SOCKS5_URL = os.getenv('SOCKS5_URL', '')
    
    # MediaMTX
    MEDIAMTX_RTSP_HOST = '127.0.0.1'
    MEDIAMTX_RTSP_PORT = 8554
    MEDIAMTX_API_HOST = '127.0.0.1'
    MEDIAMTX_API_PORT = 9997
    
    # FFmpeg
    FFMPEG_BIN = '/usr/local/bin/ffmpeg'
    FFMPEG_LOG_DIR = '/var/log/ffmpeg'
    
    # Paths
    LOG_DIR = '/var/log/iptv'
