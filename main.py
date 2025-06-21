#!/usr/bin/env python3
"""
Meeting Processor - Main Entry Point
Clean, modular architecture with focused responsibilities
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from watchdog.observers import Observer

from config.settings import Settings, ConfigurationError
from core.audio_processor import AudioProcessor
from core.transcription import TranscriptionService
from core.claude_analyzer import ClaudeAnalyzer
from core.file_manager import FileManager
from entities.detector import EntityDetector
from entities.manager import ObsidianEntityManager
from obsidian.formatter import ObsidianFormatter
from monitoring.file_watcher import MeetingFileHandler
from utils.logger import Logger
from core.task_extractor import TaskExtractor
from core.dashboard_orchestrator import DashboardOrchestrator


class MeetingProcessor:
    """Main orchestrator that coordinates all components"""
    
    def __init__(self):
        self.logger = Logger.setup()
        
        try:
            # Initialize settings with validation
            self.settings = Settings()
        except ConfigurationError as e:
            self.logger.error(f"Configuration Error: {str(e)}")
            print("\n❌ Configuration error detected. Please fix the issues above and restart.")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Unexpected error during initialization: {str(e)}")
            sys.exit(1)
        
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
        self.task_extractor = TaskExtractor(self.settings.anthropic_client)
        self.dashboard_orchestrator = DashboardOrchestrator(self.file_manager, self.settings.anthropic_client)
        
        self.logger.info(f"Meeting Processor initialized successfully")
        self.logger.info(f"Configuration: {self.settings.get_config_summary()}")
        self.logger.info(f"Monitoring: {self.file_manager.input_dir}")
        self.logger.info(f"Output: {self.file_manager.output_dir}")
        self.logger.info(f"Obsidian: {self.file_manager.obsidian_vault_path}")
    
    def process_meeting_file(self, mp4_path: Path):
        """Complete processing pipeline for a meeting file"""
        try:
            self.logger.info(f"🎬 Starting processing: {mp4_path.name}")
            
            # Check if we have the necessary API clients
            if not self.settings.openai_client and not self.settings.testing_mode:
                self.logger.warning(f"⚠️  Skipping {mp4_path.name} - OpenAI client not available")
                self._create_api_key_reminder(mp4_path)
                return
            
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
            # Don't crash the whole application for one file
            self.logger.error(f"Skipping file {mp4_path.name} due to error")
    
    def _create_api_key_reminder(self, mp4_path: Path):
        """Create a reminder note about missing API keys"""
        reminder_content = f"""# API Key Required - {mp4_path.name}

**File Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Original File:** {mp4_path.name}

## ⚠️ Missing API Keys

To process this meeting recording, you need to configure:

1. **OpenAI API Key** - Required for transcription
   - Get your key at: https://platform.openai.com/api-keys
   - Set in `.env` file: `OPENAI_API_KEY=sk-...`

2. **Anthropic API Key** - Required for analysis (optional but recommended)
   - Get your key at: https://console.anthropic.com/
   - Set in `.env` file: `ANTHROPIC_API_KEY=sk-...`

## File Location
- **Original MP4:** {mp4_path}
- **Status:** Awaiting API key configuration

Once you've added the API keys, restart the Meeting Processor to process this file.
"""
        
        reminder_filename = f"API-KEY-REQUIRED_{mp4_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        reminder_path = self.file_manager.output_dir / reminder_filename
        
        with open(reminder_path, 'w', encoding='utf-8') as f:
            f.write(reminder_content)
        
        self.logger.info(f"📝 Created API key reminder: {reminder_filename}")
    
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
                self.logger.warning("⚠️ Transcription failed, creating placeholder")
                return self._create_placeholder_analysis(flac_path)
            
            # Analyze with Claude if available
            if self.settings.anthropic_client:
                result = self.claude_analyzer.analyze_transcript(transcript, flac_path.name)
                if not result:
                    # Create result with transcript but no analysis
                    result = {
                        "timestamp": datetime.now().isoformat(),
                        "source_file": flac_path.name,
                        "transcript": transcript,
                        "analysis": self._create_basic_analysis(transcript),
                        "entities": {'people': [], 'companies': [], 'technologies': []}
                    }
                else:
                    # Detect entities
                    self.logger.info("🔍 Detecting entities...")
                    entities = self.entity_detector.detect_all_entities(transcript, flac_path.name)
                    result['entities'] = entities
            else:
                # Create basic result without Claude analysis
                result = {
                    "timestamp": datetime.now().isoformat(),
                    "source_file": flac_path.name,
                    "transcript": transcript,
                    "analysis": self._create_basic_analysis(transcript),
                    "entities": {'people': [], 'companies': [], 'technologies': []}
                }
                self.logger.info("📝 Created basic analysis (no Anthropic key)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Transcription processing error: {str(e)}")
            return self._create_placeholder_analysis(flac_path)
    
    def _create_basic_analysis(self, transcript: str) -> str:
        """Create basic analysis when Claude is not available"""
        word_count = len(transcript.split())
        char_count = len(transcript)
        
        return f"""# Meeting Analysis

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Analysis Type:** Basic (Anthropic API key required for full analysis)

