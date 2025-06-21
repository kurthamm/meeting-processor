#!/usr/bin/env python3
"""
Meeting Processor - Main Entry Point
Clean, modular architecture with focused responsibilities
"""

import sys
import time
import json
import queue
import threading
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from watchdog.observers import Observer

from config.settings import Settings, ConfigurationError
from core.audio_processor import AudioProcessor
from core.transcription import TranscriptionService
from core.claude_analyzer import ClaudeAnalyzer
from core.file_manager import FileManager
from core.task_extractor import TaskExtractor
from core.dashboard_orchestrator import DashboardOrchestrator
from entities.detector import EntityDetector
from entities.manager import ObsidianEntityManager
from obsidian.formatter import ObsidianFormatter
from monitoring.file_watcher import MeetingFileHandler
from utils.logger import Logger


class MeetingProcessor:
    """Main orchestrator that coordinates all components"""

    def __init__(self):
        self.logger = Logger.setup()

        # Load and validate settings
        self.settings = Settings()

        # Initialize file management - directories are created in FileManager.__init__
        self.file_manager = FileManager(self.settings)

        # Core components
        self.audio_processor = AudioProcessor(self.file_manager.output_dir)
        self.transcription_service = TranscriptionService(
            self.settings.openai_client,
            self.audio_processor
        )
        self.claude_analyzer = ClaudeAnalyzer(self.settings.anthropic_client)

        # Entity & formatting
        self.entity_detector = EntityDetector(self.settings.anthropic_client)
        self.entity_manager = ObsidianEntityManager(
            self.file_manager,
            self.settings.anthropic_client
        )
        self.obsidian_formatter = ObsidianFormatter(self.claude_analyzer)
        self.task_extractor = TaskExtractor(self.settings.anthropic_client)
        self.dashboard_orchestrator = DashboardOrchestrator(
            self.file_manager,
            self.settings.anthropic_client
        )

        # File-processing queue & workers
        self.processing_queue = queue.Queue()
        self.shutdown_event = threading.Event()
        self.processed_files = set()   # store by filename
        self.processing_files = set()
        self.file_lock = threading.Lock()

        self.logger.info("Meeting Processor initialized successfully")
        self.logger.info(f"Input dir:  {self.file_manager.input_dir}")
        self.logger.info(f"Output dir: {self.file_manager.output_dir}")
        self.logger.info(f"Vault path: {self.file_manager.obsidian_vault_path}")

    def start_processing_workers(self, num_workers: int = 2):
        """Kick off background threads to handle files"""
        for i in range(num_workers):
            t = threading.Thread(
                target=self._processing_worker,
                name=f"Worker-{i}",
                daemon=True
            )
            t.start()
            self.logger.info(f"Started {t.name}")

    def _processing_worker(self):
        while not self.shutdown_event.is_set():
            try:
                mp4_path = self.processing_queue.get(timeout=1)
                if mp4_path is None:
                    break  # shutdown signal
                try:
                    self._process_meeting_file(mp4_path)
                finally:
                    self.processing_queue.task_done()
            except queue.Empty:
                continue

    def queue_file_for_processing(self, file_path: Path) -> bool:
        """Add a new MP4 to the work queue if it hasn't been seen"""
        name = file_path.name
        with self.file_lock:
            if (name in self.processed_files or
                name in self.processing_files or
                self.file_manager.is_file_processed(name)):
                return False
            self.processing_files.add(name)

        self.processing_queue.put(file_path)
        self.logger.info(f"Queued: {name}")
        return True

    def _process_meeting_file(self, mp4_path: Path):
        name = mp4_path.name
        try:
            self.logger.info(f"→ Processing {name}")
            if not self.settings.openai_client and not self.settings.testing_mode:
                self._create_api_key_reminder(mp4_path)
                return

            flac = self.audio_processor.convert_mp4_to_flac(mp4_path)
            if not flac:
                self.logger.error(f"Conversion failed: {name}")
                return

            analysis = self._run_transcription_and_analysis(flac)
            if not analysis:
                self.logger.error(f"Analysis failed: {flac.name}")
                return

            self._save_analysis(analysis, name)
            self.file_manager.move_processed_file(mp4_path)

            with self.file_lock:
                self.processed_files.add(name)
                self.processing_files.discard(name)
            self.file_manager.mark_file_processed(name)

            self.logger.info(f"✔️ Completed: {name}")

        except Exception:
            self.logger.exception(f"Pipeline error for {name}")
            with self.file_lock:
                self.processing_files.discard(name)

    def _create_api_key_reminder(self, mp4_path: Path):
        """Write a note reminding the user to set their API keys"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"API-KEY-REQUIRED_{mp4_path.stem}_{ts}.md"
        content = f"""# API Key Required — {mp4_path.name}

Please configure your API keys in `.env` before retrying:

- **OPENAI_API_KEY** (for transcription)
- **ANTHROPIC_API_KEY** (for analysis)

