"""
AI-powered entity management for Meeting Processor
Creates and manages entity notes with intelligent context extraction
"""

from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING
from utils.logger import LoggerMixin, log_success, log_error, log_warning
from .ai_context import AIContextExtractor

if TYPE_CHECKING:
    from core.file_manager import FileManager


class ObsidianEntityManager(LoggerMixin):
    """Creates and manages entity notes with AI-powered smart templates"""
    
    def __init__(self, file_manager: 'FileManager', anthropic_client):
        self.file_manager = file_manager
        self.ai_context = AIContextExtractor(anthropic_client, file_manager)
        
        # Flexible patterns for finding entity sections
        self.entity_section_patterns = {
            'people': [
                r'people\s*mentioned\s*:?',
                r'attendees?\s*:?',
                r'participants?\s*:?',
                r'people\s*:?',
                r'who\s*was\s*there\s*:?'
            ],
            'companies': [
                r'companies?\s*discussed\s*:?',
                r'organizations?\s*:?',
                r'clients?\s*:?',
                r'companies?\s*:?',
                r'business\s*entities\s*:?'
            ],
            'technologies': [
                r'technolog(?:y|ies)\s*referenced\s*:?',
                r'tech(?:nolog(?:y|ies))?\s*:?',
                r'tools?\s*:?',
                r'systems?\s*:?',
                r'software\s*:?',
                r'technolog(?:y|ies)\s*:?'
            ]
        }
    
    def create_entity_notes(self, entities: Dict[str, List[str]], 
                          meeting_filename: str, meeting_date: str) -> Dict[str, List[str]]:
        """Create individual Obsidian notes for each detected entity with AI context"""
        entity_links = {'people': [], 'companies': [], 'technologies': []}
        
        self.logger.info("🏗️  Starting AI-powered entity note creation...")
        
        # Create People notes with AI context
        for person in entities.get('people', []):
            link = self._create_person_note(person, meeting_filename, meeting_date)
            if link:
                entity_links['people'].append(link)
        
        # Create Company notes with AI context
        for company in entities.get('companies', []):
            link = self._create_company_note(company, meeting_filename, meeting_date)
            if link:
                entity_links['companies'].append(link)
            
        # Create Technology notes with AI context
        for technology in entities.get('technologies', []):
            link = self._create_technology_note(technology, meeting_filename, meeting_date)
            if link:
                entity_links['technologies'].append(link)
        
        total_links = len(entity_links['people']) + len(entity_links['companies']) + len(entity_links['technologies'])
        log_success(self.logger, f"Created {total_links} smart entity links with AI context")
        
        return entity_links
    
    def _create_person_note(self, person_name: str, meeting_filename: str, meeting_date: str) -> Optional[str]:
        """Create a person note with AI-enhanced context"""
        safe_name = person_name.replace(' ', '-').replace('/', '-')
        filename = f"{safe_name}.md"
        
        person_path = Path(self.file_manager.obsidian_vault_path) / "People" / filename
        
        if person_path.exists():
            self._append_meeting_reference(person_path, meeting_filename, meeting_date)
            self.logger.debug(f"📝 Updated existing person note: {person_name}")
        else:
            # Get AI-enhanced context
            self.logger.debug(f"🧠 Getting AI context for person: {person_name}")
            context = self.ai_context.get_person_context(person_name, meeting_filename)
            
            # Determine relationship tag
            relationship = context.get('relationship', '').lower().replace(' ', '-')
            if not relationship:
                relationship = 'contact'
            
            # Build the person note content
            content = f"""# {person_name}

**Type:** Person
**Status:** Active
**First Detected:** {meeting_date}
**Last Updated:** {meeting_date}

## Basic Information
**Full Name:** {person_name}
**Title/Role:** {context.get('role', '')}
**Email:** {context.get('email', '')}
**Phone:** {context.get('phone', '')}
**Company:** {context.get('company', '')}
**Department:** {context.get('department', '')}
**Location:** 

## Professional Context
**Relationship to {context.get('employer', 'Us')}:** {context.get('relationship', '')}
**Decision Authority:** {context.get('authority', '')}
**Reports To:** 
**Direct Reports:** 

## Expertise & Skills
**Primary Skills:** 
**Technologies Known:** 
**Specializations:** 
**Industry Experience:** 

## Communication Style
**Preferred Contact Method:** 
**Response Time:** 
**Meeting Preferences:** 
**Technical Level:** 

## Active Tasks & Responsibilities
### Assigned Tasks
`$= dv.table(["Task", "Status", "Priority", "Due Date"], dv.pages('"Tasks"').where(p => p.assigned_to && p.assigned_to.path === dv.current().file.path).map(p => [p.file.link, p.status, p.priority, p.due_date]))`

### Tasks Mentioned In
`$= dv.list(dv.pages('"Tasks"').where(p => p.file.content && p.file.content.includes("{person_name}") && (!p.assigned_to || p.assigned_to.path !== dv.current().file.path)).map(p => p.file.link))`

## Project Involvement
**Current Projects:** {context.get('projects', '')}
**Past Projects:** 
**Key Contributions:** 

## Meeting History
<!-- Auto-updated by meeting processor -->
- [[{meeting_filename}]] - {meeting_date}

### All Meetings Attended
`$= dv.table(["Meeting", "Date", "Type"], dv.pages('"Meetings"').where(p => p.file.outlinks && p.file.outlinks.some(link => link.path === dv.current().file.path)).sort(p => p.date, 'desc').map(p => [p.file.link, p.date, p.meeting_type]))`

## Technologies Used
`$= dv.list(dv.pages('"Technologies"').where(p => p.file.inlinks && p.file.inlinks.some(link => link.path === dv.current().file.path)).map(p => p.file.link))`

## Companies Involved With
`$= dv.table(["Company", "Relationship"], dv.pages('"Companies"').where(p => p.file.content && p.file.content.includes("{person_name}")).map(p => [p.file.link, p.relationship_to_neuraflash || ""]))`

## Key Interactions
**Topics They Care About:** 
**Common Questions:** 
**Decision Patterns:** 
**Pain Points:** 

## Relationship Intelligence
**Influence Network:** 
**Key Relationships:** 
**Communication Frequency:** 
**Last Interaction:** {meeting_date}

## Notes & Observations
{context.get('notes', '')}
<!-- Add manual observations about working style, preferences, etc. -->

## Action Items
- [ ] Send introduction email
- [ ] Schedule follow-up meeting
- [ ] Share requested resources

---
**Tags:** #person #contact #{relationship}
**Created:** {meeting_date}
**Source:** Auto-generated from meeting transcript
"""
            self._save_entity_note("People", filename, content)
            self.logger.info(f"👤 Created new person note: {person_name}")
        
        return f"[[People/{safe_name}|{person_name}]]"
    
    def _create_company_note(self, company_name: str, meeting_filename: str, meeting_date: str) -> Optional[str]:
        """Create a company note with AI-enhanced context"""
        safe_name = company_name.replace(' ', '-').replace('/', '-')
        filename = f"{safe_name}.md"
        
        company_path = Path(self.file_manager.obsidian_vault_path) / "Companies" / filename
        
        if company_path.exists():
            self._append_meeting_reference(company_path, meeting_filename, meeting_date)
            self.logger.debug(f"📝 Updated existing company note: {company_name}")
        else:
            # Get AI-enhanced context
            self.logger.debug(f"🧠 Getting AI context for company: {company_name}")
            context = self.ai_context.get_company_context(company_name, meeting_filename)
            
            content = f"""# {company_name}

Type: Company
Status: Active
**Current Employer:** {"Yes" if company_name.lower() == context.get('employer', '').lower() else "No"}
First Mentioned: {meeting_date}

## Company Information
Industry: {context.get('industry', '')}
Size: {context.get('size', '')}
Location: {context.get('location', '')}
Website: 

## Key Contacts
{context.get('key_contacts', '')}

### All Contacts from This Company
`$= dv.table(["Person", "Role", "Email"], dv.pages('"People"').where(p => p.company === "{company_name}").sort(p => p.title_role, 'asc').map(p => [p.file.link, p.title_role || "", p.email || ""]))`

## Relationship Context
**Relationship to {context.get('employer', 'Us')}:** {context.get('relationship', '')}
**Business Needs:** {context.get('business_needs', '')}

## Meeting History
- [[{meeting_filename}]] - {meeting_date}

### All Meetings with This Company
`$= dv.table(["Meeting", "Date", "Type"], dv.pages('"Meetings"').where(p => p.file.outlinks && p.file.outlinks.some(link => link.path === dv.current().file.path)).sort(p => p.date, 'desc').map(p => [p.file.link, p.date, p.meeting_type]))`

## Active Projects
{context.get('projects', '')}

### Project Details
`$= dv.list(dv.pages('"Meetings"').where(p => p.file.outlinks && p.file.outlinks.some(link => link.path === dv.current().file.path) && (p.tags && p.tags.includes("#project"))).sort(p => p.date, 'desc').map(p => p.file.link))`

## Technologies Used
{context.get('technologies', '')}

### Technology Stack
`$= dv.list(dv.pages('"Technologies"').where(p => p.file.inlinks && p.file.inlinks.some(link => link.path === dv.current().file.path)).map(p => p.file.link))`

## Active Tasks
`$= dv.table(["Task", "Status", "Priority", "Due Date"], dv.pages('"Tasks"').where(p => p.file.content && p.file.content.includes("{company_name}") && p.status !== "done").sort(p => p.priority, 'desc').map(p => [p.file.link, p.status, p.priority, p.due_date]))`

## Relationship Status
- [{"x" if company_name.lower() == context.get('employer', '').lower() else " "}] Current Employer
- [{"x" if "client" in context.get('relationship', '').lower() else " "}] Client
- [{"x" if "vendor" in context.get('relationship', '').lower() else " "}] Vendor
- [{"x" if "partner" in context.get('relationship', '').lower() else " "}] Partner
- [{"x" if "prospect" in context.get('relationship', '').lower() else " "}] Prospect

## Contract Information
Contract Start: 
Contract End: 
Contract Value: 
Payment Terms: 

## Decision Makers
`$= dv.table(["Person", "Authority Level"], dv.pages('"People"').where(p => p.company === "{company_name}" && p.decision_authority).map(p => [p.file.link, p.decision_authority]))`

## Communication History
### Recent Communications
`$= dv.table(["Meeting", "Date", "Key Decisions"], dv.pages('"Meetings"').where(p => p.file.outlinks && p.file.outlinks.some(link => link.path === dv.current().file.path)).sort(p => p.date, 'desc').limit(5).map(p => [p.file.link, p.date, p.key_decisions_made || ""]))`

## Notes
{context.get('notes', '')}

---
Tags: #company #business #{context.get('relationship', 'prospect').lower().replace(' ', '-')}
Created: {meeting_date}
Last Updated: {meeting_date}
"""
            self._save_entity_note("Companies", filename, content)
            self.logger.info(f"🏢 Created new company note: {company_name}")
        
        return f"[[Companies/{safe_name}|{company_name}]]"
        
    def _create_technology_note(self, tech_name: str, meeting_filename: str, meeting_date: str) -> Optional[str]:
        """Create a technology note with AI-enhanced context"""
        safe_name = tech_name.replace(' ', '-').replace('/', '-')
        filename = f"{safe_name}.md"
        
        tech_path = Path(self.file_manager.obsidian_vault_path) / "Technologies" / filename
        
        if tech_path.exists():
            self._append_meeting_reference(tech_path, meeting_filename, meeting_date)
            self.logger.debug(f"📝 Updated existing technology note: {tech_name}")
        else:
            # Get AI-enhanced context
            self.logger.debug(f"🧠 Getting AI context for technology: {tech_name}")
            context = self.ai_context.get_technology_context(tech_name, meeting_filename)
            
            content = f"""# {tech_name}

Type: Technology
Category: {context.get('category', '')}
Status: {context.get('status', 'In Use')}
First Mentioned: {meeting_date}

## Overview
{context.get('usage', '')}

## Use Cases
{context.get('use_cases', '')}

## Integration Points
{context.get('integrations', '')}

## Business Value
{context.get('business_value', '')}

## Implementation Status
**Current Status:** {context.get('status', '')}
**Owner/Responsible:** {context.get('owner', '')}
**Implementation Date:** 
**Next Review:** 

## People Using This Technology
`$= dv.table(["Person", "Role", "Company"], dv.pages('"People"').where(p => p.file.outlinks && p.file.outlinks.some(link => link.path === dv.current().file.path) || (p.file.content && p.file.content.includes("{tech_name}"))).map(p => [p.file.link, p.title_role || "", p.company || ""]))`

## Companies Using This Technology
`$= dv.list(dv.pages('"Companies"').where(p => p.technologies_used && p.technologies_used.includes("{tech_name}") || (p.file.content && p.file.content.includes("{tech_name}"))).map(p => p.file.link))`

## Active Tasks Related to This Technology
`$= dv.table(["Task", "Status", "Priority"], dv.pages('"Tasks"').where(p => p.file.content && p.file.content.includes("{tech_name}") && p.status !== "done").sort(p => p.priority, 'desc').map(p => [p.file.link, p.status, p.priority]))`

## Challenges & Issues
{context.get('challenges', '')}

### Open Issues
`$= dv.list(dv.pages('"Meetings"').where(p => p.file.outlinks && p.file.outlinks.some(link => link.path === dv.current().file.path) && p.issues_identified && p.issues_identified.includes("{tech_name}")).sort(p => p.date, 'desc').map(p => p.file.link))`

## Future Plans
{context.get('future_plans', '')}

## Technical Details
**Version:** 
**License:** 
**Support Level:** 
**Dependencies:** 

## Cost Information
**Monthly Cost:** 
**Annual Cost:** 
**ROI:** 

## Training & Documentation
**Training Required:** 
**Documentation Location:** 
**Expert Contacts:** 

## Meeting References
- [[{meeting_filename}]] - {meeting_date}

### All Meetings Discussing This Technology
`$= dv.table(["Meeting", "Date", "Type"], dv.pages('"Meetings"').where(p => p.file.outlinks && p.file.outlinks.some(link => link.path === dv.current().file.path)).sort(p => p.date, 'desc').map(p => [p.file.link, p.date, p.meeting_type]))`

## Decision History
`$= dv.table(["Meeting", "Date", "Decisions"], dv.pages('"Meetings"').where(p => p.file.outlinks && p.file.outlinks.some(link => link.path === dv.current().file.path) && p.key_decisions_made).sort(p => p.date, 'desc').map(p => [p.file.link, p.date, p.key_decisions_made]))`

## Performance Metrics


---
Tags: #technology #tools #{context.get('category', 'general').lower().replace(' ', '-')}
Created: {meeting_date}
Last Updated: {meeting_date}
"""
            self._save_entity_note("Technologies", filename, content)
            self.logger.info(f"💻 Created new technology note: {tech_name}")
        
        return f"[[Technologies/{safe_name}|{tech_name}]]"
    
    def _save_entity_note(self, folder: str, filename: str, content: str):
        """Save entity note to Obsidian vault"""
        try:
            folder_path = Path(self.file_manager.obsidian_vault_path) / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            
            file_path = folder_path / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            log_success(self.logger, f"Created AI-enhanced entity note: {folder}/{filename}")
            
        except Exception as e:
            log_error(self.logger, f"Error creating entity note {folder}/{filename}", e)
    
    def _append_meeting_reference(self, note_path: Path, meeting_filename: str, meeting_date: str):
        """Append meeting reference to existing entity note"""
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            meeting_ref = f"- [[{meeting_filename}]] - {meeting_date}"
            
            # Check if reference already exists
            if meeting_ref in content:
                self.logger.debug(f"📋 Meeting reference already exists in {note_path.name}")
                return
            
            # Find meeting history section and add new reference
            if "## Meeting History" in content or "## Meeting References" in content:
                lines = content.split('\n')
                updated = False
                
                for i, line in enumerate(lines):
                    if line.strip() in ["## Meeting History", "## Meeting References"]:
                        # Find next section or end of file
                        insert_pos = i + 1
                        while (insert_pos < len(lines) and 
                               not lines[insert_pos].startswith('##') and
                               lines[insert_pos].strip()):
                            insert_pos += 1
                        lines.insert(insert_pos, meeting_ref)
                        updated = True
                        break
                
                if updated:
                    # Update Last Updated timestamp
                    for i, line in enumerate(lines):
                        if line.startswith('Last Updated:') or line.startswith('**Last Updated:**'):
                            lines[i] = f"**Last Updated:** {meeting_date}"
                            break
                    
                    updated_content = '\n'.join(lines)
                    
                    with open(note_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    self.logger.debug(f"📝 Updated entity note: {note_path.name}")
            
        except Exception as e:
            log_error(self.logger, f"Error updating entity note {note_path}", e)
    
    def update_meeting_note_with_entities(self, meeting_path: Path, entity_links: Dict[str, List[str]]):
        """Update the meeting note to include links to detected entities using flexible patterns"""
        try:
            with open(meeting_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # More flexible approach - look for various patterns
            updated_content = self._flexible_entity_update(content, entity_links)
            
            # If flexible update didn't work, try to add a new section
            if updated_content == content:
                self.logger.info("🔄 No entity sections found, adding new Entity Connections section")
                updated_content = self._add_entity_section(content, entity_links)
            
            # Write updated content
            with open(meeting_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            total_entities = sum(len(links) for links in entity_links.values())
            log_success(self.logger, f"Updated meeting note with {total_entities} AI-enhanced entity links")
            
        except Exception as e:
            log_error(self.logger, f"Error updating meeting note with entity links", e)
    
    def _flexible_entity_update(self, content: str, entity_links: Dict[str, List[str]]) -> str:
        """Flexibly update entity sections using multiple patterns"""
        import re
        
        updated_content = content
        
        # Try to update each entity type
        for entity_type, patterns in self.entity_section_patterns.items():
            if entity_type not in entity_links or not entity_links[entity_type]:
                continue
            
            entity_string = ', '.join(entity_links[entity_type])
            updated = False
            
            # Try each pattern
            for pattern in patterns:
                # Look for pattern with various formatting
                full_pattern = rf'(\*\*)?({pattern})(\*\*)?\s*:?\s*([^\n]*)'
                
                match = re.search(full_pattern, updated_content, re.IGNORECASE | re.MULTILINE)
                if match:
                    # Found a matching section
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # Reconstruct the line with entities
                    prefix = match.group(1) or ''
                    label = match.group(2)
                    suffix = match.group(3) or ''
                    
                    new_line = f"{prefix}{label}{suffix}: {entity_string}"
                    
                    # Replace the line
                    lines = updated_content.split('\n')
                    for i, line in enumerate(lines):
                        if match.group(0) in line:
                            lines[i] = new_line
                            updated = True
                            break
                    
                    if updated:
                        updated_content = '\n'.join(lines)
                        self.logger.debug(f"✅ Updated {entity_type} section using pattern: {pattern}")
                        break
            
            if not updated:
                self.logger.debug(f"⚠️  Could not find section for {entity_type}")
        
        return updated_content
    
    def _add_entity_section(self, content: str, entity_links: Dict[str, List[str]]) -> str:
        """Add a new Entity Connections section if none exists"""
        # Find where to insert - before AI Analysis or Complete Transcript
        insert_markers = [
            "## AI Analysis",
            "## Complete Transcript",
            "## Transcript",
            "---"  # Before the footer
        ]
        
        insert_pos = len(content)
        for marker in insert_markers:
            pos = content.find(marker)
            if pos != -1:
                insert_pos = pos
                break
        
        # Build entity section
        entity_section = "\n## Entity Connections\n"
        
        if entity_links.get('people'):
            entity_section += f"**People Mentioned:** {', '.join(entity_links['people'])}\n"
        else:
            entity_section += "**People Mentioned:** None detected\n"
        
        if entity_links.get('companies'):
            entity_section += f"**Companies Discussed:** {', '.join(entity_links['companies'])}\n"
        else:
            entity_section += "**Companies Discussed:** None detected\n"
        
        if entity_links.get('technologies'):
            entity_section += f"**Technologies Referenced:** {', '.join(entity_links['technologies'])}\n"
        else:
            entity_section += "**Technologies Referenced:** None detected\n"
        
        entity_section += "\n"
        
        # Insert the section
        updated_content = content[:insert_pos] + entity_section + content[insert_pos:]
        
        return updated_content
    
    def get_entity_statistics(self) -> Dict[str, int]:
        """Get statistics about existing entity notes"""
        stats = {}
        
        try:
            for folder in ['People', 'Companies', 'Technologies']:
                folder_path = Path(self.file_manager.obsidian_vault_path) / folder
                if folder_path.exists():
                    md_files = list(folder_path.glob('*.md'))
                    stats[folder.lower()] = len(md_files)
                else:
                    stats[folder.lower()] = 0
            
            stats['total'] = sum(stats.values())
            
            self.logger.debug(f"📊 Entity statistics: {stats}")
            
        except Exception as e:
            log_error(self.logger, "Error getting entity statistics", e)
            stats = {'people': 0, 'companies': 0, 'technologies': 0, 'total': 0}
        
        return stats