import os
import logging.handlers
from .windows import LOG_FILE, APPDATA_DIR

def setup_logging():
    """Configure logging for Windows deployment"""
    # Ensure log directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler
    logger.addHandler(file_handler)
    
    # Log startup
    logging.info("Application started")

# Get a logger instance
logger = logging.getLogger(__name__)

# Log messages at various levels
logger.debug("Debugging information.")
logger.info("Informational message.")
logger.warning("Warning about potential issues.")
logger.error("An error occurred.")
logger.critical("Critical issue that needs immediate attention.")