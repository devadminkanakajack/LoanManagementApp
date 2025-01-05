import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Any


def setup_logging(app: Any) -> None:
    """Configure logging for the application.
    
    Args:
        app: The Flask application instance
    """
    try:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(app.config['LOG_FILE_PATH'])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Set logging level
        log_level = getattr(logging, app.config['LOG_LEVEL'].upper())
        
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
        )

        # File handler
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE_PATH'],
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)

        # Add handlers to app logger
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(log_level)

        # Remove default handler if in debug mode
        if app.debug:
            for handler in app.logger.handlers:
                app.logger.removeHandler(handler)
                
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        raise
