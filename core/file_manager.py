"""
File management for Meeting Processor
Handles file operations, directory setup, and processing tracking
"""

import shutil
import time
from pathlib import Path
from typing import Set
from utils.logger import LoggerMixin, log_success, log_error, log_warning


class FileManager(LoggerMixin):
    """Handles file operations and tracking"""
    
    def __init__(self, settings):
        self.settings = settings
        self.input_dir = Path(settings.input_dir)
        self.output_dir = Path(settings.output_dir)
        self.processed_dir = Path(settings.processed_dir)
        self.obsidian_vault_path = settings.obsidian_vault_path
        self.obsidian_folder_path = settings.obsidian_folder_path
        
        self.processed_files_log = self.output_dir / 'processed_files.txt'
        self.processed_files: Set[str] = set()
        
        self._setup_directories()
        self._load_processed_files()
    
    def _setup_directories(self):
        """Create necessary directories"""
        directories = [
            self.input_dir,
            self.output_dir,
            self.processed_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"📁 Ensured directory exists: {directory}")
        
        # Create Obsidian vault structure
        obsidian_meetings_path = Path(self.obsidian_vault_path) / self.obsidian_folder_path
        obsidian_meetings_path.mkdir(parents=True, exist_ok=True)
        
        # Create entity folders
        for folder in self.settings.entity_folders:
            entity_path = Path(self.obsidian_vault_path) / folder
            entity_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"📁 Created entity folder: {folder}")
        
        log_success(self.logger, "Directory structure initialized")
    
    def _load_processed_files(self):
        """Load list of already processed files"""
        try:
            # Clear processed files in testing mode
            if self.settings.testing_mode:
                self.logger.info("🔄 TESTING MODE: Clearing processed files list")
                self.processed_files = set()
                if self.processed_files_log.exists():
                    self.processed_files_log.unlink()
                return
            
            if self.processed_files_log.exists():
                with open(self.processed_files_log, 'r') as f:
                    self.processed_files = set(line.strip() for line in f)
                self.logger.info(f"📋 Loaded {len(self.processed_files)} processed files")
        except Exception as e:
            log_error(self.logger, "Error loading processed files list", e)
    
    def is_file_processed(self, filename: str) -> bool:
        """Check if file has already been processed"""
        return filename in self.processed_files
    
    def mark_file_processed(self, filename: str):
        """Mark file as processed"""
        try:
            self.processed_files.add(filename)
            with open(self.processed_files_log, 'a') as f:
                f.write(f"{filename}\n")
            self.logger.debug(f"✓ Marked as processed: {filename}")
        except Exception as e:
            log_error(self.logger, f"Error marking file as processed: {filename}", e)
    
    def move_processed_file(self, source_path: Path) -> bool:
        """Move processed file to processed directory"""
        try:
            if not source_path.exists():
                log_warning(self.logger, f"Source file not found: {source_path}")
                return False
            
            dest_path = self.processed_dir / source_path.name
            
            # Handle existing files
            if dest_path.exists():
                timestamp = int(time.time())
                base_name = dest_path.stem
                extension = dest_path.suffix
                dest_path = self.processed_dir / f"{base_name}_{timestamp}{extension}"
            
            shutil.move(str(source_path), str(dest_path))
            log_success(self.logger, f"Moved to processed: {source_path.name}")
            return True
            
        except Exception as e:
            log_error(self.logger, f"Error moving file {source_path}", e)
            return False
    
    def save_to_obsidian_vault(self, filename: str, content: str) -> bool:
        """Save content to Obsidian vault"""
        try:
            vault_path = Path(self.obsidian_vault_path) / self.obsidian_folder_path / filename
            vault_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(vault_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            log_success(self.logger, f"Saved to vault: {vault_path}")
            return True
            
        except Exception as e:
            log_error(self.logger, f"Error saving to vault: {filename}", e)
            return False
    
    def get_output_path(self, filename: str) -> Path:
        """Get full output path for a file"""
        return self.output_dir / filename
    
    def get_vault_path(self, filename: str) -> Path:
        """Get full vault path for a file"""
        return Path(self.obsidian_vault_path) / self.obsidian_folder_path / filename
    
    def cleanup_old_files(self, days: int = 30):
        """Clean up old processed files"""
        try:
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            cleaned_count = 0
            
            for file_path in self.processed_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                log_success(self.logger, f"Cleaned up {cleaned_count} old files")
                
        except Exception as e:
            log_error(self.logger, "Error during cleanup", e)