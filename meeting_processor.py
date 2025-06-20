class FileManager:
    """Handles file operations and tracking"""
    
    def __init__(self, input_dir: Path, output_dir: Path, processed_dir: Path, 
                 obsidian_vault_path: str, obsidian_folder_path: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_dir = processed_dir
        self.obsidian_vault_path = obsidian_vault_path
        self.obsidian_folder_path = obsidian_folder_path
        
        self.processed_files_log = self.output_dir / 'processed_files.txt'
        self.processed_files = set()
        self.logger = logging.getLogger(__name__)
        
        self._setup_directories()
        self._load_processed_files()
    
    def _setup_directories(self):
        """Create necessary directories"""
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Obsidian vault directory structure
        obsidian_full_path = Path(self.obsidian_vault_path) / self.obsidian_folder_path
        obsidian_full_path.mkdir(parents=True, exist_ok=True)
    
    def _load_processed_files(self):
        """Load list of already processed files"""
        try:
            # For testing - allow reprocessing files
            testing_mode = os.getenv('TESTING_MODE', 'false').lower() == 'true'
            if testing_mode:
                self.logger.info("TESTING MODE: Clearing processed files list")
                self.processed_files = set()
                if self.processed_files_log.exists():
                    self.processed_files_log.unlink()
                return
            
            if self.processed_files_log.exists():
                with open(self.processed_files_log, 'r') as f:
                    self.processed_files = set(line.strip() for line in f if line.strip())
                self.logger.info(f"Loaded {len(self.processed_files)} previously processed files")
        except Exception as e:
            self.logger.warning(f"Could not load processed files log: {e}")
            self.processed_files = set()
    
    def mark_file_processed(self, filename: str):
        """Mark a file as processed"""
        try:
            self.processed_files.add(filename)
            with open(self.processed_files_log, 'a') as f:
                f.write(f"{filename}\n")
            self.logger.info(f"Marked {filename} as processed")
        except Exception as e:
            self.logger.error(f"Could not mark file as processed: {e}")
    
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
            
            self.logger.info(f"Successfully saved {filename} to Obsidian vault: {vault_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving to Obsidian vault: {str(e)}")
            return False
    
    def move_processed_file(self, file_path: Path):
        """Move processed MP4 file to processed directory"""
        try:
            processed_path = self.processed_dir / file_path.name
            self.processed_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Attempting to move {file_path} to {processed_path}")
            
            # Copy file
            try:
                shutil.copyfile(file_path, processed_path)
                self.logger.info(f"Successfully copied {file_path.name}")
            except Exception as copy_error:
                self.logger.info(f"copyfile failed ({copy_error}), trying manual byte copy")
                with open(file_path, 'rb') as src, open(processed_path, 'wb') as dst:
                    dst.write(src.read())
                self.logger.info(f"Successfully copied {file_path.name} using manual byte copy")
            
            # Wait and then remove original
            time.sleep(1.0)
            
            try:
                file_path.unlink()
                self.logger.info(f"Successfully moved {file_path.name} to processed directory")
            except Exception as delete_error:
                self.logger.error(f"Copy succeeded but delete failed: {delete_error}")
                self.logger.warning(f"File {file_path.name} copied to processed but original remains")
                
        except Exception as e:
            self.logger.error(f"Error moving processed file: {str(e)}")
            raise Exception(f"Unable to move processed file {file_path.name}")


class ObsidianFormatter:
    """Handles Obsidian note formatting"""
    
    def __init__(self, claude_analyzer: ClaudeAnalyzer):
        self.claude_analyzer = claude_analyzer
        self.logger = logging.getLogger(__name__)
    
    def create_obsidian_note(self, analysis_text: str, transcript: str, 
                           filename: str, meeting_topic: str) -> str:
        """Convert analysis to Obsidian note format"""
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        meeting_date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
        
        clean_title = meeting_topic.replace('-', ' ')
        
        self.logger.info("Identifying speakers in transcript with full content preservation...")
        formatted_transcript = self.claude_analyzer.identify_speakers(transcript)
        
        # Build the note content without f-string to avoid syntax issues
        note_parts = []
        note_parts.append("Type: Meeting")
        note_parts.append(f"Date: {meeting_date}")
        note_parts.append("Project: ")
        note_parts.append("Meeting Type: Technical Review / Sales Call / Planning / Standup / Demo / Crisis")
        note_parts.append("Duration: ")
        note_parts.append("Status: Processed")
        note_parts.append("")
        note_parts.append("## Attendees")
        note_parts.append("Internal Team: ")
        note_parts.append("Client/External: ")
        note_parts.append("Key Decision Makers: ")
        note_parts.append("")
        note_parts.append("## Meeting Context")
        note_parts.append("Purpose: ")
        note_parts.append("Agenda Items: ")
        note_parts.append("Background: ")
        note_parts.append("Expected Outcomes: ")
        note_parts.append("")
        note_parts.append("## Key Decisions Made")
        note_parts.append("<!-- Extracted automatically and manually added -->")
        note_parts.append("")
        note_parts.append("## Action Items")
        note_parts.append("<!-- Links to task records -->")
        note_parts.append("")
        note_parts.append("## Technical Discussions")
        note_parts.append("Architecture Decisions: ")
        note_parts.append("Technology Choices: ")
        note_parts.append("Integration Approaches: ")
        note_parts.append("Performance Considerations: ")
        note_parts.append("")
        note_parts.append("## Issues Identified")
        note_parts.append("Blockers: ")
        note_parts.append("Technical Challenges: ")
        note_parts.append("Business Risks: ")
        note_parts.append("Dependencies: ")
        note_parts.append("")
        note_parts.append("## Opportunities Discovered")
        note_parts.append("Upsell Potential: ")
        note_parts.append("Future Projects: ")
        note_parts.append("New Requirements: ")
        note_parts.append("Partnership Options: ")
        note_parts.append("")
        note_parts.append("## Knowledge Captured")
        note_parts.append("New Insights: ")
        note_parts.append("Best Practices: ")
        note_parts.append("Lessons Learned: ")
        note_parts.append("Process Improvements: ")
        note_parts.append("")
        note_parts.append("## Follow-up Required")
        note_parts.append("Next Meeting: ")
        note_parts.append("Documentation Needed: ")
        note_parts.append("Research Tasks: ")
        note_parts.append("Client Communication: ")
        note_parts.append("")
        note_parts.append("## Entity Connections")
        note_parts.append("People Mentioned: ")
        note_parts.append("Companies Discussed: ")
        note_parts.append("Technologies Referenced: ")
        note_parts.append("Solutions Applied: ")
        note_parts.append("Related Projects: ")
        note_parts.append("")
        note_parts.append("## Meeting Quality")
        note_parts.append("Effectiveness: High / Medium / Low")
        note_parts.append("Decision Quality: Good / Fair / Poor")
        note_parts.append("Action Clarity: Clear / Unclear")
        note_parts.append("Follow-up Needed: Yes / No")
        note_parts.append("")
        note_parts.append("## AI Analysis")
        note_parts.append("")
        note_parts.append(analysis_text)
        note_parts.append("")
        note_parts.append("## Complete Transcript")
        note_parts.append("")
        note_parts.append(formatted_transcript)
        note_parts.append("")
        note_parts.append("---")
        note_parts.append("Tags: #meeting #project/active #type/technical-review")
        note_parts.append("Audio File: ")
        note_parts.append(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        note_parts.append("Auto-generated: Yes")
        
        return "\n".join(note_parts)


class MeetingProcessor:
    """Main meeting processor that orchestrates all components"""
    
    def __init__(self):
        self.logger = Logger.setup()
        
        # Initialize API clients
        self._init_api_clients()
        
        # Initialize directories and file management
        self._init_directories()
        
        # Initialize components
        self.audio_processor = AudioProcessor(self.file_manager.output_dir)
        self.transcription_service = TranscriptionService(self.openai_client, self.audio_processor)
        self.claude_analyzer = ClaudeAnalyzer(self.anthropic_client)
        self.obsidian_formatter = ObsidianFormatter(self.claude_analyzer)
        self.entity_detector = EntityDetector(self.anthropic_client)
        
        self.logger.info(f"Monitoring directory: {self.file_manager.input_dir}")
        self.logger.info(f"Output directory: {self.file_manager.output_dir}")
        self.logger.info(f"Obsidian vault path: {self.file_manager.obsidian_vault_path}")
    
    def _init_api_clients(self):
        """Initialize API clients"""
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        
        if not self.anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        if not OPENAI_AVAILABLE:
            self.logger.warning("OpenAI module not installed - will create placeholder analysis only")
            self.openai_client = None
        elif not self.openai_key:
            self.logger.warning("OPENAI_API_KEY not found - will create placeholder analysis only")
            self.openai_client = None
        else:
            self.openai_client = openai.OpenAI(api_key=self.openai_key)
            self.logger.info("OpenAI client initialized successfully")
        
        self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
    
    def _init_directories(self):
        """Initialize directory structure and file manager"""
        input_dir = Path(os.getenv('INPUT_DIR', '/app/input'))
        output_dir = Path(os.getenv('OUTPUT_DIR', '/app/output'))
        processed_dir = Path(os.getenv('PROCESSED_DIR', '/app/processed'))
        obsidian_vault_path = os.getenv('OBSIDIAN_VAULT_PATH', '/app/obsidian_vault')
        obsidian_folder_path = os.getenv('OBSIDIAN_FOLDER_PATH', 'Meetings')
        
        self.file_manager = FileManager(
            input_dir, output_dir, processed_dir,
            obsidian_vault_path, obsidian_folder_path
        )
    
    def create_placeholder_analysis(self, flac_path: Path) -> Dict[str, Any]:
        """Create placeholder analysis when transcription is not available"""
        file_size = flac_path.stat().st_size / (1024 * 1024)
        
        analysis = f"""# Meeting Analysis - {flac_path.stem}

**File:** {flac_path.name}
**Size:** {file_size:.2f} MB
**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Audio File Processed

This system successfully detected and converted your meeting recording to FLAC format. 

**Note:** To enable full transcription and analysis, ensure both API keys are properly configured.

## Current Status

- ✅ MP4 detected and processed
- ✅ Audio converted to FLAC format
- ⏳ Transcription requires OpenAI API key
- ⏳ Analysis requires transcript

## File Location

Your audio file has been saved and is ready for processing:
- **FLAC File:** Available in the output directory
- **Original MP4:** Moved to processed directory
"""

        return {
            "timestamp": datetime.now().isoformat(),
            "source_file": flac_path.name,
            "transcript": "Transcription not available - OpenAI API key required",
            "analysis": analysis,
            "file_size_mb": round(file_size, 2),
            "status": "audio_converted_awaiting_api_key"
        }
    
    def save_analysis(self, analysis: Dict[str, Any], original_filename: str) -> Path:
        """Save the analysis to files including Obsidian format"""
        # Extract meeting topic for filename if we have a transcript
        meeting_topic = "Meeting-Recording"  # Default
        if ('transcript' in analysis and 
            not analysis['transcript'].startswith('Transcription not available')):
            meeting_topic = self.claude_analyzer.extract_meeting_topic(analysis['transcript'])
        
        # Create enhanced filename with topic, date, and time
        meeting_date = datetime.now().strftime("%Y-%m-%d")
        meeting_time = datetime.now().strftime("%H-%M")
        enhanced_filename = f"{meeting_topic}_{meeting_date}_{meeting_time}"
        
        # Create Obsidian note if we have a transcript
        if ('transcript' in analysis and 
            not analysis['transcript'].startswith('Transcription not available')):
            obsidian_content = self.obsidian_formatter.create_obsidian_note(
                analysis['analysis'], 
                analysis['transcript'], 
                original_filename,
                meeting_topic
            )
            
            # Save Obsidian note with enhanced filename
            obsidian_filename = f"{enhanced_filename}_meeting.md"
            obsidian_path = self.file_manager.output_dir / obsidian_filename
            
            with open(obsidian_path, 'w', encoding='utf-8') as f:
                f.write(obsidian_content)
            
            self.logger.info(f"Obsidian meeting note saved to {obsidian_path}")
            
            # Save to Obsidian vault via direct file system access
            success = self.file_manager.save_to_obsidian_vault(obsidian_filename, obsidian_content)
            if success:
                self.logger.info("Meeting note successfully saved to Obsidian vault")
            else:
                self.logger.warning("Failed to save to Obsidian vault - note saved locally only")
        
        # Save original JSON format with enhanced filename
        analysis_filename = f"{enhanced_filename}_analysis.json"
        analysis_path = self.file_manager.output_dir / analysis_filename
        
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        # Save original markdown format with enhanced filename
        md_filename = f"{enhanced_filename}_analysis.md"
        md_path = self.file_manager.output_dir / md_filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# Meeting Analysis - {meeting_topic}\n\n")
            f.write(f"**Processed:** {analysis['timestamp']}\n")
            f.write(f"**Source:** {analysis['source_file']}\n\n")
            f.write("---\n\n")
            
            if ('transcript' in analysis and 
                not analysis['transcript'].startswith('Transcription not available')):
                f.write("## Complete Transcript\n\n")
                f.write(analysis['transcript'])
                f.write("\n\n---\n\n")
                f.write("## Analysis\n\n")
                f.write(analysis['analysis'])
                
                # Save separate transcript file with enhanced filename
                txt_filename = f"{enhanced_filename}_transcript.txt"
                txt_path = self.file_manager.output_dir / txt_filename
                with open(txt_path, 'w', encoding='utf-8') as txt_file:
                    txt_file.write(analysis['transcript'])
            else:
                f.write(analysis['analysis'])
        
        self.logger.info(f"Analysis saved to {analysis_path} and {md_path}")
        return analysis_path
    
    def process_meeting_file(self, mp4_path: Path):
        """Complete processing pipeline for a meeting file"""
        try:
            self.logger.info(f"Starting processing of {mp4_path}")
            
            # Convert MP4 to FLAC
            flac_path = self.audio_processor.convert_mp4_to_flac(mp4_path)
            if not flac_path:
                self.logger.error(f"Failed to convert {mp4_path}")
                return
            
            # Process with transcription and analysis
            analysis = self._process_with_transcription(flac_path)
            if not analysis:
                self.logger.error(f"Failed to process {flac_path}")
                return
            
            # Save results and move processed file
            self.save_analysis(analysis, mp4_path.name)
            self.file_manager.move_processed_file(mp4_path)
            self.file_manager.mark_file_processed(mp4_path.name)
            
            self.logger.info(f"Successfully completed processing of {mp4_path.name}")
            
        except Exception as e:
            self.logger.error(f"Error in processing pipeline: {str(e)}")
    
    def _process_with_transcription(self, flac_path: Path) -> Optional[Dict[str, Any]]:
        """Process FLAC file - either with full transcription or placeholder"""
        try:
            if self.openai_client:
                self.logger.info(f"Processing {flac_path} with Whisper + Claude AI")
                
                # Transcribe audio
                transcript = self.transcription_service.transcribe_audio(flac_path)
                if not transcript:
                    self.logger.error(f"Failed to transcribe {flac_path}")
                    return self.create_placeholder_analysis(flac_path)
                
                # Analyze with Claude
                result = self.claude_analyzer.analyze_transcript(transcript, flac_path.name)
                if not result:
                    self.logger.error(f"Failed to analyze transcript with Claude AI")
                    return self.create_placeholder_analysis(flac_path)
                
                # Detect entities
                entities = self.entity_detector.detect_all_entities(transcript, flac_path.name)
                result['entities'] = entities
                
                return result
            else:
                self.logger.info(f"Creating placeholder analysis for {flac_path}")
                return self.create_placeholder_analysis(flac_path)
            
        except Exception as e:
            self.logger.error(f"Error processing: {str(e)}")
            return self.create_placeholder_analysis(flac_path)
    
    def process_existing_files(self):
        """Process any existing MP4 files on startup"""
        self.logger.info("Checking for existing MP4 files...")
        
        all_files = list(self.file_manager.input_dir.iterdir())
        self.logger.info(f"All files in directory: {[f.name for f in all_files]}")
        
        existing_files = [
            f for f in all_files 
            if f.is_file() and f.suffix.lower() == '.mp4'
        ]
        
        self.logger.info(f"MP4 files found: {[f.name for f in existing_files]}")
        
        if existing_files:
            self.logger.info(f"Found {len(existing_files)} existing MP4 file(s)")
            for mp4_file in existing_files:
                if not self.file_manager.is_file_processed(mp4_file.name):
                    self.logger.info(f"Processing existing file: {mp4_file.name}")
                    self.process_meeting_file(mp4_file)
                else:
                    self.logger.info(f"File {mp4_file.name} already processed, skipping")
        else:
            self.logger.info("No existing MP4 files found")


class MeetingFileHandler(FileSystemEventHandler):
    """File system event handler for new MP4 files"""
    
    def __init__(self, processor: MeetingProcessor):
        self.processor = processor
        self.processing_files = set()
        self.logger = logging.getLogger(__name__)

    def on_created(self, event):
        if event.is_directory:
            return
        self.logger.info(f"File created: {event.src_path}")
        self._handle_file_event(event.src_path, "created")

    def on_moved(self, event):
        if event.is_directory:
            return
        self.logger.info(f"File moved: {event.src_path} -> {event.dest_path}")
        self._handle_file_event(event.dest_path, "moved")

    def on_modified(self, event):
        if event.is_directory:
            return
        self.logger.info(f"File modified: {event.src_path}")
        self._handle_file_event(event.src_path, "modified")

    def _handle_file_event(self, file_path_str: str, event_type: str):
        """Handle file system events for MP4 files"""
        file_path = Path(file_path_str)
        
        self.logger.info(f"Handling {event_type} event for: {file_path}")
        
        if file_path.suffix.lower() != '.mp4':
            self.logger.info(f"Ignoring non-MP4 file: {file_path}")
            return
        
        # Check if already processed
        if self.processor.file_manager.is_file_processed(file_path.name):
            self.logger.info(f"File {file_path.name} already processed, skipping")
            return
        
        # Check if we're already processing this file
        if str(file_path) in self.processing_files:
            self.logger.info(f"Already processing {file_path.name}, skipping")
            return
        
        # Wait for file to be completely written
        self.logger.info("Waiting 3 seconds for file to stabilize...")
        time.sleep(3)
        
        # Verify file still exists and is accessible
        if not file_path.exists():
            self.logger.warning(f"File {file_path} no longer exists")
            return
        
        self.logger.info(f"File size: {file_path.stat().st_size} bytes")
        
        # Process the file
        self.processing_files.add(str(file_path))
        
        try:
            self.logger.info(f"Starting to process {file_path.name}")
            self.processor.process_meeting_file(file_path)
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
        finally:
            self.processing_files.discard(str(file_path))


def main():
    """Main application entry point"""
    try:
        logger = Logger.setup()
        logger.info("Starting Meeting Processor...")
        
        # Initialize processor
        processor = MeetingProcessor()
        
        # Process existing files on startup
        processor.process_existing_files()
        
        # Set up file system monitoring
        event_handler = MeetingFileHandler(processor)
        observer = Observer()
        observer.schedule(event_handler, str(processor.file_manager.input_dir), recursive=False)
        
        # Start monitoring
        observer.start()
        logger.info("Meeting Processor is running. Press Ctrl+C to stop.")
        
        # Periodic backup scan for new files
        processed_files = set()
        
        try:
            while True:
                time.sleep(2)  # Check every 2 seconds for testing
                
                # Periodic scan for new files (backup for watchdog)
                try:
                    current_files = list(processor.file_manager.input_dir.glob("*.mp4"))
                    for mp4_file in current_files:
                        file_key = str(mp4_file)
                        if (file_key not in processed_files and 
                            not processor.file_manager.is_file_processed(mp4_file.name)):
                            logger.info(f"Periodic scan found new file: {mp4_file.name}")
                            processed_files.add(file_key)
                            processor.process_meeting_file(mp4_file)
                except Exception as e:
                    logger.error(f"Error in periodic scan: {e}")
                    
        except KeyboardInterrupt:
            logger.info("Stopping Meeting Processor...")
            observer.stop()
        
        observer.join()
        logger.info("Meeting Processor stopped.")
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    main()#!/usr/bin/env python3
"""
Meeting Processor - Enhanced version with topic extraction and complete transcripts
Refactored for better organization and maintainability
"""

import os
import time
import logging
import shutil
import signal
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

import anthropic
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Logger:
    """Centralized logging configuration"""
    
    @staticmethod
    def setup() -> logging.Logger:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('meeting_processor.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio conversion and chunking operations"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
    
    def convert_mp4_to_flac(self, mp4_path: Path) -> Optional[Path]:
        """Convert MP4 to FLAC using ffmpeg with compression for Whisper"""
        try:
            flac_filename = mp4_path.stem + '.flac'
            flac_path = self.output_dir / flac_filename
            
            self.logger.info(f"Converting {mp4_path} to {flac_path}")
            
            cmd = [
                'ffmpeg', '-i', str(mp4_path),
                '-vn',  # No video
                '-ac', '1',  # Mono audio (reduces file size)
                '-ar', '16000',  # 16kHz sample rate (good for speech)
                '-acodec', 'flac',
                '-compression_level', '12',  # Maximum compression
                '-y',
                str(flac_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                file_size = flac_path.stat().st_size
                file_size_mb = file_size / (1024 * 1024)
                self.logger.info(f"Successfully converted {mp4_path.name} to FLAC ({file_size_mb:.1f}MB)")
                
                if file_size > 25 * 1024 * 1024:
                    self.logger.warning(f"FLAC file too large ({file_size_mb:.1f}MB), will need to chunk for Whisper")
                
                return flac_path
            else:
                self.logger.error(f"FFmpeg error: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error converting {mp4_path}: {str(e)}")
            return None
    
    def chunk_audio_file(self, audio_path: Path, chunk_duration_minutes: int = 10) -> List[Path]:
        """Split large audio file into smaller chunks for Whisper processing"""
        try:
            chunks = []
            chunk_duration_seconds = chunk_duration_minutes * 60
            
            # Get audio duration
            cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', 
                   '-of', 'csv=p=0', str(audio_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            total_duration = float(result.stdout.strip())
            
            self.logger.info(f"Audio duration: {total_duration:.1f} seconds, creating chunks...")
            
            # Create chunks
            chunk_number = 0
            for start_time in range(0, int(total_duration), chunk_duration_seconds):
                chunk_number += 1
                chunk_filename = f"{audio_path.stem}_chunk_{chunk_number:02d}.flac"
                chunk_path = audio_path.parent / chunk_filename
                
                cmd = [
                    'ffmpeg', '-i', str(audio_path),
                    '-ss', str(start_time),
                    '-t', str(chunk_duration_seconds),
                    '-ac', '1', '-ar', '16000',
                    '-acodec', 'flac',
                    '-compression_level', '12',
                    '-y', str(chunk_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    chunk_size = chunk_path.stat().st_size / (1024 * 1024)
                    self.logger.info(f"Created chunk {chunk_number}: {chunk_filename} ({chunk_size:.1f}MB)")
                    chunks.append(chunk_path)
                else:
                    self.logger.error(f"Failed to create chunk {chunk_number}: {result.stderr}")
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error chunking audio file: {str(e)}")
            return []


class TranscriptionService:
    """Handles OpenAI Whisper transcription"""
    
    def __init__(self, openai_client: Optional[openai.OpenAI], audio_processor: AudioProcessor):
        self.openai_client = openai_client
        self.audio_processor = audio_processor
        self.logger = logging.getLogger(__name__)
    
    def transcribe_audio(self, audio_path: Path) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper"""
        if not self.openai_client:
            self.logger.warning("OpenAI client not available - skipping transcription")
            return None
        
        file_size = audio_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        # Handle large files by chunking
        if file_size > 25 * 1024 * 1024:
            return self._transcribe_large_file(audio_path, file_size_mb)
        else:
            return self._transcribe_single_file(audio_path, file_size_mb)
    
    def _transcribe_large_file(self, audio_path: Path, file_size_mb: float) -> Optional[str]:
        """Transcribe large files by chunking"""
        self.logger.info(f"File too large ({file_size_mb:.1f}MB), splitting into chunks...")
        chunks = self.audio_processor.chunk_audio_file(audio_path)
        
        if not chunks:
            self.logger.error("Failed to create audio chunks")
            return None
        
        full_transcript = []
        for i, chunk_path in enumerate(chunks, 1):
            self.logger.info(f"Transcribing chunk {i}/{len(chunks)}: {chunk_path.name}")
            
            chunk_text = self._transcribe_chunk(chunk_path, i)
            full_transcript.append(chunk_text)
            
            # Clean up chunk file
            self._cleanup_chunk(chunk_path)
        
        combined_transcript = " ".join(full_transcript)
        self.logger.info(f"Successfully completed transcription of {len(chunks)} chunks")
        return combined_transcript
    
    def _transcribe_single_file(self, audio_path: Path, file_size_mb: float) -> Optional[str]:
        """Transcribe a single file"""
        self.logger.info(f"Transcribing {audio_path} with Whisper ({file_size_mb:.1f}MB)")
        
        try:
            with open(audio_path, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            result_text = transcript.text if hasattr(transcript, 'text') else str(transcript)
            self.logger.info(f"Successfully transcribed {audio_path.name} ({len(result_text)} characters)")
            return result_text
            
        except Exception as e:
            self.logger.error(f"Error transcribing {audio_path}: {str(e)}")
            return None
    
    def _transcribe_chunk(self, chunk_path: Path, chunk_number: int) -> str:
        """Transcribe a single chunk with timeout handling"""
        try:
            with open(chunk_path, 'rb') as audio_file:
                def timeout_handler(signum, frame):
                    raise TimeoutError("Whisper API call timed out")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(60)
                
                try:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        timeout=120
                    )
                    
                    chunk_text = transcript.text.strip() if hasattr(transcript, 'text') else str(transcript).strip()
                    self.logger.info(f"Successfully transcribed chunk {chunk_number} ({len(chunk_text)} characters)")
                    return chunk_text
                    
                finally:
                    signal.alarm(0)
                    
        except TimeoutError:
            self.logger.error(f"Timeout transcribing chunk {chunk_number} - skipping")
            return f"[Audio section {chunk_number} could not be transcribed - timeout]"
        except Exception as e:
            self.logger.error(f"Error transcribing chunk {chunk_number}: {e}")
            return f"[Audio section {chunk_number} could not be transcribed: {str(e)}]"
    
    def _cleanup_chunk(self, chunk_path: Path):
        """Clean up temporary chunk file"""
        try:
            chunk_path.unlink()
            self.logger.info(f"Cleaned up chunk file: {chunk_path.name}")
        except Exception as e:
            self.logger.warning(f"Could not clean up chunk file: {e}")


class ClaudeAnalyzer:
    """Handles Claude AI analysis and speaker identification"""
    
    def __init__(self, anthropic_client: anthropic.Anthropic):
        self.anthropic_client = anthropic_client
        self.logger = logging.getLogger(__name__)
    
    def extract_meeting_topic(self, transcript: str) -> str:
        """Extract meeting topic using Claude AI for filename generation"""
        try:
            self.logger.info("Extracting meeting topic for filename...")
            
            topic_prompt = f"""Please analyze this meeting transcript and extract a concise meeting topic that would be suitable for a filename. 

Requirements:
- Maximum 4-6 words
- Use title case 
- Replace spaces with hyphens
- Remove special characters that aren't suitable for filenames
- Focus on the main subject/purpose of the meeting

Examples of good topics:
- "DEAL-Payroll-Implementation"
- "Q3-Sales-Review"
- "Project-Kickoff-Meeting"
- "Budget-Planning-Session"

Transcript excerpt (first 1000 characters):
{transcript[:1000]}

Please respond with just the topic in the format specified above, nothing else."""

            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                messages=[{"role": "user", "content": topic_prompt}]
            )
            
            topic = response.content[0].text.strip()
            
            # Clean up the topic to ensure it's filename-safe
            topic = re.sub(r'[^\w\-]', '', topic)
            topic = re.sub(r'-+', '-', topic)  # Remove multiple consecutive hyphens
            topic = topic.strip('-')  # Remove leading/trailing hyphens
            
            self.logger.info(f"Extracted meeting topic: {topic}")
            return topic
            
        except Exception as e:
            self.logger.error(f"Error extracting meeting topic: {str(e)}")
            return "Meeting-Recording"  # Fallback topic
    
    def analyze_transcript(self, transcript: str, audio_filename: str) -> Optional[Dict[str, Any]]:
        """Analyze transcript with Claude AI"""
        try:
            self.logger.info("Analyzing transcript with Claude AI")
            
            prompt = f"""Please analyze this meeting transcript and provide a comprehensive analysis:

**Audio File:** {audio_filename}
**Transcript:**
{transcript}

Please provide:

1. **Meeting Summary**: Brief overview of the meeting purpose and key topics
2. **Major Decisions**: List all decisions made during the meeting
3. **Action Items/Tasks**: Extract all tasks assigned, including who is responsible and deadlines if mentioned
4. **Key Discussion Points**: Important topics discussed in detail
5. **Participants**: List of people who spoke (if identifiable from the transcript)
6. **Next Steps**: Any follow-up actions or future meetings mentioned
7. **Important Quotes**: Any significant statements or commitments made

Format the response as a well-structured document that can be easily reviewed and shared.

IMPORTANT: Ensure the analysis captures ALL content from the transcript without summarization or omission of details."""

            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis = response.content[0].text
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "source_file": audio_filename,
                "transcript": transcript,
                "analysis": analysis
            }
            
            self.logger.info("Successfully analyzed transcript with Claude AI")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing with Claude AI: {str(e)}")
            return None
    
    def identify_speakers(self, transcript: str) -> str:
        """Use Claude to identify and format speakers in the transcript"""
        try:
            if len(transcript) > 10000:
                self.logger.info(f"Transcript is long ({len(transcript)} chars), processing in chunks for speaker ID")
                return self._identify_speakers_chunked(transcript)
            
            return self._identify_speakers_single(transcript)
            
        except Exception as e:
            self.logger.error(f"Error identifying speakers: {str(e)}")
            return transcript
    
    def _identify_speakers_single(self, transcript: str) -> str:
        """Identify speakers in a single transcript"""
        speaker_prompt = f"""Please analyze this meeting transcript and identify different speakers. Add speaker labels that preserve ALL the original content.

CRITICAL REQUIREMENTS:
1. Keep 100% of the original transcript content - do not summarize, omit, or paraphrase ANY spoken words
2. Only add speaker labels like "Speaker A:", "Speaker B:", etc. at the beginning of speaker turns
3. Preserve all conversation details, technical terms, names, and complete sentences
4. Do not replace any content with summaries like "[Continues with technical instructions]"
5. If you cannot complete the full formatting due to length, return the original transcript unchanged

Try to identify natural speaker changes based on:
- Changes in topic or perspective  
- Conversational patterns (questions/answers)
- Different speaking styles or vocabulary
- Context clues about roles

Original transcript:
{transcript}

Please return the COMPLETE transcript with only speaker labels added, maintaining every single word from the original."""

        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            messages=[{"role": "user", "content": speaker_prompt}]
        )
        
        formatted_transcript = response.content[0].text
        
        # Verify that the formatted transcript is not significantly shorter than original
        if len(formatted_transcript) < len(transcript) * 0.85:
            self.logger.warning(f"Formatted transcript seems truncated. Using original.")
            return transcript
        
        self.logger.info(f"Successfully formatted transcript with speakers")
        return formatted_transcript
    
    def _identify_speakers_chunked(self, transcript: str) -> str:
        """Process very long transcripts in chunks for speaker identification"""
        try:
            chunks = self._split_transcript_into_chunks(transcript)
            self.logger.info(f"Split transcript into {len(chunks)} chunks at sentence boundaries")
            
            formatted_chunks = []
            
            for i, chunk in enumerate(chunks):
                self.logger.info(f"Processing speaker ID for chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
                formatted_chunk = self._process_speaker_chunk(chunk, i, len(chunks))
                formatted_chunks.append(formatted_chunk)
            
            result = "\n\n".join(formatted_chunks)
            
            # Final verification
            if len(result) < len(transcript) * 0.7:
                self.logger.warning("Chunked result seems too short, using original")
                return transcript
            
            self.logger.info("Successfully completed chunked speaker identification")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in chunked speaker identification: {e}")
            return transcript
    
    def _split_transcript_into_chunks(self, transcript: str, chunk_size: int = 5000, overlap: int = 200) -> List[str]:
        """Split transcript into manageable chunks"""
        sentences = transcript.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                if len(current_chunk) > overlap:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + sentence + ". "
                else:
                    current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _process_speaker_chunk(self, chunk: str, chunk_index: int, total_chunks: int) -> str:
        """Process a single chunk for speaker identification"""
        chunk_prompt = f"""Add speaker labels to this transcript chunk. Keep ALL original content exactly as is.

This is chunk {chunk_index + 1} of {total_chunks} from a longer meeting transcript.

CRITICAL REQUIREMENTS:
1. Add ONLY speaker labels like "Speaker A:", "Speaker B:" at the beginning of speaker turns
2. Keep 100% of the original words - no changes, no summarization, no corrections
3. Maintain all technical terms, numbers, and conversation flow exactly
4. Do not reorganize or clean up the text
5. Do NOT add any commentary, explanations, or chunk references
6. Return ONLY the transcript content with speaker labels added
7. If you cannot complete the full formatting, return the original chunk unchanged

Original chunk:
{chunk}

RETURN ONLY THE TRANSCRIPT WITH SPEAKER LABELS - NO OTHER TEXT:"""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8000,
                messages=[{"role": "user", "content": chunk_prompt}]
            )
            
            formatted_chunk = response.content[0].text.strip()
            
            # Verify chunk wasn't significantly altered
            if len(formatted_chunk) < len(chunk) * 0.75:
                self.logger.warning(f"Chunk {chunk_index + 1} seems heavily modified, using original")
                return chunk
            
            self.logger.info(f"Successfully processed chunk {chunk_index + 1}")
            return formatted_chunk
            
        except Exception as e:
            self.logger.error(f"Error processing chunk {chunk_index + 1}: {e}")
            return chunk


class EntityDetector:
    """Detects entities from meeting transcripts"""
    
    def __init__(self, anthropic_client: anthropic.Anthropic):
        self.logger = logging.getLogger(__name__)
        self.anthropic_client = anthropic_client
        
        # Technology keywords specific to your Amazon Connect work
        self.technology_keywords = {
            'Amazon Connect', 'AWS Lambda', 'Salesforce', 'Lambda', 'Connect',
            'DynamoDB', 'API Gateway', 'CloudFormation', 'S3', 'CloudWatch',
            'OmniFlow', 'SSML', 'IVR', 'CRM', 'Lex', 'Polly', 'Kinesis',
            'Service Cloud', 'Sales Cloud', 'Voice call record', 'Contact flow'
        }
    
    def extract_people_names(self, transcript: str) -> List[str]:
        """Extract potential people names from transcript"""
        import re
        
        # Better pattern for actual names (2+ consecutive capitalized words)
        name_patterns = [
            r'\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b',  # First Last (John Smith)
            r'\b[A-Z][a-z]{3,}\b'  # Single names at least 4 chars (Madison, not "So")
        ]
        
        potential_names = []
        for pattern in name_patterns:
            matches = re.findall(pattern, transcript)
            potential_names.extend(matches)
        
        # Much more comprehensive false positives list
        false_positives = {
            # Common words that get capitalized
            'Speaker', 'That', 'This', 'There', 'They', 'Then', 'Those', 'These',
            'What', 'When', 'Where', 'Which', 'With', 'Will', 'Would', 'Were',
            'Yeah', 'Okay', 'Sure', 'Right', 'Well', 'Good', 'Great', 'Fine',
            'Perfect', 'Cool', 'Nice', 'Awesome', 'Sweet', 'Excellent',
            'Please', 'Thank', 'Thanks', 'Sorry', 'Excuse', 'Pardon',
            'Hello', 'Goodbye', 'Morning', 'Afternoon', 'Evening', 'Night',
            'Today', 'Tomorrow', 'Yesterday', 'Tonight', 'Later', 'Earlier',
            
            # Common conversation words from transcripts
            'Like', 'Just', 'Really', 'Actually', 'Basically', 'Obviously',
            'Definitely', 'Probably', 'Maybe', 'Perhaps', 'Exactly', 'Totally',
            'Cause', 'Because', 'However', 'Therefore', 'Otherwise', 'Unless',
            'Though', 'Although', 'While', 'Since', 'Until', 'Before', 'After',
            'Above', 'Below', 'Over', 'Under', 'Through', 'Around', 'Between',
            'During', 'Without', 'Within', 'Behind', 'Beside', 'Across', 'Along',
            
            # Meeting/call specific words
            'Codes', 'Code', 'Call', 'Phone', 'Number', 'Press', 'Enter', 'Type',
            'Click', 'Select', 'Choose', 'Pick', 'Menu', 'Option', 'Button',
            'Screen', 'Page', 'Site', 'Link', 'File', 'Document', 'Report',
            'Email', 'Message', 'Text', 'Voice', 'Audio', 'Video', 'Image',
            
            # Action words
            'Give', 'Take', 'Make', 'Send', 'Get', 'Put', 'Set', 'Let',
            'Help', 'Show', 'Tell', 'Ask', 'Say', 'Talk', 'Speak', 'Listen',
            'Look', 'See', 'Watch', 'Read', 'Write', 'Edit', 'Copy', 'Paste',
            'Save', 'Open', 'Close', 'Start', 'Stop', 'Run', 'Load', 'Wait',
            'Hold', 'Keep', 'Move', 'Go', 'Come', 'Turn', 'Change', 'Switch',
            
            # Question words and responses
            'Does', 'Did', 'Will', 'Can', 'Could', 'Should', 'Would', 'Might',
            'Must', 'Need', 'Want', 'Have', 'Has', 'Had', 'Are', 'Is', 'Was',
            'Been', 'Being', 'Do', 'Done', 'Going', 'Coming', 'Working',
            
            # Tech/business terms and companies
            'PSA', 'DNA', 'Connect', 'Amazon', 'AWS', 'Salesforce', 'Google',
            'Microsoft', 'Apple', 'Oracle', 'IBM', 'Adobe', 'Intel', 'Cisco',
            'Lambda', 'CloudFormation', 'DynamoDB', 'OmniFlow', 'SSML',
            
            # Other common words from the transcript
            'Post', 'Using', 'Make', 'Deploys', 'Input', 'Transfer', 'Lyft', 'Cobra',
            'Whatever', 'Something', 'Nothing', 'Everything', 'Anything',
            'Someone', 'Anyone', 'Everyone', 'Nobody', 'Somebody', 'Everybody',
            'Somewhere', 'Anywhere', 'Everywhere', 'Nowhere',
            
            # Days of week
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
            
            # Months
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December',
            
            # Meeting-specific terms
            'Meeting', 'Call', 'Conference', 'Discussion', 'Review', 'Demo',
            'Presentation', 'Training', 'Workshop', 'Session', 'Agenda',
            'Quality', 'Survey', 'Question', 'Answer', 'Document', 'Report',
            'Analysis', 'Summary', 'Overview', 'Details', 'Information'
        }
        
        # Keep names that are likely people
        people_names = []
        for name in potential_names:
            # Skip if in false positives
            if name in false_positives:
                continue
            
            # Skip single words that are too short (less than 4 chars)
            if ' ' not in name and len(name) < 4:
                continue
                
            # Skip words that are all caps (likely acronyms)
            if name.isupper():
                continue
                
            # Skip words that look like they might be technical terms
            if any(tech in name.upper() for tech in ['API', 'URL', 'HTTP', 'SQL', 'XML', 'JSON', 'CSV', 'PDF']):
                continue
            
            # Skip words that end with common suffixes that aren't names
            if any(name.lower().endswith(suffix) for suffix in ['ing', 'tion', 'sion', 'ness', 'ment', 'able', 'ible']):
                continue
            
            people_names.append(name)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_names = []
        for name in people_names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)
        
        return unique_names
    
    def extract_companies(self, transcript: str) -> List[str]:
        """Extract company names from transcript"""
        import re
        
        # Look for explicit company indicators
        company_patterns = [
            r'\b([A-Z][a-zA-Z\s&]{2,}(?:Corp|Corporation|Inc|LLC|Ltd|Company|Co\.))\b',
            r'\b([A-Z][a-zA-Z\s&]{3,}(?:\s+Industries|\s+Systems|\s+Solutions|\s+Services))\b',
        ]
        
        companies = []
        for pattern in company_patterns:
            matches = re.findall(pattern, transcript)
            companies.extend(matches)
        
        # Look for well-known company names mentioned in context
        known_companies = {
            # Your specific context
            'PSA': 'PSA',  # Professional Sports Authenticator
            
            # Major tech companies
            'Salesforce': 'Salesforce',
            'Amazon': 'Amazon',
            'Google': 'Google', 
            'Microsoft': 'Microsoft',
            'Apple': 'Apple',
            'Oracle': 'Oracle',
            'IBM': 'IBM',
            'Adobe': 'Adobe',
            'Cisco': 'Cisco',
            'Intel': 'Intel',
            
            # Other common companies
            'Netflix': 'Netflix',
            'Tesla': 'Tesla',
            'Meta': 'Meta',
            'Facebook': 'Facebook',
            'Twitter': 'Twitter',
            'X': 'X',
            'LinkedIn': 'LinkedIn',
            'Zoom': 'Zoom',
            'Slack': 'Slack',
            'Spotify': 'Spotify',
            'Uber': 'Uber',
            'Lyft': 'Lyft',
            'Airbnb': 'Airbnb'
        }
        
        # Find known companies in transcript (case insensitive)
        transcript_words = re.findall(r'\b[A-Za-z]+\b', transcript)
        for word in transcript_words:
            for company_key, company_name in known_companies.items():
                if word.lower() == company_key.lower():
                    companies.append(company_name)
                    break
        
        # Clean up and filter results
        cleaned_companies = []
        for company in companies:
            company = company.strip()
            
            # Skip if too short
            if len(company) < 2:
                continue
                
            # Skip obvious false positives
            if company.lower() in ['and', 'the', 'for', 'with', 'from', 'that', 'this', 'you', 'are', 'can', 'will']:
                continue
                
            cleaned_companies.append(company)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_companies = []
        for company in cleaned_companies:
            if company not in seen:
                seen.add(company)
                unique_companies.append(company)
        
        return unique_companies
    
    def extract_technologies(self, transcript: str) -> List[str]:
        """Extract technology mentions from transcript"""
        found_technologies = []
        
        transcript_lower = transcript.lower()
        
        for tech in self.technology_keywords:
            if tech.lower() in transcript_lower:
                found_technologies.append(tech)
        
        return found_technologies
    
    def detect_all_entities(self, transcript: str, meeting_filename: str) -> Dict[str, List[str]]:
        """Detect all entities using Claude AI for better accuracy"""
        self.logger.info(f"🔍 ENTITY DETECTION: Starting analysis for {meeting_filename}")
        
        try:
            prompt = f"""Analyze this meeting transcript and extract entities. Be very conservative and only extract entities you're confident about.

Extract:
1. PEOPLE: Real person names only (first names, full names, but NOT common words, company names, or generic terms)
2. COMPANIES: Business organizations, clients, vendors (including acronyms like PSA if they refer to companies)
3. TECHNOLOGIES: Software platforms, tools, systems, programming languages, cloud services

Rules:
- Only extract real entities, not common words that happen to be capitalized
- For people: Only actual human names (e.g., "Madison", "John Smith") 
- For companies: Business entities (e.g., "PSA", "Salesforce", "Amazon")
- For technologies: Technical systems and tools (e.g., "Lambda", "Connect", "OmniFlow")
- Be conservative - if unsure, don't include it

Transcript:
{transcript}

Return ONLY a JSON object in this exact format:
{{"people": ["name1", "name2"], "companies": ["company1", "company2"], "technologies": ["tech1", "tech2"]}}"""

            self.logger.info("📤 ENTITY DETECTION: Sending transcript to Claude for analysis...")
            
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse Claude's response
            response_text = response.content[0].text.strip()
            self.logger.info(f"📥 ENTITY DETECTION: Raw Claude response: {response_text}")
            
            # Try to extract JSON from response
            import json
            try:
                # Look for JSON in the response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    entities = json.loads(json_str)
                    self.logger.info(f"✅ ENTITY DETECTION: Successfully parsed JSON: {json_str}")
                else:
                    raise ValueError("No JSON found in response")
                
                # Validate structure
                required_keys = ['people', 'companies', 'technologies']
                for key in required_keys:
                    if key not in entities:
                        entities[key] = []
                        self.logger.warning(f"⚠️  ENTITY DETECTION: Missing '{key}' in response, setting to empty list")
                    elif not isinstance(entities[key], list):
                        entities[key] = []
                        self.logger.warning(f"⚠️  ENTITY DETECTION: '{key}' is not a list, converting to empty list")
                
                # Detailed logging of findings
                self.logger.info("🎯 ENTITY DETECTION RESULTS:")
                self.logger.info(f"   👥 PEOPLE DETECTED ({len(entities['people'])}): {entities['people']}")
                if entities['people']:
                    for person in entities['people']:
                        self.logger.info(f"      → Would create: /People/{person.replace(' ', '-')}.md")
                else:
                    self.logger.info("      → No people detected")
                
                self.logger.info(f"   🏢 COMPANIES DETECTED ({len(entities['companies'])}): {entities['companies']}")
                if entities['companies']:
                    for company in entities['companies']:
                        self.logger.info(f"      → Would create: /Companies/{company.replace(' ', '-')}.md")
                else:
                    self.logger.info("      → No companies detected")
                
                self.logger.info(f"   💻 TECHNOLOGIES DETECTED ({len(entities['technologies'])}): {entities['technologies']}")
                if entities['technologies']:
                    for tech in entities['technologies']:
                        self.logger.info(f"      → Would create: /Technologies/{tech.replace(' ', '-')}.md")
                else:
                    self.logger.info("      → No technologies detected")
                
                total_entities = len(entities['people']) + len(entities['companies']) + len(entities['technologies'])
                self.logger.info(f"📊 ENTITY DETECTION SUMMARY: {total_entities} total entities detected")
                
                return entities
                
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"❌ ENTITY DETECTION: Failed to parse Claude's response: {e}")
                self.logger.error(f"❌ ENTITY DETECTION: Raw response was: {response_text}")
                # Fallback to empty results
                return {'people': [], 'companies': [], 'technologies': []}
            
        except Exception as e:
            self.logger.error(f"❌ ENTITY DETECTION: Error in AI entity detection: {str(e)}")
            # Fallback to empty results
            return {'people': [], 'companies': [], 'technologies': []}