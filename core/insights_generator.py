"""
Insights Generator for Dashboard Generator
Generates AI-powered insights and analyzes trends
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.logger import LoggerMixin


class InsightsGenerator(LoggerMixin):
    """Generates insights and trends from vault intelligence data"""
    
    def __init__(self, anthropic_client=None):
        self.anthropic_client = anthropic_client
    
    def generate_insights(self, intelligence: Dict[str, Any]) -> List[str]:
        """Generate AI-powered insights about patterns and opportunities"""
        insights = []
        
        # Extract data for analysis
        meetings_data = intelligence.get('meetings', {})
        people_data = intelligence.get('people', {})
        tasks_data = intelligence.get('tasks', {})
        companies_data = intelligence.get('companies', {})
        
        # Meeting frequency insights
        insights.extend(self._analyze_meeting_patterns(meetings_data))
        
        # Task management insights
        insights.extend(self._analyze_task_patterns(tasks_data))
        
        # Relationship insights
        insights.extend(self._analyze_relationship_patterns(people_data))
        
        # Business insights
        insights.extend(self._analyze_business_patterns(companies_data))
        
        # General productivity insights
        insights.extend(self._generate_productivity_insights(intelligence))
        
        return insights
    
    def _analyze_meeting_patterns(self, meetings_data: Dict[str, Any]) -> List[str]:
        """Analyze meeting patterns and generate insights"""
        insights = []
        
        this_week = meetings_data.get('this_week', 0)
        total = meetings_data.get('total', 0)
        
        if this_week > 10:
            insights.append("🔥 High meeting volume this week - consider consolidating or delegating")
        elif this_week < 2:
            insights.append("📉 Light meeting schedule - good time for deep work")
        elif this_week >= 5:
            insights.append("⚖️ Balanced meeting load - maintaining good rhythm")
        
        # Meeting frequency analysis
        if total > 50:
            insights.append("📈 Extensive meeting history - rich collaboration network")
        elif total < 10:
            insights.append("🌱 Building meeting cadence - consider regular check-ins")
        
        return insights
    
    def _analyze_task_patterns(self, tasks_data: Dict[str, Any]) -> List[str]:
        """Analyze task patterns and workload"""
        insights = []
        
        my_tasks = tasks_data.get('my_tasks', 0)
        urgent_tasks = tasks_data.get('urgent', [])
        by_priority = tasks_data.get('by_priority', {})
        
        # Workload insights
        if my_tasks > 20:
            insights.append("⚠️ High personal task load - prioritize ruthlessly")
        elif my_tasks < 5:
            insights.append("🎯 Light task load - good time to take on new projects")
        
        # Urgency insights
        urgent_count = len(urgent_tasks)
        if urgent_count > 5:
            insights.append(f"🚨 {urgent_count} urgent tasks need immediate attention")
        elif urgent_count > 0:
            insights.append(f"⏰ {urgent_count} urgent task(s) to address")
        
        # Priority distribution insights
        high_priority = by_priority.get('high', 0)
        total_tasks = sum(by_priority.values())
        
        if total_tasks > 0:
            high_ratio = high_priority / total_tasks
            if high_ratio > 0.5:
                insights.append("🔥 Many high-priority tasks - review priority criteria")
            elif high_ratio < 0.1:
                insights.append("📋 Good priority balance - most tasks are manageable")
        
        return insights
    
    def _analyze_relationship_patterns(self, people_data: Dict[str, Any]) -> List[str]:
        """Analyze relationship and networking patterns"""
        insights = []
        
        this_week_interactions = people_data.get('this_week', 0)
        total_people = people_data.get('total', 0)
        top_contacts = people_data.get('top_contacts', [])
        
        # Networking activity
        if this_week_interactions < 3:
            insights.append("🤝 Light networking week - consider reaching out to key contacts")
        elif this_week_interactions > 10:
            insights.append("👥 High social engagement - great for relationship building")
        
        # Network size insights
        if total_people > 50:
            insights.append("🌐 Strong professional network - leverage for opportunities")
        elif total_people < 10:
            insights.append("🌱 Growing network - focus on quality connections")
        
        # Contact frequency insights
        if top_contacts:
            most_frequent = top_contacts[0]
            meeting_count = most_frequent.get('meeting_count', 0)
            if meeting_count > 10:
                insights.append(f"🔗 Strong connection with {most_frequent['name']} - key relationship")
        
        return insights
    
    def _analyze_business_patterns(self, companies_data: Dict[str, Any]) -> List[str]:
        """Analyze business relationship patterns"""
        insights = []
        
        total_companies = companies_data.get('total', 0)
        active_clients = companies_data.get('active_clients', [])
        by_relationship = companies_data.get('by_relationship', {})
        
        # Client engagement
        client_count = len(active_clients)
        if client_count > 5:
            insights.append("💼 Strong client portfolio - focus on retention")
        elif client_count > 0:
            insights.append(f"🎯 {client_count} active client(s) - opportunity for growth")
        
        # Business relationship diversity
        relationship_types = len(by_relationship)
        if relationship_types > 3:
            insights.append("🤝 Diverse business relationships - good ecosystem balance")
        
        # Partnership opportunities
        partners = by_relationship.get('partner', 0)
        if partners > 2:
            insights.append("🤝 Multiple partnerships - leverage for mutual growth")
        
        return insights
    
    def _generate_productivity_insights(self, intelligence: Dict[str, Any]) -> List[str]:
        """Generate general productivity and growth insights"""
        insights = []
        
        # Knowledge base growth
        total_meetings = intelligence.get('meetings', {}).get('total', 0)
        total_people = intelligence.get('people', {}).get('total', 0)
        total_companies = intelligence.get('companies', {}).get('total', 0)
        
        total_knowledge_nodes = total_meetings + total_people + total_companies
        
        if total_knowledge_nodes > 100:
            insights.append("🧠 Rich knowledge base - your 2nd brain is thriving")
        elif total_knowledge_nodes > 50:
            insights.append("📈 Knowledge base growing - your 2nd brain is expanding")
        else:
            insights.append("🌱 Building your 2nd brain - consistency is key")
        
        # Activity balance insights
        meetings_this_week = intelligence.get('meetings', {}).get('this_week', 0)
        my_tasks = intelligence.get('tasks', {}).get('my_tasks', 0)
        
        if meetings_this_week > 8 and my_tasks > 15:
            insights.append("⚡ High activity week - ensure time for execution")
        elif meetings_this_week < 3 and my_tasks < 5:
            insights.append("🎯 Quiet week - good for strategic planning")
        
        return insights
    
    def analyze_trends(self, intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends and patterns over time"""
        trends = {}
        
        # Meeting frequency trends
        meetings = intelligence.get('meetings', {})
        trends['meeting_frequency'] = {
            'this_week': meetings.get('this_week', 0),
            'this_month': meetings.get('this_month', 0),
            'trend': self._calculate_meeting_trend(meetings)
        }
        
        # Task creation trends
        tasks = intelligence.get('tasks', {})
        trends['task_creation'] = {
            'total': tasks.get('total', 0),
            'my_tasks': tasks.get('my_tasks', 0),
            'urgent': len(tasks.get('urgent', [])),
            'trend': self._calculate_task_trend(tasks)
        }
        
        # Network growth trends
        people = intelligence.get('people', {})
        trends['network_growth'] = {
            'total_people': people.get('total', 0),
            'this_week_interactions': people.get('this_week', 0),
            'trend': self._calculate_network_trend(people)
        }
        
        # Business development trends
        companies = intelligence.get('companies', {})
        trends['business_development'] = {
            'total_companies': companies.get('total', 0),
            'active_clients': len(companies.get('active_clients', [])),
            'trend': self._calculate_business_trend(companies)
        }
        
        return trends
    
    def _calculate_meeting_trend(self, meetings_data: Dict[str, Any]) -> str:
        """Calculate meeting frequency trend"""
        this_week = meetings_data.get('this_week', 0)
        this_month = meetings_data.get('this_month', 0)
        
        # Rough estimate of weekly average for the month
        weekly_avg = this_month / 4 if this_month > 0 else 0
        
        if this_week > weekly_avg * 1.2:
            return 'increasing'
        elif this_week < weekly_avg * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_task_trend(self, tasks_data: Dict[str, Any]) -> str:
        """Calculate task creation trend"""
        urgent_count = len(tasks_data.get('urgent', []))
        my_tasks = tasks_data.get('my_tasks', 0)
        
        # Simple heuristic based on urgency and personal load
        if urgent_count > 3 or my_tasks > 15:
            return 'increasing'
        elif urgent_count == 0 and my_tasks < 5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_network_trend(self, people_data: Dict[str, Any]) -> str:
        """Calculate networking trend"""
        this_week = people_data.get('this_week', 0)
        total = people_data.get('total', 0)
        
        # If we have recent interactions and a growing network
        if this_week > 3 and total > 10:
            return 'growing'
        elif this_week < 2:
            return 'stable'
        else:
            return 'growing'
    
    def _calculate_business_trend(self, companies_data: Dict[str, Any]) -> str:
        """Calculate business development trend"""
        active_clients = len(companies_data.get('active_clients', []))
        total = companies_data.get('total', 0)
        
        if active_clients > 3 and total > 5:
            return 'expanding'
        elif active_clients > 0:
            return 'developing'
        else:
            return 'building'
    
    def get_priority_recommendations(self, intelligence: Dict[str, Any]) -> List[str]:
        """Get actionable priority recommendations"""
        recommendations = []
        
        # Based on urgent tasks
        urgent_tasks = intelligence.get('tasks', {}).get('urgent', [])
        if len(urgent_tasks) > 3:
            recommendations.append("🚨 Address urgent tasks immediately")
        
        # Based on meeting load
        this_week_meetings = intelligence.get('meetings', {}).get('this_week', 0)
        if this_week_meetings > 8:
            recommendations.append("📅 Consider consolidating or rescheduling some meetings")
        
        # Based on networking
        networking_interactions = intelligence.get('people', {}).get('this_week', 0)
        if networking_interactions < 2:
            recommendations.append("🤝 Schedule time for relationship building")
        
        # Based on business development
        active_clients = len(intelligence.get('companies', {}).get('active_clients', []))
        if active_clients > 0:
            recommendations.append("💼 Follow up with active clients")
        
        return recommendations