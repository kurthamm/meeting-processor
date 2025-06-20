"""
Dashboard Builder for Dashboard Generator
Handles content formatting and dashboard construction
"""

import os
from datetime import datetime
from typing import Dict, List, Any
from utils.logger import LoggerMixin


class DashboardBuilder(LoggerMixin):
    """Builds formatted dashboard content from intelligence data"""
    
    def build_primary_dashboard(self, intelligence: Dict[str, Any]) -> str:
        """Build the primary dashboard content"""
        
        # Get user and company from environment variables
        user_name = os.getenv('OBSIDIAN_USER_NAME', 'me')
        user_file_name = user_name.replace(' ', '-')
        company_name = os.getenv('OBSIDIAN_COMPANY_NAME', 'NeuraFlash')
        company_file_name = company_name.replace(' ', '-')
        
        # Build dataview queries for the dashboard
        dataview_recent_meetings = '''```dataview
table without id
  file.link as "Meeting",
  date as "Date",
  meeting-type as "Type",
  length(filter(file.outlinks, (x) => contains(string(x), "Tasks/"))) as "Tasks"
from "Meetings"
sort date desc
limit 10
```'''

        dataview_urgent_tasks = '''```dataview
task
from "Tasks"
where !completed
where priority = "high" or contains(deadline, dateformat(date(today), "yyyy-MM-dd"))
sort priority desc
limit 10
```'''

        dataview_recent_people = '''```dataview
table without id
  file.link as "Person",
  company as "Company",
  length(filter(file.inlinks, (x) => contains(string(x), "Meetings/"))) as "Meetings"
from "People"
where file.mtime >= date(today) - dur(7 days)
sort file.mtime desc
limit 10
```'''

        # Updated to use company name from environment
        dataview_active_companies = '''```dataview
table without id
  file.link as "Company",
  relationship-to-''' + company_file_name.lower() + ''' as "Relationship",
  length(filter(file.inlinks, (x) => contains(string(x), "Meetings/"))) as "Meetings"
from "Companies"
where contains(relationship-status, "Client") or contains(relationship-status, "Active")
sort file.mtime desc
```'''

        dataview_tech_in_use = '''```dataview
table without id
  file.link as "Technology",
  status as "Status",
  category as "Category"
from "Technologies"
where status = "In Use" or status = "Active"
sort category asc
```'''

        # Updated to use the user name from environment
        dataview_my_tasks = '''```dataview
task
from "Tasks"
where contains(assigned-to, "[[People/''' + user_file_name + ''']]") or contains(assigned-to, "''' + user_name + '''")
where !completed
group by priority
```'''

        content_parts = [
            f"# 🧠 Command Center Dashboard - {company_name}",
            "",
            f"**User:** {user_name}",
            f"**Last Updated:** {intelligence['generated_at']}",
            f"**Auto-generated from your 2nd brain data**",
            "",
            "## 📊 Quick Stats",
            ""
        ]
        
        # Add quick stats section
        content_parts.extend(self._build_quick_stats_section(intelligence))
        
        # Add urgent tasks with dataview
        content_parts.extend([
            "## 🚨 Urgent Tasks & Deadlines",
            "",
            dataview_urgent_tasks,
            ""
        ])
        
        # Add recent meetings with dataview
        content_parts.extend([
            "## 📅 Recent Meetings",
            "",
            dataview_recent_meetings,
            ""
        ])
        
        # Add my tasks section
        content_parts.extend([
            f"## 📋 My Tasks ({user_name})",
            "",
            dataview_my_tasks,
            ""
        ])
        
        # Add recent people interactions
        content_parts.extend([
            "## 👥 Recent People Activity",
            "",
            dataview_recent_people,
            ""
        ])
        
        # Add active companies
        content_parts.extend([
            "## 🏢 Active Companies",
            "",
            dataview_active_companies,
            ""
        ])
        
        # Add technologies in use
        content_parts.extend([
            "## 💻 Technologies in Use",
            "",
            dataview_tech_in_use,
            ""
        ])
        
        # Add insights section
        content_parts.extend(self._build_insights_section(intelligence))
        
        # Add quick actions section
        content_parts.extend(self._build_quick_actions_section(intelligence))
        
        # Add navigation section
        content_parts.extend(self._build_navigation_section())
        
        # Add footer
        content_parts.extend(self._build_footer())
        
        return "\n".join(content_parts)
    
    def _build_quick_stats_section(self, intelligence: Dict[str, Any]) -> List[str]:
        """Build the quick stats section with dataview queries"""
        
        # Build inline dataview queries for counts
        stats_content = [
            "```dataview",
            "table without id",
            '  length(filter(file.folder, (x) => x = "Meetings")) as "Total Meetings",',
            '  length(filter(file.folder, (x) => x = "Tasks")) as "Total Tasks",',
            '  length(filter(file.folder, (x) => x = "People")) as "People Network",',
            '  length(filter(file.folder, (x) => x = "Companies")) as "Companies",',
            '  length(filter(file.folder, (x) => x = "Technologies")) as "Technologies"',
            "limit 1",
            "```",
            ""
        ]
        
        return stats_content
    
    def _build_urgent_section(self, intelligence: Dict[str, Any]) -> List[str]:
        """Build the urgent attention section - now handled by dataview"""
        # This is now handled by the dataview query in the main dashboard
        return []
    
    def _build_recent_activity_section(self, intelligence: Dict[str, Any]) -> List[str]:
        """Build the recent activity section - now handled by dataview"""
        # This is now handled by the dataview queries in the main dashboard
        return []
    
    def _build_insights_section(self, intelligence: Dict[str, Any]) -> List[str]:
        """Build the AI insights section"""
        insights = intelligence.get('insights', [])
        
        if not insights:
            return []
        
        content = [
            "## 💡 AI Insights",
            ""
        ]
        
        for insight in insights[:5]:  # Top 5 insights
            content.append(f"- {insight}")
        
        content.append("")
        return content
    
    def _build_relationships_section(self, intelligence: Dict[str, Any]) -> List[str]:
        """Build the key relationships section - now handled by dataview"""
        # This is now handled by the people dataview query
        return []
    
    def _build_technology_section(self, intelligence: Dict[str, Any]) -> List[str]:
        """Build the technology focus section - now handled by dataview"""
        # This is now handled by the technology dataview query
        return []
    
    def _build_quick_actions_section(self, intelligence: Dict[str, Any]) -> List[str]:
        """Build the quick actions section"""
        content = [
            "## ⚡ Quick Actions",
            ""
        ]
        
        # Add dataview query for overdue tasks
        overdue_tasks_query = '''```dataview
list
from "Tasks"
where !completed
where deadline < date(today)
limit 5
```'''
        
        content.extend([
            "### ⚠️ Overdue Tasks",
            "",
            overdue_tasks_query,
            "",
            "### 📝 Actions",
            "- [ ] Review overdue tasks above",
            "- [ ] Plan next week's key priorities",
            "- [ ] Update project statuses",
            "- [ ] Review and update task assignments",
            ""
        ])
        
        return content
    
    def _build_navigation_section(self) -> List[str]:
        """Build the navigation section"""
        return [
            "## 🔗 Navigation",
            "",
            "### 📊 Dashboards",
            "- [[Meta/dashboards/|📊 All Dashboards]]",
            "",
            "### 📁 Main Directories", 
            "- [[Meetings/|📅 Meeting Notes]]",
            "- [[Tasks/|📋 Task Management]]",
            "- [[People/|👥 People Directory]]",
            "- [[Companies/|🏢 Company Directory]]", 
            "- [[Technologies/|💻 Technology Stack]]",
            "",
            "### 🎯 Quick Access",
            "- Create new: [[Templates/meeting-template|Meeting]] | [[Templates/task-template|Task]] | [[Templates/person-template|Person]]",
            "- Search: [[Tasks#Active|Active Tasks]] | [[Meetings#This Week|This Week's Meetings]]",
            "",
        ]
    
    def _build_footer(self) -> List[str]:
        """Build the footer section"""
        return [
            "---",
            "*This dashboard uses live Dataview queries that update automatically*",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "**Tags:** #dashboard #command-center #2nd-brain"
        ]
    
    def build_trends_section(self, trends: Dict[str, Any]) -> List[str]:
        """Build a trends section for dashboards with dataview"""
        content = [
            "## 📈 Trends & Patterns",
            "",
            "### Meeting Frequency (Last 30 Days)",
            "",
            '''```dataview
table without id
  dateformat(date, "ccc") as "Day",
  length(filter(pages("Meetings"), (p) => p.date = date)) as "Meetings"
from "Meetings"
where date >= date(today) - dur(30 days)
group by dateformat(date, "yyyy-MM-dd") as date
sort date desc
```''',
            ""
        ]
        
        return content
    
    def build_summary_stats(self, intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Build summary statistics for other components"""
        return {
            'total_meetings': intelligence.get('meetings', {}).get('total', 0),
            'total_tasks': intelligence.get('tasks', {}).get('total', 0),
            'total_people': intelligence.get('people', {}).get('total', 0),
            'total_companies': intelligence.get('companies', {}).get('total', 0),
            'urgent_tasks': len(intelligence.get('tasks', {}).get('urgent', [])),
            'this_week_meetings': intelligence.get('meetings', {}).get('this_week', 0),
            'recent_interactions': len(intelligence.get('people', {}).get('recent_interactions', []))
        }