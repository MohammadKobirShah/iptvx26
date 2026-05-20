import logging
import time
import threading
from app.worker_manager import WorkerManager
from app.config import Config

logger = logging.getLogger(__name__)

class StreamMonitor:
    def __init__(self, worker_manager: WorkerManager):
        self.worker_manager = worker_manager
        self.running = False
        self.thread = None
    
    def start(self):
        """Start monitoring in background thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Stream monitor started")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Stream monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                dead_workers = self.worker_manager.check_health()
                
                for stream_id in dead_workers:
                    logger.warning(f"Worker dead: {stream_id}, restarting...")
                    self.worker_manager.restart_channel(stream_id)
                
                running = self.worker_manager.get_running_count()
                total = len(self.worker_manager.workers)
                
                if dead_workers:
                    logger.info(f"Health check: {running}/{total} running, restarted {len(dead_workers)}")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(5)
