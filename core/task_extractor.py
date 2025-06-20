"""
Comprehensive Task Extraction for Meeting Processor
Extracts ALL tasks from meetings for complete project visibility
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from utils.logger import LoggerMixin, log_success, log_error
from pathlib import Path


class TaskExtractor(LoggerMixin):
    """Extracts all tasks from meeting transcripts for complete project visibility"""
    
    def __init__(self, anthropic_client):
        self.anthropic_client = anthropic_client
        self.model = "claude-3-5-sonnet-20241022"
    
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
            
            # Enrich tasks with metadata
            enriched_tasks = []
            for i, task in enumerate(tasks, 1):
                enriched_task = {
                    **task,
                    'meeting_source': meeting_filename,
                    'meeting_date': meeting_date,
                    'extracted_date': datetime.now().strftime("%Y-%m-%d"),
                    'status': 'unassigned' if not task.get('assigned_to') else 'assigned',
                    'task_id': self._generate_task_id(task, meeting_filename, i),
                    'task_number': i
                }
                enriched_tasks.append(enriched_task)
            
            self.logger.info(f"✅ Extracted {len(enriched_tasks)} total tasks")
            
            # Log task assignments for visibility
            assigned_tasks = [t for t in enriched_tasks if t['assigned_to']]
            unassigned_tasks = [t for t in enriched_tasks if not t['assigned_to']]
            
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
4. **Priority**: How urgent is this? (if indicated)
5. **Context**: Why is this needed?
6. **Deliverable**: What is the expected output?
7. **Dependencies**: What needs to happen first?
8. **Category**: Type of task (technical, business, administrative, research, etc.)

Transcript:
{transcript}

Return a JSON array of ALL tasks found:
[
  {{
    "task": "Specific action or deliverable",
    "assigned_to": "Person's name or 'unassigned'",
    "deadline": "YYYY-MM-DD or 'not specified'",
    "priority": "high/medium/low or 'not specified'",
    "context": "Background and reason for task",
    "deliverable": "Expected output or result",
    "dependencies": "Prerequisites or blockers",
    "category": "technical/business/administrative/research/communication",
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
                        
                        validated_task = {
                            'task': task.get('task', '').strip(),
                            'assigned_to': assigned_to,
                            'deadline': task.get('deadline', 'not specified').strip(),
                            'priority': task.get('priority', 'not specified').strip(),
                            'context': task.get('context', '').strip(),
                            'deliverable': task.get('deliverable', '').strip(),
                            'dependencies': task.get('dependencies', '').strip(),
                            'category': task.get('category', 'general').strip(),
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
        
        return f"{task_snippet}-{meeting_snippet}-{date_snippet}-{task_number:02d}"
    
    def create_task_note(self, task: Dict[str, str], file_manager) -> Optional[str]:
        """Create an individual Obsidian task note"""
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
            if task['deadline'] != 'not specified':
                try:
                    deadline_date = datetime.strptime(task['deadline'], "%Y-%m-%d")
                    deadline_text = f"📅 {deadline_date.strftime('%Y-%m-%d')}"
                    
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
            
            # Determine priority and category emojis
            priority_emoji = {
                'high': '🔥',
                'medium': '⚡',
                'low': '📌'
            }.get(task['priority'].lower(), '📋')
            
            category_emoji = {
                'technical': '💻',
                'business': '💼',
                'administrative': '📋',
                'research': '🔍',
                'communication': '💬',
                'meeting': '📅'
            }.get(task['category'].lower(), '📝')
            
            # Assignment status
            assignment_status = "🔒 ASSIGNED" if task['assigned_to'] != 'unassigned' else "🆓 AVAILABLE"
            
            content = f"""# {priority_emoji} {category_emoji} {task['task']}

## Task Details
- **Status:** {assignment_status}
- **Assigned To:** {task['assigned_to'].title()}
- **Priority:** {task['priority'].title()}
- **Category:** {task['category'].title()}
- **Deadline:** {deadline_text}
- **Source:** [[{task['meeting_source']}]]
- **Meeting Date:** {task['meeting_date']}

## Description
{task['task']}

## Context & Background
{task['context']}

## Expected Deliverable
{task['deliverable']}

## Dependencies & Prerequisites
{task['dependencies']}

## Source Quote
> {task['quote']}

## Progress Tracking
- [ ] Task understood and scoped
- [ ] Dependencies identified and resolved
- [ ] Work in progress
- [ ] Ready for review
- [ ] Completed

## Notes & Updates


## Related Tasks


