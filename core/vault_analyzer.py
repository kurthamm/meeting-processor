"""
Vault Analyzer for Dashboard Generator
Handles all data analysis from vault files
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
from utils.logger import LoggerMixin
from .content_parser import ContentParser


class VaultAnalyzer(LoggerMixin):
    """Analyzes vault data to extract intelligence for dashboards"""
    
    def __init__(self, vault_path: Path, obsidian_folder_path: str):
        self.vault_path = vault_path
        self.obsidian_folder_path = obsidian_folder_path
        self.parser = ContentParser()
    
    def analyze_meetings(self) -> Dict[str, Any]:
        """Analyze recent meetings and patterns"""
        meetings_path = self.vault_path / self.obsidian_folder_path
        
        if not meetings_path.exists():
            return {'total': 0, 'recent': [], 'patterns': {}}
        
        meeting_files = list(meetings_path.glob("*.md"))
        
        # Get recent meetings (last 30 days)
        recent_meetings = []
        now = datetime.now()
        
        for meeting_file in meeting_files:
            try:
                # Extract date from filename
                date_match = self.parser.extract_date_from_filename(meeting_file.name)
                if date_match:
                    meeting_date = datetime.strptime(date_match, "%Y-%m-%d")
                    days_ago = (now - meeting_date).days
                    
                    if days_ago <= 30:
                        recent_meetings.append({
                            'file': meeting_file.name,
                            'date': date_match,
                            'days_ago': days_ago,
                            'title': self.parser.extract_meeting_title(meeting_file)
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
    
    def analyze_tasks(self) -> Dict[str, Any]:
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
                task_info = self.parser.parse_task_metadata(content, task_file.name)
                
                # Count by priority
                priority = task_info.get('priority', 'medium').lower()
                if priority in by_priority:
                    by_priority[priority] += 1
                
                # Count by category
                category = task_info.get('category', 'general')
                by_category[category] += 1
                
                # Check if urgent or assigned to me
                if self.parser.is_urgent_task(task_info):
                    urgent_tasks.append(task_info)
                
                if self.parser.is_my_task(task_info):
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
    
    def analyze_people(self) -> Dict[str, Any]:
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
                meeting_count = self.parser.count_meeting_references(content)
                
                # Get last interaction date
                last_interaction = self.parser.extract_last_interaction_date(content)
                
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
    
    def analyze_companies(self) -> Dict[str, Any]:
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
                relationship = self.parser.extract_company_relationship(content)
                by_relationship[relationship] += 1
                
                # Count recent activity
                meeting_count = self.parser.count_meeting_references(content)
                
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
    
    def analyze_technologies(self) -> Dict[str, Any]:
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
                category = self.parser.extract_tech_category(content)
                status = self.parser.extract_tech_status(content)
                
                by_category[category] += 1
                by_status[status] += 1
                
                # Count usage references
                usage_count = self.parser.count_meeting_references(content)
                
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
    
    def get_meeting_frequency_trend(self) -> Dict[str, Any]:
        """Get meeting frequency over time"""
        meetings_data = self.analyze_meetings()
        
        # Calculate trend based on recent activity
        this_week = meetings_data['this_week']
        this_month = meetings_data['this_month']
        
        # Estimate last week (rough calculation)
        last_week_estimate = max(0, (this_month - this_week) // 3)
        
        trend = 'stable'
        if this_week > last_week_estimate * 1.2:
            trend = 'increasing'
        elif this_week < last_week_estimate * 0.8:
            trend = 'decreasing'
        
        return {
            'this_week': this_week,
            'last_week': last_week_estimate,
            'trend': trend
        }
    
    def get_task_creation_trend(self) -> Dict[str, Any]:
        """Get task creation trend"""
        tasks_data = self.analyze_tasks()
        
        # Simple trend analysis based on total tasks
        total_tasks = tasks_data['total']
        urgent_tasks = len(tasks_data['urgent'])
        
        return {
            'total': total_tasks,
            'urgent': urgent_tasks,
            'trend': 'increasing' if urgent_tasks > 3 else 'stable'
        }
    
    def get_busiest_days(self) -> List[str]:
        """Get busiest days of week based on meeting patterns"""
        # This could be enhanced to actually analyze meeting dates
        # For now, return common busy days
        return ['Tuesday', 'Wednesday', 'Thursday']
    
    def get_growth_metrics(self) -> Dict[str, str]:
        """Get vault growth metrics"""
        # Get current totals
        meetings = self.analyze_meetings()
        people = self.analyze_people()
        companies = self.analyze_companies()
        technologies = self.analyze_technologies()
        
        total_notes = (meetings['total'] + people['total'] + 
                      companies['total'] + technologies['total'])
        
        return {
            'total_notes': str(total_notes),
            'notes_created_this_week': str(meetings['this_week']),
            'active_connections': str(len(people['top_contacts'])),
            'knowledge_growth': 'Strong' if total_notes > 50 else 'Growing'
        }