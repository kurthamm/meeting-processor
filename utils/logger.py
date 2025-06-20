"""
Logging configuration for Meeting Processor
Provides consistent logging across all modules
"""

import logging
import sys
from pathlib import Path


class Logger:
    """Centralized logging configuration"""
    
    _initialized = False
    
    @staticmethod
    def setup(log_file: str = 'meeting_processor.log', level: int = logging.INFO) -> logging.Logger:
        """Setup logging configuration if not already done"""
        if not Logger._initialized:
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Create file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            
            # Create console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(level)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)
            
            # Prevent duplicate logging from sub-modules
            root_logger.propagate = False
            
            Logger._initialized = True
            
            # Log startup message
            logger = logging.getLogger(__name__)
            logger.info("🔧 Logging system initialized")
            logger.info(f"📄 Log file: {log_file}")
        
        return logging.getLogger(__name__)
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger for a specific module"""
        return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capability to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")


# Convenience functions for common logging patterns
def log_step(logger: logging.Logger, step: str, description: str):
    """Log a processing step with emoji"""
    logger.info(f"🔄 {step}: {description}")


def log_success(logger: logging.Logger, message: str):
    """Log a success message with emoji"""
    logger.info(f"✅ {message}")


def log_error(logger: logging.Logger, message: str, exception: Exception = None):
    """Log an error message with emoji"""
    if exception:
        logger.error(f"❌ {message}: {str(exception)}")
    else:
        logger.error(f"❌ {message}")


def log_warning(logger: logging.Logger, message: str):
    """Log a warning message with emoji"""
    logger.warning(f"⚠️  {message}")


def log_entity_detection(logger: logging.Logger, entities: dict, filename: str):
    """Log entity detection results"""
    logger.info("🎯 ENTITY DETECTION RESULTS:")
    logger.info(f"   👥 PEOPLE ({len(entities.get('people', []))}): {entities.get('people', [])}")
    logger.info(f"   🏢 COMPANIES ({len(entities.get('companies', []))}): {entities.get('companies', [])}")
    logger.info(f"   💻 TECHNOLOGIES ({len(entities.get('technologies', []))}): {entities.get('technologies', [])}")
    
    total = len(entities.get('people', [])) + len(entities.get('companies', [])) + len(entities.get('technologies', []))
    logger.info(f"📊 TOTAL ENTITIES: {total} detected for {filename}")


def log_file_processing(logger: logging.Logger, filename: str, step: str, details: str = ""):
    """Log file processing steps"""
    emoji_map = {
        'start': '🎬',
        'convert': '🎵',
        'transcribe': '🎤',
        'analyze': '🧠',
        'entities': '🔍',
        'save': '💾',
        'complete': '✅',
        'error': '❌',
        'skip': '⏭️'
    }
    
    emoji = emoji_map.get(step, '🔄')
    message = f"{emoji} {filename}: {step.title()}"
    if details:
        message += f" - {details}"
    
    logger.info(message)