"""
Audio processing for Meeting Processor
Handles MP4 to FLAC conversion and audio chunking for large files
"""

import subprocess
from pathlib import Path
from typing import List, Optional
from utils.logger import LoggerMixin, log_success, log_error, log_warning


class AudioProcessor(LoggerMixin):
    """Handles audio conversion and chunking operations"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.max_file_size_mb = 25  # Whisper API limit
    
    def convert_mp4_to_flac(self, mp4_path: Path) -> Optional[Path]:
        """Convert MP4 to FLAC using ffmpeg with compression for Whisper"""
        try:
            flac_filename = mp4_path.stem + '.flac'
            flac_path = self.output_dir / flac_filename
            
            self.logger.info(f"🎵 Converting {mp4_path.name} to FLAC")
            
            cmd = [
                'ffmpeg', '-i', str(mp4_path),
                '-vn',  # No video
                '-ac', '1',  # Mono audio (reduces file size)
                '-ar', '16000',  # 16kHz sample rate (good for speech)
                '-acodec', 'flac',
                '-compression_level', '12',  # Maximum compression
                '-y',  # Overwrite output file
                str(flac_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                file_size_mb = flac_path.stat().st_size / (1024 * 1024)
                log_success(self.logger, f"Converted {mp4_path.name} to FLAC ({file_size_mb:.1f}MB)")
                
                if file_size_mb > self.max_file_size_mb:
                    log_warning(self.logger, f"FLAC file is {file_size_mb:.1f}MB (>{self.max_file_size_mb}MB), will need chunking")
                
                return flac_path
            else:
                log_error(self.logger, f"FFmpeg conversion failed for {mp4_path.name}")
                self.logger.debug(f"FFmpeg stderr: {result.stderr}")
                return None
                
        except Exception as e:
            log_error(self.logger, f"Error converting {mp4_path.name}", e)
            return None
    
    def chunk_audio_file(self, audio_path: Path, chunk_duration_minutes: int = 10) -> List[Path]:
        """Split large audio file into smaller chunks for Whisper processing"""
        try:
            chunks = []
            chunk_duration_seconds = chunk_duration_minutes * 60
            
            # Get audio duration first
            duration = self._get_audio_duration(audio_path)
            if duration is None:
                log_error(self.logger, f"Could not determine duration of {audio_path.name}")
                return []
            
            self.logger.info(f"🔪 Chunking {audio_path.name} ({duration:.1f}s) into {chunk_duration_minutes}min segments")
            
            # Create chunks
            chunk_number = 0
            for start_time in range(0, int(duration), chunk_duration_seconds):
                chunk_number += 1
                chunk_filename = f"{audio_path.stem}_chunk_{chunk_number:02d}.flac"
                chunk_path = audio_path.parent / chunk_filename
                
                success = self._create_audio_chunk(
                    audio_path, chunk_path, start_time, chunk_duration_seconds, chunk_number
                )
                
                if success:
                    chunks.append(chunk_path)
                else:
                    log_warning(self.logger, f"Failed to create chunk {chunk_number}")
            
            log_success(self.logger, f"Created {len(chunks)} audio chunks")
            return chunks
            
        except Exception as e:
            log_error(self.logger, f"Error chunking {audio_path.name}", e)
            return []
    
    def _get_audio_duration(self, audio_path: Path) -> Optional[float]:
        """Get duration of audio file in seconds"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', 
                '-show_entries', 'format=duration', 
                '-of', 'csv=p=0', 
                str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
            else:
                self.logger.debug(f"ffprobe failed: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.debug(f"Error getting duration: {e}")
            return None
    
    def _create_audio_chunk(self, source_path: Path, chunk_path: Path, 
                           start_time: int, duration: int, chunk_number: int) -> bool:
        """Create a single audio chunk"""
        try:
            cmd = [
                'ffmpeg', '-i', str(source_path),
                '-ss', str(start_time),
                '-t', str(duration),
                '-ac', '1',  # Mono
                '-ar', '16000',  # 16kHz sample rate
                '-acodec', 'flac',
                '-compression_level', '12',
                '-y',  # Overwrite
                str(chunk_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                chunk_size_mb = chunk_path.stat().st_size / (1024 * 1024)
                self.logger.debug(f"✓ Created chunk {chunk_number}: {chunk_path.name} ({chunk_size_mb:.1f}MB)")
                return True
            else:
                self.logger.debug(f"✗ Chunk {chunk_number} creation failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.debug(f"✗ Error creating chunk {chunk_number}: {e}")
            return False
    
    def cleanup_chunks(self, base_filename: str):
        """Clean up chunk files after processing"""
        try:
            pattern = f"{base_filename}_chunk_*.flac"
            chunk_files = list(self.output_dir.glob(pattern))
            
            for chunk_file in chunk_files:
                chunk_file.unlink()
                self.logger.debug(f"🗑️  Cleaned up chunk: {chunk_file.name}")
            
            if chunk_files:
                self.logger.info(f"🗑️  Cleaned up {len(chunk_files)} chunk files")
                
        except Exception as e:
            log_warning(self.logger, f"Error cleaning up chunks: {e}")
    
    def validate_ffmpeg_installation(self) -> bool:
        """Check if ffmpeg and ffprobe are available"""
        try:
            # Test ffmpeg
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                return False
            
            # Test ffprobe
            result = subprocess.run(['ffprobe', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                return False
            
            self.logger.debug("✓ FFmpeg installation validated")
            return True
            
        except FileNotFoundError:
            log_error(self.logger, "FFmpeg not found - install ffmpeg to process audio files")
            return False
        except Exception as e:
            log_error(self.logger, "Error validating FFmpeg installation", e)
            return False