"""
Dashboard Builder for Dashboard Generator
Handles content formatting and dashboard construction with optimized queries
"""

import os
from datetime import datetime
from typing import Dict, List, Any
from utils.logger import LoggerMixin


class DashboardBuilder(LoggerMixin):
    """Builds formatted dashboard content from intelligence data"""
    
    def build_primary_dashboard(self, intelligence: Dict[str, Any]) -> str:
        """Build the primary dashboard content with optimized queries"""
        
        # Get user and company from environment variables
        user_name = os.getenv('OBSIDIAN_USER_NAME', 'me')
        user_file_name = user_name.replace(' ', '-')
        company_name = os.getenv('OBSIDIAN_COMPANY_NAME', 'NeuraFlash')
        company_file_name = company_name.replace(' ', '-')
        
        # Build optimized dataview queries with limits and specific fields
        dataview_recent_meetings = '''```dataview
table without id
  file.link as "Meeting",
  date as "Date",
  default(meeting-type, "General") as "Type",
  length(filter(file.outlinks, (x) => contains(string(x), "Tasks/"))) as "Tasks"
from "Meetings"
where file.name != this.file.name
sort date desc
limit 10
```'''

        dataview_urgent_tasks = '''```dataview
table without id
  link(file.link, truncate(default(title, file.name), 50)) as "Task",
  default(priority, "medium") as "Priority",
  default(assigned_to, "unassigned") as "Assigned",
  default(due_date, "-") as "Due"
from "Tasks"
where status != "done" AND status != "cancelled"
where priority = "critical" OR priority = "high" OR (due_date != null AND due_date <= date(today) + dur(3 days))
where file.name != this.file.name
sort choice(priority = "critical", 1, choice(priority = "high", 2, 3)) asc, due_date asc
limit 10
```'''

        dataview_recent_people = '''```dataview
table without id
  file.link as "Person",
  default(company, "-") as "Company",
  length(filter(file.inlinks, (x) => contains(string(x), "Meetings/"))) as "Meetings"
from "People"
where file.mtime >= date(today) - dur(7 days)
where file.name != this.file.name
sort file.mtime desc
limit 10
```'''

        # Optimized company query with relationship fallback
        dataview_active_companies = f'''```dataview
table without id
  file.link as "Company",
  default(relationship-to-{company_file_name.lower()}, default(relationship, "prospect")) as "Relationship",
  length(filter(file.inlinks, (x) => contains(string(x), "Meetings/"))) as "Meetings"
from "Companies"
where contains(string(relationship-status), "Client") 
   OR contains(string(relationship-status), "Active")
   OR file.mtime >= date(today) - dur(30 days)
where file.name != this.file.name
sort choice(contains(string(relationship-status), "Client"), 1, 2) asc, file.mtime desc
limit 10
```'''

        dataview_tech_in_use = '''```dataview
table without id
  file.link as "Technology",
  default(status, "Unknown") as "Status",
  default(category, "General") as "Category"
from "Technologies"
where status = "In Use" OR status = "Active" OR status = "Deployed"
where file.name != this.file.name
sort category asc, file.name asc
limit 15
```'''

        # Optimized personal tasks query
        dataview_my_tasks = f'''```dataview
table without id
  link(file.link, truncate(default(title, file.name), 40)) as "Task",
  default(priority, "medium") as "Pri",
  default(status, "new") as "Status",
  default(due_date, "-") as "Due"
from "Tasks"
where (contains(string(assigned_to), "{user_name}") OR contains(string(assigned_to), "[[People/{user_file_name}]]"))
where status != "done" AND status != "cancelled"
where file.name != this.file.name
sort priority desc, due_date asc
limit 20
```'''

        # Build dashboard sections
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
            "",
            "_No urgent tasks_ <!-- Fallback text -->",
            ""
        ])
        
        # Add recent meetings with dataview
        content_parts.extend([
            "## 📅 Recent Meetings",
            "",
            dataview_recent_meetings,
            "",
            "_No recent meetings_ <!-- Fallback text -->",
            ""
        ])
        
        # Add my tasks section
        content_parts.extend([
            f"## 📋 My Tasks ({user_name})",
            "",
            dataview_my_tasks,
            "",
            "_No personal tasks assigned_ <!-- Fallback text -->",
            ""
        ])
        
        # Add recent people interactions
        content_parts.extend([
            "## 👥 Recent People Activity",
            "",
            dataview_recent_people,
            "",
            "_No recent people activity_ <!-- Fallback text -->",
            ""
        ])
        
        # Add active companies
        content_parts.extend([
            "## 🏢 Active Companies",
            "",
            dataview_active_companies,
            "",
            "_No active companies_ <!-- Fallback text -->",
            ""
        ])
        
        # Add technologies in use
        content_parts.extend([
            "## 💻 Technologies in Use",
            "",
            dataview_tech_in_use,
            "",
            "_No technologies tracked_ <!-- Fallback text -->",
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
        """Build the quick stats section with inline metrics"""
        stats_content = []
        
        # Get metrics from intelligence
        meetings = intelligence.get('meetings', {})
        tasks = intelligence.get('tasks', {})
        people = intelligence.get('people', {})
        companies = intelligence.get('companies', {})
        technologies = intelligence.get('technologies', {})
        
        # Build stats grid
        stats_content.extend([
            f"- 📅 **Meetings:** {meetings.get('total', 0)} total | {meetings.get('this_week', 0)} this week",
            f"- 📋 **Tasks:** {tasks.get('total', 0)} total | {tasks.get('my_tasks', 0)} assigned to me",
            f"- 👥 **People:** {people.get('total', 0)} total | {people.get('this_week', 0)} interactions this week",
            f"- 🏢 **Companies:** {companies.get('total', 0)} total | {len(companies.get('active_clients', []))} active clients",
            f"- 💻 **Technologies:** {technologies.get('total', 0)} total | {len(technologies.get('most_used', []))} in active use",
            ""
        ])
        
        return stats_content
    
    def _build_insights_section(self, intelligence: Dict[str, Any]) -> List[str]:
        """Build the AI insights section"""
        insights = intelligence.get('insights', [])
        
        if not insights:
            return []
        
        content = [
            "## 💡 AI Insights & Recommendations",
            ""
        ]
        
        for insight in insights[:6]:  # Top 6 insights
            content.append(f"- {insight}")
        
        content.append("")
        return content
    
    def _build_quick_actions_section(self, intelligence: Dict[str, Any]) -> List[str]:
        """Build the quick actions section with dynamic overdue tasks"""
        content = [
            "## ⚡ Quick Actions",
            ""
        ]
        
        # Add dataview query for overdue tasks
        overdue_tasks_query = '''```dataview
list link(file.link, truncate(default(title, file.name), 60))
from "Tasks"
where status != "done" AND status != "cancelled"
where due_date < date(today)
sort priority desc
limit 5
```'''
        
        content.extend([
            "### ⚠️ Overdue Tasks",
            "",
            overdue_tasks_query,
            "",
            "### 📝 Recommended Actions",
        ])
        
        # Add dynamic recommendations based on intelligence
        tasks = intelligence.get('tasks', {})
        meetings = intelligence.get('meetings', {})
        
        if len(tasks.get('urgent', [])) > 0:
            content.append("- [ ] Address urgent tasks immediately")
        
        if tasks.get('my_tasks', 0) > 10:
            content.append("- [ ] Review and prioritize task backlog")
        
        if meetings.get('this_week', 0) > 8:
            content.append("- [ ] Consider consolidating or delegating meetings")
        
        # Always include these standard actions
        content.extend([
            "- [ ] Plan next week's key priorities",
            "- [ ] Update project statuses in active tasks",
            "- [ ] Review and close completed tasks",
            ""
        ])
        
        return content
    
    def _build_navigation_section(self) -> List[str]:
        """Build the navigation section"""
        return [
            "## 🔗 Quick Navigation",
            "",
            "### 📊 Dashboards & Views",
            "- [[Meta/dashboards/Task-Dashboard|📋 Unified Task Dashboard]]",
            "- [[Meta/dashboards/|📊 All Dashboards]]",
            "",
            "### 📁 Main Directories", 
            "- [[Meetings/|📅 All Meetings]]",
            "- [[Tasks/|📋 All Tasks]]",
            "- [[People/|👥 People Directory]]",
            "- [[Companies/|🏢 Company Directory]]", 
            "- [[Technologies/|💻 Technology Stack]]",
            "",
            "### 🎯 Quick Searches",
            "- [[Tasks#status = \"in_progress\"|🚀 In Progress Tasks]]",
            "- [[Tasks#priority = \"high\" OR priority = \"critical\"|🔥 High Priority Tasks]]",
            "- [[Meetings#date >= date(today) - dur(7 days)|📅 This Week's Meetings]]",
            "- [[People#file.mtime >= date(today) - dur(30 days)|👥 Recently Updated Contacts]]",
            "",
            "### ➕ Create New",
            "- [[Templates/meeting-template|📅 New Meeting Note]]",
            "- [[Templates/task-template|📋 New Task]]",
            "- [[Templates/person-template|👤 New Person]]",
            "- [[Templates/company-template|🏢 New Company]]",
            "",
        ]
    
    def _build_footer(self) -> List[str]:
        """Build the footer section"""
        return [
            "---",
            "",
            "## 📈 Dashboard Settings",
            "",
            f"- **Update Frequency:** Every {os.getenv('DASHBOARD_UPDATE_HOURS', '6')} hours",
            f"- **Morning Refresh:** {os.getenv('DASHBOARD_MORNING_HOUR', '9')}:00",
            f"- **High Impact Threshold:** {os.getenv('DASHBOARD_HIGH_PRIORITY_THRESHOLD', '2')} high priority tasks",
            "",
            "*This dashboard uses live Dataview queries that update automatically as your vault changes.*",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "**Tags:** #dashboard #command-center #2nd-brain",
            "",
            "---",
            "",
            "_To customize dashboard update frequency, set environment variables in your `.env` file._"
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
            'recent_interactions': len(intelligence.get('people', {}).get('recent_interactions', [])),
            'active_clients': len(intelligence.get('companies', {}).get('active_clients', [])),
            'technologies_in_use': len(intelligence.get('technologies', {}).get('most_used', []))
        }