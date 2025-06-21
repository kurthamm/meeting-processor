"""
Obsidian note formatting for Meeting Processor
Handles conversion of analysis to structured Obsidian notes
"""

import re
from datetime import datetime
from typing import TYPE_CHECKING
from utils.logger import LoggerMixin, log_success

if TYPE_CHECKING:
    from core.claude_analyzer import ClaudeAnalyzer


class ObsidianFormatter(LoggerMixin):
    """Handles Obsidian note formatting"""
    
    def __init__(self, claude_analyzer: 'ClaudeAnalyzer'):
        self.claude_analyzer = claude_analyzer
    
    def create_obsidian_note(self, analysis_text: str, transcript: str, 
                           filename: str, meeting_topic: str) -> str:
        """Convert analysis to Obsidian note format"""
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        meeting_date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
        
        clean_title = meeting_topic.replace('-', ' ')
        
        # Only identify speakers if Claude is available
        if self.claude_analyzer and self.claude_analyzer.anthropic_client:
            self.logger.info("🎭 Identifying speakers in transcript...")
            formatted_transcript = self.claude_analyzer.identify_speakers(transcript)
        else:
            self.logger.info("📝 Using raw transcript (no speaker identification without Anthropic)")
            formatted_transcript = transcript
        
        # Build structured note content
        note_content = self._build_note_structure(
            clean_title, meeting_date, analysis_text, formatted_transcript, meeting_topic
        )
        
        log_success(self.logger, f"Created Obsidian note for {meeting_topic}")
        return note_content
    
    def _build_note_structure(self, title: str, date: str, analysis: str, transcript: str, meeting_topic: str) -> str:
        """Build the structured Obsidian note with consistent formatting"""
        
        # Build dataview queries using f-strings to avoid quote conflicts
        dataview_tasks = f"""```dataview
TABLE WITHOUT ID
  file.link as Task,
  status as Status,
  priority as Priority,
  assigned_to as "Assigned To",
  due_date as "Due Date"
FROM "Tasks"
WHERE meeting_source = this.file.name OR contains(meeting_source, "{meeting_topic}")
SORT priority DESC, due_date ASC
```"""

        dataview_follow_ups = f"""```dataview
list
from "Meetings"
where contains(file.text, "{meeting_topic}") or contains(follow-up-required, this.file.link)
where file.name != this.file.name
sort date desc
```"""

        dataview_related_meetings = """```dataview
table without id
  file.link as "Meeting",
  date as "Date",
  meeting-type as "Type"
from "Meetings"
where (contains(project, this.project) or any(file.etags, (t) => contains(this.file.etags, t)))
where file.name != this.file.name
sort date desc
limit 5
```"""

        # Build the note with YAML frontmatter
        note_parts = [
            "---",
            f"type: meeting",
            f"date: {date}",
            f"meeting_topic: {meeting_topic}",
            f"project: ",
            f"meeting_type: ",
            f"duration: ",
            f"status: processed",
            f"attendees_internal: ",
            f"attendees_external: ",
            f"key_decision_makers: ",
            f"tags:",
            f"  - meeting",
            f"  - project/active",
            f"  - type/technical-review",
            f"  - auto-generated",
            f"audio_file: ",
            f"processed_date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"auto_generated: true",
            "---",
            "",
            f"# {title}",
            "",
            "## Meeting Information",
            f"**Type:** Meeting",
            f"**Date:** {date}",
            f"**Project:** ",
            f"**Meeting Type:** Technical Review / Sales Call / Planning / Standup / Demo / Crisis",
            f"**Duration:** ",
            f"**Status:** Processed",
            "",
            "## Attendees",
            "**Internal Team:** ",
            "**Client/External:** ",
            "**Key Decision Makers:** ",
            "",
            "## Meeting Context",
            "**Purpose:** ",
            "**Agenda Items:** ",
            "**Background:** ",
            "**Expected Outcomes:** ",
            "",
            "## Key Decisions Made",
            "<!-- Extracted automatically and manually added -->",
            "",
            "## Action Items",
            "<!-- Links to task records will be populated here -->",
            "",
            "### All Tasks from This Meeting",
            dataview_tasks,
            "",
            "## Technical Discussions",
            "**Architecture Decisions:** ",
            "**Technology Choices:** ",
            "**Integration Approaches:** ",
            "**Performance Considerations:** ",
            "",
            "## Issues Identified",
            "**Blockers:** ",
            "**Technical Challenges:** ",
            "**Business Risks:** ",
            "**Dependencies:** ",
            "",
            "## Opportunities Discovered",
            "**Upsell Potential:** ",
            "**Future Projects:** ",
            "**New Requirements:** ",
            "**Partnership Options:** ",
            "",
            "## Knowledge Captured",
            "**New Insights:** ",
            "**Best Practices:** ",
            "**Lessons Learned:** ",
            "**Process Improvements:** ",
            "",
            "## Follow-up Required",
            "**Next Meeting:** ",
            "**Documentation Needed:** ",
            "**Research Tasks:** ",
            "**Client Communication:** ",
            "",
            "### Follow-up Meetings",
            dataview_follow_ups,
            "",
            "## Entity Connections",
            "People Mentioned: ",
            "Companies Discussed: ",
            "Technologies Referenced: ",
            "Solutions Applied: ",
            "Related Projects: ",
            "",
            "## Related Meetings",
            dataview_related_meetings,
            "",
            "## Meeting Quality",
            "**Effectiveness:** High / Medium / Low",
            "**Decision Quality:** Good / Fair / Poor",
            "**Action Clarity:** Clear / Unclear",
            "**Follow-up Needed:** Yes / No",
            "",
            "## AI Analysis",
            "",
            analysis,
            "",
            "## Complete Transcript",
            "",
            transcript,
            "",
            "---",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
        ]
        
        return "\n".join(note_parts)
    
    def create_summary_note(self, analysis: str, meeting_topic: str) -> str:
        """Create a shorter summary note for quick reference"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M')
        
        note_parts = [
            "---",
            f"type: meeting-summary",
            f"date: {current_date}",
            f"meeting_topic: {meeting_topic}",
            f"tags:",
            f"  - meeting",
            f"  - summary",
            f"generated: {current_date} {current_time}",
            "---",
            "",
            f"# {meeting_topic} - Summary",
            "",
            f"**Date:** {current_date}",
            f"**Type:** Meeting Summary",
            "",
            "## Quick Summary",
            "",
            analysis,
            "",
            "---",
            f"*Generated: {current_date} {current_time}*"
        ]
        
        return "\n".join(note_parts)
    
    def extract_action_items(self, analysis: str) -> list:
        """Extract action items from analysis text"""
        action_items = []
        
        # Look for common action item patterns
        patterns = [
            r'action\s+items?[:\-](.+?)(?=\n\n|\n[A-Z]|$)',
            r'tasks?[:\-](.+?)(?=\n\n|\n[A-Z]|$)',
            r'to\s+do[:\-](.+?)(?=\n\n|\n[A-Z]|$)',
            r'follow\s+up[:\-](.+?)(?=\n\n|\n[A-Z]|$)',
            r'next\s+steps?[:\-](.+?)(?=\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, analysis, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                items_text = match.group(1).strip()
                # Split by line breaks and clean up
                items = [item.strip('- •*').strip() for item in items_text.split('\n') if item.strip()]
                action_items.extend(items)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in action_items:
            if item and item not in seen and len(item) > 5:  # Skip very short items
                unique_items.append(item)
                seen.add(item)
        
        return unique_items
    
    def extract_decisions(self, analysis: str) -> list:
        """Extract decisions from analysis text"""
        decisions = []
        
        # Look for decision patterns
        patterns = [
            r'decisions?[:\-](.+?)(?=\n\n|\n[A-Z]|$)',
            r'decided[:\-](.+?)(?=\n\n|\n[A-Z]|$)',
            r'agreed[:\-](.+?)(?=\n\n|\n[A-Z]|$)',
            r'concluded[:\-](.+?)(?=\n\n|\n[A-Z]|$)',
            r'determined[:\-](.+?)(?=\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, analysis, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                decisions_text = match.group(1).strip()
                items = [item.strip('- •*').strip() for item in decisions_text.split('\n') if item.strip()]
                decisions.extend(items)
        
        # Remove duplicates
        seen = set()
        unique_decisions = []
        for decision in decisions:
            if decision and decision not in seen and len(decision) > 5:
                unique_decisions.append(decision)
                seen.add(decision)
        
        return unique_decisions
    
    def format_for_export(self, content: str, format_type: str = 'markdown') -> str:
        """Format content for different export types"""
        if format_type == 'markdown':
            return content
        elif format_type == 'plain_text':
            # Remove markdown formatting
            plain = re.sub(r'#+\s*', '', content)  # Remove headers
            plain = re.sub(r'\*\*(.*?)\*\*', r'\1', plain)  # Remove bold
            plain = re.sub(r'\*(.*?)\*', r'\1', plain)  # Remove italic
            plain = re.sub(r'\[\[(.*?)\]\]', r'\1', plain)  # Remove links
            plain = re.sub(r'```[\s\S]*?```', '', plain)  # Remove code blocks
            plain = re.sub(r'---[\s\S]*?---', '', plain)  # Remove frontmatter
            return plain.strip()
        else:
            return content
    
    def validate_note_structure(self, content: str) -> bool:
        """Validate that the note has proper structure"""
        required_sections = [
            "## Meeting Information",
            "## Action Items",
            "## Entity Connections",
            "## Complete Transcript"
        ]
        
        for section in required_sections:
            if section not in content:
                self.logger.warning(f"Missing required section: {section}")
                return False
        
        return True