"""
Health Check Utility for Meeting Processor
Validates system configuration and dependencies
"""

import os
import subprocess
from datetime import datetime
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
    
    def run_diagnostic_report(self) -> str:
        """Generate a detailed diagnostic report"""
        report_lines = [
            "=" * 60,
            "MEETING PROCESSOR DIAGNOSTIC REPORT",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SYSTEM CONFIGURATION",
            "-" * 30,
            f"Vault Path: {self.settings.obsidian_vault_path}",
            f"Input Directory: {self.file_manager.input_dir}",
            f"Output Directory: {self.file_manager.output_dir}",
            f"Processed Directory: {self.file_manager.processed_dir}",
            "",
            "API CONFIGURATION",
            "-" * 30,
            f"OpenAI API Key: {'✓ Configured' if self.settings.openai_api_key else '✗ Not configured'}",
            f"Anthropic API Key: {'✓ Configured' if self.settings.anthropic_api_key else '✗ Not configured'}",
            "",
            "HEALTH CHECK RESULTS",
            "-" * 30
        ]
        
        health_status = self.check_system_health()
        
        for check_name, result in health_status.items():
            if check_name == 'overall_status':
                continue
                
            status = '✓' if result.get('status', False) else '✗'
            report_lines.append(f"{check_name.title()}: {status}")
            
            if 'details' in result:
                for key, value in result['details'].items():
                    report_lines.append(f"  - {key}: {value}")
        
        report_lines.extend([
            "",
            "OVERALL STATUS",
            "-" * 30,
            f"System Health: {health_status['overall_status'].upper()}",
            "",
            "=" * 60
        ])
        
        return "\n".join(report_lines)
    
    def check_file_processing_readiness(self, file_path: Path) -> Dict[str, Any]:
        """Check if system is ready to process a specific file"""
        readiness = {
            'ready': True,
            'issues': []
        }
        
        # Check file exists
        if not file_path.exists():
            readiness['ready'] = False
            readiness['issues'].append(f"File does not exist: {file_path}")
            return readiness
        
        # Check file is MP4
        if file_path.suffix.lower() != '.mp4':
            readiness['ready'] = False
            readiness['issues'].append(f"File is not an MP4: {file_path.suffix}")
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb == 0:
            readiness['ready'] = False
            readiness['issues'].append("File is empty")
        elif file_size_mb > 1000:  # Warn for files over 1GB
            readiness['issues'].append(f"File is very large ({file_size_mb:.1f}MB) - processing may be slow")
        
        # Check API keys
        if not self.settings.openai_api_key:
            readiness['ready'] = False
            readiness['issues'].append("OpenAI API key not configured - cannot transcribe")
        
        if not self.settings.anthropic_api_key:
            readiness['issues'].append("Anthropic API key not configured - analysis will be limited")
        
        # Check FFmpeg
        ffmpeg_check = self._check_ffmpeg()
        if not ffmpeg_check['status']:
            readiness['ready'] = False
            readiness['issues'].append("FFmpeg not available - cannot convert audio")
        
        # Check vault access
        vault_check = self._check_vault_access()
        if not vault_check['status']:
            readiness['ready'] = False
            readiness['issues'].append("Obsidian vault not accessible")
        
        return readiness
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        stats = {}
        
        try:
            # Count files in directories
            input_files = list(self.file_manager.input_dir.glob("*.mp4"))
            output_files = list(self.file_manager.output_dir.glob("*.md"))
            processed_files = list(self.file_manager.processed_dir.glob("*.mp4"))
            
            stats['file_counts'] = {
                'input_mp4s': len(input_files),
                'output_notes': len(output_files),
                'processed_mp4s': len(processed_files)
            }
            
            # Get directory sizes
            stats['directory_sizes'] = {
                'input': self._get_directory_size(self.file_manager.input_dir),
                'output': self._get_directory_size(self.file_manager.output_dir),
                'processed': self._get_directory_size(self.file_manager.processed_dir)
            }
            
            # Get vault statistics
            vault_path = Path(self.settings.obsidian_vault_path)
            if vault_path.exists():
                stats['vault_stats'] = {
                    'meetings': len(list((vault_path / self.settings.obsidian_folder_path).glob("*.md"))) if (vault_path / self.settings.obsidian_folder_path).exists() else 0,
                    'people': len(list((vault_path / "People").glob("*.md"))) if (vault_path / "People").exists() else 0,
                    'companies': len(list((vault_path / "Companies").glob("*.md"))) if (vault_path / "Companies").exists() else 0,
                    'technologies': len(list((vault_path / "Technologies").glob("*.md"))) if (vault_path / "Technologies").exists() else 0,
                    'tasks': len(list((vault_path / "Tasks").glob("*.md"))) if (vault_path / "Tasks").exists() else 0
                }
            else:
                stats['vault_stats'] = None
                
        except Exception as e:
            self.logger.error(f"Error getting system stats: {e}")
            
        return stats
    
    def _get_directory_size(self, directory: Path) -> str:
        """Get human-readable directory size"""
        try:
            total_size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
            
            # Convert to human-readable format
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    return f"{total_size:.1f} {unit}"
                total_size /= 1024.0
            
            return f"{total_size:.1f} TB"
            
        except Exception:
            return "Unknown"
    
    def verify_dependencies(self) -> Dict[str, Any]:
        """Verify all external dependencies"""
        dependencies = {}
        
        # Check Python packages
        required_packages = [
            'anthropic',
            'openai',
            'watchdog',
            'pydub',
            'python-dotenv',
            'requests',
            'aiofiles'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                dependencies[package] = {'installed': True, 'version': 'Unknown'}
            except ImportError:
                dependencies[package] = {'installed': False, 'version': None}
        
        # Check external tools
        dependencies['ffmpeg'] = self._check_ffmpeg()['details']
        
        return dependencies