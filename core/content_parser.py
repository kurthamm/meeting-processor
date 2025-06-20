"""
Content Parser for Dashboard Generator
Handles all text extraction and parsing from vault files
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from utils.logger import LoggerMixin


class ContentParser(LoggerMixin):
    """Handles parsing and extraction of content from vault files"""
    
    def extract_date_from_filename(self, filename: str) -> Optional[str]:
        """Extract date from meeting filename"""
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(date_pattern, filename)
        return match.group(1) if match else None
    
    def extract_meeting_title(self, meeting_file: Path) -> str:
        """Extract meeting title from filename"""
        # Remove date and extension, clean up
        title = meeting_file.stem
        title = re.sub(r'_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}', '', title)
        title = title.replace('-', ' ').replace('_', ' ')
        return title.title()
    
    def parse_task_metadata(self, content: str, filename: str) -> Dict[str, str]:
        """Parse task metadata from content"""
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
        
        # Extract category
        category_match = re.search(r'\*\*Category:\*\* (.+)', content)
        if category_match:
            metadata['category'] = category_match.group(1).strip()
        
        return metadata
    
    def is_urgent_task(self, task_info: Dict[str, str]) -> bool:
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
    
    def is_my_task(self, task_info: Dict[str, str]) -> bool:
        """Check if task is assigned to me"""
        assigned_to = task_info.get('assigned_to', '').lower()
        return 'kurt' in assigned_to or assigned_to == 'unassigned'
    
    def extract_last_interaction_date(self, content: str) -> Optional[str]:
        """Extract last interaction date from person content"""
        # Look for most recent date in meeting history
        date_matches = re.findall(r'(\d{4}-\d{2}-\d{2})', content)
        return max(date_matches) if date_matches else None
    
    def extract_company_relationship(self, content: str) -> str:
        """Extract company relationship type"""
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
    
    def extract_tech_category(self, content: str) -> str:
        """Extract technology category"""
        cat_match = re.search(r'Category: (.+)', content)
        return cat_match.group(1).strip() if cat_match else 'general'
    
    def extract_tech_status(self, content: str) -> str:
        """Extract technology status"""
        status_match = re.search(r'Status: (.+)', content)
        return status_match.group(1).strip() if status_match else 'unknown'
    
    def count_meeting_references(self, content: str, exclude_self_refs: bool = True) -> int:
        """Count meeting references in content"""
        total_links = content.count('[[')
        
        if exclude_self_refs:
            # Subtract self-references (like [[People/Name]] in a person's file)
            self_refs = (content.count('[[People') + 
                        content.count('[[Companies') + 
                        content.count('[[Technologies'))
            return max(0, total_links - self_refs)
        
        return total_links
    
    def extract_tags(self, content: str) -> list:
        """Extract tags from content"""
        tag_matches = re.findall(r'#(\w+)', content)
        return list(set(tag_matches))  # Remove duplicates
    
    def extract_status_from_content(self, content: str, status_patterns: Dict[str, str]) -> str:
        """Extract status using provided patterns"""
        for status, pattern in status_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                return status
        return 'unknown'