Restart the processor after updating.
"""
        path = self.file_manager.output_dir / filename
        path.write_text(content, encoding="utf-8")
        self.logger.info(f"Reminder written: {filename}")

    def _run_transcription_and_analysis(self, flac_path: Path) -> Optional[Dict]:
        """Core: Whisper → Claude → Entities"""
        try:
            transcript = self.transcription_service.transcribe_audio(flac_path)
            if not transcript:
                return None

            result = {
                "timestamp": datetime.now().isoformat(),
                "source_file": flac_path.name,
                "transcript": transcript
            }

            # Full analysis if Anthropic is configured
            if self.settings.anthropic_client:
                analysis_text = self.claude_analyzer.analyze_transcript(
                    transcript, flac_path.name
                ) or self._basic_analysis(transcript)
                result["analysis"] = analysis_text
                result["entities"] = self.entity_detector.detect_all_entities(
                    transcript, flac_path.name
                )
            else:
                result["analysis"] = self._basic_analysis(transcript)
                result["entities"] = {"people": [], "companies": [], "technologies": []}

            return result

        except Exception:
            self.logger.exception("Transcription/analysis error")
            return None

    def _basic_analysis(self, transcript: str) -> str:
        """Fallback summary when Claude is unavailable"""
        wc = len(transcript.split())
        cc = len(transcript)
        return (
            f"# Basic Analysis\n\n"
            f"- Words: {wc}\n"
            f"- Characters: {cc}\n"
            f"- Estimated length: {wc//130} min\n"
        )

    def _save_analysis(self, analysis: Dict, original_name: str):
        """Persist JSON, Markdown, entity notes, tasks, and dashboards"""
        date = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H-%M")
        topic = self.claude_analyzer.extract_meeting_topic(
            analysis["transcript"]
        ) if self.settings.anthropic_client else "Meeting"

        base = f"{topic}_{date}_{time_str}"
        md_name = f"{base}_meeting.md"
        json_name = f"{base}_analysis.json"

        # 1) JSON
        (self.file_manager.output_dir / json_name).write_text(
            json.dumps(analysis, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        self.logger.info(f"Saved JSON: {json_name}")

        # 2) Markdown note
        md_content = self.obsidian_formatter.create_obsidian_note(
            analysis["analysis"],
            analysis["transcript"],
            original_name,
            topic
        )
        (self.file_manager.output_dir / md_name).write_text(
            md_content, encoding="utf-8"
        )

        # 3) Entity notes - only create if entities were detected
        links = {}
        if analysis.get("entities") and self.settings.anthropic_client:
            # Only create entity notes if we have entities
            entity_count = sum(len(v) for v in analysis["entities"].values())
            if entity_count > 0:
                links = self.entity_manager.create_entity_notes(
                    analysis["entities"], base, date
                )
            else:
                self.logger.debug("No entities detected - skipping entity note creation")

        # 4) Task notes
        tasks = []
        if self.settings.anthropic_client:
            tasks = self.task_extractor.extract_all_tasks(
                analysis["transcript"], base, date
            )
            for task in tasks:
                self.task_extractor.create_task_note(task, self.file_manager)

        # 5) Inject task links
        if tasks:
            md_content = self._inject_task_links(md_content, tasks)
            (self.file_manager.obsidian_vault_path
             / self.file_manager.obsidian_folder_path
             / md_name).write_text(md_content, encoding="utf-8")

        # 6) Save to vault & update entities
        saved = self.file_manager.save_to_obsidian_vault(md_name, md_content)
        if saved and links:
            vault_path = (Path(self.file_manager.obsidian_vault_path)
                          / self.file_manager.obsidian_folder_path
                          / md_name)
            self.entity_manager.update_meeting_note_with_entities(vault_path, links)

        # 7) Dashboard updates
        self._maybe_update_dashboard(base, date, tasks, analysis.get("entities", {}))

    def _inject_task_links(self, content: str, tasks: List[Dict]) -> str:
        """Add a bullet list of task links under the Action Items header"""
        pattern = r'(#{2,}\s*Action\s*Items?\s*\n)'
        match = re.search(pattern, content, re.IGNORECASE)
        if not match:
            self.logger.warning("Action Items header not found")
            return content

        insert = match.end()
        # Fixed: Using 'task_id' to match task_extractor.py
        section = "\n".join(f"- [ ] [[Tasks/{t['task_id']}|{t['task']}]]" for t in tasks)
        return content[:insert] + section + "\n\n" + content[insert:]

    def _maybe_update_dashboard(
        self, base: str, date: str, tasks: List[Dict], entities: Dict
    ):
        """Conditionally update dashboards based on meeting importance"""
        data = {"filename": base, "date": date, "has_transcript": True}
        self.dashboard_orchestrator.maybe_refresh(data, tasks, entities)

    def process_existing_files(self):
        """Queue any MP4s already in the input folder"""
        found = list(self.file_manager.input_dir.glob("*.mp4"))
        self.logger.info(f"Found {len(found)} existing MP4(s)")
        for f in found:
            self.queue_file_for_processing(f)

    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down...")
        self.shutdown_event.set()
        # Signal workers to stop
        for _ in range(self.processing_queue.maxsize or 2):
            self.processing_queue.put(None)
        self.processing_queue.join()
        self.logger.info("Shutdown complete")


def main() -> int:
    logger = Logger.setup()
    try:
        logger.info("Starting Meeting Processor")
        proc = MeetingProcessor()
        proc.start_processing_workers()
        proc.process_existing_files()

        handler = MeetingFileHandler(proc)
        obs = Observer()
        obs.schedule(handler, str(proc.file_manager.input_dir), recursive=False)
        obs.start()
        logger.info("Watching for new files… (Ctrl+C to exit)")

        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Interrupt received, exiting…")
    except ConfigurationError as e:
        logger.error(f"Config error: {e}")
        return 1
    except Exception:
        logger.exception("Fatal error")
        return 1
    finally:
        if 'obs' in locals():
            obs.stop()
            obs.join()
        if 'proc' in locals():
            proc.shutdown()
        logger.info("Processor stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())