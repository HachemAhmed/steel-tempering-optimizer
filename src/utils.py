"""
Utility module providing logging functionality and stdout suppression.
"""
import logging
import config

class NullWriter:
    """Suppresses stdout output by redirecting writes to null."""
    def write(self, text): 
        pass
    
    def flush(self): 
        pass

def setup_logger():
    """
    Configures the logging system with file output.
    Creates the log file when first called.
    """
    logger = logging.getLogger('steel_project')
    logger.setLevel(logging.WARNING)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(module)s] - %(message)s', 
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler(config.LOG_FILE_PATH, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def log_error(message, level='ERROR', exc_info=None):
    """
    Logs an error message. Initializes logger lazily on first call.
    
    Args:
        message: Error message to log
        level: Logging level ('ERROR', 'WARNING', 'CRITICAL')
        exc_info: Exception info for traceback
    """
    logger = logging.getLogger('steel_project')
    
    # Lazy initialization: setup logger if not configured yet
    if not logger.handlers:
        setup_logger()
    
    if level == 'CRITICAL':
        logger.critical(message, exc_info=exc_info)
    elif level == 'WARNING':
        logger.warning(message, exc_info=exc_info)
    else:
        logger.error(message, exc_info=exc_info)