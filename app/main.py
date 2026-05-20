import logging
import signal
import sys
import time
from app.config import Config
from app.playlist_parser import M3UParser
from app.worker_manager import WorkerManager
from app.stream_monitor import StreamMonitor
import app.api as api_module

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global instances
parser = None
worker_manager = None
monitor = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal, stopping...")
    shutdown()
    sys.exit(0)

def shutdown():
    """Graceful shutdown"""
    global monitor, worker_manager
    
    if monitor:
        monitor.stop()
    
    if worker_manager:
        worker_manager.stop_all()
    
    logger.info("Shutdown complete")

def initialize():
    """Initialize the system"""
    global parser, worker_manager, monitor
    
    logger.info("Initializing IPTV streaming system...")
    
    # Determine M3U source
    m3u_source = Config.M3U_URL or Config.M3U_CONTENT
    
    if not m3u_source:
        logger.error("No M3U source configured! Set M3U_URL or M3U_CONTENT environment variable")
        return False
    
    # Parse playlist
    parser = M3UParser(m3u_source)
    channels = parser.parse()
    
    if not channels:
        logger.error("No channels found in M3U playlist!")
        return False
    
    logger.info(f"Found {len(channels)} channels")
    
    # Limit to MAX_WORKERS
    if len(channels) > Config.MAX_WORKERS:
        logger.warning(f"Limiting to {Config.MAX_WORKERS} channels (MAX_WORKERS setting)")
        channels = channels[:Config.MAX_WORKERS]
    
    # Create worker manager
    worker_manager = WorkerManager()
    
    # Start workers
    started = worker_manager.start_all(channels)
    logger.info(f"Started {started} workers")
    
    # Set global references for API
    api_module.parser = parser
    api_module.worker_manager = worker_manager
    
    # Start monitor
    monitor = StreamMonitor(worker_manager)
    monitor.start()
    
    logger.info("System initialized successfully")
    return True

def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize
    if not initialize():
        logger.error("Failed to initialize system")
        sys.exit(1)
    
    logger.info("IPTV Manager running. Press Ctrl+C to stop.")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        shutdown()

if __name__ == '__main__':
    main()
