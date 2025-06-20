"""
Entity detection for Meeting Processor
Detects people, companies, and technologies from meeting transcripts using Claude AI
"""

import json
from typing import Dict, List, Set
from utils.logger import LoggerMixin, log_entity_detection, log_error, log_warning


class EntityDetector(LoggerMixin):
    """Detects entities from meeting transcripts using Claude AI"""
    
    def __init__(self, anthropic_client):
        self.anthropic_client = anthropic_client
        self.model = "claude-3-5-sonnet-20241022"
        
        # Technology keywords for better detection accuracy
        self.technology_keywords = {
            'Amazon Connect', 'AWS Lambda', 'Salesforce', 'Lambda', 'Connect',
            'DynamoDB', 'API Gateway', 'CloudFormation', 'S3', 'CloudWatch',
            'OmniFlow', 'SSML', 'IVR', 'CRM', 'Lex', 'Polly', 'Kinesis',
            'Service Cloud', 'Sales Cloud', 'Voice call record', 'Contact flow',
            'React', 'Node.js', 'Python', 'JavaScript', 'Docker', 'Kubernetes',
            'PostgreSQL', 'MySQL', 'Redis', 'MongoDB', 'GraphQL', 'REST API'
        }
        
        # Known false positives to exclude
        self.false_positives = {
            'Cobra', 'Transfer', 'Post', 'Using', 'Make', 'Input', 
            'Call', 'Voice', 'Audio', 'System', 'Record', 'Number',
            'File', 'Data', 'Process', 'Service', 'Application', 'Solution',
            'Platform', 'Network', 'Security', 'Support', 'Management',
            'Development', 'Implementation', 'Configuration', 'Integration'
        }
    
    def detect_all_entities(self, transcript: str, meeting_filename: str) -> Dict[str, List[str]]:
        """Detect all entities using Claude AI for better accuracy"""
        self.logger.info(f"🔍 Starting entity detection for {meeting_filename}")
        
        try:
            prompt = self._build_detection_prompt(transcript)
            
            self.logger.debug("📤 Sending transcript to Claude for entity analysis...")
            
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            entities = self._parse_entity_response(response.content[0].text.strip())
            
            # Enhance with keyword detection for technologies
            entities = self.enhance_with_keyword_detection(entities, transcript)
            
            # Log detailed results
            log_entity_detection(self.logger, entities, meeting_filename)
            
            return entities
            
        except Exception as e:
            log_error(self.logger, f"Error in AI entity detection for {meeting_filename}", e)
            return {'people': [], 'companies': [], 'technologies': []}
    
    def _build_detection_prompt(self, transcript: str) -> str:
        """Build the entity detection prompt"""
        return f"""Analyze this meeting transcript and extract entities. Be very conservative and only extract entities you're confident about.

Extract:
1. PEOPLE: Real person names only (first names, full names, but NOT common words, company names, or generic terms)
2. COMPANIES: Business organizations, clients, vendors (including acronyms like PSA if they refer to companies)
3. TECHNOLOGIES: Software platforms, tools, systems, programming languages, cloud services

Rules:
- Only extract real entities, not common words that happen to be capitalized
- For people: Only actual human names (e.g., "Madison", "John Smith") 
- For companies: Business entities (e.g., "PSA", "Salesforce", "Amazon")
- For technologies: Technical systems and tools (e.g., "Lambda", "Connect", "OmniFlow")
- Be conservative - if unsure, don't include it
- EXCLUDE these known false positives: {', '.join(self.false_positives)}

Transcript:
{transcript}

Return ONLY a JSON object in this exact format:
{{"people": ["name1", "name2"], "companies": ["company1", "company2"], "technologies": ["tech1", "tech2"]}}"""
    
    def _parse_entity_response(self, response_text: str) -> Dict[str, List[str]]:
        """Parse Claude's entity detection response"""
        try:
            self.logger.debug(f"📥 Raw Claude response: {response_text}")
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                entities = json.loads(json_str)
                self.logger.debug(f"✅ Successfully parsed JSON: {json_str}")
            else:
                raise ValueError("No JSON found in response")
            
            # Validate and clean structure
            validated_entities = self._validate_entity_structure(entities)
            
            # Filter out false positives
            filtered_entities = self._filter_false_positives(validated_entities)
            
            return filtered_entities
            
        except (json.JSONDecodeError, ValueError) as e:
            log_error(self.logger, f"Failed to parse Claude's entity response: {e}")
            self.logger.debug(f"Raw response was: {response_text}")
            return {'people': [], 'companies': [], 'technologies': []}
    
    def _validate_entity_structure(self, entities: dict) -> Dict[str, List[str]]:
        """Validate and ensure proper entity structure"""
        required_keys = ['people', 'companies', 'technologies']
        validated = {}
        
        for key in required_keys:
            if key not in entities:
                validated[key] = []
                log_warning(self.logger, f"Missing '{key}' in response, setting to empty list")
            elif not isinstance(entities[key], list):
                validated[key] = []
                log_warning(self.logger, f"'{key}' is not a list, converting to empty list")
            else:
                # Clean up strings in the list
                validated[key] = [str(item).strip() for item in entities[key] if item and str(item).strip()]
        
        return validated
    
    def _filter_false_positives(self, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Filter out known false positives and duplicates"""
        filtered = {}
        
        for category, items in entities.items():
            filtered_items = []
            seen = set()
            
            for item in items:
                # Skip false positives
                if item in self.false_positives:
                    self.logger.debug(f"🚫 Filtered false positive: {item}")
                    continue
                
                # Skip duplicates (case-insensitive)
                item_lower = item.lower()
                if item_lower in seen:
                    self.logger.debug(f"🚫 Filtered duplicate: {item}")
                    continue
                
                # Skip very short names (likely false positives)
                if len(item) < 2:
                    self.logger.debug(f"🚫 Filtered too short: {item}")
                    continue
                
                # Additional filtering for specific categories
                if not self._category_specific_validation(item, category):
                    continue
                
                filtered_items.append(item)
                seen.add(item_lower)
            
            filtered[category] = filtered_items
        
        return filtered
    
    def _category_specific_validation(self, item: str, category: str) -> bool:
        """Apply category-specific validation rules"""
        
        if category == 'people':
            # People should not contain common business terms
            business_terms = {'inc', 'corp', 'llc', 'ltd', 'company', 'solutions', 'systems', 'services'}
            if any(term in item.lower() for term in business_terms):
                self.logger.debug(f"🚫 Filtered business term in person: {item}")
                return False
            
            # People names should not be all caps (likely acronyms)
            if item.isupper() and len(item) > 1:
                self.logger.debug(f"🚫 Filtered all-caps name: {item}")
                return False
        
        elif category == 'companies':
            # Companies should not be common words
            common_words = {'meeting', 'call', 'team', 'project', 'client', 'customer'}
            if item.lower() in common_words:
                self.logger.debug(f"🚫 Filtered common word in company: {item}")
                return False
        
        elif category == 'technologies':
            # Technologies should not be common business terms
            if item.lower() in {'email', 'phone', 'website', 'document', 'report', 'presentation'}:
                self.logger.debug(f"🚫 Filtered common term in technology: {item}")
                return False
        
        return True
    
    def enhance_with_keyword_detection(self, entities: Dict[str, List[str]], transcript: str) -> Dict[str, List[str]]:
        """Enhance entity detection with keyword-based detection for technologies"""
        enhanced = entities.copy()
        
        # Look for known technology keywords that might have been missed
        transcript_lower = transcript.lower()
        detected_techs = set(item.lower() for item in enhanced['technologies'])
        
        for tech_keyword in self.technology_keywords:
            if (tech_keyword.lower() in transcript_lower and 
                tech_keyword.lower() not in detected_techs):
                
                # Verify it appears as a proper entity (not part of another word)
                import re
                pattern = r'\b' + re.escape(tech_keyword.lower()) + r'\b'
                if re.search(pattern, transcript_lower):
                    enhanced['technologies'].append(tech_keyword)
                    self.logger.debug(f"🔍 Added keyword-detected tech: {tech_keyword}")
        
        return enhanced
    
    def detect_entity_relationships(self, entities: Dict[str, List[str]], transcript: str) -> Dict[str, Dict[str, List[str]]]:
        """Detect relationships between entities mentioned together"""
        relationships = {
            'person_company': {},  # person -> [companies]
            'person_technology': {},  # person -> [technologies]
            'company_technology': {}  # company -> [technologies]
        }
        
        try:
            # Simple co-occurrence detection
            transcript_sentences = transcript.split('.')
            
            for person in entities['people']:
                relationships['person_company'][person] = []
                relationships['person_technology'][person] = []
                
                for sentence in transcript_sentences:
                    if person.lower() in sentence.lower():
                        # Look for companies in same sentence
                        for company in entities['companies']:
                            if company.lower() in sentence.lower():
                                relationships['person_company'][person].append(company)
                        
                        # Look for technologies in same sentence
                        for tech in entities['technologies']:
                            if tech.lower() in sentence.lower():
                                relationships['person_technology'][person].append(tech)
            
            for company in entities['companies']:
                relationships['company_technology'][company] = []
                
                for sentence in transcript_sentences:
                    if company.lower() in sentence.lower():
                        for tech in entities['technologies']:
                            if tech.lower() in sentence.lower():
                                relationships['company_technology'][company].append(tech)
            
            # Remove duplicates
            for rel_type in relationships:
                for entity in relationships[rel_type]:
                    relationships[rel_type][entity] = list(set(relationships[rel_type][entity]))
            
            self.logger.debug(f"🔗 Detected entity relationships: {sum(len(v) for rel in relationships.values() for v in rel.values())} connections")
            
        except Exception as e:
            log_error(self.logger, "Error detecting entity relationships", e)
        
        return relationships
    
    def get_entity_statistics(self, entities: Dict[str, List[str]]) -> Dict[str, int]:
        """Get statistics about detected entities"""
        stats = {}
        for category, items in entities.items():
            stats[category] = len(items)
        stats['total'] = sum(stats.values())
        return stats
    
    def validate_entities(self, entities: Dict[str, List[str]]) -> bool:
        """Validate that entities dict has proper structure"""
        required_keys = ['people', 'companies', 'technologies']
        
        if not isinstance(entities, dict):
            return False
        
        for key in required_keys:
            if key not in entities:
                return False
            if not isinstance(entities[key], list):
                return False
        
        return True
    
    def get_confidence_score(self, entities: Dict[str, List[str]], transcript: str) -> float:
        """Calculate confidence score for entity detection"""
        try:
            total_entities = sum(len(items) for items in entities.values())
            
            if total_entities == 0:
                return 0.0
            
            # Calculate based on various factors
            factors = []
            
            # Factor 1: Keyword match rate for technologies
            tech_keywords_found = 0
            for tech in entities['technologies']:
                if tech in self.technology_keywords:
                    tech_keywords_found += 1
            
            if entities['technologies']:
                tech_confidence = tech_keywords_found / len(entities['technologies'])
                factors.append(tech_confidence)
            
            # Factor 2: Entity distribution (balanced is better)
            distribution_score = 1.0 - abs(0.33 - len(entities['people'])/total_entities) - abs(0.33 - len(entities['companies'])/total_entities) - abs(0.33 - len(entities['technologies'])/total_entities)
            factors.append(max(0.0, distribution_score))
            
            # Factor 3: No obvious false positives
            false_positive_penalty = 0.0
            for category, items in entities.items():
                for item in items:
                    if item in self.false_positives:
                        false_positive_penalty += 0.1
            
            false_positive_score = max(0.0, 1.0 - false_positive_penalty)
            factors.append(false_positive_score)
            
            # Calculate overall confidence
            confidence = sum(factors) / len(factors) if factors else 0.0
            
            self.logger.debug(f"📊 Entity detection confidence: {confidence:.2f}")
            return confidence
            
        except Exception as e:
            log_error(self.logger, "Error calculating confidence score", e)
            return 0.0
    
    def export_entities_summary(self, entities: Dict[str, List[str]], meeting_filename: str) -> str:
        """Export a summary of detected entities"""
        try:
            summary_lines = [
                f"# Entity Detection Summary - {meeting_filename}",
                f"",
                f"**Detection Date:** {self._get_current_timestamp()}",
                f"**Total Entities:** {sum(len(items) for items in entities.values())}",
                f"",
                f"## People ({len(entities['people'])})",
            ]
            
            if entities['people']:
                for person in sorted(entities['people']):
                    summary_lines.append(f"- {person}")
            else:
                summary_lines.append("- None detected")
            
            summary_lines.extend([
                f"",
                f"## Companies ({len(entities['companies'])})",
            ])
            
            if entities['companies']:
                for company in sorted(entities['companies']):
                    summary_lines.append(f"- {company}")
            else:
                summary_lines.append("- None detected")
            
            summary_lines.extend([
                f"",
                f"## Technologies ({len(entities['technologies'])})",
            ])
            
            if entities['technologies']:
                for tech in sorted(entities['technologies']):
                    summary_lines.append(f"- {tech}")
            else:
                summary_lines.append("- None detected")
            
            confidence = self.get_confidence_score(entities, "")
            summary_lines.extend([
                f"",
                f"## Detection Quality",
                f"- **Confidence Score:** {confidence:.2f}/1.00",
                f"- **Model Used:** {self.model}",
                f"",
                f"---",
                f"*Generated by Meeting Processor Entity Detection*"
            ])
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            log_error(self.logger, "Error exporting entities summary", e)
            return f"Error generating summary: {str(e)}"
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for exports"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")