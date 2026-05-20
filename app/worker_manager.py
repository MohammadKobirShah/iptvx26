import subprocess
import logging
import time
import os
from typing import Dict, List, Optional
from datetime import datetime
from app.config import Config

logger = logging.getLogger(__name__)

class FFmpegWorker:
    def __init__(self, channel: Dict):
        self.channel = channel
        self.process: Optional[subprocess.Popen] = None
        self.start_time = None
        self.restart_count = 0
        self.log_file = None
    
    def build_command(self) -> List[str]:
        """Build FFmpeg command"""
        stream_id = self.channel['stream_id']
        source_url = self.channel['url']
        output_url = f"rtsp://{Config.MEDIAMTX_RTSP_HOST}:{Config.MEDIAMTX_RTSP_PORT}/{stream_id}"
        
        cmd = [Config.FFMPEG_BIN]
        
        # Proxy
        if Config.ENABLE_PROXY and Config.SOCKS5_URL:
            cmd.extend(['-http_proxy', Config.SOCKS5_URL])
        
        # Input flags (ultra-low latency)
        cmd.extend([
            '-hide_banner',
            '-loglevel', 'error',
            '-fflags', 'nobuffer+genpts+discardcorrupt',
            '-flags', 'low_delay',
            '-analyzeduration', '100000',
            '-probesize', '100000',
            '-max_delay', '0',
            '-reorder_queue_size', '0',
            '-buffer_size', '2048000',
            # Reconnect flags
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '5',
            '-timeout', '10000000',
        ])
        
        # Input
        cmd.extend(['-i', source_url])
        
        # Output flags (COPY MODE - NO TRANSCODING)
        cmd.extend([
            '-c', 'copy',
            '-copyts',
            '-copytb', '1',
            '-avoid_negative_ts', 'make_zero',
            '-max_muxing_queue_size', '1024',
            '-flush_packets', '1',
        ])
        
        # Output format
        cmd.extend(['-f', 'rtsp'])
        
        # Output URL
        cmd.append(output_url)
        
        return cmd
    
    def start(self) -> bool:
        """Start FFmpeg worker"""
        if self.is_running():
            return True
        
        try:
            os.makedirs(Config.FFMPEG_LOG_DIR, exist_ok=True)
            
            log_path = os.path.join(Config.FFMPEG_LOG_DIR, f"{self.channel['stream_id']}.log")
            self.log_file = open(log_path, 'a')
            
            cmd = self.build_command()
            
            logger.info(f"Starting worker for {self.channel['name']}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=self.log_file,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True
            )
            
            self.start_time = datetime.now()
            self.restart_count += 1
            
            time.sleep(1)
            
            if self.process.poll() is not None:
                logger.error(f"Worker failed to start for {self.channel['name']}")
                return False
            
            logger.info(f"Worker started for {self.channel['name']} (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Error starting worker for {self.channel['name']}: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop FFmpeg worker"""
        if not self.is_running():
            return True
        
        try:
            logger.info(f"Stopping worker for {self.channel['name']}")
            self.process.terminate()
            
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            
            if self.log_file:
                self.log_file.close()
                self.log_file = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping worker for {self.channel['name']}: {e}")
            return False
    
    def restart(self) -> bool:
        """Restart worker"""
        self.stop()
        time.sleep(2)
        return self.start()
    
    def is_running(self) -> bool:
        """Check if worker is running"""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def get_status(self) -> Dict:
        """Get worker status"""
        return {
            'channel': self.channel['name'],
            'stream_id': self.channel['stream_id'],
            'running': self.is_running(),
            'pid': self.process.pid if self.is_running() else None,
            'uptime': str(datetime.now() - self.start_time) if self.start_time else None,
            'restart_count': self.restart_count
        }


class WorkerManager:
    def __init__(self):
        self.workers: Dict[str, FFmpegWorker] = {}
    
    def add_channel(self, channel: Dict) -> bool:
        """Add and start a channel worker"""
        stream_id = channel['stream_id']
        
        if stream_id in self.workers:
            return False
        
        worker = FFmpegWorker(channel)
        
        if worker.start():
            self.workers[stream_id] = worker
            time.sleep(Config.WORKER_START_DELAY)
            return True
        return False
    
    def remove_channel(self, stream_id: str) -> bool:
        """Remove and stop a channel worker"""
        if stream_id not in self.workers:
            return False
        
        worker = self.workers[stream_id]
        worker.stop()
        del self.workers[stream_id]
        return True
    
    def restart_channel(self, stream_id: str) -> bool:
        """Restart a channel worker"""
        if stream_id not in self.workers:
            return False
        return self.workers[stream_id].restart()
    
    def start_all(self, channels: List[Dict]) -> int:
        """Start workers for all channels"""
        # Limit to MAX_WORKERS
        channels = channels[:Config.MAX_WORKERS]
        
        logger.info(f"Starting workers for {len(channels)} channels")
        
        started = 0
        for channel in channels:
            if self.add_channel(channel):
                started += 1
        
        logger.info(f"Started {started}/{len(channels)} workers")
        return started
    
    def stop_all(self) -> int:
        """Stop all workers"""
        logger.info(f"Stopping all {len(self.workers)} workers")
        
        stopped = 0
        for stream_id in list(self.workers.keys()):
            if self.remove_channel(stream_id):
                stopped += 1
        
        return stopped
    
    def check_health(self) -> List[str]:
        """Check health and return dead workers"""
        dead = []
        for stream_id, worker in self.workers.items():
            if not worker.is_running():
                dead.append(stream_id)
        return dead
    
    def get_all_status(self) -> List[Dict]:
        """Get status of all workers"""
        return [worker.get_status() for worker in self.workers.values()]
    
    def get_running_count(self) -> int:
        """Get count of running workers"""
        return sum(1 for worker in self.workers.values() if worker.is_running())
