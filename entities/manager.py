"""
Entity Manager for Obsidian Notes
Creates and manages entity notes with AI context
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from utils.logger import LoggerMixin, log_success, log_error
from entities.ai_context import AIContextExtractor


class ObsidianEntityManager(LoggerMixin):
    """Manages entity notes in Obsidian with AI-powered context"""
    
    def __init__(self, file_manager, anthropic_client):
        self.file_manager = file_manager
        self.anthropic_client = anthropic_client
        self.ai_context = AIContextExtractor(anthropic_client)
        self.vault_path = Path(file_manager.obsidian_vault_path)
        
        # Ensure entity folders exist
        for folder in ['People', 'Companies', 'Technologies']:
            (self.vault_path / folder).mkdir(parents=True, exist_ok=True)
    
    def create_entity_notes(self, entities: Dict[str, List[str]], meeting_filename: str, 
                          meeting_date: str) -> Dict[str, List[str]]:
        """Create or update entity notes with AI context"""
        try:
            self.logger.info("🏗️  Starting AI-powered entity note creation...")
            
            entity_links = {
                'people': [],
                'companies': [],
                'technologies': []
            }
            
            # Process each entity type
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    entity_path = self._create_or_update_entity_note(
                        entity, entity_type, meeting_filename, meeting_date
                    )
                    
                    if entity_path:
                        # Create wiki-style link
                        link = f"[[{entity_type.capitalize()}/{entity}|{entity}]]"
                        entity_links[entity_type].append(link)
            
            total_entities = sum(len(links) for links in entity_links.values())
            self.logger.info(f"✅ Created {total_entities} smart entity links with AI context")
            
            return entity_links
            
        except Exception as e:
            log_error(self.logger, "Error creating entity notes", e)
            return {'people': [], 'companies': [], 'technologies': []}
    
    def _create_or_update_entity_note(self, entity_name: str, entity_type: str, 
                                    meeting_filename: str, meeting_date: str) -> Optional[Path]:
        """Create or update a single entity note with AI context"""
        try:
            # Determine folder based on entity type
            folder_map = {
                'people': 'People',
                'companies': 'Companies',
                'technologies': 'Technologies'
            }
            
            folder = folder_map.get(entity_type, 'Entities')
            entity_folder = self.vault_path / folder
            entity_folder.mkdir(parents=True, exist_ok=True)
            
            # Sanitize entity name for filename
            safe_entity_name = re.sub(r'[^\w\s-]', '', entity_name)
            safe_entity_name = re.sub(r'\s+', '-', safe_entity_name.strip())
            
            entity_path = entity_folder / f"{safe_entity_name}.md"
            
            # Check if entity note already exists
            if entity_path.exists():
                # Update existing note
                self._update_entity_note(entity_path, meeting_filename, meeting_date)
            else:
                # Create new note with AI context
                ai_context = self.ai_context.extract_entity_context(
                    entity_name, entity_type, meeting_filename
                )
                
                content = self._generate_entity_note_content(
                    entity_name, entity_type, ai_context, meeting_filename, meeting_date
                )
                
                with open(entity_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.logger.info(f"✅ Created AI-enhanced entity note: {folder}/{safe_entity_name}.md")
                log_success(self.logger, f"Created new {entity_type[:-1]} note: {entity_name}")
            
            return entity_path
            
        except Exception as e:
            log_error(self.logger, f"Error creating entity note for {entity_name}", e)
            return None
    
    def _generate_entity_note_content(self, entity_name: str, entity_type: str, 
                                    ai_context: Dict, meeting_filename: str, 
                                    meeting_date: str) -> str:
        """Generate simplified entity note content"""
        
        if entity_type == 'people':
            return self._generate_person_note(entity_name, ai_context, meeting_filename, meeting_date)
        elif entity_type == 'companies':
            return self._generate_company_note(entity_name, ai_context, meeting_filename, meeting_date)
        elif entity_type == 'technologies':
            return self._generate_technology_note(entity_name, ai_context, meeting_filename, meeting_date)
        else:
            return self._generate_generic_entity_note(entity_name, entity_type, ai_context, 
                                                    meeting_filename, meeting_date)
    
    def _generate_person_note(self, name: str, context: Dict, meeting_filename: str, 
                            meeting_date: str) -> str:
        """Generate simplified person note"""
        
        # Extract context with defaults
        company = context.get('company', '')
        role = context.get('role', '')
        email = context.get('email', '')
        summary = context.get('summary', f'{name} was mentioned in a meeting.')
        
        content = f"""# {name}

