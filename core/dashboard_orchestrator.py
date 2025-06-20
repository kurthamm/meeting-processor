"""
Dashboard Orchestrator - Main coordinator for dashboard generation
Coordinates all dashboard components while maintaining the original interface
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from utils.logger import LoggerMixin, log_success, log_error

from .vault_analyzer import VaultAnalyzer
from .content_parser import ContentParser
from .insights_generator import InsightsGenerator
from .dashboard_builder import DashboardBuilder


class DashboardOrchestrator(LoggerMixin):
    """Main orchestrator that coordinates all dashboard generation components"""
    
    def __init__(self, file_manager, anthropic_client=None):
        self.file_manager = file_manager
        self.anthropic_client = anthropic_client
        self.vault_path = Path(file_manager.obsidian_vault_path)
        
        # Initialize components
        self.vault_analyzer = VaultAnalyzer(
            vault_path=self.vault_path,
            obsidian_folder_path=file_manager.obsidian_folder_path
        )
        self.content_parser = ContentParser()
        self.insights_generator = InsightsGenerator(anthropic_client)
        self.dashboard_builder = DashboardBuilder()
    
    def create_primary_dashboard(self) -> str:
        """Create the main command center dashboard - maintains original interface"""
        try:
            self.logger.info("🎯 Generating primary 2nd brain dashboard...")
            
            # Collect intelligence from all sources
            intelligence = self._gather_vault_intelligence()
            
            # Generate dashboard content
            dashboard_content = self.dashboard_builder.build_primary_dashboard(intelligence)
            
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
        self.logger.info("🔍 Gathering vault intelligence...")
        
        intelligence = {
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        
        try:
            # Analyze all data sources
            intelligence['meetings'] = self.vault_analyzer.analyze_meetings()
            intelligence['tasks'] = self.vault_analyzer.analyze_tasks()
            intelligence['people'] = self.vault_analyzer.analyze_people()
            intelligence['companies'] = self.vault_analyzer.analyze_companies()
            intelligence['technologies'] = self.vault_analyzer.analyze_technologies()
            
            # Generate trends
            intelligence['trends'] = self._analyze_trends(intelligence)
            
            # Generate insights
            intelligence['insights'] = self.insights_generator.generate_insights(intelligence)
            
            self.logger.info("✅ Vault intelligence gathered successfully")
            
        except Exception as e:
            log_error(self.logger, "Error gathering vault intelligence", e)
            # Return minimal intelligence to prevent total failure
            intelligence.update({
                'meetings': {'total': 0, 'recent': [], 'this_week': 0},
                'tasks': {'total': 0, 'urgent': [], 'my_tasks': 0},
                'people': {'total': 0, 'recent_interactions': [], 'top_contacts': []},
                'companies': {'total': 0, 'active_clients': [], 'by_relationship': {}},
                'technologies': {'total': 0, 'most_used': [], 'by_category': {}},
                'trends': {},
                'insights': ['⚠️ Error gathering full intelligence - showing basic data']
            })
        
        return intelligence
    
    def _analyze_trends(self, intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends and patterns over time"""
        try:
            trends = {
                'meeting_frequency': self.vault_analyzer.get_meeting_frequency_trend(),
                'task_creation': self.vault_analyzer.get_task_creation_trend(),
                'busiest_days': self.vault_analyzer.get_busiest_days(),
                'growth_metrics': self.vault_analyzer.get_growth_metrics()
            }
            
            # Add insights-generated trends
            insights_trends = self.insights_generator.analyze_trends(intelligence)
            trends.update(insights_trends)
            
            return trends
            
        except Exception as e:
            log_error(self.logger, "Error analyzing trends", e)
            return {}
    
    # Additional methods for extended functionality
    def create_custom_dashboard(self, dashboard_type: str, **kwargs) -> str:
        """Create custom dashboards for specific purposes"""
        try:
            intelligence = self._gather_vault_intelligence()
            
            if dashboard_type == "tasks_focus":
                return self._create_tasks_dashboard(intelligence, **kwargs)
            elif dashboard_type == "relationships":
                return self._create_relationships_dashboard(intelligence, **kwargs)
            elif dashboard_type == "business":
                return self._create_business_dashboard(intelligence, **kwargs)
            else:
                self.logger.warning(f"Unknown dashboard type: {dashboard_type}")
                return ""
                
        except Exception as e:
            log_error(self.logger, f"Error creating {dashboard_type} dashboard", e)
            return ""
    
    def _create_tasks_dashboard(self, intelligence: Dict[str, Any], **kwargs) -> str:
        """Create a tasks-focused dashboard"""
        tasks_data = intelligence.get('tasks', {})
        
        content_parts = [
            "# 📋 Tasks Focus Dashboard",
            "",
            f"**Generated:** {intelligence['generated_at']}",
            "",
            "## 📊 Task Overview",
            "",
            f"- **Total Tasks:** {tasks_data.get('total', 0)}",
            f"- **My Tasks:** {tasks_data.get('my_tasks', 0)}",
            f"- **Urgent Tasks:** {len(tasks_data.get('urgent', []))}",
            "",
        ]
        
        # Add urgent tasks
        urgent_tasks = tasks_data.get('urgent', [])
        if urgent_tasks:
            content_parts.extend([
                "## 🚨 Urgent Tasks",
                ""
            ])
            for task in urgent_tasks:
                content_parts.append(f"- [ ] **{task.get('title', 'Unknown')}** - {task.get('deadline', 'No deadline')}")
            content_parts.append("")
        
        # Add priority breakdown
        by_priority = tasks_data.get('by_priority', {})
        if by_priority:
            content_parts.extend([
                "## 📈 Priority Breakdown",
                "",
                f"- 🔥 **High Priority:** {by_priority.get('high', 0)}",
                f"- ⚡ **Medium Priority:** {by_priority.get('medium', 0)}",
                f"- 📌 **Low Priority:** {by_priority.get('low', 0)}",
                ""
            ])
        
        dashboard_content = "\n".join(content_parts)
        
        # Save dashboard
        dashboard_path = self.vault_path / "Meta" / "dashboards" / "📋-Tasks-Focus.md"
        dashboard_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_content)
        
        return str(dashboard_path)
    
    def _create_relationships_dashboard(self, intelligence: Dict[str, Any], **kwargs) -> str:
        """Create a relationships-focused dashboard"""
        people_data = intelligence.get('people', {})
        
        content_parts = [
            "# 👥 Relationships Dashboard",
            "",
            f"**Generated:** {intelligence['generated_at']}",
            "",
            "## 📊 Network Overview",
            "",
            f"- **Total Contacts:** {people_data.get('total', 0)}",
            f"- **Recent Interactions:** {people_data.get('this_week', 0)} this week",
            "",
        ]
        
        # Add top contacts
        top_contacts = people_data.get('top_contacts', [])
        if top_contacts:
            content_parts.extend([
                "## 🌟 Top Contacts",
                ""
            ])
            for contact in top_contacts[:5]:
                contact_link = f"[[People/{contact['name'].replace(' ', '-')}|{contact['name']}]]"
                content_parts.append(f"- {contact_link} - {contact['meeting_count']} interactions")
            content_parts.append("")
        
        dashboard_content = "\n".join(content_parts)
        
        # Save dashboard
        dashboard_path = self.vault_path / "Meta" / "dashboards" / "👥-Relationships.md"
        dashboard_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_content)
        
        return str(dashboard_path)
    
    def _create_business_dashboard(self, intelligence: Dict[str, Any], **kwargs) -> str:
        """Create a business-focused dashboard"""
        companies_data = intelligence.get('companies', {})
        
        content_parts = [
            "# 💼 Business Dashboard",
            "",
            f"**Generated:** {intelligence['generated_at']}",
            "",
            "## 📊 Business Overview",
            "",
            f"- **Total Companies:** {companies_data.get('total', 0)}",
            f"- **Active Clients:** {len(companies_data.get('active_clients', []))}",
            "",
        ]
        
        # Add client information
        active_clients = companies_data.get('active_clients', [])
        if active_clients:
            content_parts.extend([
                "## 🎯 Active Clients",
                ""
            ])
            for client in active_clients:
                client_link = f"[[Companies/{client['name'].replace(' ', '-')}|{client['name']}]]"
                content_parts.append(f"- {client_link} - {client['meeting_count']} interactions")
            content_parts.append("")
        
        dashboard_content = "\n".join(content_parts)
        
        # Save dashboard
        dashboard_path = self.vault_path / "Meta" / "dashboards" / "💼-Business.md"
        dashboard_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_content)
        
        return str(dashboard_path)
    
    def get_intelligence_summary(self) -> Dict[str, Any]:
        """Get a summary of current vault intelligence"""
        try:
            intelligence = self._gather_vault_intelligence()
            return self.dashboard_builder.build_summary_stats(intelligence)
        except Exception as e:
            log_error(self.logger, "Error getting intelligence summary", e)
            return {}
    
    def refresh_all_dashboards(self) -> List[str]:
        """Refresh all dashboards"""
        created_dashboards = []
        
        try:
            # Create primary dashboard
            primary = self.create_primary_dashboard()
            if primary:
                created_dashboards.append(primary)
            
            # Create custom dashboards
            tasks_dashboard = self.create_custom_dashboard("tasks_focus")
            if tasks_dashboard:
                created_dashboards.append(tasks_dashboard)
            
            relationships_dashboard = self.create_custom_dashboard("relationships")
            if relationships_dashboard:
                created_dashboards.append(relationships_dashboard)
            
            business_dashboard = self.create_custom_dashboard("business")
            if business_dashboard:
                created_dashboards.append(business_dashboard)
            
            log_success(self.logger, f"Refreshed {len(created_dashboards)} dashboards")
            
        except Exception as e:
            log_error(self.logger, "Error refreshing dashboards", e)
        
        return created_dashboards