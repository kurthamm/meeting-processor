#!/usr/bin/env python3
"""
Meeting Processor - Main Entry Point
Clean, modular architecture with focused responsibilities
"""

import time
from pathlib import Path
from watchdog.observers import Observer

from config.settings import Settings
from core.audio_processor import AudioProcessor
from core.transcription import TranscriptionService
from core.claude_analyzer import ClaudeAnalyzer
from core.file_manager import FileManager
from entities.detector import EntityDetector
from entities.manager import ObsidianEntityManager
from obsidian.formatter import ObsidianFormatter
from monitoring.file_watcher import MeetingFileHandler
from utils.logger import Logger


class MeetingProcessor:
    """Main orchestrator that coordinates all components"""
    
    def __init__(self):
        self.logger = Logger.setup()
        self.settings = Settings()
        
        # Initialize file management
        self.file_manager = FileManager(self.settings)
        
        # Initialize core processing components
        self.audio_processor = AudioProcessor(self.file_manager.output_dir)
        self.transcription_service = TranscriptionService(
            self.settings.openai_client, 
            self.audio_processor
        )
        self.claude_analyzer = ClaudeAnalyzer(self.settings.anthropic_client)
        
        # Initialize entity and formatting components
        self.entity_detector = EntityDetector(self.settings.anthropic_client)
        self.entity_manager = ObsidianEntityManager(
            self.file_manager, 
            self.settings.anthropic_client
        )
        self.obsidian_formatter = ObsidianFormatter(self.claude_analyzer)
        
        self.logger.info(f"Meeting Processor initialized")
        self.logger.info(f"Monitoring: {self.file_manager.input_dir}")
        self.logger.info(f"Output: {self.file_manager.output_dir}")
        self.logger.info(f"Obsidian: {self.file_manager.obsidian_vault_path}")
    
    def process_meeting_file(self, mp4_path: Path):
        """Complete processing pipeline for a meeting file"""
        try:
            self.logger.info(f"🎬 Starting processing: {mp4_path.name}")
            
            # Step 1: Convert audio
            flac_path = self.audio_processor.convert_mp4_to_flac(mp4_path)
            if not flac_path:
                self.logger.error(f"❌ Audio conversion failed: {mp4_path}")
                return
            
            # Step 2: Process with transcription and analysis
            analysis = self._process_with_transcription(flac_path)
            if not analysis:
                self.logger.error(f"❌ Processing failed: {flac_path}")
                return
            
            # Step 3: Save results and clean up
            self._save_analysis(analysis, mp4_path.name)
            self.file_manager.move_processed_file(mp4_path)
            self.file_manager.mark_file_processed(mp4_path.name)
            
            self.logger.info(f"✅ Successfully completed: {mp4_path.name}")
            
        except Exception as e:
            self.logger.error(f"❌ Processing pipeline error: {str(e)}")
    
    def _process_with_transcription(self, flac_path: Path):
        """Process FLAC file with full pipeline"""
        try:
            if not self.settings.openai_client:
                self.logger.info("📝 Creating placeholder (no OpenAI key)")
                return self._create_placeholder_analysis(flac_path)
            
            self.logger.info(f"🎤 Transcribing with Whisper: {flac_path.name}")
            
            # Transcribe audio
            transcript = self.transcription_service.transcribe_audio(flac_path)
            if not transcript:
                return self._create_placeholder_analysis(flac_path)
            
            # Analyze with Claude
            result = self.claude_analyzer.analyze_transcript(transcript, flac_path.name)
            if not result:
                return self._create_placeholder_analysis(flac_path)
            
            # Detect entities
            self.logger.info("🔍 Detecting entities...")
            entities = self.entity_detector.detect_all_entities(transcript, flac_path.name)
            result['entities'] = entities
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Transcription processing error: {str(e)}")
            return self._create_placeholder_analysis(flac_path)
    
    def _create_placeholder_analysis(self, flac_path: Path):
        """Create placeholder when transcription unavailable"""
        from datetime import datetime
        
        file_size = flac_path.stat().st_size / (1024 * 1024)
        
        analysis = f"""# Meeting Analysis - {flac_path.stem}

**File:** {flac_path.name}
**Size:** {file_size:.2f} MB
**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Audio File Processed

Successfully detected and converted meeting recording to FLAC format.

**Note:** Full transcription requires OpenAI API key configuration.

## Current Status

- ✅ MP4 detected and processed
- ✅ Audio converted to FLAC format
- ⏳ Transcription requires OpenAI API key
- ⏳ Analysis requires transcript

## File Location

- **FLAC File:** Available in output directory
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
    
    def _save_analysis(self, analysis, original_filename: str):
        """Save analysis results with entity integration"""
        from datetime import datetime
        import json
        
        # Extract meeting topic for filename
        meeting_topic = "Meeting-Recording"
        if ('transcript' in analysis and 
            not analysis['transcript'].startswith('Transcription not available')):
            meeting_topic = self.claude_analyzer.extract_meeting_topic(analysis['transcript'])
        
        # Create enhanced filename
        meeting_date = datetime.now().strftime("%Y-%m-%d")
        meeting_time = datetime.now().strftime("%H-%M")
        enhanced_filename = f"{meeting_topic}_{meeting_date}_{meeting_time}"
        
        # Save Obsidian note with entity integration
        if ('transcript' in analysis and 
            not analysis['transcript'].startswith('Transcription not available')):
            
            obsidian_filename = f"{enhanced_filename}_meeting.md"
            obsidian_content = self.obsidian_formatter.create_obsidian_note(
                analysis['analysis'], 
                analysis['transcript'], 
                original_filename,
                meeting_topic
            )
            
            # Save locally first
            obsidian_path = self.file_manager.output_dir / obsidian_filename
            with open(obsidian_path, 'w', encoding='utf-8') as f:
                f.write(obsidian_content)
            
            # Create entity notes if entities detected
            entity_links = {'people': [], 'companies': [], 'technologies': []}
            if 'entities' in analysis and analysis['entities']:
                self.logger.info("🔗 Creating entity notes with AI context...")
                entity_links = self.entity_manager.create_entity_notes(
                    analysis['entities'], 
                    obsidian_filename.replace('.md', ''),
                    meeting_date
                )
            
            # Save to Obsidian vault
            success = self.file_manager.save_to_obsidian_vault(obsidian_filename, obsidian_content)
            if success and entity_links and any(entity_links.values()):
                vault_path = Path(self.file_manager.obsidian_vault_path) / self.file_manager.obsidian_folder_path / obsidian_filename
                self.entity_manager.update_meeting_note_with_entities(vault_path, entity_links)
        
        # Save JSON and markdown formats
        analysis_path = self.file_manager.output_dir / f"{enhanced_filename}_analysis.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Analysis saved: {analysis_path.name}")
    
    def process_existing_files(self):
        """Process any existing MP4 files on startup"""
        self.logger.info("🔍 Checking for existing MP4 files...")
        
        existing_files = [
            f for f in self.file_manager.input_dir.iterdir() 
            if f.is_file() and f.suffix.lower() == '.mp4'
        ]
        
        if existing_files:
            self.logger.info(f"📁 Found {len(existing_files)} existing MP4 file(s)")
            for mp4_file in existing_files:
                if not self.file_manager.is_file_processed(mp4_file.name):
                    self.logger.info(f"🎬 Processing existing: {mp4_file.name}")
                    self.process_meeting_file(mp4_file)
                else:
                    self.logger.info(f"⏭️  Already processed: {mp4_file.name}")
        else:
            self.logger.info("📭 No existing MP4 files found")


def main():
    """Application entry point"""
    try:
        logger = Logger.setup()
        logger.info("🚀 Starting Meeting Processor...")
        
        # Initialize processor
        processor = MeetingProcessor()
        
        # Process existing files
        processor.process_existing_files()
        
        # Set up file monitoring
        event_handler = MeetingFileHandler(processor)
        observer = Observer()
        observer.schedule(event_handler, str(processor.file_manager.input_dir), recursive=False)
        
        # Start monitoring
        observer.start()
        logger.info("👀 File monitoring active. Press Ctrl+C to stop.")
        
        # Main loop with periodic backup scan
        processed_files = set()
        try:
            while True:
                time.sleep(2)
                
                # Backup scan for new files
                try:
                    current_files = list(processor.file_manager.input_dir.glob("*.mp4"))
                    for mp4_file in current_files:
                        file_key = str(mp4_file)
                        if (file_key not in processed_files and 
                            not processor.file_manager.is_file_processed(mp4_file.name)):
                            logger.info(f"🔍 Backup scan found: {mp4_file.name}")
                            processed_files.add(file_key)
                            processor.process_meeting_file(mp4_file)
                except Exception as e:
                    logger.error(f"❌ Backup scan error: {e}")
                    
        except KeyboardInterrupt:
            logger.info("🛑 Stopping Meeting Processor...")
            observer.stop()
        
        observer.join()
        logger.info("✅ Meeting Processor stopped")
        
    except Exception as e:
        logger = Logger.get_logger(__name__)
        logger.error(f"💥 Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    main()