**Company:** {company}
**Role:** {role}
**Email:** {email}
**Last Contact:** {meeting_date}

## About
{summary}

## Active Tasks
```dataview
TABLE WITHOUT ID
  file.link as Task,
  status as Status,
  priority as Priority,
  due_date as "Due Date"
FROM "Tasks"
WHERE assigned_to = this.file.name OR contains(assigned_to, "{name}")
WHERE status != "done" AND status != "cancelled"
SORT priority DESC
```

## Meeting History
<!-- Auto-updated by meeting processor -->
- [[{meeting_filename}]] - {meeting_date}

```dataview
TABLE WITHOUT ID 
  file.link as "Meeting",
  date as "Date",
  type as "Type"
FROM "Meetings"
WHERE contains(file.outlinks, this.file.link)
SORT date DESC
LIMIT 10
```

## Notes
<!-- Additional context and observations -->

---
**Tags:** #person #contact
**Created:** {meeting_date}
**Source:** Auto-generated from meeting transcript
"""
        return content
    
    def _generate_company_note(self, company: str, context: Dict, meeting_filename: str, 
                             meeting_date: str) -> str:
        """Generate simplified company note"""
        
        # Extract context
        industry = context.get('industry', '')
        relationship = context.get('relationship_to_employer', 'Unknown')
        summary = context.get('summary', f'{company} was discussed in a meeting.')
        technologies_used = context.get('technologies_used', [])
        
        tech_list = '\n'.join([f"- {tech}" for tech in technologies_used]) if technologies_used else ""
        
        content = f"""# {company}

**Industry:** {industry}
**Relationship:** {relationship}
**Status:** Active
**Website:** 

## Overview
{summary}

## Key Contacts
```dataview
TABLE WITHOUT ID
  file.link as "Person",
  role as "Role",
  email as "Email"
FROM "People"
WHERE company = "{company}"
SORT role ASC
```

## Active Projects & Tasks
```dataview
TABLE WITHOUT ID
  file.link as Task,
  status as Status,
  priority as Priority,
  due_date as "Due Date"
FROM "Tasks"
WHERE contains(file.content, "{company}")
WHERE status != "done" AND status != "cancelled"
SORT priority DESC
```

## Meeting History
<!-- Auto-updated by meeting processor -->
- [[{meeting_filename}]] - {meeting_date}

```dataview
TABLE WITHOUT ID
  file.link as "Meeting",
  date as "Date",
  type as "Type"
FROM "Meetings"
WHERE contains(file.outlinks, this.file.link)
SORT date DESC
LIMIT 10
```

## Technologies Used
{tech_list}

```dataview
LIST
FROM "Technologies"
WHERE contains(file.inlinks, this.file.link)
```

---
**Tags:** #company #{relationship.lower().replace(' ', '-')}
**Created:** {meeting_date}
"""
        return content
    
    def _generate_technology_note(self, technology: str, context: Dict, meeting_filename: str, 
                                meeting_date: str) -> str:
        """Generate simplified technology note"""
        
        # Extract context
        category = context.get('category', 'tool')
        status = context.get('current_status', 'in use')
        summary = context.get('summary', f'{technology} was referenced in a meeting.')
        use_cases = context.get('use_cases', [])
        
        use_case_list = '\n'.join([f"- {uc}" for uc in use_cases]) if use_cases else ""
        
        content = f"""# {technology}

**Category:** {category}
**Status:** {status}
**Owner:** 

## Overview
{summary}

## Current Usage
{use_case_list}

## Related Tasks
```dataview
TABLE WITHOUT ID
  file.link as Task,
  status as Status,
  priority as Priority
FROM "Tasks"
WHERE contains(file.content, "{technology}")
WHERE status != "done"
SORT priority DESC
```