## Transcript Statistics
- **Word Count:** {word_count:,} words
- **Character Count:** {char_count:,} characters
- **Estimated Duration:** ~{word_count // 150} minutes

## Transcript Available
The full transcript has been captured and is available below.

**Note:** To get:
- Meeting summary
- Action items extraction
- Key decisions
- Speaker identification
- Entity detection

Please configure your Anthropic API key in the `.env` file.

## Next Steps
1. Add Anthropic API key for full AI analysis
2. Review the transcript below
3. Manually extract any urgent action items
"""
    
    def _create_placeholder_analysis(self, flac_path: Path):
        """Create placeholder when transcription unavailable"""
        file_size = flac_path.stat().st_size / (1024 * 1024)
        
        analysis = f"""# Meeting Analysis - {flac_path.stem}

**File:** {flac_path.name}
**Size:** {file_size:.2f} MB
**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Audio File Processed

Successfully detected and converted meeting recording to FLAC format.

**Note:** Full transcription requires OpenAI API key configuration.
**Note:** Analysis requires Anthropic API key configuration.

## Current Status

- ✅ MP4 detected and processed
- ✅ Audio converted to FLAC format
- ⏳ Transcription requires OpenAI API key
- ⏳ Analysis requires Anthropic API key

## File Location

- **FLAC File:** Available in output directory
- **Original MP4:** Moved to processed directory

## How to Enable Full Processing

1. **Get API Keys:**
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/

2. **Add to `.env` file:**
   ```
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-...
   ```

3. **Restart Meeting Processor**
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
        
        # Initialize variables for conditional processing
        all_tasks = []
        
        # Extract meeting topic for filename
        meeting_topic = "Meeting-Recording"
        if ('transcript' in analysis and 
            not analysis['transcript'].startswith('Transcription not available') and
            self.settings.anthropic_client):
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
            
            # Create entity notes if entities detected and Anthropic is available
            entity_links = {'people': [], 'companies': [], 'technologies': []}
            if 'entities' in analysis and analysis['entities'] and self.settings.anthropic_client:
                self.logger.info("🔗 Creating entity notes with AI context...")
                entity_links = self.entity_manager.create_entity_notes(
                    analysis['entities'], 
                    obsidian_filename.replace('.md', ''),
                    meeting_date
                )
            
            # Extract all tasks for project visibility (if Anthropic available)
            task_links = []
            if self.settings.anthropic_client:
                self.logger.info("📋 Extracting tasks from meeting...")
                all_tasks = self.task_extractor.extract_all_tasks(
                    analysis['transcript'], 
                    obsidian_filename.replace('.md', ''),
                    meeting_date
                )

                if all_tasks:
                    # Create individual task notes in /Tasks folder
                    for task in all_tasks:
                        task_file_path = self.task_extractor.create_task_note(task, self.file_manager)
                        if task_file_path:
                            # Extract just the filename for linking
                            task_filename = Path(task_file_path).stem
                            task_link = f"[[Tasks/{task_filename}|{task['task']}]]"
                            task_links.append(task_link)
                    
                    self.logger.info("📊 Skipping meeting-specific dashboard - using unified Dataview dashboard")
                    
                    # Update the obsidian content to include task links
                    if task_links:
                        obsidian_content = self._update_meeting_note_with_task_links(
                            obsidian_content, 
                            task_links
                        )
            
            # Smart dashboard update
            meeting_data = {
                'filename': obsidian_filename,
                'date': meeting_date,
                'has_transcript': True
            }
            
            self.update_dashboard_intelligently(meeting_data, all_tasks, analysis.get('entities'))
            
            # Save to Obsidian vault
            self.logger.info(f"🚀 Attempting to save to vault: {obsidian_filename}")
            
            success = self.file_manager.save_to_obsidian_vault(obsidian_filename, obsidian_content)
            
            if success:
                self.logger.info(f"✅ Saved to vault: {obsidian_filename}")
                
                if entity_links and any(entity_links.values()):
                    vault_path = Path(self.file_manager.obsidian_vault_path) / self.file_manager.obsidian_folder_path / obsidian_filename
                    self.logger.info(f"🔗 Updating entity links at: {vault_path}")
                    self.entity_manager.update_meeting_note_with_entities(vault_path, entity_links)
            else:
                self.logger.error(f"❌ Failed to save to vault: {obsidian_filename}")
        
        # Save JSON and markdown formats
        analysis_path = self.file_manager.output_dir / f"{enhanced_filename}_analysis.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Analysis saved: {analysis_path.name}")
    
    def _update_meeting_note_with_task_links(self, obsidian_content: str, task_links: List[str]) -> str:
        """Update the meeting note to include links to created task files"""
        try:
            lines = obsidian_content.split('\n')
            updated_lines = []
            in_action_items_section = False
            
            for line in lines:
                # Look for the Action Items section
                if line.strip() == "## Action Items":
                    updated_lines.append(line)
                    updated_lines.append("<!-- Links to task records -->")
                    
                    # Add all task links
                    for task_link in task_links:
                        updated_lines.append(f"- [ ] {task_link}")
                    
                    in_action_items_section = True
                    continue
                
                # Skip the placeholder comment and move to next section
                elif in_action_items_section and line.strip().startswith("<!--"):
                    continue
                
                # When we hit the next section, we're done with action items
                elif in_action_items_section and line.startswith("##"):
                    in_action_items_section = False
                    updated_lines.append("")  # Add spacing
                    updated_lines.append(line)
                
                # Skip any existing action item lines in this section
                elif in_action_items_section and (line.strip().startswith("- [ ]") or line.strip().startswith("- [x]")):
                    continue
                    
                else:
                    updated_lines.append(line)
            
            self.logger.info(f"✅ Updated meeting note with {len(task_links)} task links")
            return '\n'.join(updated_lines)
            
        except Exception as e:
            self.logger.error(f"Error updating meeting note with task links: {e}")
            return obsidian_content  # Return original content if update fails
    
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

    def update_dashboard_intelligently(self, meeting_data: Dict, all_tasks: Optional[List] = None, entities: Optional[Dict] = None):
        """Smart dashboard updating strategy with configurable thresholds"""
        
        # Always update for high-impact meetings
        if self._is_high_impact_meeting(meeting_data, all_tasks, entities):
            self.logger.info("🔥 High-impact meeting detected - updating dashboard")
            self.dashboard_orchestrator.create_primary_dashboard()
            return
        
        # Time-based updates
        last_update = self._get_last_dashboard_update()
        hours_since = (datetime.now() - last_update).total_seconds() / 3600
        
        # Use configurable threshold
        update_threshold = self.settings.dashboard_update_thresholds.get('hours_between_updates', 6)
        if hours_since >= update_threshold:
            self.logger.info(f"⏰ {hours_since:.1f} hours since last update - refreshing dashboard")
            self.dashboard_orchestrator.create_primary_dashboard()
            return
        
        # Morning refresh (if not updated since yesterday)
        morning_hour = self.settings.dashboard_update_thresholds.get('morning_refresh_hour', 9)
        if datetime.now().hour == morning_hour and hours_since >= 12:
            self.logger.info("🌅 Morning dashboard refresh")
            self.dashboard_orchestrator.create_primary_dashboard()
            return
        
        # Weekly summary on Monday mornings
        if datetime.now().weekday() == 0 and datetime.now().hour == morning_hour and hours_since >= 48:
            self.logger.info("📊 Weekly Monday dashboard refresh")
            self.dashboard_orchestrator.create_primary_dashboard()
            return
            
        # Just log that meeting was processed
        self.logger.info(f"📊 Dashboard up-to-date ({hours_since:.1f}h ago), skipping refresh")
    
    def _is_high_impact_meeting(self, meeting_data: Dict, all_tasks: Optional[List] = None, entities: Optional[Dict] = None) -> bool:
        """Determine if meeting warrants immediate dashboard update"""
        try:
            # Use configurable thresholds
            thresholds = self.settings.dashboard_update_thresholds
            
            # High priority tasks created
            if all_tasks:
                high_priority_tasks = [t for t in all_tasks if t.get('priority', '').lower() in ['high', 'critical']]
                urgent_tasks = [t for t in all_tasks if self._is_urgent_task_data(t)]
                critical_tasks = [t for t in all_tasks if t.get('priority', '').lower() == 'critical']
                
                if len(critical_tasks) >= thresholds.get('critical_tasks', 1):
                    self.logger.info(f"🚨 High-impact: {len(critical_tasks)} critical tasks created")
                    return True
                
                if len(high_priority_tasks) >= thresholds.get('high_priority_tasks', 2):
                    self.logger.info(f"🔥 High-impact: {len(high_priority_tasks)} high-priority tasks created")
                    return True
                
                if len(urgent_tasks) >= thresholds.get('urgent_tasks', 1):
                    self.logger.info(f"🚨 High-impact: {len(urgent_tasks)} urgent tasks created")
                    return True
                
                # Large number of total tasks
                if len(all_tasks) >= thresholds.get('total_tasks', 5):
                    self.logger.info(f"📋 High-impact: {len(all_tasks)} tasks created")
                    return True
            
            # Important new contacts (companies marked as clients)
            if entities:
                new_companies = entities.get('companies', [])
                if len(new_companies) >= thresholds.get('new_companies', 2):
                    self.logger.info(f"🏢 High-impact: {len(new_companies)} new companies detected")
                    return True
                
                new_people = entities.get('people', [])
                if len(new_people) >= thresholds.get('new_people', 3):
                    self.logger.info(f"👥 High-impact: {len(new_people)} new people detected")
                    return True
            
            # Meeting topic keywords that indicate importance
            meeting_filename = meeting_data.get('filename', '').lower()
            high_impact_keywords = thresholds.get('high_impact_keywords', [
                'client', 'sales', 'contract', 'deal', 'strategy', 'executive', 
                'board', 'crisis', 'urgent', 'critical', 'launch', 'review',
                'kickoff', 'milestone', 'deadline', 'emergency'
            ])
            
            for keyword in high_impact_keywords:
                if keyword in meeting_filename:
                    self.logger.info(f"🎯 High-impact: Meeting contains keyword '{keyword}'")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error evaluating meeting impact: {e}")
            return False  # Default to not high-impact if error
    
    def _is_urgent_task_data(self, task_data: dict) -> bool:
        """Check if task data indicates urgency"""
        try:
            # Check deadline urgency
            deadline = task_data.get('deadline', '')
            if deadline and deadline != 'not specified':
                try:
                    from datetime import datetime
                    deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                    days_until = (deadline_date - datetime.now()).days
                    
                    # Use configurable urgency threshold
                    urgency_days = self.settings.dashboard_update_thresholds.get('urgent_task_days', 3)
                    if days_until <= urgency_days:
                        return True
                except:
                    pass
            
            # Check for urgent keywords in task description
            task_desc = task_data.get('task', '').lower()
            urgent_keywords = ['urgent', 'asap', 'immediately', 'critical', 'emergency', 'today', 'now']
            
            for keyword in urgent_keywords:
                if keyword in task_desc:
                    return True
            
            # Check if priority is critical
            if task_data.get('priority', '').lower() == 'critical':
                return True
            
            return False
            
        except Exception:
            return False
    
    def _get_last_dashboard_update(self) -> datetime:
        """Get the timestamp of the last dashboard update"""
        try:
            dashboard_path = Path(self.file_manager.obsidian_vault_path) / "Meta" / "dashboards" / "🧠-Command-Center.md"
            
            if dashboard_path.exists():
                return datetime.fromtimestamp(dashboard_path.stat().st_mtime)
            else:
                # No dashboard exists, return very old date to force update
                return datetime(2020, 1, 1)
                
        except Exception as e:
            self.logger.warning(f"Error getting last dashboard update time: {e}")
            return datetime(2020, 1, 1)  # Force update on error


def main():
    """Application entry point"""
    try:
        logger = Logger.setup()
        logger.info("🚀 Starting Meeting Processor...")
        
        # Initialize processor (validation happens inside)
        try:
            processor = MeetingProcessor()
        except SystemExit:
            # Configuration error already logged
            return
        
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