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
            dataview_tech_in