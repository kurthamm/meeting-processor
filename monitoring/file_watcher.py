"""
File system monitoring for Meeting Processor
Handles file system events and MP4 file detection
"""

import time
from pathlib import Path
from typing import Set, TYPE_CHECKING
from watchdog.events import FileSystemEventHandler
from utils.logger import LoggerMixin, log_file_processing, log_warning

if TYPE_CHECKING:
    from main import MeetingProcessor


class MeetingFileHandler(FileSystemEventHandler, LoggerMixin):
    """File system event handler for new MP4 files"""
    
    def __init__(self, processor: 'MeetingProcessor'):
        super().__init__()
        self.processor = processor
        self.processing_files: Set[str] = set()
        self.file_stabilization_delay = 3  # seconds to wait for file to stabilize
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        self.logger.debug(f"📁 File created: {event.src_path}")
        self._handle_file_event(event.src_path, "created")

    def on_moved(self, event):
        """Handle file move events"""
        if event.is_directory:
            return
        
        self.logger.debug(f"📁 File moved: {event.src_path} -> {event.dest_path}")
        self._handle_file_event(event.dest_path, "moved")

    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        self.logger.debug(f"📁 File modified: {event.src_path}")
        self._handle_file_event(event.src_path, "modified")

    def _handle_file_event(self, file_path_str: str, event_type: str):
        """Handle file system events for MP4 files"""
        file_path = Path(file_path_str)
        
        log_file_processing(self.logger, file_path.name, 'detect', f"Event: {event_type}")
        
        # Only process MP4 files
        if file_path.suffix.lower() != '.mp4':
            self.logger.debug(f"⏭️  Ignoring non-MP4 file: {file_path.name}")
            return
        
        # Check if already processed
        if self.processor.file_manager.is_file_processed(file_path.name):
            log_file_processing(self.logger, file_path.name, 'skip', "Already processed")
            return
        
        # Check if we're already processing this file
        file_key = str(file_path)
        if file_key in self.processing_files:
            self.logger.debug(f"⏭️  Already processing: {file_path.name}")
            return
        
        # Validate file before processing
        if not self._validate_file_for_processing(file_path):
            return
        
        # Mark as processing and handle
        self.processing_files.add(file_key)
        
        try:
            log_file_processing(self.logger, file_path.name, 'start')
            self.processor.process_meeting_file(file_path)
        except Exception as e:
            log_file_processing(self.logger, file_path.name, 'error', str(e))
        finally:
            self.processing_files.discard(file_key)
    
    def _validate_file_for_processing(self, file_path: Path) -> bool:
        """Validate that file is ready for processing"""
        try:
            # Wait for file to stabilize (finish copying/writing)
            self.logger.debug(f"⏳ Waiting {self.file_stabilization_delay}s for file to stabilize...")
            time.sleep(self.file_stabilization_delay)
            
            # Check if file still exists
            if not file_path.exists():
                log_warning(self.logger, f"File no longer exists: {file_path.name}")
                return False
            
            # Check if it's actually a file
            if not file_path.is_file():
                log_warning(self.logger, f"Path is not a file: {file_path.name}")
                return False
            
            # Check file size (should be > 0)
            file_size = file_path.stat().st_size
            if file_size == 0:
                log_warning(self.logger, f"File is empty: {file_path.name}")
                return False
            
            # Log file info
            file_size_mb = file_size / (1024 * 1024)
            self.logger.info(f"📊 File validated: {file_path.name} ({file_size_mb:.1f}MB)")
            
            return True
            
        except Exception as e:
            log_warning(self.logger, f"File validation failed for {file_path.name}: {e}")
            return False
    
    def get_processing_status(self) -> dict:
        """Get current processing status"""
        return {
            'currently_processing': len(self.processing_files),
            'processing_files': list(self.processing_files)
        }
    
    def is_processing_file(self, file_path: str) -> bool:
        """Check if a specific file is currently being processed"""
        return str(file_path) in self.processing_files


class FileMonitor(LoggerMixin):
    """Enhanced file monitoring with backup scanning"""
    
    def __init__(self, processor: 'MeetingProcessor'):
        self.processor = processor
        self.processed_files_in_session: Set[str] = set()
        self.scan_interval = 2  # seconds between backup scans
    
    def backup_scan(self):
        """Backup scan for files that might have been missed by watchdog"""
        try:
            current_files = list(self.processor.file_manager.input_dir.glob("*.mp4"))
            
            for mp4_file in current_files:
                file_key = str(mp4_file)
                
                # Skip if already processed in this session or previously
                if (file_key in self.processed_files_in_session or 
                    self.processor.file_manager.is_file_processed(mp4_file.name)):
                    continue
                
                log_file_processing(self.logger, mp4_file.name, 'detect', "Backup scan")
                self.processed_files_in_session.add(file_key)
                self.processor.process_meeting_file(mp4_file)
                
        except Exception as e:
            self.logger.debug(f"Error in backup scan: {e}")
    
    def get_scan_statistics(self) -> dict:
        """Get monitoring statistics"""
        try:
            input_files = list(self.processor.file_manager.input_dir.glob("*"))
            mp4_files = [f for f in input_files if f.suffix.lower() == '.mp4']
            
            return {
                'total_files_in_input': len(input_files),
                'mp4_files_in_input': len(mp4_files),
                'processed_in_session': len(self.processed_files_in_session),
                'total_processed_ever': len(self.processor.file_manager.processed_files)
            }
        except Exception as e:
            self.logger.debug(f"Error getting scan statistics: {e}")
            return {}