"""
Health Check Utility for Meeting Processor
Validates system configuration and dependencies
"""

import subprocess
from pathlib import Path
from typing import Dict, Any
from utils.logger import LoggerMixin


class HealthCheck(LoggerMixin):
    """System health and configuration checker"""
    
    def __init__(self, file_manager, settings):
        self.file_manager = file_manager
        self.settings = settings
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health and configuration"""
        self.logger.info("🏥 Running system health check...")
        
        health_status = {
            'directories': self._check_directories(),
            'api_keys': self._check_api_keys(),
            'vault_access': self._check_vault_access(),
            'ffmpeg': self._check_ffmpeg(),
            'templates': self._check_templates(),
            'overall_status': 'healthy'
        }
        
        # Determine overall status
        critical_checks = ['directories', 'api_keys', 'vault_access', 'ffmpeg']
        for check in critical_checks:
            if not health_status[check]['status']:
                health_status['overall_status'] = 'unhealthy'
                break
        
        self._log_health_summary(health_status)
        return health_status
    
    def _check_directories(self) -> Dict[str, Any]:
        """Check if all required directories exist and are accessible"""
        try:
            directories = {
                'input': self.file_manager.input_dir,
                'output': self.file_manager.output_dir,
                'processed': self.file_manager.processed_dir,
                'vault': Path(self.settings.obsidian_vault_path)
            }
            
            results = {}
            all_good = True
            
            for name, path in directories.items():
                exists = path.exists()
                writable = path.is_dir() and os.access(path, os.W_OK) if exists else False
                results[name] = {
                    'path': str(path),
                    'exists': exists,
                    'writable': writable
                }
                if not exists or not writable:
                    all_good = False
            
            return {
                'status': all_good,
                'details': results
            }
            
        except Exception as e:
            self.logger.error(f"Error checking directories: {e}")
            return {'status': False, 'error': str(e)}
    
    def _check_api_keys(self) -> Dict[str, Any]:
        """Check if API keys are configured"""
        return {
            'status': bool(self.settings.anthropic_api_key),
            'details': {
                'openai': bool(self.settings.openai_api_key),
                'anthropic': bool(self.settings.anthropic_api_key)
            }
        }
    
    def _check_vault_access(self) -> Dict[str, Any]:
        """Check Obsidian vault accessibility"""
        try:
            vault_path = Path(self.settings.obsidian_vault_path)
            meetings_path = vault_path / self.settings.obsidian_folder_path
            
            return {
                'status': vault_path.exists() and vault_path.is_dir(),
                'details': {
                    'vault_exists': vault_path.exists(),
                    'meetings_folder_exists': meetings_path.exists(),
                    'entity_folders': {
                        folder: (vault_path / folder).exists() 
                        for folder in self.settings.entity_folders
                    }
                }
            }
            
        except Exception as e:
            return {'status': False, 'error': str(e)}
    
    def _check_ffmpeg(self) -> Dict[str, Any]:
        """Check if FFmpeg is installed and accessible"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'], 
                capture_output=True, 
                text=True
            )
            
            return {
                'status': result.returncode == 0,
                'details': {
                    'installed': result.returncode == 0,
                    'version': result.stdout.split('\n')[0] if result.returncode == 0 else 'Not found'
                }
            }
            
        except FileNotFoundError:
            return {
                'status': False,
                'details': {'installed': False, 'error': 'FFmpeg not found in PATH'}
            }
    
    def _check_templates(self) -> Dict[str, Any]:
        """Check if required templates exist"""
        try:
            templates_path = Path(self.settings.obsidian_vault_path) / "Templates"
            
            required_templates = [
                'meeting-template.md',
                'task-template.md',
                'person-template.md',
                'company-template.md',
                'technology-template.md'
            ]
            
            template_status = {}
            all_exist = True
            
            for template in required_templates:
                exists = (templates_path / template).exists()
                template_status[template] = exists
                if not exists:
                    all_exist = False
            
            return {
                'status': all_exist,
                'details': template_status
            }
            
        except Exception as e:
            return {'status': False, 'error': str(e)}
    
    def _log_health_summary(self, health_status: Dict[str, Any]):
        """Log health check summary"""
        if health_status['overall_status'] == 'healthy':
            self.logger.info("✅ System health check: ALL SYSTEMS OPERATIONAL")
        else:
            self.logger.warning("⚠️  System health check: ISSUES DETECTED")
        
        # Log details for any failures
        for check, result in health_status.items():
            if check != 'overall_status' and isinstance(result, dict) and not result.get('status', True):
                self.logger.warning(f"   ❌ {check}: FAILED")
                if 'details' in result:
                    self.logger.debug(f"      Details: {result['details']}")