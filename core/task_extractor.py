"""
Comprehensive Task Extraction for Meeting Processor
Extracts ALL tasks from meetings for complete project visibility
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from utils.logger import LoggerMixin, log_success, log_error


class TaskExtractor(LoggerMixin):
    """Extracts all tasks from meeting transcripts for complete project visibility"""
    
    def __init__(self, anthropic_client):
        self.anthropic_client = anthropic_client
        self.model = "claude-3-5-sonnet-20241022"
        
        # Agile/Scrum standards
        self.TASK_STATUSES = ['new', 'ready', 'in_progress', 'in_review', 'done', 'blocked', 'cancelled']
        self.TASK_PRIORITIES = ['critical', 'high', 'medium', 'low']
        self.TASK_CATEGORIES = ['technical', 'business', 'process', 'documentation', 'research']
    
    def extract_all_tasks(self, transcript: str, meeting_filename: str, 
                         meeting_date: str) -> List[Dict[str, str]]:
        """Extract ALL tasks and action items from the meeting"""
        try:
            self.logger.info(f"📋 Extracting all tasks from {meeting_filename}")
            
            prompt = self._build_comprehensive_extraction_prompt(transcript)
            
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            tasks = self._parse_task_response(response.content[0].text.strip())
            
            # Enrich tasks with metadata and consistent linking
            enriched_tasks = []
            for i, task in enumerate(tasks, 1):
                enriched_task = {
                    **task,
                    'meeting_source': f"[[Meetings/{meeting_filename}]]",  # Always use wiki link format
                    'meeting_filename': meeting_filename,  # Keep raw filename for reference
                    'meeting_date': meeting_date,
                    'extracted_date': datetime.now().strftime("%Y-%m-%d"),
                    'status': 'new',  # All tasks start as 'new' in Agile workflow
                    'task_id': self._generate_task_id(task, meeting_filename, i),
                    'task_number': i
                }
                enriched_tasks.append(enriched_task)
            
            self.logger.info(f"✅ Extracted {len(enriched_tasks)} total tasks")
            
            # Log task assignments for visibility
            assigned_tasks = [t for t in enriched_tasks if t['assigned_to'] and t['assigned_to'] != 'unassigned']
            unassigned_tasks = [t for t in enriched_tasks if not t['assigned_to'] or t['assigned_to'] == 'unassigned']
            
            self.logger.info(f"   📌 {len(assigned_tasks)} assigned, {len(unassigned_tasks)} unassigned")
            
            return enriched_tasks
            
        except Exception as e:
            log_error(self.logger, f"Error extracting tasks from {meeting_filename}", e)
            return []
    
    def _build_comprehensive_extraction_prompt(self, transcript: str) -> str:
        """Build comprehensive task extraction prompt"""
        return f"""Analyze this meeting transcript and extract ALL action items, tasks, and follow-ups mentioned.

EXTRACT EVERYTHING:
- Explicit tasks assigned to specific people
- Action items mentioned without clear ownership
- Follow-up activities discussed
- Deliverables and deadlines mentioned
- Research or investigation tasks
- Meeting scheduling and coordination tasks
- Documentation or communication tasks

For each task, extract:
1. **Task Description**: What needs to be done?
2. **Assigned To**: Who is responsible? (use exact name from transcript, or "unassigned")
3. **Deadline**: When is this due? (if mentioned)
4. **Priority**: How urgent is this? (critical/high/medium/low)
5. **Context**: Why is this needed?
6. **Deliverable**: What is the expected output?
7. **Dependencies**: What needs to happen first?
8. **Category**: Type of task (technical/business/process/documentation/research)

Transcript:
{transcript}

Return a JSON array of ALL tasks found:
[
  {{
    "task": "Specific action or deliverable",
    "assigned_to": "Person's name or 'unassigned'",
    "deadline": "YYYY-MM-DD or 'not specified'",
    "priority": "critical/high/medium/low",
    "context": "Background and reason for task",
    "deliverable": "Expected output or result",
    "dependencies": "Prerequisites or blockers",
    "category": "technical/business/process/documentation/research",
    "quote": "Exact quote from transcript mentioning this task"
  }}
]

