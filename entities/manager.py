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
            
            content = f"""# {person_name}

Type: Person
Status: Active
First Mentioned: {meeting_date}

## Contact Information
Email: {context.get('email', '')}
Phone: {context.get('phone', '')}
Role: {context.get('role', '')}
Company: {context.get('company', '')}

## Relationship Context
**Relationship to {context.get('employer', 'Us')}:** {context.get('relationship', '')}
**Decision Authority:** {context.get('authority', '')}
**Department:** {context.get('department', '')}

## Meeting History
- [[{meeting_filename}]] - {meeting_date}

## Notes
{context.get('notes', '')}

## Projects Involved
{context.get('projects', '')}

## Key Relationships


## Communication Preferences


## Expertise Areas


---
Tags: #person #contact
Created: {meeting_date}
Last Updated: {meeting_date}
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
**Current Employer:** No
First Mentioned: {meeting_date}

## Company Information
Industry: {context.get('industry', '')}
Size: {context.get('size', '')}
Location: {context.get('location', '')}
Website: 

## Key Contacts
{context.get('key_contacts', '')}

## Relationship Context
**Relationship to {context.get('employer', 'Us')}:** {context.get('relationship', '')}
**Business Needs:** {context.get('business_needs', '')}

## Meeting History
- [[{meeting_filename}]] - {meeting_date}

## Active Projects
{context.get('projects', '')}

## Technologies Used
{context.get('technologies', '')}

## Relationship Status
- [ ] Current Employer
- [ ] Client
- [ ] Vendor
- [ ] Partner
- [ ] Prospect

## Contract Information
Contract Start: 
Contract End: 
Contract Value: 
Payment Terms: 

## Decision Makers


## Communication History


## Notes
{context.get('notes', '')}

---
Tags: #company #business
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

## Challenges & Issues
{context.get('challenges', '')}

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

## Decision History


## Performance Metrics


---
Tags: #technology #tools
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
                        if line.startswith('Last Updated:'):
                            lines[i] = f"Last Updated: {meeting_date}"
                            break
                    
                    updated_content = '\n'.join(lines)
                    
                    with open(note_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    self.logger.debug(f"📝 Updated entity note: {note_path.name}")
            
        except Exception as e:
            log_error(self.logger, f"Error updating entity note {note_path}", e)
    
    def update_meeting_note_with_entities(self, meeting_note_path: Path, entity_links: Dict[str, List[str]]):
        """Update the meeting note to include links to detected entities"""
        try:
            with open(meeting_note_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find Entity Connections section and populate it
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == "People Mentioned:":
                    if entity_links['people']:
                        lines[i] = f"People Mentioned: {', '.join(entity_links['people'])}"
                    else:
                        lines[i] = "People Mentioned: None detected"
                elif line.strip() == "Companies Discussed:":
                    if entity_links['companies']:
                        lines[i] = f"Companies Discussed: {', '.join(entity_links['companies'])}"
                    else:
                        lines[i] = "Companies Discussed: None detected"
                elif line.strip() == "Technologies Referenced:":
                    if entity_links['technologies']:
                        lines[i] = f"Technologies Referenced: {', '.join(entity_links['technologies'])}"
                    else:
                        lines[i] = "Technologies Referenced: None detected"
            
            updated_content = '\n'.join(lines)
            
            with open(meeting_note_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            total_entities = sum(len(links) for links in entity_links.values())
            log_success(self.logger, f"Updated meeting note with {total_entities} AI-enhanced entity links")
            
        except Exception as e:
            log_error(self.logger, f"Error updating meeting note with entity links", e)
    
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
    
    def find_existing_entity(self, entity_name: str, entity_type: str) -> Optional[Path]:
        """Find if an entity note already exists"""
        try:
            safe_name = entity_name.replace(' ', '-').replace('/', '-')
            filename = f"{safe_name}.md"
            
            folder_map = {
                'person': 'People',
                'people': 'People',
                'company': 'Companies',
                'companies': 'Companies',
                'technology': 'Technologies',
                'technologies': 'Technologies'
            }
            
            folder = folder_map.get(entity_type.lower())
            if not folder:
                return None
            
            entity_path = Path(self.file_manager.obsidian_vault_path) / folder / filename
            
            return entity_path if entity_path.exists() else None
            
        except Exception as e:
            log_error(self.logger, f"Error finding existing entity {entity_name}", e)
            return None
    
    def bulk_update_entity_notes(self, updates: Dict[str, Dict[str, str]]) -> int:
        """Bulk update multiple entity notes with new information"""
        updated_count = 0
        
        try:
            for entity_name, update_data in updates.items():
                entity_type = update_data.get('type', 'unknown')
                entity_path = self.find_existing_entity(entity_name, entity_type)
                
                if entity_path:
                    success = self._update_entity_note(entity_path, update_data)
                    if success:
                        updated_count += 1
                else:
                    log_warning(self.logger, f"Entity note not found for bulk update: {entity_name}")
            
            log_success(self.logger, f"Bulk updated {updated_count} entity notes")
            
        except Exception as e:
            log_error(self.logger, "Error in bulk update operation", e)
        
        return updated_count
    
    def _update_entity_note(self, entity_path: Path, update_data: Dict[str, str]) -> bool:
        """Update an existing entity note with new information"""
        try:
            with open(entity_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            updated = False
            
            # Update specific fields based on update_data
            for field, new_value in update_data.items():
                if field == 'type':  # Skip metadata
                    continue
                
                for i, line in enumerate(lines):
                    if line.startswith(f"{field.title()}:") and new_value:
                        lines[i] = f"{field.title()}: {new_value}"
                        updated = True
                        break
            
            if updated:
                # Update timestamp
                from datetime import datetime
                current_date = datetime.now().strftime("%Y-%m-%d")
                
                for i, line in enumerate(lines):
                    if line.startswith('Last Updated:'):
                        lines[i] = f"Last Updated: {current_date}"
                        break
                
                updated_content = '\n'.join(lines)
                
                with open(entity_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                self.logger.debug(f"📝 Updated entity note: {entity_path.name}")
                return True
            
            return False
            
        except Exception as e:
            log_error(self.logger, f"Error updating entity note {entity_path}", e)
            return False
    
    def export_entity_index(self) -> str:
        """Export an index of all entity notes"""
        try:
            index_lines = [
                "# Entity Index",
                "",
                f"Generated: {self._get_current_timestamp()}",
                ""
            ]
            
            # Export People
            people_path = Path(self.file_manager.obsidian_vault_path) / "People"
            if people_path.exists():
                people_files = sorted(people_path.glob('*.md'))
                index_lines.extend([
                    f"## People ({len(people_files)})",
                    ""
                ])
                
                for person_file in people_files:
                    person_name = person_file.stem.replace('-', ' ')
                    index_lines.append(f"- [[People/{person_file.stem}|{person_name}]]")
                
                index_lines.append("")
            
            # Export Companies
            companies_path = Path(self.file_manager.obsidian_vault_path) / "Companies"
            if companies_path.exists():
                company_files = sorted(companies_path.glob('*.md'))
                index_lines.extend([
                    f"## Companies ({len(company_files)})",
                    ""
                ])
                
                for company_file in company_files:
                    company_name = company_file.stem.replace('-', ' ')
                    index_lines.append(f"- [[Companies/{company_file.stem}|{company_name}]]")
                
                index_lines.append("")
            
            # Export Technologies
            tech_path = Path(self.file_manager.obsidian_vault_path) / "Technologies"
            if tech_path.exists():
                tech_files = sorted(tech_path.glob('*.md'))
                index_lines.extend([
                    f"## Technologies ({len(tech_files)})",
                    ""
                ])
                
                for tech_file in tech_files:
                    tech_name = tech_file.stem.replace('-', ' ')
                    index_lines.append(f"- [[Technologies/{tech_file.stem}|{tech_name}]]")
            
            index_lines.extend([
                "",
                "---",
                "*Generated by Meeting Processor Entity Manager*"
            ])
            
            return "\n".join(index_lines)
            
        except Exception as e:
            log_error(self.logger, "Error exporting entity index", e)
            return f"Error generating entity index: {str(e)}"
    
    def cleanup_orphaned_entities(self) -> int:
        """Clean up entity notes that have no meeting references"""
        cleaned_count = 0
        
        try:
            for folder in ['People', 'Companies', 'Technologies']:
                folder_path = Path(self.file_manager.obsidian_vault_path) / folder
                
                if not folder_path.exists():
                    continue
                
                for entity_file in folder_path.glob('*.md'):
                    try:
                        with open(entity_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check if there are any meeting references
                        if "## Meeting History" in content or "## Meeting References" in content:
                            lines = content.split('\n')
                            has_meetings = False
                            
                            for line in lines:
                                if line.strip().startswith('- [[') and ('.md]]' in line or ']]' in line):
                                    has_meetings = True
                                    break
                            
                            if not has_meetings:
                                # This entity has no meeting references
                                self.logger.warning(f"🗑️  Found orphaned entity: {entity_file.name}")
                                # Uncomment the next line to actually delete orphaned entities
                                # entity_file.unlink()
                                # cleaned_count += 1
                    
                    except Exception as e:
                        log_error(self.logger, f"Error checking entity file {entity_file.name}", e)
            
            if cleaned_count > 0:
                log_success(self.logger, f"Cleaned up {cleaned_count} orphaned entity notes")
            else:
                self.logger.info("🧹 No orphaned entities found")
            
        except Exception as e:
            log_error(self.logger, "Error in cleanup operation", e)
        
        return cleaned_count
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for exports"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")