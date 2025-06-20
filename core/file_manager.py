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
        self.input_dir = settings.input_dir
        self.output_dir = settings.output_dir
        self.processed_dir = settings.processed_dir
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
                self.logger.info("🧪 TESTING MODE: Clearing processed files list")
                self.processed_files = set()
                if self.processed_files_log.exists():
                    self.processed_files_log.unlink()
                return
            
            if self.processed_files_log.exists():
                with open(self.processed_files_log, 'r') as f:
                    self.processed_files = set(line.strip() for line in f if line.strip())
                self.logger.info(f"📋 Loaded {len(self.processed_files)} previously processed files")
            else:
                self.logger.info("📋 No previous processing history found")
                
        except Exception as e:
            log_warning(self.logger, f"Could not load processed files log: {e}")
            self.processed_files = set()
    
    def mark_file_processed(self, filename: str):
        """Mark a file as processed"""
        try:
            self.processed_files.add(filename)
            with open(self.processed_files_log, 'a') as f:
                f.write(f"{filename}\n")
            self.logger.debug(f"✓ Marked {filename} as processed")
        except Exception as e:
            log_error(self.logger, f"Could not mark {filename} as processed", e)
    
    def is_file_processed(self, filename: str) -> bool:
        """Check if a file has already been processed"""
        return filename in self.processed_files
    
    def save_to_obsidian_vault(self, filename: str, content: str) -> bool:
        """Save content directly to Obsidian vault via file system"""
        try:
            vault_file_path = Path(self.obsidian_vault_path) / self.obsidian_folder_path / filename
            vault_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(vault_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            log_success(self.logger, f"Saved {filename} to Obsidian vault")
            return True
            
        except Exception as e:
            log_error(self.logger, f"Failed to save {filename} to Obsidian vault", e)
            return False
    
    def move_processed_file(self, file_path: Path):
        """Move processed MP4 file to processed directory"""
        try:
            processed_path = self.processed_dir / file_path.name
            self.processed_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"📦 Moving {file_path.name} to processed directory")
            
            # Copy file first
            try:
                shutil.copyfile(file_path, processed_path)
                self.logger.debug(f"✓ Copied {file_path.name}")
            except Exception as copy_error:
                self.logger.debug(f"Standard copy failed, trying manual copy: {copy_error}")
                with open(file_path, 'rb') as src, open(processed_path, 'wb') as dst:
                    dst.write(src.read())
                self.logger.debug(f"✓ Manual copy successful: {file_path.name}")
            
            # Wait a moment then remove original
            time.sleep(1.0)
            
            try:
                file_path.unlink()
                log_success(self.logger, f"Moved {file_path.name} to processed directory")
            except Exception as delete_error:
                log_warning(self.logger, f"Copy succeeded but delete failed for {file_path.name}: {delete_error}")
                
        except Exception as e:
            log_error(self.logger, f"Failed to move {file_path.name}", e)
            raise Exception(f"Unable to move processed file {file_path.name}")
    
    def cleanup_temp_files(self, file_pattern: str):
        """Clean up temporary files matching a pattern"""
        try:
            temp_files = list(self.output_dir.glob(file_pattern))
            for temp_file in temp_files:
                temp_file.unlink()
                self.logger.debug(f"🗑️  Cleaned up temp file: {temp_file.name}")
            
            if temp_files:
                self.logger.info(f"🗑️  Cleaned up {len(temp_files)} temporary files")
                
        except Exception as e:
            log_warning(self.logger, f"Error cleaning up temp files: {e}")
    
    def get_file_info(self, file_path: Path) -> dict:
        """Get detailed file information"""
        try:
            stat = file_path.stat()
            return {
                'name': file_path.name,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': stat.st_mtime,
                'exists': file_path.exists(),
                'is_file': file_path.is_file()
            }
        except Exception as e:
            return {
                'name': file_path.name if file_path else 'unknown',
                'size_bytes': 0,
                'size_mb': 0,
                'modified': 0,
                'exists': False,
                'is_file': False,
                'error': str(e)
            }
    
    def get_directory_stats(self) -> dict:
        """Get statistics about directories"""
        try:
            stats = {}
            
            # Input directory stats
            if self.input_dir.exists():
                input_files = list(self.input_dir.iterdir())
                mp4_files = [f for f in input_files if f.suffix.lower() == '.mp4']
                stats['input'] = {
                    'total_files': len(input_files),
                    'mp4_files': len(mp4_files),
                    'mp4_filenames': [f.name for f in mp4_files]
                }
            else:
                stats['input'] = {'total_files': 0, 'mp4_files': 0, 'mp4_filenames': []}
            
            # Output directory stats
            if self.output_dir.exists():
                output_files = list(self.output_dir.iterdir())
                stats['output'] = {
                    'total_files': len(output_files),
                    'analysis_files': len([f for f in output_files if f.suffix == '.json']),
                    'markdown_files': len([f for f in output_files if f.suffix == '.md'])
                }
            else:
                stats['output'] = {'total_files': 0, 'analysis_files': 0, 'markdown_files': 0}
            
            # Processed directory stats
            if self.processed_dir.exists():
                processed_files = list(self.processed_dir.iterdir())
                stats['processed'] = {
                    'total_files': len(processed_files),
                    'mp4_files': len([f for f in processed_files if f.suffix.lower() == '.mp4'])
                }
            else:
                stats['processed'] = {'total_files': 0, 'mp4_files': 0}
            
            # Processing history stats
            stats['history'] = {
                'total_processed': len(self.processed_files),
                'log_exists': self.processed_files_log.exists()
            }
            
            return stats
            
        except Exception as e:
            log_error(self.logger, "Error getting directory stats", e)
            return {}
    
    def validate_directory_structure(self) -> bool:
        """Validate that all required directories exist and are writable"""
        try:
            required_dirs = [
                self.input_dir,
                self.output_dir,
                self.processed_dir
            ]
            
            for directory in required_dirs:
                if not directory.exists():
                    log_error(self.logger, f"Required directory does not exist: {directory}")
                    return False
                
                if not directory.is_dir():
                    log_error(self.logger, f"Path is not a directory: {directory}")
                    return False
                
                # Test write access
                test_file = directory / '.write_test'
                try:
                    test_file.touch()
                    test_file.unlink()
                except Exception:
                    log_error(self.logger, f"Directory is not writable: {directory}")
                    return False
            
            # Validate Obsidian vault path
            vault_path = Path(self.obsidian_vault_path)
            if not vault_path.exists():
                try:
                    vault_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    log_error(self.logger, f"Cannot create Obsidian vault directory: {vault_path}", e)
                    return False
            
            log_success(self.logger, "Directory structure validation passed")
            return True
            
        except Exception as e:
            log_error(self.logger, "Error validating directory structure", e)
            return False
    
    def backup_processed_files_log(self) -> bool:
        """Create a backup of the processed files log"""
        try:
            if not self.processed_files_log.exists():
                return True
            
            backup_path = self.output_dir / f"processed_files_backup_{int(time.time())}.txt"
            shutil.copy2(self.processed_files_log, backup_path)
            
            log_success(self.logger, f"Created backup: {backup_path.name}")
            return True
            
        except Exception as e:
            log_error(self.logger, "Error backing up processed files log", e)
            return False
    
    def reset_processing_history(self) -> bool:
        """Reset the processing history (for testing or maintenance)"""
        try:
            # Backup first
            self.backup_processed_files_log()
            
            # Clear in-memory set
            self.processed_files.clear()
            
            # Remove log file
            if self.processed_files_log.exists():
                self.processed_files_log.unlink()
            
            log_success(self.logger, "Processing history reset")
            return True
            
        except Exception as e:
            log_error(self.logger, "Error resetting processing history", e)
            return False