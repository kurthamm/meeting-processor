"""
Configuration management for Meeting Processor
Handles environment variables, API clients, and settings
"""

import os
from pathlib import Path
from typing import Optional
import anthropic

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from dotenv import load_dotenv


class Settings:
    """Centralized configuration management"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize API clients
        self._init_api_clients()
        
        # Initialize directory paths
        self._init_directories()
        
        # Initialize processing settings
        self._init_processing_settings()
    
    def _init_api_clients(self):
        """Initialize API clients with proper error handling"""
        # Anthropic (required)
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
        
        # OpenAI (optional - will create placeholder analysis without it)
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.openai_client = None
        
        if not OPENAI_AVAILABLE:
            print("⚠️  OpenAI module not installed - placeholder analysis only")
        elif not self.openai_key:
            print("⚠️  OPENAI_API_KEY not found - placeholder analysis only")
        else:
            self.openai_client = openai.OpenAI(api_key=self.openai_key)
            print("✅ OpenAI client initialized")
    
    def _init_directories(self):
        """Initialize directory paths from environment"""
        self.input_dir = Path(os.getenv('INPUT_DIR', '/app/input'))
        self.output_dir = Path(os.getenv('OUTPUT_DIR', '/app/output'))
        self.processed_dir = Path(os.getenv('PROCESSED_DIR', '/app/processed'))
        
        # Obsidian vault configuration
        self.obsidian_vault_path = os.getenv('OBSIDIAN_VAULT_PATH', '/app/obsidian_vault')
        self.obsidian_folder_path = os.getenv('OBSIDIAN_FOLDER_PATH', 'Meetings')
        
        # Docker configuration
        self.host_uid = os.getenv('HOST_UID', '1000')
        self.host_gid = os.getenv('HOST_GID', '1000')
    
    def _init_processing_settings(self):
        """Initialize processing-specific settings"""
        # Testing mode allows reprocessing files
        self.testing_mode = os.getenv('TESTING_MODE', 'false').lower() == 'true'
        
        # Audio processing settings
        self.chunk_duration_minutes = int(os.getenv('CHUNK_DURATION_MINUTES', '10'))
        self.max_file_size_mb = int(os.getenv('MAX_FILE_SIZE_MB', '25'))
        
        # File monitoring settings
        self.file_stabilization_delay = int(os.getenv('FILE_STABILIZATION_DELAY', '3'))
        self.backup_scan_interval = int(os.getenv('BACKUP_SCAN_INTERVAL', '2'))
    
    @property
    def has_openai(self) -> bool:
        """Check if OpenAI is available for transcription"""
        return self.openai_client is not None
    
    @property
    def entity_folders(self) -> list:
        """Get list of entity folders to create"""
        return ['People', 'Companies', 'Technologies']
    
    def get_log_file_path(self) -> Path:
        """Get path for log file"""
        return Path('meeting_processor.log')
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return f"""Settings:
  Input Dir: {self.input_dir}
  Output Dir: {self.output_dir}
  Processed Dir: {self.processed_dir}
  Obsidian Vault: {self.obsidian_vault_path}
  Obsidian Folder: {self.obsidian_folder_path}
  Testing Mode: {self.testing_mode}
  OpenAI Available: {self.has_openai}
  Chunk Duration: {self.chunk_duration_minutes}min
  Max File Size: {self.max_file_size_mb}MB"""