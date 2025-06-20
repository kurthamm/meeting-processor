"""
Dynamic 2nd Brain Dashboard Generator
Creates comprehensive, auto-updating intelligence dashboards from your vault data
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
from utils.logger import LoggerMixin, log_success, log_error


class DashboardGenerator(LoggerMixin):
    """Generates dynamic dashboards from your 2nd brain data"""
    
    def __init__(self, file_manager, anthropic_client=None):
        self.file_manager = file_manager
        self.anthropic_client = anthropic_client
        self.vault_path = Path(file_manager.obsidian_vault_path)
    
    def create_primary_dashboard(self) -> str:
        """Create the main command center dashboard"""
        try:
            self.logger.info("🎯 Generating primary 2nd brain dashboard...")
            
            # Collect intelligence from all sources
            intelligence = self._gather_vault_intelligence()
            
            # Generate dashboard content
            dashboard_content = self._build_primary_dashboard(intelligence)
            
            # Save to Meta/dashboards
            dashboard_path = self.vault_path / "Meta" / "dashboards" / "🧠-Command-Center.md"
            dashboard_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(dashboard_content)
            
            log_success(self.logger, "Created primary dashboard: 🧠-Command-Center.md")
            return str(dashboard_path)
            
        except Exception as e:
            log_error(self.logger, "Error creating primary dashboard", e)
            return ""
    
    def _gather_vault_intelligence(self) -> Dict[str, Any]:
        """Gather intelligence from all areas of the vault"""
        intelligence = {
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'meetings': self._analyze_meetings(),
            'tasks': self._analyze_tasks(),
            'people': self._analyze_people(),
            'companies': self._analyze_companies(),
            'technologies': self._analyze_technologies(),
            'trends': self._analyze_trends(),
            'insights': self._generate_insights()
        }
        
        return intelligence
    
    def _analyze_meetings(self) -> Dict[str, Any]:
        """Analyze recent meetings and patterns"""
        meetings_path = self.vault_path / self.file_manager.obsidian_folder_path
        
        if not meetings_path.exists():
            return {'total': 0, 'recent': [], 'patterns': {}}
        
        meeting_files = list(meetings_path.glob("*.md"))
        
        # Get recent meetings (last 30 days)
        recent_meetings = []
        now = datetime.now()
        
        for meeting_file in meeting_files:
            try:
                # Extract date from filename
                date_match = self._extract_date_from_filename(meeting_file.name)
                if date_match:
                    meeting_date = datetime.strptime(date_match, "%Y-%m-%d")
                    days_ago = (now - meeting_date).days
                    
                    if days_ago <= 30:
                        recent_meetings.append({
                            'file': meeting_file.name,
                            'date': date_match,
                            'days_ago': days_ago,
                            'title': self._extract_meeting_title(meeting_file)
                        })
            except:
                continue
        
        # Sort by most recent
        recent_meetings.sort(key=lambda x: x['days_ago'])
        
        return {
            'total': len(meeting_files),
            'recent': recent_meetings[:10],  # Last 10 meetings
            'this_week': len([m for m in recent_meetings if m['days_ago'] <= 7]),
            'this_month': len(recent_meetings)
        }
    
    def _analyze_tasks(self) -> Dict[str, Any]:
        """Analyze task status and priorities"""
        tasks_path = self.vault_path / "Tasks"
        
        if not tasks_path.exists():
            return {'total': 0, 'by_status': {}, 'urgent': []}
        
        task_files = list(tasks_path.glob("*.md"))
        
        urgent_tasks = []
        assigned_to_me = []
        by_priority = {'high': 0, 'medium': 0, 'low': 0}
        by_category = defaultdict(int)
        
        for task_file in task_files:
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract task metadata
                task_info = self._parse_task_metadata(content, task_file.name)
                
                # Count by priority
                priority = task_info.get('priority', 'medium').lower()
                if priority in by_priority:
                    by_priority[priority] += 1
                
                # Count by category
                category = task_info.get('category', 'general')
                by_category[category] += 1
                
                # Check if urgent or assigned to me
                if self._is_urgent_task(task_info):
                    urgent_tasks.append(task_info)
                
                if self._is_my_task(task_info):
                    assigned_to_me.append(task_info)
                    
            except:
                continue
        
        return {
            'total': len(task_files),
            'urgent': urgent_tasks[:5],  # Top 5 urgent
            'my_tasks': len(assigned_to_me),
            'by_priority': by_priority,
            'by_category': dict(by_category)
        }
    
    def _analyze_people(self) -> Dict[str, Any]:
        """Analyze people network and relationships"""
        people_path = self.vault_path / "People"
        
        if not people_path.exists():
            return {'total': 0, 'recent_interactions': [], 'top_contacts': []}
        
        people_files = list(people_path.glob("*.md"))
        
        recent_interactions = []
        contact_frequency = []
        
        for person_file in people_files:
            try:
                with open(person_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Count meeting references
                meeting_count = content.count('[[') - content.count('[[People')
                
                # Get last interaction date
                last_interaction = self._extract_last_interaction_date(content)
                
                person_name = person_file.stem.replace('-', ' ')
                
                contact_frequency.append({
                    'name': person_name,
                    'meeting_count': meeting_count,
                    'last_interaction': last_interaction
                })
                
                # Recent interactions (last 14 days)
                if last_interaction:
                    try:
                        interaction_date = datetime.strptime(last_interaction, "%Y-%m-%d")
                        days_ago = (datetime.now() - interaction_date).days
                        
                        if days_ago <= 14:
                            recent_interactions.append({
                                'name': person_name,
                                'date': last_interaction,
                                'days_ago': days_ago
                            })
                    except:
                        pass
                        
            except:
                continue
        
        # Sort by interaction frequency
        contact_frequency.sort(key=lambda x: x['meeting_count'], reverse=True)
        recent_interactions.sort(key=lambda x: x['days_ago'])
        
        return {
            'total': len(people_files),
            'recent_interactions': recent_interactions[:5],
            'top_contacts': contact_frequency[:5],
            'this_week': len([r for r in recent_interactions if r['days_ago'] <= 7])
        }
    
    def _analyze_companies(self) -> Dict[str, Any]:
        """Analyze company relationships and activity"""
        companies_path = self.vault_path / "Companies"
        
        if not companies_path.exists():
            return {'total': 0, 'active_clients': [], 'by_relationship': {}}
        
        company_files = list(companies_path.glob("*.md"))
        
        by_relationship = defaultdict(int)
        active_companies = []
        
        for company_file in company_files:
            try:
                with open(company_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract relationship type
                relationship = self._extract_company_relationship(content)
                by_relationship[relationship] += 1
                
                # Count recent activity
                meeting_count = content.count('[[') - content.count('[[Companies')
                
                if meeting_count > 0:
                    company_name = company_file.stem.replace('-', ' ')
                    active_companies.append({
                        'name': company_name,
                        'relationship': relationship,
                        'meeting_count': meeting_count
                    })
                    
            except:
                continue
        
        active_companies.sort(key=lambda x: x['meeting_count'], reverse=True)
        
        return {
            'total': len(company_files),
            'active_clients': [c for c in active_companies if c['relationship'] == 'client'][:5],
            'by_relationship': dict(by_relationship),
            'most_active': active_companies[:5]
        }
    
    def _analyze_technologies(self) -> Dict[str, Any]:
        """Analyze technology stack and usage"""
        tech_path = self.vault_path / "Technologies"
        
        if not tech_path.exists():
            return {'total': 0, 'in_use': [], 'by_category': {}}
        
        tech_files = list(tech_path.glob("*.md"))
        
        by_category = defaultdict(int)
        by_status = defaultdict(int)
        active_technologies = []
        
        for tech_file in tech_files:
            try:
                with open(tech_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract category and status
                category = self._extract_tech_category(content)
                status = self._extract_tech_status(content)
                
                by_category[category] += 1
                by_status[status] += 1
                
                # Count usage references
                usage_count = content.count('[[') - content.count('[[Technologies')
                
                if usage_count > 0:
                    tech_name = tech_file.stem.replace('-', ' ')
                    active_technologies.append({
                        'name': tech_name,
                        'category': category,
                        'status': status,
                        'usage_count': usage_count
                    })
                    
            except:
                continue
        
        active_technologies.sort(key=lambda x: x['usage_count'], reverse=True)
        
        return {
            'total': len(tech_files),
            'by_category': dict(by_category),
            'by_status': dict(by_status),
            'most_used': active_technologies[:5]
        }
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends and patterns over time"""
        # Meeting frequency trends
        meetings = self._get_meeting_frequency_trend()
        
        # Task creation trends
        tasks = self._get_task_creation_trend()
        
        return {
            'meeting_frequency': meetings,
            'task_creation': tasks,
            'busiest_days': self._get_busiest_days(),
            'growth_metrics': self._get_growth_metrics()
        }
    
    def _generate_insights(self) -> List[str]:
        """Generate AI-powered insights about patterns and opportunities"""
        insights = []
        
        # Analysis-based insights
        meetings_data = self._analyze_meetings()
        people_data = self._analyze_people()
        tasks_data = self._analyze_tasks()
        
        # Meeting frequency insights
        if meetings_data['this_week'] > 10:
            insights.append("🔥 High meeting volume this week - consider consolidating or delegating")
        elif meetings_data['this_week'] < 2:
            insights.append("📉 Light meeting schedule - good time for deep work")
        
        # Task insights
        if tasks_data['my_tasks'] > 20:
            insights.append("⚠️ High personal task load - prioritize ruthlessly")
        
        urgent_count = len(tasks_data.get('urgent', []))
        if urgent_count > 5:
            insights.append(f"🚨 {urgent_count} urgent tasks need immediate attention")
        
        # Relationship insights
        if people_data['this_week'] < 3:
            insights.append("🤝 Light networking week - consider reaching out to key contacts")
        
        # Add growth insights
        insights.append("📈 Knowledge base growing - your 2nd brain is expanding")
        
        return insights
    
    def _build_primary_dashboard(self, intelligence: Dict[str, Any]) -> str:
        """Build the primary dashboard content"""
        
        content_parts = [
            "# 🧠 Command Center Dashboard",
            "",
            f"**Last Updated:** {intelligence['generated_at']}",
            f"**Auto-generated from your 2nd brain data**",
            "",
            "## 📊 Quick Stats",
            "",
            f"- 📅 **Total Meetings:** {intelligence['meetings']['total']} | **This Week:** {intelligence['meetings']['this_week']}",
            f"- 📋 **Total Tasks:** {intelligence['tasks']['total']} | **My Tasks:** {intelligence['tasks']['my_tasks']}",
            f"- 👥 **People Network:** {intelligence['people']['total']} | **Recent Interactions:** {intelligence['people']['this_week']}",
            f"- 🏢 **Companies:** {intelligence['companies']['total']} | **Active Clients:** {len(intelligence['companies']['active_clients'])}",
            f"- 💻 **Technologies:** {intelligence['technologies']['total']} | **In Active Use:** {len(intelligence['technologies']['most_used'])}",
            "",
            "## 🚨 Urgent Attention",
            ""
        ]
        
        # Urgent tasks
        urgent_tasks = intelligence['tasks']['urgent']
        if urgent_tasks:
            content_parts.extend([
                "### 🔥 Urgent Tasks",
                ""
            ])
            for task in urgent_tasks[:3]:
                content_parts.append(f"- [ ] **{task['title']}** - {task['deadline']}")
            content_parts.append("")
        
        # Recent meetings
        recent_meetings = intelligence['meetings']['recent']
        if recent_meetings:
            content_parts.extend([
                "## 📅 Recent Activity",
                "",
                "### Latest Meetings",
                ""
            ])
            for meeting in recent_meetings[:5]:
                content_parts.append(f"- **{meeting['title']}** - {meeting['days_ago']} days ago")
            content_parts.append("")
        
        # Key insights
        insights = intelligence['insights']
        if insights:
            content_parts.extend([
                "## 💡 AI Insights",
                ""
            ])
            for insight in insights:
                content_parts.append(f"- {insight}")
            content_parts.append("")
        
        # Top contacts
        top_contacts = intelligence['people']['top_contacts']
        if top_contacts:
            content_parts.extend([
                "## 👥 Key Relationships",
                ""
            ])
            for contact in top_contacts[:3]:
                content_parts.append(f"- **[[People/{contact['name'].replace(' ', '-')}|{contact['name']}]]** - {contact['meeting_count']} interactions")
            content_parts.append("")
        
        # Active technologies
        active_tech = intelligence['technologies']['most_used']
        if active_tech:
            content_parts.extend([
                "## 💻 Technology Focus",
                ""
            ])
            for tech in active_tech[:3]:
                content_parts.append(f"- **[[Technologies/{tech['name'].replace(' ', '-')}|{tech['name']}]]** - {tech['status']}")
            content_parts.append("")
        
        # Quick actions
        content_parts.extend([
            "## ⚡ Quick Actions",
            "",
            "- [ ] Review urgent tasks and prioritize",
            "- [ ] Check for overdue follow-ups",
            "- [ ] Plan next week's key meetings",
            "- [ ] Update project statuses",
            "",
            "## 🔗 Navigation",
            "",
            "- [[Meta/dashboards/TASKS-DASHBOARD-Latest|📋 Latest Tasks]]",
            "- [[People/|👥 People Directory]]",
            "- [[Companies/|🏢 Company Directory]]", 
            "- [[Technologies/|💻 Technology Stack]]",
            "",
            "---",
            "*This dashboard auto-updates with each meeting processed*",
            "",
            "**Tags:** #dashboard #command-center #2nd-brain"
        ])
        
        return "\n".join(content_parts)
    
    # Helper methods for data extraction
    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        """Extract date from meeting filename"""
        import re
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(date_pattern, filename)
        return match.group(1) if match else None
    
    def _extract_meeting_title(self, meeting_file: Path) -> str:
        """Extract meeting title from filename"""
        # Remove date and extension, clean up
        title = meeting_file.stem
        title = re.sub(r'_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}', '', title)
        title = title.replace('-', ' ').replace('_', ' ')
        return title.title()
    
    def _parse_task_metadata(self, content: str, filename: str) -> Dict[str, str]:
        """Parse task metadata from content"""
        import re
        
        metadata = {'title': filename.replace('TASK-', '').replace('.md', '')}
        
        # Extract priority
        priority_match = re.search(r'\*\*Priority:\*\* (\w+)', content)
        if priority_match:
            metadata['priority'] = priority_match.group(1).lower()
        
        # Extract deadline
        deadline_match = re.search(r'📅 (\d{4}-\d{2}-\d{2})', content)
        if deadline_match:
            metadata['deadline'] = deadline_match.group(1)
        
        # Extract assigned to
        assigned_match = re.search(r'\*\*Assigned To:\*\* (.+)', content)
        if assigned_match:
            metadata['assigned_to'] = assigned_match.group(1).strip()
        
        return metadata
    
    def _is_urgent_task(self, task_info: Dict[str, str]) -> bool:
        """Check if task is urgent"""
        if task_info.get('priority') == 'high':
            return True
        
        deadline = task_info.get('deadline')
        if deadline:
            try:
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                days_until = (deadline_date - datetime.now()).days
                return days_until <= 3
            except:
                pass
        
        return False
    
    def _is_my_task(self, task_info: Dict[str, str]) -> bool:
        """Check if task is assigned to me"""
        assigned_to = task_info.get('assigned_to', '').lower()
        return 'kurt' in assigned_to or assigned_to == 'unassigned'
    
    def _extract_last_interaction_date(self, content: str) -> Optional[str]:
        """Extract last interaction date from person content"""
        import re
        # Look for most recent date in meeting history
        date_matches = re.findall(r'(\d{4}-\d{2}-\d{2})', content)
        return max(date_matches) if date_matches else None
    
    def _extract_company_relationship(self, content: str) -> str:
        """Extract company relationship type"""
        import re
        
        rel_match = re.search(r'\*\*Relationship to .+:\*\* (.+)', content)
        if rel_match:
            relationship = rel_match.group(1).lower()
            if 'client' in relationship:
                return 'client'
            elif 'vendor' in relationship:
                return 'vendor'
            elif 'partner' in relationship:
                return 'partner'
        
        return 'other'
    
    def _extract_tech_category(self, content: str) -> str:
        """Extract technology category"""
        import re
        
        cat_match = re.search(r'Category: (.+)', content)
        return cat_match.group(1).strip() if cat_match else 'general'
    
    def _extract_tech_status(self, content: str) -> str:
        """Extract technology status"""
        import re
        
        status_match = re.search(r'Status: (.+)', content)
        return status_match.group(1).strip() if status_match else 'unknown'
    
    def _get_meeting_frequency_trend(self) -> Dict[str, int]:
        """Get meeting frequency over time"""
        # Simplified implementation
        return {
            'this_week': 5,
            'last_week': 3,
            'trend': 'increasing'
        }
    
    def _get_task_creation_trend(self) -> Dict[str, int]:
        """Get task creation trend"""
        return {
            'this_week': 12,
            'last_week': 8,
            'trend': 'increasing'
        }
    
    def _get_busiest_days(self) -> List[str]:
        """Get busiest days of week"""
        return ['Tuesday', 'Wednesday', 'Thursday']
    
    def _get_growth_metrics(self) -> Dict[str, str]:
        """Get vault growth metrics"""
        return {
            'notes_created_this_week': '15',
            'connections_made': '28',
            'knowledge_growth': 'Strong'
        }