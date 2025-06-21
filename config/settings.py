"""
Configuration settings for Meeting Processor
Includes API key validation and comprehensive error handling
"""

import os
import sys
from pathlib import Path
from typing import Optional
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass


class Settings:
    """Centralized configuration management with validation"""
    
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
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '').strip()
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
        
        # Obsidian Configuration
        self.obsidian_vault_path = os.getenv('OBSIDIAN_VAULT_PATH', '/obsidian_vault')
        self.obsidian_folder_path = os.getenv('OBSIDIAN_FOLDER_PATH', 'Meetings')
        
        # User Configuration
        self.obsidian_user_name = os.getenv('OBSIDIAN_USER_NAME', '').strip()
        self.obsidian_company_name = os.getenv('OBSIDIAN_COMPANY_NAME', '').strip()
        
        # Docker paths
        self.input_dir = os.getenv('INPUT_DIR', '/app/input')
        self.output_dir = os.getenv('OUTPUT_DIR', '/app/output')
        self.processed_dir = os.getenv('PROCESSED_DIR', '/app/processed')
        
        # Entity folders for Obsidian
        self.entity_folders = ['People', 'Companies', 'Technologies']
        
        # Task configuration
        self.task_folder = 'Tasks'
        self.task_dashboard_path = 'Meta/dashboards/Task-Dashboard.md'
        
        # Testing mode
        self.testing_mode = os.getenv('TESTING_MODE', 'false').lower() == 'true'
        
        # Performance settings (for dashboard updates)
        self.dashboard_update_thresholds = {
            'high_priority_tasks': 2,
            'urgent_tasks': 1,
            'new_companies': 2,
            'new_people': 3,
            'total_tasks': 5,
            'hours_between_updates': 6
        }
        
        # Validate configuration before initializing clients
        self._validate_configuration()
        
        # Initialize API clients
        self.openai_client = self._init_openai_client()
        self.anthropic_client = self._init_anthropic_client()
        
        # Print configuration summary
        self._print_configuration_summary()
    
    def _validate_configuration(self):
        """Validate all configuration settings"""
        print("🔍 Validating configuration...")
        
        # Validate API keys
        self._validate_api_keys()
        
        # Validate paths
        self._validate_paths()
        
        # Validate Obsidian settings
        self._validate_obsidian_settings()
        
        print("✅ Configuration validation passed")
    
    def _validate_api_keys(self):
        """Validate API key formats and warn about missing keys"""
        errors = []
        warnings = []
        
        # OpenAI API Key Validation
        if self.openai_api_key:
            if not self.openai_api_key.startswith('sk-'):
                errors.append(
                    "Invalid OpenAI API key format. "
                    "OpenAI keys should start with 'sk-'. "
                    "Please check your OPENAI_API_KEY in .env file."
                )
            elif len(self.openai_api_key) < 20:
                errors.append(
                    "OpenAI API key appears too short. "
                    "Please ensure you copied the complete key."
                )
            else:
                print("✅ OpenAI API key format validated")
        else:
            warnings.append(
                "No OpenAI API key found. "
                "Transcription features will be disabled."
            )
        
        # Anthropic API Key Validation
        if self.anthropic_api_key:
            # Anthropic keys can start with 'sk-ant-' or sometimes just 'sk-'
            if not (self.anthropic_api_key.startswith('sk-ant-') or 
                    self.anthropic_api_key.startswith('sk-')):
                errors.append(
                    "Invalid Anthropic API key format. "
                    "Anthropic keys should start with 'sk-ant-' or 'sk-'. "
                    "Please check your ANTHROPIC_API_KEY in .env file."
                )
            elif len(self.anthropic_api_key) < 20:
                errors.append(
                    "Anthropic API key appears too short. "
                    "Please ensure you copied the complete key."
                )
            else:
                print("✅ Anthropic API key format validated")
        else:
            warnings.append(
                "No Anthropic API key found. "
                "Analysis and entity detection features will be disabled."
            )
        
        # Check for swapped keys (common mistake)
        if (self.openai_api_key.startswith('sk-ant-') or 
            self.anthropic_api_key.startswith('sk-') and not self.anthropic_api_key.startswith('sk-ant-')):
            errors.append(
                "API keys may be swapped! "
                "Please verify that OpenAI and Anthropic keys are in the correct fields."
            )
        
        # Print warnings
        for warning in warnings:
            print(f"⚠️  {warning}")
        
        # Raise error if any validation failed
        if errors:
            error_message = "\n".join([f"❌ {error}" for error in errors])
            raise ConfigurationError(
                f"\nConfiguration Errors Found:\n{error_message}\n\n"
                "Please fix these issues in your .env file and restart."
            )
    
    def _validate_paths(self):
        """Validate that required paths exist or can be created"""
        # Validate Obsidian vault path
        vault_path = Path(self.obsidian_vault_path)
        if not vault_path.exists():
            raise ConfigurationError(
                f"❌ Obsidian vault path does not exist: {self.obsidian_vault_path}\n"
                "Please check your OBSIDIAN_VAULT_PATH in .env file."
            )
        
        if not vault_path.is_dir():
            raise ConfigurationError(
                f"❌ Obsidian vault path is not a directory: {self.obsidian_vault_path}"
            )
        
        # Check if we can write to the vault
        test_file = vault_path / '.meeting_processor_test'
        try:
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            raise ConfigurationError(
                f"❌ Cannot write to Obsidian vault: {self.obsidian_vault_path}\n"
                f"Error: {str(e)}"
            )
        
        print(f"✅ Obsidian vault path validated: {self.obsidian_vault_path}")
        
        # Docker paths will be created if they don't exist
        for path_name, path_value in [
            ('Input', self.input_dir),
            ('Output', self.output_dir),
            ('Processed', self.processed_dir)
        ]:
            path_obj = Path(path_value)
            if not path_obj.exists():
                print(f"📁 {path_name} directory will be created: {path_value}")
    
    def _validate_obsidian_settings(self):
        """Validate Obsidian-specific settings"""
        # Check if required folders exist in vault
        vault_path = Path(self.obsidian_vault_path)
        
        # Check for Meta folder structure
        meta_path = vault_path / "Meta"
        if not meta_path.exists():
            print("📁 Meta folder will be created in Obsidian vault")
        
        dashboards_path = meta_path / "dashboards"
        if not dashboards_path.exists():
            print("📁 Meta/dashboards folder will be created")
        
        templates_path = meta_path / "templates"
        if not templates_path.exists():
            print("📁 Meta/templates folder will be created")
        
        # Validate folder name
        if not self.obsidian_folder_path:
            raise ConfigurationError(
                "❌ OBSIDIAN_FOLDER_PATH cannot be empty. "
                "Please specify a folder name for meeting notes (e.g., 'Meetings')."
            )
        
        # Check for invalid characters in folder name
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in self.obsidian_folder_path for char in invalid_chars):
            raise ConfigurationError(
                f"❌ OBSIDIAN_FOLDER_PATH contains invalid characters: {self.obsidian_folder_path}\n"
                f"Please avoid these characters: {' '.join(invalid_chars)}"
            )
        
        print(f"✅ Obsidian folder path validated: {self.obsidian_folder_path}")
    
    def _init_openai_client(self) -> Optional[OpenAI]:
        """Initialize OpenAI client if API key is available"""
        if self.openai_api_key:
            try:
                client = OpenAI(api_key=self.openai_api_key)
                # Test the client with a minimal API call
                if not self.testing_mode:
                    self._test_openai_client(client)
                print("✅ OpenAI client initialized successfully")
                return client
            except Exception as e:
                print(f"❌ Failed to initialize OpenAI client: {str(e)}")
                print("⚠️  Transcription features will be disabled")
                return None
        else:
            print("⚠️  No OpenAI API key - transcription will not be available")
            return None
    
    def _init_anthropic_client(self) -> Optional[Anthropic]:
        """Initialize Anthropic client if API key is available"""
        if self.anthropic_api_key:
            try:
                client = Anthropic(api_key=self.anthropic_api_key)
                # Test the client with a minimal API call
                if not self.testing_mode:
                    self._test_anthropic_client(client)
                print("✅ Anthropic client initialized successfully")
                return client
            except Exception as e:
                print(f"❌ Failed to initialize Anthropic client: {str(e)}")
                print("⚠️  Analysis features will be disabled")
                return None
        else:
            print("⚠️  No Anthropic API key - analysis will not be available")
            return None
    
    def _test_openai_client(self, client: OpenAI):
        """Test OpenAI client with a minimal API call"""
        try:
            # Just list models to verify authentication
            models = client.models.list()
            # If we get here, the API key is valid
        except Exception as e:
            if "authentication" in str(e).lower() or "api key" in str(e).lower():
                raise ConfigurationError(
                    f"❌ OpenAI API key authentication failed: {str(e)}\n"
                    "Please verify your OPENAI_API_KEY is correct."
                )
            # Other errors might be network issues, ignore for now
            print(f"⚠️  Could not verify OpenAI API key (network issue?): {str(e)}")
    
    def _test_anthropic_client(self, client: Anthropic):
        """Test Anthropic client with a minimal API call"""
        try:
            # Send a minimal message to test authentication
            response = client.messages.create(
                model="claude-3-haiku-20240307",  # Cheapest model for testing
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            # If we get here, the API key is valid
        except Exception as e:
            if "authentication" in str(e).lower() or "api_key" in str(e).lower():
                raise ConfigurationError(
                    f"❌ Anthropic API key authentication failed: {str(e)}\n"
                    "Please verify your ANTHROPIC_API_KEY is correct."
                )
            # Other errors might be network issues, ignore for now
            print(f"⚠️  Could not verify Anthropic API key (network issue?): {str(e)}")
    
    def _print_configuration_summary(self):
        """Print configuration summary"""
        print("\n📋 Configuration Summary:")
        print("=" * 50)
        print(f"OpenAI Available: {'✅' if self.openai_client else '❌'}")
        print(f"Anthropic Available: {'✅' if self.anthropic_client else '❌'}")
        print(f"Vault Path: {self.obsidian_vault_path}")
        print(f"Meetings Folder: {self.obsidian_folder_path}")
        print(f"Testing Mode: {'ON' if self.testing_mode else 'OFF'}")
        if self.obsidian_user_name:
            print(f"User: {self.obsidian_user_name}")
        if self.obsidian_company_name:
            print(f"Company: {self.obsidian_company_name}")
        print("=" * 50)
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
    
    def get_dashboard_threshold(self, threshold_name: str) -> int:
        """Get dashboard update threshold value"""
        return self.dashboard_update_thresholds.get(threshold_name, 1)