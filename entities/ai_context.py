"""
AI context extraction for Meeting Processor
Extracts intelligent context about entities from meeting transcripts
"""

import json
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING
from utils.logger import LoggerMixin, log_success, log_error, log_warning

if TYPE_CHECKING:
    from core.file_manager import FileManager


class AIContextExtractor(LoggerMixin):
    """Extracts AI-powered context for entities"""
    
    def __init__(self, anthropic_client, file_manager: 'FileManager'):
        self.anthropic_client = anthropic_client
        self.file_manager = file_manager
        self.model = "claude-3-5-sonnet-20241022"
    
    def get_employer_context(self) -> Optional[str]:
        """Find the user's current employer company for context"""
        try:
            companies_path = Path(self.file_manager.obsidian_vault_path) / "Companies"
            if not companies_path.exists():
                return None
                
            # Look for company with "Current Employer: Yes"
            for company_file in companies_path.glob("*.md"):
                try:
                    with open(company_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "**Current Employer:** Yes" in content:
                            company_name = company_file.stem.replace('-', ' ')
                            self.logger.info(f"🏢 Found employer context: {company_name}")
                            return company_name
                except Exception:
                    continue
                    
            return None
        except Exception as e:
            log_error(self.logger, "Error reading employer context", e)
            return None

    def get_meeting_transcript(self, meeting_filename: str) -> Optional[str]:
        """Extract transcript from meeting file for AI analysis"""
        try:
            meeting_path = Path(self.file_manager.obsidian_vault_path) / self.file_manager.obsidian_folder_path / f"{meeting_filename}.md"
            
            if meeting_path.exists():
                with open(meeting_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Extract transcript section
                    if "## Complete Transcript" in content:
                        transcript_start = content.find("## Complete Transcript")
                        transcript_section = content[transcript_start:]
                        return transcript_section[:5000]  # First 5000 chars for analysis
            
            return None
        except Exception as e:
            log_error(self.logger, f"Error reading meeting transcript", e)
            return None

    def get_person_context(self, person_name: str, meeting_filename: str) -> Dict[str, str]:
        """Use AI to extract context about a person from the meeting transcript"""
        try:
            employer = self.get_employer_context() or "our company"
            transcript = self.get_meeting_transcript(meeting_filename)
            
            if not transcript:
                return {"employer": employer}
            
            prompt = f"""Analyze this meeting transcript and extract context about {person_name}. 

My company: {employer}
Person to analyze: {person_name}

Extract only information that is explicitly mentioned or clearly implied in the transcript:
1. Role/Title (if mentioned)
2. Company they work for (if mentioned) 
3. Email or contact info (if mentioned)
4. Their relationship to {employer} (colleague, client contact, vendor rep, partner, prospect)
5. Decision-making authority (if implied)
6. Department or team (if mentioned)
7. Key projects or initiatives they're involved in
8. Important context about them

Transcript excerpt:
{transcript[:3000]}

Return ONLY a JSON object with these fields (empty string if not found):
{{"role": "", "company": "", "email": "", "phone": "", "relationship": "", "authority": "", "department": "", "projects": "", "notes": "", "employer": "{employer}"}}"""

            context = self._get_ai_context(prompt, person_name, "person")
            return context
            
        except Exception as e:
            log_error(self.logger, f"Error getting AI person context for {person_name}", e)
            return {"employer": self.get_employer_context() or "our company"}

    def get_company_context(self, company_name: str, meeting_filename: str) -> Dict[str, str]:
        """Use AI to extract context about a company from the meeting transcript"""
        try:
            employer = self.get_employer_context() or "our company"
            transcript = self.get_meeting_transcript(meeting_filename)
            
            if not transcript:
                return {"employer": employer}
            
            prompt = f"""Analyze this meeting transcript and extract context about {company_name}.

My company: {employer}
Company to analyze: {company_name}

Extract only information that is explicitly mentioned or clearly implied:
1. Industry or business type
2. Relationship to {employer} (client, vendor, partner, competitor, prospect)
3. Size or scale (if mentioned)
4. Location (if mentioned)
5. Current projects or engagement with {employer}
6. Key people mentioned from this company
7. Technologies they use (if mentioned)
8. Business needs or challenges discussed

Transcript excerpt:
{transcript[:3000]}

Return ONLY a JSON object with these fields (empty string if not found):
{{"industry": "", "relationship": "", "size": "", "location": "", "projects": "", "key_contacts": "", "technologies": "", "business_needs": "", "notes": "", "employer": "{employer}"}}"""

            context = self._get_ai_context(prompt, company_name, "company")
            return context
            
        except Exception as e:
            log_error(self.logger, f"Error getting AI company context for {company_name}", e)
            return {"employer": employer}
    
    def get_technology_context(self, tech_name: str, meeting_filename: str) -> Dict[str, str]:
        """Use AI to extract context about a technology from the meeting transcript"""
        try:
            employer = self.get_employer_context() or "our company"
            transcript = self.get_meeting_transcript(meeting_filename)
            
            if not transcript:
                return {"employer": employer}
            
            prompt = f"""Analyze this meeting transcript and extract context about {tech_name}.

My company: {employer}
Technology to analyze: {tech_name}

Extract only information that is explicitly mentioned or clearly implied:
1. How {employer} uses this technology
2. Implementation status (planning, in progress, deployed, evaluating)
3. Use cases or applications discussed
4. Integration points with other systems
5. Business value or benefits mentioned
6. Challenges or issues discussed
7. Who is responsible for this technology
8. Future plans or decisions needed

Transcript excerpt:
{transcript[:3000]}

Return ONLY a JSON object with these fields (empty string if not found):
{{"usage": "", "status": "", "use_cases": "", "integrations": "", "business_value": "", "challenges": "", "owner": "", "future_plans": "", "category": "", "employer": "{employer}"}}"""

            context = self._get_ai_context(prompt, tech_name, "technology")
            return context
            
        except Exception as e:
            log_error(self.logger, f"Error getting AI technology context for {tech_name}", e)
            return {"employer": employer}
    
    def _get_ai_context(self, prompt: str, entity_name: str, entity_type: str) -> Dict[str, str]:
        """Get AI context using Claude"""
        try:
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            
            # Parse JSON response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                context = json.loads(json_str)
                
                relationship = context.get('relationship', 'unknown')
                self.logger.info(f"🧠 AI extracted context for {entity_name}: {relationship}")
                return context
            else:
                log_warning(self.logger, f"No valid JSON in AI response for {entity_name}")
                return {"employer": self.get_employer_context() or "our company"}
            
        except json.JSONDecodeError as e:
            log_error(self.logger, f"Failed to parse AI response JSON for {entity_name}", e)
            return {"employer": self.get_employer_context() or "our company"}
        except Exception as e:
            log_error(self.logger, f"Error getting AI context for {entity_name}", e)
            return {"employer": self.get_employer_context() or "our company"}
    
    def validate_context(self, context: Dict[str, str], entity_type: str) -> bool:
        """Validate that context has expected fields for entity type"""
        required_fields = {
            'person': ['employer', 'relationship'],
            'company': ['employer', 'relationship'],
            'technology': ['employer', 'status']
        }
        
        fields = required_fields.get(entity_type, [])
        
        for field in fields:
            if field not in context:
                return False
        
        return True
    
    def enhance_context_with_history(self, context: Dict[str, str], entity_name: str, entity_type: str) -> Dict[str, str]:
        """Enhance context by checking existing entity notes for additional info"""
        try:
            existing_note = self._find_existing_entity_note(entity_name, entity_type)
            if existing_note:
                with open(existing_note, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                # Extract existing info to enhance context
                enhanced_context = context.copy()
                
                # Look for email in existing note
                if not enhanced_context.get('email') and 'Email:' in existing_content:
                    email_line = [line for line in existing_content.split('\n') if 'Email:' in line]
                    if email_line:
                        email = email_line[0].split('Email:')[1].strip()
                        if email and email != '':
                            enhanced_context['email'] = email
                
                return enhanced_context
            
            return context
            
        except Exception as e:
            log_error(self.logger, f"Error enhancing context for {entity_name}", e)
            return context
    
    def _find_existing_entity_note(self, entity_name: str, entity_type: str) -> Optional[Path]:
        """Find existing entity note"""
        try:
            safe_name = entity_name.replace(' ', '-').replace('/', '-')
            filename = f"{safe_name}.md"
            
            folder_map = {
                'person': 'People',
                'company': 'Companies', 
                'technology': 'Technologies'
            }
            
            folder = folder_map.get(entity_type)
            if not folder:
                return None
            
            entity_path = Path(self.file_manager.obsidian_vault_path) / folder / filename
            return entity_path if entity_path.exists() else None
            
        except Exception:
            return None