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
        
        self.logger.info("🎭 Identifying speakers in transcript...")
        formatted_transcript = self.claude_analyzer.identify_speakers(transcript)
        
        # Build structured note content
        note_content = self._build_note_structure(
            clean_title, meeting_date, analysis_text, formatted_transcript, meeting_topic
        )
        
        log_success(self.logger, f"Created Obsidian note for {meeting_topic}")
        return note_content
    
    def _build_note_structure(self, title: str, date: str, analysis: str, transcript: str, meeting_topic: str) -> str:
        """Build the structured Obsidian note - simplified version"""
        
        # Extract key information from analysis
        attendees = self._extract_attendees_from_analysis(analysis)
        decisions = self._extract_decisions_from_analysis(analysis)
        
        # Build dataview query for tasks
        dataview_tasks = '''```dataview
TABLE WITHOUT ID
  file.link as Task,
  status as Status,
  priority as Priority,
  assigned_to as "Assigned To",
  due_date as "Due Date"
FROM "Tasks"
WHERE meeting_source = this.file.name OR contains(meeting_source, "''' + meeting_topic + '''")
SORT 
  choice(priority = "critical", 1, priority = "high", 2, priority = "medium", 3, priority = "low", 4) ASC,
  due_date ASC
```'''

        dataview_related_meetings = '''```dataview
TABLE WITHOUT ID
  file.link as "Meeting",
  date as "Date",
  type as "Type"
FROM "Meetings"
WHERE project = this.project AND file.name != this.file.name
SORT date DESC
LIMIT 5
```'''

        note_parts = [
            f"# {title}",
            "",
            f"Date: {date}",
            "Type: Meeting",
            "Duration: ",
            "Project: ",
            "",
            "## Attendees",
            attendees if attendees else "To be added",
            "",
            "## Action Items",
            "<!-- Task links will be automatically populated here -->",
            "",
            "### All Tasks from This Meeting",
            dataview_tasks,
            "",
            "## Key Decisions",
            decisions if decisions else "<!-- Key decisions from this meeting -->",
            "",
            "## Summary",
            "",
            analysis,
            "",
            "## Next Steps",
            "<!-- Follow-up actions and next meeting plans -->",
            "",
            "## Entity Connections",
            "**People:** ",
            "**Companies:** ",
            "**Technologies:** ",
            "",
            "## Related Meetings",
            dataview_related_meetings,
            "",
            "## Complete Transcript",
            "",
            formatted_transcript,
            "",
            "---",
            f"**Tags:** #meeting #type/meeting",
            f"**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "**Auto-generated:** Yes"
        ]
        
        return "\n".join(note_parts)
    
    def _extract_attendees_from_analysis(self, analysis: str) -> str:
        """Extract attendees from AI analysis"""
        # Look for participants section
        participants_match = re.search(r'(?:Participants?|Attendees?)(?:\s*:)?\s*\n(.*?)(?=\n\n|\n##|$)', 
                                     analysis, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if participants_match:
            attendees = participants_match.group(1).strip()
            # Clean up the formatting
            attendees = re.sub(r'^[-\*]\s*', '', attendees, flags=re.MULTILINE)
            return attendees
        return ""
    
    def _extract_decisions_from_analysis(self, analysis: str) -> str:
        """Extract key decisions from AI analysis"""
        # Look for decisions section
        decisions_match = re.search(r'(?:Major Decisions?|Key Decisions?)(?:\s*:)?\s*\n(.*?)(?=\n\n|\n##|$)', 
                                  analysis, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if decisions_match:
            decisions = decisions_match.group(1).strip()
            # Format as bullet points
            lines = decisions.split('\n')
            formatted_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith(('- ', '* ', '• ')):
                    # Check if line starts with number
                    if re.match(r'^\d+\.?\s', line):
                        line = re.sub(r'^\d+\.?\s*', '- ', line)
                    else:
                        line = f"- {line}"
                formatted_lines.append(line)
            return '\n'.join(formatted_lines)
        return ""
    
    def create_summary_note(self, analysis: str, meeting_topic: str) -> str:
        """Create a shorter summary note for quick reference"""
        note_parts = [
            f"# {meeting_topic} - Summary",
            "",
            f"Date: {datetime.now().strftime('%Y-%m-%d')}",
            "Type: Meeting Summary",
            "",
            "## Quick Summary",
            "",
            analysis,
            "",
            "---",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "Tags: #meeting #summary"
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
            r'follow\s+up[:\-](.+?)(?=\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, analysis, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                items_text = match.group(1).strip()
                # Split by line breaks and clean up
                items = [item.strip('- ').strip() for item in items_text.split('\n') if item.strip()]
                action_items.extend(items)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in action_items:
            if item and item not in seen:
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
            r'agreed[:\-](.+?)(?=\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, analysis, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                decisions_text = match.group(1).strip()
                items = [item.strip('- ').strip() for item in decisions_text.split('\n') if item.strip()]
                decisions.extend(items)
        
        # Remove duplicates
        seen = set()
        unique_decisions = []
        for decision in decisions:
            if decision and decision not in seen:
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
            return plain
        else:
            return content