## Implementation History
<!-- Auto-updated by meeting processor -->
- [[{meeting_filename}]] - {meeting_date}

```dataview
TABLE WITHOUT ID
  file.link as "Meeting",
  date as "Date"
FROM "Meetings"
WHERE contains(file.outlinks, this.file.link)
SORT date DESC
LIMIT 10
```

---
**Tags:** #technology #{category.lower().replace(' ', '-')}
**Created:** {meeting_date}
"""
        return content
    
    def _generate_generic_entity_note(self, entity_name: str, entity_type: str, 
                                    context: Dict, meeting_filename: str, 
                                    meeting_date: str) -> str:
        """Generate generic entity note for unknown types"""
        
        summary = context.get('summary', f'{entity_name} was mentioned in a meeting.')
        
        content = f"""# {entity_name}

**Type:** {entity_type.title()}
**Status:** Active
**First Detected:** {meeting_date}

## Overview
{summary}

## Meeting History
<!-- Auto-updated by meeting processor -->
- [[{meeting_filename}]] - {meeting_date}

```dataview
TABLE WITHOUT ID
  file.link as "Meeting",
  date as "Date"
FROM "Meetings"
WHERE contains(file.text, "{entity_name}")
SORT date DESC
```

## Related Tasks
```dataview
LIST
FROM "Tasks"
WHERE contains(file.text, "{entity_name}")
WHERE status != "done"
SORT priority DESC
```

---
**Tags:** #entity #{entity_type}
**Created:** {meeting_date}
"""
        return content
    
    def _update_entity_note(self, entity_path: Path, meeting_filename: str, meeting_date: str):
        """Update existing entity note with new meeting reference"""
        try:
            with open(entity_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the meeting history section
            meeting_link = f"- [[{meeting_filename}]] - {meeting_date}"
            
            # Check if this meeting is already linked
            if meeting_filename not in content:
                # Find where to insert the new meeting link
                history_match = re.search(r'## Meeting History\n(.*?)(?=\n##|\n```|\Z)', 
                                        content, re.DOTALL)
                
                if history_match:
                    # Insert after the comment line
                    insert_pos = content.find('<!-- Auto-updated by meeting processor -->')
                    if insert_pos > 0:
                        # Find the end of this line
                        line_end = content.find('\n', insert_pos)
                        if line_end > 0:
                            # Insert the new meeting link
                            new_content = (
                                content[:line_end + 1] +
                                meeting_link + '\n' +
                                content[line_end + 1:]
                            )
                            
                            # Update last contact date if it's a person
                            if '/People/' in str(entity_path):
                                new_content = re.sub(
                                    r'\*\*Last Contact:\*\* .*',
                                    f'**Last Contact:** {meeting_date}',
                                    new_content
                                )
                            
                            # Write updated content
                            with open(entity_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            
                            self.logger.debug(f"Updated entity note: {entity_path.name}")
            
        except Exception as e:
            log_error(self.logger, f"Error updating entity note {entity_path}", e)
    
    def update_meeting_note_with_entities(self, meeting_path: Path, entity_links: Dict[str, List[str]]):
        """Update meeting note with entity links"""
        try:
            with open(meeting_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update people section
            if entity_links.get('people'):
                people_str = ', '.join(entity_links['people'])
                content = re.sub(
                    r'(\*\*People:\*\*).*',
                    f'\\1 {people_str}',
                    content
                )
            
            # Update companies section
            if entity_links.get('companies'):
                companies_str = ', '.join(entity_links['companies'])
                content = re.sub(
                    r'(\*\*Companies:\*\*).*',
                    f'\\1 {companies_str}',
                    content
                )
            
            # Update technologies section
            if entity_links.get('technologies'):
                tech_str = ', '.join(entity_links['technologies'])
                content = re.sub(
                    r'(\*\*Technologies:\*\*).*',
                    f'\\1 {tech_str}',
                    content
                )
            
            # Write updated content
            with open(meeting_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            total_links = sum(len(links) for links in entity_links.values())
            self.logger.info(f"✅ Updated meeting note with {total_links} AI-enhanced entity links")
            
        except Exception as e:
            log_error(self.logger, "Error updating meeting note with entities", e)