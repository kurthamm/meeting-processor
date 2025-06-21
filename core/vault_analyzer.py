"""
Vault Analyzer for Dashboard Generator - COMPLETE OPTIMIZED VERSION
Handles all data analysis from vault files with caching and async operations
"""

import asyncio
import aiofiles
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from functools import lru_cache
from utils.logger import LoggerMixin
from .content_parser import ContentParser


class CachedFileData:
    """Represents cached file metadata and content"""
    def __init__(self, path: Path, mtime: float, content: str, metadata: Dict[str, Any]):
        self.path = path
        self.mtime = mtime
        self.content = content
        self.metadata = metadata
        self.cache_time = datetime.now()


class VaultAnalyzer(LoggerMixin):
    """Analyzes vault data to extract intelligence for dashboards - COMPLETE OPTIMIZED VERSION"""
    
    def __init__(self, vault_path: Path, obsidian_folder_path: str):
        self.vault_path = vault_path
        self.obsidian_folder_path = obsidian_folder_path
        self.parser = ContentParser()
        
        # Cache configuration
        self._file_cache: Dict[str, CachedFileData] = {}
        self._cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes
        self._max_cache_size = 1000  # Maximum files to cache
        
        # Performance settings
        self._max_workers = 4  # Thread pool size
        self._batch_size = 50  # Files to process in each batch
        
        # Cache statistics
        self._cache_hits = 0
        self._cache_misses = 0
    
    def analyze_meetings(self) -> Dict[str, Any]:
        """Synchronous wrapper for backward compatibility"""
        return asyncio.run(self.analyze_meetings_async())
    
    async def analyze_meetings_async(self) -> Dict[str, Any]:
        """Analyze recent meetings and patterns using async I/O"""
        meetings_path = self.vault_path / self.obsidian_folder_path
        
        if not meetings_path.exists():
            return {'total': 0, 'recent': [], 'patterns': {}}
        
        meeting_files = list(meetings_path.glob("*.md"))
        self.logger.info(f"🔍 Analyzing {len(meeting_files)} meeting files...")
        
        # Process files in batches
        recent_meetings = []
        now = datetime.now()
        
        # Use asyncio to read files concurrently
        tasks = []
        for batch_start in range(0, len(meeting_files), self._batch_size):
            batch_end = min(batch_start + self._batch_size, len(meeting_files))
            batch = meeting_files[batch_start:batch_end]
            tasks.append(self._process_meeting_batch(batch, now))
        
        # Gather results
        batch_results = await asyncio.gather(*tasks)
        for batch_result in batch_results:
            recent_meetings.extend(batch_result)
        
        # Sort by most recent
        recent_meetings.sort(key=lambda x: x['days_ago'])
        
        # Log cache performance
        self._log_cache_stats()
        
        return {
            'total': len(meeting_files),
            'recent': recent_meetings[:10],
            'this_week': len([m for m in recent_meetings if m['days_ago'] <= 7]),
            'this_month': len(recent_meetings)
        }
    
    async def _process_meeting_batch(self, meeting_files: List[Path], now: datetime) -> List[Dict[str, Any]]:
        """Process a batch of meeting files concurrently"""
        tasks = []
        for meeting_file in meeting_files:
            tasks.append(self._analyze_single_meeting(meeting_file, now))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_results = []
        for result in results:
            if isinstance(result, dict) and result:
                valid_results.append(result)
            elif isinstance(result, Exception):
                self.logger.debug(f"Error processing meeting: {result}")
        
        return valid_results
    
    async def _analyze_single_meeting(self, meeting_file: Path, now: datetime) -> Optional[Dict[str, Any]]:
        """Analyze a single meeting file with caching"""
        try:
            # Check cache first
            cached_data = self._get_cached_file(meeting_file)
            
            if cached_data:
                # Use cached metadata
                date_match = cached_data.metadata.get('date')
                title = cached_data.metadata.get('title')
            else:
                # Read file asynchronously
                async with aiofiles.open(meeting_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                
                # Extract metadata
                date_match = self.parser.extract_date_from_filename(meeting_file.name)
                title = self.parser.extract_meeting_title(meeting_file)
                
                # Cache the result
                metadata = {'date': date_match, 'title': title}
                self._cache_file(meeting_file, content, metadata)
            
            if date_match:
                meeting_date = datetime.strptime(date_match, "%Y-%m-%d")
                days_ago = (now - meeting_date).days
                
                if days_ago <= 30:
                    return {
                        'file': meeting_file.name,
                        'date': date_match,
                        'days_ago': days_ago,
                        'title': title
                    }
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error analyzing meeting {meeting_file.name}: {e}")
            return None
    
    def analyze_tasks(self) -> Dict[str, Any]:
        """Analyze task status using parallel processing"""
        tasks_path = self.vault_path / "Tasks"
        
        if not tasks_path.exists():
            return {'total': 0, 'by_status': {}, 'urgent': []}
        
        task_files = list(tasks_path.glob("*.md"))
        self.logger.info(f"📋 Analyzing {len(task_files)} task files...")
        
        # Use ThreadPoolExecutor for CPU-bound task parsing
        urgent_tasks = []
        assigned_to_me = []
        by_priority = {'high': 0, 'medium': 0, 'low': 0}
        by_category = defaultdict(int)
        
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Submit all tasks to the executor
            future_to_file = {
                executor.submit(self._analyze_task_file, task_file): task_file 
                for task_file in task_files
            }
            
            # Process completed tasks
            for future in as_completed(future_to_file):
                task_file = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        task_info, is_urgent, is_mine = result
                        
                        # Update counters
                        priority = task_info.get('priority', 'medium').lower()
                        if priority in by_priority:
                            by_priority[priority] += 1
                        
                        category = task_info.get('category', 'general')
                        by_category[category] += 1
                        
                        if is_urgent:
                            urgent_tasks.append(task_info)
                        if is_mine:
                            assigned_to_me.append(task_info)
                            
                except Exception as e:
                    self.logger.debug(f"Error processing task {task_file.name}: {e}")
        
        # Sort urgent tasks by deadline
        urgent_tasks.sort(key=lambda x: x.get('deadline', '9999-99-99'))
        
        return {
            'total': len(task_files),
            'urgent': urgent_tasks[:5],
            'my_tasks': len(assigned_to_me),
            'by_priority': by_priority,
            'by_category': dict(by_category)
        }
    
    def _analyze_task_file(self, task_file: Path) -> Optional[Tuple[Dict[str, str], bool, bool]]:
        """Analyze a single task file with caching"""
        try:
            # Check cache
            cached_data = self._get_cached_file(task_file)
            
            if cached_data:
                task_info = cached_data.metadata
            else:
                # Read and parse file
                with open(task_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                task_info = self.parser.parse_task_metadata(content, task_file.name)
                
                # Cache the result
                self._cache_file(task_file, content, task_info)
            
            # Check urgency and assignment
            is_urgent = self.parser.is_urgent_task(task_info)
            is_mine = self.parser.is_my_task(task_info)
            
            return task_info, is_urgent, is_mine
            
        except Exception as e:
            self.logger.debug(f"Error analyzing task {task_file.name}: {e}")
            return None
    
    def analyze_people(self) -> Dict[str, Any]:
        """Analyze people with parallel processing"""
        people_path = self.vault_path / "People"
        
        if not people_path.exists():
            return {'total': 0, 'recent_interactions': [], 'top_contacts': []}
        
        people_files = list(people_path.glob("*.md"))
        self.logger.info(f"👥 Analyzing {len(people_files)} people files...")
        
        # Process in parallel
        recent_interactions = []
        contact_frequency = []
        
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_to_file = {
                executor.submit(self._analyze_person_file, person_file): person_file
                for person_file in people_files
            }
            
            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    if result:
                        person_data, recent_interaction = result
                        contact_frequency.append(person_data)
                        
                        if recent_interaction:
                            recent_interactions.append(recent_interaction)
                            
                except Exception as e:
                    self.logger.debug(f"Error processing person: {e}")
        
        # Sort results
        contact_frequency.sort(key=lambda x: x['meeting_count'], reverse=True)
        recent_interactions.sort(key=lambda x: x['days_ago'])
        
        return {
            'total': len(people_files),
            'recent_interactions': recent_interactions[:5],
            'top_contacts': contact_frequency[:5],
            'this_week': len([r for r in recent_interactions if r['days_ago'] <= 7])
        }
    
    def _analyze_person_file(self, person_file: Path) -> Optional[Tuple[Dict[str, Any], Optional[Dict[str, Any]]]]:
        """Analyze a single person file"""
        try:
            cached_data = self._get_cached_file(person_file)
            
            if cached_data:
                content = cached_data.content
                meeting_count = cached_data.metadata.get('meeting_count', 0)
                last_interaction = cached_data.metadata.get('last_interaction')
            else:
                with open(person_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                meeting_count = self.parser.count_meeting_references(content)
                last_interaction = self.parser.extract_last_interaction_date(content)
                
                # Cache metadata
                metadata = {
                    'meeting_count': meeting_count,
                    'last_interaction': last_interaction
                }
                self._cache_file(person_file, content, metadata)
            
            person_name = person_file.stem.replace('-', ' ')
            
            person_data = {
                'name': person_name,
                'meeting_count': meeting_count,
                'last_interaction': last_interaction
            }
            
            # Check for recent interaction
            recent_interaction = None
            if last_interaction:
                try:
                    interaction_date = datetime.strptime(last_interaction, "%Y-%m-%d")
                    days_ago = (datetime.now() - interaction_date).days
                    
                    if days_ago <= 14:
                        recent_interaction = {
                            'name': person_name,
                            'date': last_interaction,
                            'days_ago': days_ago
                        }
                except:
                    pass
            
            return person_data, recent_interaction
            
        except Exception as e:
            self.logger.debug(f"Error analyzing person {person_file.name}: {e}")
            return None
    
    def analyze_companies(self) -> Dict[str, Any]:
        """Analyze company relationships and activity with caching"""
        companies_path = self.vault_path / "Companies"
        
        if not companies_path.exists():
            return {'total': 0, 'active_clients': [], 'by_relationship': {}}
        
        company_files = list(companies_path.glob("*.md"))
        self.logger.info(f"🏢 Analyzing {len(company_files)} company files...")
        
        by_relationship = defaultdict(int)
        active_companies = []
        
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_to_file = {
                executor.submit(self._analyze_company_file, company_file): company_file
                for company_file in company_files
            }
            
            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    if result:
                        company_data, relationship = result
                        by_relationship[relationship] += 1
                        
                        if company_data['meeting_count'] > 0:
                            active_companies.append(company_data)
                            
                except Exception as e:
                    self.logger.debug(f"Error processing company: {e}")
        
        active_companies.sort(key=lambda x: x['meeting_count'], reverse=True)
        
        return {
            'total': len(company_files),
            'active_clients': [c for c in active_companies if c['relationship'] == 'client'][:5],
            'by_relationship': dict(by_relationship),
            'most_active': active_companies[:5]
        }
    
    def _analyze_company_file(self, company_file: Path) -> Optional[Tuple[Dict[str, Any], str]]:
        """Analyze a single company file"""
        try:
            cached_data = self._get_cached_file(company_file)
            
            if cached_data:
                content = cached_data.content
                relationship = cached_data.metadata.get('relationship', 'other')
                meeting_count = cached_data.metadata.get('meeting_count', 0)
            else:
                with open(company_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                relationship = self.parser.extract_company_relationship(content)
                meeting_count = self.parser.count_meeting_references(content)
                
                # Cache metadata
                metadata = {
                    'relationship': relationship,
                    'meeting_count': meeting_count
                }
                self._cache_file(company_file, content, metadata)
            
            company_name = company_file.stem.replace('-', ' ')
            
            company_data = {
                'name': company_name,
                'relationship': relationship,
                'meeting_count': meeting_count
            }
            
            return company_data, relationship
            
        except Exception as e:
            self.logger.debug(f"Error analyzing company {company_file.name}: {e}")
            return None
    
    def analyze_technologies(self) -> Dict[str, Any]:
        """Analyze technology stack and usage with caching"""
        tech_path = self.vault_path / "Technologies"
        
        if not tech_path.exists():
            return {'total': 0, 'in_use': [], 'by_category': {}}
        
        tech_files = list(tech_path.glob("*.md"))
        self.logger.info(f"💻 Analyzing {len(tech_files)} technology files...")
        
        by_category = defaultdict(int)
        by_status = defaultdict(int)
        active_technologies = []
        
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_to_file = {
                executor.submit(self._analyze_technology_file, tech_file): tech_file
                for tech_file in tech_files
            }
            
            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    if result:
                        tech_data, category, status = result
                        by_category[category] += 1
                        by_status[status] += 1
                        
                        if tech_data['usage_count'] > 0:
                            active_technologies.append(tech_data)
                            
                except Exception as e:
                    self.logger.debug(f"Error processing technology: {e}")
        
        active_technologies.sort(key=lambda x: x['usage_count'], reverse=True)
        
        return {
            'total': len(tech_files),
            'by_category': dict(by_category),
            'by_status': dict(by_status),
            'most_used': active_technologies[:5]
        }
    
    def _analyze_technology_file(self, tech_file: Path) -> Optional[Tuple[Dict[str, Any], str, str]]:
        """Analyze a single technology file"""
        try:
            cached_data = self._get_cached_file(tech_file)
            
            if cached_data:
                content = cached_data.content
                category = cached_data.metadata.get('category', 'general')
                status = cached_data.metadata.get('status', 'unknown')
                usage_count = cached_data.metadata.get('usage_count', 0)
            else:
                with open(tech_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                category = self.parser.extract_tech_category(content)
                status = self.parser.extract_tech_status(content)
                usage_count = self.parser.count_meeting_references(content)
                
                # Cache metadata
                metadata = {
                    'category': category,
                    'status': status,
                    'usage_count': usage_count
                }
                self._cache_file(tech_file, content, metadata)
            
            tech_name = tech_file.stem.replace('-', ' ')
            
            tech_data = {
                'name': tech_name,
                'category': category,
                'status': status,
                'usage_count': usage_count
            }
            
            return tech_data, category, status
            
        except Exception as e:
            self.logger.debug(f"Error analyzing technology {tech_file.name}: {e}")
            return None
    
    # Cache management methods
    def _get_cached_file(self, file_path: Path) -> Optional[CachedFileData]:
        """Get file from cache if valid"""
        cache_key = str(file_path)
        
        if cache_key in self._file_cache:
            cached = self._file_cache[cache_key]
            
            # Check if file has been modified
            current_mtime = file_path.stat().st_mtime
            if current_mtime == cached.mtime:
                # Check if cache is not expired
                if datetime.now() - cached.cache_time < self._cache_ttl:
                    self._cache_hits += 1
                    return cached
            
            # Remove stale cache entry
            del self._file_cache[cache_key]
        
        self._cache_misses += 1
        return None
    
    def _cache_file(self, file_path: Path, content: str, metadata: Dict[str, Any]):
        """Add file to cache"""
        # Implement simple LRU by removing oldest entries if cache is full
        if len(self._file_cache) >= self._max_cache_size:
            # Remove oldest 10% of entries
            sorted_entries = sorted(
                self._file_cache.items(),
                key=lambda x: x[1].cache_time
            )
            for key, _ in sorted_entries[:self._max_cache_size // 10]:
                del self._file_cache[key]
        
        cache_key = str(file_path)
        mtime = file_path.stat().st_mtime
        
        self._file_cache[cache_key] = CachedFileData(
            path=file_path,
            mtime=mtime,
            content=content,
            metadata=metadata
        )
    
    def _log_cache_stats(self):
        """Log cache performance statistics"""
        total_requests = self._cache_hits + self._cache_misses
        if total_requests > 0:
            hit_rate = (self._cache_hits / total_requests) * 100
            self.logger.debug(
                f"📊 Cache stats: {self._cache_hits} hits, {self._cache_misses} misses "
                f"({hit_rate:.1f}% hit rate), {len(self._file_cache)} entries"
            )
    
    def clear_cache(self):
        """Clear the file cache"""
        self._file_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        self.logger.info("🗑️ Cache cleared")
    
    # Batch processing for better performance
    async def analyze_vault_async(self) -> Dict[str, Any]:
        """Analyze entire vault using async operations"""
        self.logger.info("🚀 Starting optimized vault analysis...")
        
        # Run analyses concurrently
        results = await asyncio.gather(
            self.analyze_meetings_async(),
            asyncio.to_thread(self.analyze_tasks),
            asyncio.to_thread(self.analyze_people),
            asyncio.to_thread(self.analyze_companies),
            asyncio.to_thread(self.analyze_technologies),
            return_exceptions=True
        )
        
        # Process results
        intelligence = {}
        categories = ['meetings', 'tasks', 'people', 'companies', 'technologies']
        
        for category, result in zip(categories, results):
            if isinstance(result, Exception):
                self.logger.error(f"Error analyzing {category}: {result}")
                intelligence[category] = self._get_empty_result(category)
            else:
                intelligence[category] = result
        
        self.logger.info("✅ Vault analysis complete")
        self._log_cache_stats()
        
        return intelligence
    
    def _get_empty_result(self, category: str) -> Dict[str, Any]:
        """Return empty result structure for failed analyses"""
        empty_structures = {
            'meetings': {'total': 0, 'recent': [], 'this_week': 0, 'this_month': 0},
            'tasks': {'total': 0, 'urgent': [], 'my_tasks': 0, 'by_priority': {}, 'by_category': {}},
            'people': {'total': 0, 'recent_interactions': [], 'top_contacts': [], 'this_week': 0},
            'companies': {'total': 0, 'active_clients': [], 'by_relationship': {}, 'most_active': []},
            'technologies': {'total': 0, 'by_category': {}, 'by_status': {}, 'most_used': []}
        }
        return empty_structures.get(category, {})
    
    # Additional optimization methods
    @lru_cache(maxsize=100)
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute hash of file for deep comparison"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def preload_cache(self, folders: List[str]):
        """Preload cache with files from specific folders"""
        self.logger.info(f"📥 Preloading cache for folders: {folders}")
        
        for folder in folders:
            folder_path = self.vault_path / folder
            if folder_path.exists():
                files = list(folder_path.glob("*.md"))[:100]  # Limit preload
                
                with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                    futures = [
                        executor.submit(self._preload_single_file, f)
                        for f in files
                    ]
                    
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            self.logger.debug(f"Error preloading file: {e}")
    
    def _preload_single_file(self, file_path: Path):
        """Preload a single file into cache"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract basic metadata based on file type
            metadata = {}
            if "Tasks" in str(file_path):
                metadata = self.parser.parse_task_metadata(content, file_path.name)
            elif "People" in str(file_path):
                metadata = {
                    'meeting_count': self.parser.count_meeting_references(content),
                    'last_interaction': self.parser.extract_last_interaction_date(content)
                }
            elif "Companies" in str(file_path):
                metadata = {
                    'relationship': self.parser.extract_company_relationship(content),
                    'meeting_count': self.parser.count_meeting_references(content)
                }
            elif "Technologies" in str(file_path):
                metadata = {
                    'category': self.parser.extract_tech_category(content),
                    'status': self.parser.extract_tech_status(content),
                    'usage_count': self.parser.count_meeting_references(content)
                }
            
            self._cache_file(file_path, content, metadata)
            
        except Exception as e:
            self.logger.debug(f"Error preloading {file_path.name}: {e}")
    
    # Existing methods for trend analysis
    def get_meeting_frequency_trend(self) -> Dict[str, Any]:
        """Get meeting frequency over time"""
        meetings_data = self.analyze_meetings()
        
        # Calculate trend based on recent activity
        this_week = meetings_data['this_week']
        this_month = meetings_data['this_month']
        
        # Estimate last week (rough calculation)
        last_week_estimate = max(0, (this_month - this_week) // 3)
        
        trend = 'stable'
        if this_week > last_week_estimate * 1.2:
            trend = 'increasing'
        elif this_week < last_week_estimate * 0.8:
            trend = 'decreasing'
        
        return {
            'this_week': this_week,
            'last_week': last_week_estimate,
            'trend': trend
        }
    
    def get_task_creation_trend(self) -> Dict[str, Any]:
        """Get task creation trend"""
        tasks_data = self.analyze_tasks()
        
        # Simple trend analysis based on total tasks
        total_tasks = tasks_data['total']
        urgent_tasks = len(tasks_data['urgent'])
        
        return {
            'total': total_tasks,
            'urgent': urgent_tasks,
            'trend': 'increasing' if urgent_tasks > 3 else 'stable'
        }
    
    def get_busiest_days(self) -> List[str]:
        """Get busiest days of week based on meeting patterns"""
        # This could be enhanced to actually analyze meeting dates
        # For now, return common busy days
        return ['Tuesday', 'Wednesday', 'Thursday']
    
    def get_growth_metrics(self) -> Dict[str, str]:
        """Get vault growth metrics"""
        # Get current totals
        meetings = self.analyze_meetings()
        people = self.analyze_people()
        companies = self.analyze_companies()
        technologies = self.analyze_technologies()
        
        total_notes = (meetings['total'] + people['total'] + 
                      companies['total'] + technologies['total'])
        
        return {
            'total_notes': str(total_notes),
            'notes_created_this_week': str(meetings['this_week']),
            'active_connections': str(len(people['top_contacts'])),
            'knowledge_growth': 'Strong' if total_notes > 50 else 'Growing'
        }