---
**Task ID:** {task['task_id']}  
**Created:** {task['extracted_date']}  
**Tags:** #task #{task['category']} #meeting/{task['meeting_date']} #{"assigned" if task['assigned_to'] != 'unassigned' else "unassigned"}
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
        """Create a comprehensive task dashboard with all project visibility"""
        try:
            if not tasks:
                return None
            
            dashboard_filename = f"TASKS-DASHBOARD-{meeting_filename}.md"
            
            # Save to Obsidian vault Meta/dashboards folder
            dashboards_path = Path(file_manager.obsidian_vault_path) / "Meta" / "dashboards"
            dashboards_path.mkdir(parents=True, exist_ok=True)
            
            # Also save a copy to output for backup
            output_path = file_manager.output_dir
            
            # Categorize tasks
            assigned_tasks = [t for t in tasks if t['assigned_to'] != 'unassigned']
            unassigned_tasks = [t for t in tasks if t['assigned_to'] == 'unassigned']
            
            # Group by assignee
            assignee_groups = {}
            for task in assigned_tasks:
                assignee = task['assigned_to']
                if assignee not in assignee_groups:
                    assignee_groups[assignee] = []
                assignee_groups[assignee].append(task)
            
            # Group by category
            category_groups = {}
            for task in tasks:
                category = task['category']
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(task)
            
            content_parts = [
                f"# 📊 Task Dashboard: {meeting_filename}",
                "",
                f"**Meeting Date:** {tasks[0]['meeting_date']}",
                f"**Total Tasks:** {len(tasks)}",
                f"**Assigned:** {len(assigned_tasks)} | **Available:** {len(unassigned_tasks)}",
                f"**Source:** [[{meeting_filename}]]",
                "",
                "## 📋 Task Summary",
                ""
            ]
            
            # Quick stats
            high_priority = len([t for t in tasks if t['priority'].lower() == 'high'])
            with_deadlines = len([t for t in tasks if t['deadline'] != 'not specified'])
            
            content_parts.extend([
                f"- 🔥 **High Priority:** {high_priority} tasks",
                f"- 📅 **With Deadlines:** {with_deadlines} tasks",
                f"- 👥 **Team Members:** {len(assignee_groups)} people assigned work",
                ""
            ])
            
            # Tasks by assignee
            if assignee_groups:
                content_parts.extend([
                    "## 👥 Tasks by Person",
                    ""
                ])
                
                for assignee, person_tasks in sorted(assignee_groups.items()):
                    content_parts.append(f"### {assignee} ({len(person_tasks)} tasks)")
                    
                    for task in person_tasks:
                        priority_emoji = {'high': '🔥', 'medium': '⚡', 'low': '📌'}.get(task['priority'].lower(), '📋')
                        deadline = f" - Due: {task['deadline']}" if task['deadline'] != 'not specified' else ""
                        content_parts.append(f"- [ ] {priority_emoji} **{task['task']}**{deadline}")
                    
                    content_parts.append("")
            
            # Unassigned tasks (available for pickup)
            if unassigned_tasks:
                content_parts.extend([
                    "## 🆓 Available Tasks (Unassigned)",
                    ""
                ])
                
                for task in unassigned_tasks:
                    priority_emoji = {'high': '🔥', 'medium': '⚡', 'low': '📌'}.get(task['priority'].lower(), '📋')
                    category_emoji = {'technical': '💻', 'business': '💼', 'administrative': '📋', 'research': '🔍'}.get(task['category'].lower(), '📝')
                    deadline = f" - Due: {task['deadline']}" if task['deadline'] != 'not specified' else ""
                    content_parts.append(f"- [ ] {priority_emoji} {category_emoji} **{task['task']}**{deadline}")
                
                content_parts.append("")
            
            # Tasks by category
            content_parts.extend([
                "## 📂 Tasks by Category",
                ""
            ])
            
            for category, cat_tasks in sorted(category_groups.items()):
                category_emoji = {'technical': '💻', 'business': '💼', 'administrative': '📋', 'research': '🔍', 'communication': '💬'}.get(category.lower(), '📝')
                content_parts.append(f"### {category_emoji} {category.title()} ({len(cat_tasks)} tasks)")
                
                for task in cat_tasks:
                    assignee_text = f" ({task['assigned_to']})" if task['assigned_to'] != 'unassigned' else " (Available)"
                    content_parts.append(f"- [ ] **{task['task']}**{assignee_text}")
                
                content_parts.append("")
            
            # Action items for follow-up
            content_parts.extend([
                "## 🎯 Follow-Up Actions",
                "",
                "- [ ] Review and self-assign relevant unassigned tasks",
                "- [ ] Clarify any unclear task descriptions",
                "- [ ] Add missing deadlines for urgent items", 
                "- [ ] Identify and resolve task dependencies",
                "- [ ] Schedule work time for assigned tasks",
                "",
                "## 📈 Project Health",
                "",
                f"**Task Distribution:** {'✅ Well distributed' if len(assignee_groups) > 1 else '⚠️ Consider distributing workload'}",
                f"**Deadline Clarity:** {'✅ Most tasks have deadlines' if with_deadlines > len(tasks) * 0.6 else '⚠️ Many tasks need deadlines'}",
                f"**Priority Setting:** {'✅ Priorities are clear' if high_priority > 0 else '⚠️ Consider setting task priorities'}",
                "",
                "---",
                f"*Generated from [[{meeting_filename}]] on {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
                "",
                "**Tags:** #tasks #dashboard #project #meeting-follow-up"
            ])
            
            content = "\n".join(content_parts)
            
            # Save dashboard to Obsidian vault Meta/dashboards
            dashboard_vault_path = dashboards_path / dashboard_filename
            with open(dashboard_vault_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Also save backup copy to output directory
            dashboard_output_path = output_path / dashboard_filename
            with open(dashboard_output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            log_success(self.logger, f"Created task dashboard: Meta/dashboards/{dashboard_filename}")
            return str(dashboard_vault_path)
            
        except Exception as e:
            log_error(self.logger, f"Error creating task dashboard", e)
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
                'high_priority': len([t for t in tasks if t['priority'].lower() == 'high']),
                'with_deadlines': len([t for t in tasks if t['deadline'] != 'not specified']),
                'assignees': list(set([t['assigned_to'] for t in tasks if t['assigned_to'] != 'unassigned'])),
                'categories': list(set([t['category'] for t in tasks]))
            }
            
            return stats
            
        except Exception as e:
            log_error(self.logger, "Error calculating task statistics", e)
            return {}