Be comprehensive - capture everything that represents work to be done, even if ownership is unclear."""
    
    def _parse_task_response(self, response_text: str) -> List[Dict[str, str]]:
        """Parse Claude's comprehensive task extraction response"""
        try:
            self.logger.debug(f"📥 Raw task response length: {len(response_text)} chars")
            
            # Extract JSON array from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                tasks = json.loads(json_str)
                
                # Validate and normalize task structure
                validated_tasks = []
                for task in tasks:
                    if isinstance(task, dict) and 'task' in task:
                        # Normalize assigned_to field
                        assigned_to = task.get('assigned_to', 'unassigned').strip()
                        if assigned_to.lower() in ['', 'none', 'unknown', 'unclear']:
                            assigned_to = 'unassigned'
                        
                        # Normalize priority to our standards
                        priority = task.get('priority', 'medium').strip().lower()
                        if priority not in self.TASK_PRIORITIES:
                            if priority in ['not specified', 'normal']:
                                priority = 'medium'
                            elif priority in ['urgent', 'very high']:
                                priority = 'critical'
                            else:
                                priority = 'medium'
                        
                        # Normalize category
                        category = task.get('category', 'process').strip().lower()
                        if category not in self.TASK_CATEGORIES:
                            if category in ['general', 'administrative', 'admin']:
                                category = 'process'
                            elif category in ['communication', 'meeting']:
                                category = 'process'
                            else:
                                category = 'process'
                        
                        validated_task = {
                            'task': task.get('task', '').strip(),
                            'assigned_to': assigned_to,
                            'deadline': task.get('deadline', 'not specified').strip(),
                            'priority': priority,
                            'context': task.get('context', '').strip(),
                            'deliverable': task.get('deliverable', '').strip(),
                            'dependencies': task.get('dependencies', '').strip(),
                            'category': category,
                            'quote': task.get('quote', '').strip()
                        }
                        
                        # Only add non-empty tasks
                        if validated_task['task']:
                            validated_tasks.append(validated_task)
                
                return validated_tasks
            else:
                self.logger.info("No JSON array found in response - no tasks detected")
                return []
            
        except (json.JSONDecodeError, ValueError) as e:
            log_error(self.logger, f"Failed to parse task response: {e}")
            self.logger.debug(f"Raw response was: {response_text[:500]}...")
            return []
    
    def _generate_task_id(self, task: Dict[str, str], meeting_filename: str, task_number: int) -> str:
        """Generate a unique task ID"""
        task_snippet = task['task'][:20].replace(' ', '-').lower()
        task_snippet = re.sub(r'[^a-z0-9\-]', '', task_snippet)
        meeting_snippet = meeting_filename[:15]
        date_snippet = datetime.now().strftime('%m%d')
        
        return f"TASK-{task_snippet}-{date_snippet}-{task_number:02d}"
    
    def create_task_note(self, task: Dict[str, str], file_manager) -> Optional[str]:
        """Create an individual Obsidian task note with YAML frontmatter"""
        try:
            # Create filename from task
            safe_task = re.sub(r'[^\w\s-]', '', task['task'][:40])
            safe_task = re.sub(r'\s+', '-', safe_task.strip())
            
            # Add assignment indicator to filename
            assignee_prefix = ""
            if task['assigned_to'] != 'unassigned':
                safe_assignee = re.sub(r'[^\w]', '', task['assigned_to'][:10])
                assignee_prefix = f"{safe_assignee}-"
            
            filename = f"TASK-{assignee_prefix}{safe_task}-{task['task_id'][-8:]}.md"
            
            # Save to Obsidian vault Tasks folder
            tasks_path = Path(file_manager.obsidian_vault_path) / "Tasks"
            tasks_path.mkdir(parents=True, exist_ok=True)
            
            # Also save backup to output
            output_path = file_manager.output_dir
            
            # Parse deadline for task format
            deadline_text = ""
            deadline_yaml = ""
            if task['deadline'] != 'not specified':
                try:
                    deadline_date = datetime.strptime(task['deadline'], "%Y-%m-%d")
                    deadline_yaml = deadline_date.strftime('%Y-%m-%d')
                    deadline_text = f"📅 {deadline_yaml}"
                    
                    # Add urgency indicator
                    days_until = (deadline_date - datetime.now()).days
                    if days_until < 0:
                        deadline_text += " ⚠️ OVERDUE"
                    elif days_until <= 2:
                        deadline_text += " 🔥 URGENT"
                    elif days_until <= 7:
                        deadline_text += " ⚡ SOON"
                        
                except:
                    deadline_text = f"📅 {task['deadline']}"
                    deadline_yaml = ""
            
            # Determine priority and category emojis
            priority_emoji = {
                'critical': '🚨',
                'high': '🔥',
                'medium': '⚡',
                'low': '📌'
            }.get(task['priority'], '📋')
            
            category_emoji = {
                'technical': '💻',
                'business': '💼',
                'process': '📋',
                'documentation': '📝',
                'research': '🔍'
            }.get(task['category'], '📝')
            
            # Format assigned_to as wiki link if it's a person
            assigned_to_display = task['assigned_to'].title() if task['assigned_to'] != 'unassigned' else '🔓 Unassigned'
            assigned_to_link = f"[[People/{task['assigned_to'].replace(' ', '-')}|{task['assigned_to']}]]" if task['assigned_to'] != 'unassigned' else ''
            
            # Build YAML frontmatter
            yaml_frontmatter = f"""---
status: new
priority: {task['priority']}
category: {task['category']}
assigned_to: {assigned_to_link if assigned_to_link else ''}
due_date: {deadline_yaml}
meeting_source: {task['meeting_source']}
meeting_date: {task['meeting_date']}
task_id: {task['task_id']}
created: {task['extracted_date']}
tags:
  - task
  - status/new
  - priority/{task['priority']}
  - category/{task['category']}
---"""

            content = f"""{yaml_frontmatter}

# {priority_emoji} {category_emoji} {task['task']}

## Task Details
**Status:** 🆕 New  
**Priority:** {priority_emoji} {task['priority'].title()}  
**Category:** {category_emoji} {task['category'].title()}  
**Assigned To:** {assigned_to_link if assigned_to_link else assigned_to_display}  
**Due Date:** {deadline_text if deadline_text else '📅 Not specified'}  
**Source:** {task['meeting_source']}  
**Dashboard:** [[Meta/dashboards/Task-Dashboard|📊 All Tasks Dashboard]]

## Description
{task['task']}

## Context & Background
{task['context'] if task['context'] else 'No additional context provided.'}

## Expected Deliverable
{task['deliverable'] if task['deliverable'] else 'To be determined.'}

## Dependencies & Prerequisites
{task['dependencies'] if task['dependencies'] else 'None identified.'}

## Source Quote
> {task['quote'] if task['quote'] else 'No direct quote captured.'}

## Progress Tracking
- [ ] Task understood and scoped
- [ ] Dependencies identified and resolved
- [ ] Work in progress
- [ ] Ready for review
- [ ] Completed

## Work Log
### {task['extracted_date']} - Created
- Status: `new`
- Extracted from meeting transcript
- {f"Assigned to {assigned_to_link}" if assigned_to_link else "Awaiting assignment"}

<!-- Add updates here as work progresses -->

## Notes
<!-- Additional notes and context -->

## Related Tasks
<!-- Using inline Dataview to avoid rendering issues -->

**Tasks that depend on this:**
`$= dv.list(dv.pages('"Tasks"').where(p => p.dependencies && p.dependencies.includes(dv.current().file.name)).map(p => p.file.link))`

**Tasks linked from this note:**
`$= dv.list(dv.pages('"Tasks"').where(p => p.file.outlinks && Array.from(p.file.outlinks).some(link => link.path === dv.current().file.path)).map(p => p.file.link))`

---
**Created:** {task['extracted_date']}  
**Task ID:** `{task['task_id']}`
"""
            
            # Save task note to Obsidian vault Tasks folder
            task_vault_path = tasks_path / filename
            with open(task_vault_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Save backup to output directory
            task_output_path = output_path / filename
            with open(task_output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.debug(f"📝 Created task note: Tasks/{filename}")
            return str(task_vault_path)
            
        except Exception as e:
            log_error(self.logger, f"Error creating task note", e)
            return None
    
    def create_comprehensive_dashboard(self, tasks: List[Dict[str, str]], 
                                     meeting_filename: str, file_manager) -> Optional[str]:
        """DEPRECATED: Individual meeting dashboards are no longer created.
        Use the unified Dataview dashboard instead."""
        self.logger.info("📊 Skipping meeting-specific dashboard creation - use unified Task-Dashboard.md")
        return None
    
    def get_task_statistics(self, tasks: List[Dict[str, str]]) -> Dict[str, any]:
        """Get statistics about extracted tasks"""
        try:
            if not tasks:
                return {}
            
            stats = {
                'total_tasks': len(tasks),
                'assigned_tasks': len([t for t in tasks if t['assigned_to'] != 'unassigned']),
                'unassigned_tasks': len([t for t in tasks if t['assigned_to'] == 'unassigned']),
                'critical_priority': len([t for t in tasks if t['priority'] == 'critical']),
                'high_priority': len([t for t in tasks if t['priority'] == 'high']),
                'with_deadlines': len([t for t in tasks if t['deadline'] != 'not specified']),
                'assignees': list(set([t['assigned_to'] for t in tasks if t['assigned_to'] != 'unassigned'])),
                'categories': list(set([t['category'] for t in tasks]))
            }
            
            return stats
            
        except Exception as e:
            log_error(self.logger, "Error calculating task statistics", e)
            return {}