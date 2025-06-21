"""
Configuration settings for Meeting Processor
"""

import os
from pathlib import Path
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Centralized configuration management"""
    
    # Agile/Scrum Task Standards
    TASK_STATUSES = ['new', 'ready', 'in_progress', 'in_review', 'done', 'blocked', 'cancelled']
    TASK_PRIORITIES = ['critical', 'high', 'medium', 'low']
    TASK_CATEGORIES = ['technical', 'business', 'process', 'documentation', 'research']
    
    # Task Status Emoji Mapping
    STATUS_EMOJIS = {
        'new': '🆕',
        'ready': '📋',
        'in_progress': '🚀',
        'in_review': '🔍',
        'done': '✅',
        'blocked': '🚫',
        'cancelled': '❌'
    }
    
    # Priority Emoji Mapping
    PRIORITY_EMOJIS = {
        'critical': '🚨',
        'high': '🔥',
        'medium': '⚡',
        'low': '📌'
    }
    
    # Category Emoji Mapping
    CATEGORY_EMOJIS = {
        'technical': '💻',
        'business': '💼',
        'process': '📋',
        'documentation': '📝',
        'research': '🔍'
    }
    
    def __init__(self):
        # API Keys
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')
        
        # Obsidian Configuration
        self.obsidian_vault_path = os.getenv('OBSIDIAN_VAULT_PATH', '/obsidian_vault')
        self.obsidian_folder_path = os.getenv('OBSIDIAN_FOLDER_PATH', 'Meetings')
        
        # User Configuration
        self.obsidian_user_name = os.getenv('OBSIDIAN_USER_NAME', 'Me')
        self.obsidian_company_name = os.getenv('OBSIDIAN_COMPANY_NAME', 'My Company')
        
        # Docker paths
        self.input_dir = os.getenv('INPUT_DIR', '/app/input')
        self.output_dir = os.getenv('OUTPUT_DIR', '/app/output')
        self.processed_dir = os.getenv('PROCESSED_DIR', '/app/processed')
        
        # Entity folders for Obsidian
        self.entity_folders = ['People', 'Companies', 'Technologies', 'Tasks', 'Meta/dashboards']
        
        # Task configuration
        self.task_folder = 'Tasks'
        self.task_dashboard_path = 'Meta/dashboards/Task-Dashboard.md'
        
        # Testing mode
        self.testing_mode = os.getenv('TESTING_MODE', 'false').lower() == 'true'
        
        # Initialize API clients
        self.openai_client = self._init_openai_client()
        self.anthropic_client = self._init_anthropic_client()
        
        # Validate configuration
        self._validate_configuration()
    
    def _init_openai_client(self):
        """Initialize OpenAI client if API key is available"""
        if self.openai_api_key:
            try:
                client = OpenAI(api_key=self.openai_api_key)
                print("✅ OpenAI client initialized")
                return client
            except Exception as e:
                print(f"⚠️  Error initializing OpenAI client: {e}")
                return None
        else:
            print("⚠️  No OpenAI API key found - transcription will not be available")
            return None
    
    def _init_anthropic_client(self):
        """Initialize Anthropic client if API key is available"""
        if self.anthropic_api_key:
            try:
                client = Anthropic(api_key=self.anthropic_api_key)
                print("✅ Anthropic client initialized")
                return client
            except Exception as e:
                print(f"⚠️  Error initializing Anthropic client: {e}")
                return None
        else:
            print("⚠️  No Anthropic API key found - analysis will not be available")
            return None
    
    def _validate_configuration(self):
        """Validate configuration settings"""
        warnings = []
        
        # Check paths
        if not Path(self.obsidian_vault_path).exists():
            warnings.append(f"Obsidian vault path does not exist: {self.obsidian_vault_path}")
        
        # Check API keys
        if not self.openai_api_key and not self.testing_mode:
            warnings.append("OpenAI API key not configured - transcription disabled")
        
        if not self.anthropic_api_key:
            warnings.append("Anthropic API key not configured - AI analysis disabled")
        
        # Check user configuration
        if not self.obsidian_user_name:
            warnings.append("OBSIDIAN_USER_NAME not set - using default 'Me'")
        
        if not self.obsidian_company_name:
            warnings.append("OBSIDIAN_COMPANY_NAME not set - using default 'My Company'")
        
        # Print warnings
        if warnings:
            print("\n⚠️  Configuration Warnings:")
            for warning in warnings:
                print(f"   - {warning}")
            print()
    
    @classmethod
    def get_status_emoji(cls, status: str) -> str:
        """Get emoji for a task status"""
        return cls.STATUS_EMOJIS.get(status.lower(), '📋')
    
    @classmethod
    def get_priority_emoji(cls, priority: str) -> str:
        """Get emoji for a task priority"""
        return cls.PRIORITY_EMOJIS.get(priority.lower(), '📋')
    
    @classmethod
    def get_category_emoji(cls, category: str) -> str:
        """Get emoji for a task category"""
        return cls.CATEGORY_EMOJIS.get(category.lower(), '📝')
    
    def get_config_summary(self) -> dict:
        """Get configuration summary for logging"""
        return {
            'vault_path': self.obsidian_vault_path,
            'user_name': self.obsidian_user_name,
            'company_name': self.obsidian_company_name,
            'testing_mode': self.testing_mode,
            'openai_configured': bool(self.openai_api_key),
            'anthropic_configured': bool(self.anthropic_api_key)
        }