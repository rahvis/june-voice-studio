"""
Audio Processing Pipeline for Voice Enrollment

This module handles audio quality control, format validation,
preprocessing, and chunking for voice training data.
"""

import numpy as np
import librosa
import soundfile as sf
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging
import io
import wave
import tempfile
import os

logger = logging.getLogger(__name__)

class AudioFormat(Enum):
    """Supported audio formats"""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    M4A = "m4a"

class AudioQuality(Enum):
    """Audio quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    REJECTED = "rejected"

@dataclass
class AudioMetrics:
    """Audio quality metrics"""
    duration: float
    sample_rate: int
    channels: int
    bit_depth: int
    snr_db: float
    clipping_percentage: float
    silence_percentage: float
    volume_rms: float
    quality_score: float
    quality_level: AudioQuality

@dataclass
class AudioChunk:
    """Audio chunk for training"""
    chunk_id: str
    audio_data: np.ndarray
    start_time: float
    end_time: float
    duration: float
    text_transcript: str
    quality_score: float

class AudioProcessor:
    """Processes audio files for voice enrollment"""
    
    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.min_duration = config.get('min_duration', 1.0)  # seconds
        self.max_duration = config.get('max_duration', 30.0)  # seconds
        self.target_sample_rate = config.get('target_sample_rate', 22050)
        self.target_channels = config.get('target_channels', 1)
        self.min_snr = config.get('min_snr', 15.0)  # dB
        self.max_clipping = config.get('max_clipping', 5.0)  # percentage
        self.min_silence = config.get('min_silence', 10.0)  # percentage
        
    def process_audio(self, audio_file: Union[str, bytes, np.ndarray], 
                     file_format: Optional[str] = None) -> Tuple[bool, AudioMetrics, str]:
        """
        Process and validate audio file
        
        Args:
            audio_file: Audio file path, bytes, or numpy array
            file_format: Audio file format (auto-detected if None)
            
        Returns:
            Tuple of (is_valid, metrics, error_message)
        """
        try:
            # Load audio
            if isinstance(audio_file, str):
                audio_data, sample_rate = self._load_audio_file(audio_file)
            elif isinstance(audio_file, bytes):
                audio_data, sample_rate = self._load_audio_bytes(audio_file, file_format)
            elif isinstance(audio_file, np.ndarray):
                audio_data, sample_rate = audio_file, self.target_sample_rate
            else:
                return False, None, "Invalid audio input type"
            
            # Calculate metrics
            metrics = self._calculate_audio_metrics(audio_data, sample_rate)
            
            # Validate quality
            is_valid, error_message = self._validate_audio_quality(metrics)
            
            return is_valid, metrics, error_message
            
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            return False, None, f"Processing error: {str(e)}"
    
    def preprocess_audio(self, audio_data: np.ndarray, 
                        sample_rate: int) -> np.ndarray:
        """
        Preprocess audio for training
        
        Args:
            audio_data: Input audio data
            sample_rate: Input sample rate
            
        Returns:
            Preprocessed audio data
        """
        # Resample if needed
        if sample_rate != self.target_sample_rate:
            audio_data = librosa.resample(
                audio_data, 
                orig_sr=sample_rate, 
                target_sr=self.target_sample_rate
            )
        
        # Convert to mono if needed
        if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Normalize volume
        audio_data = self._normalize_audio(audio_data)
        
        # Remove silence
        audio_data = self._remove_silence(audio_data)
        
        # Apply noise reduction
        audio_data = self._reduce_noise(audio_data)
        
        return audio_data
    
    def chunk_audio(self, audio_data: np.ndarray, 
                   sample_rate: int,
                   chunk_duration: float = 10.0,
                   overlap: float = 0.5) -> List[AudioChunk]:
        """
        Split audio into training chunks
        
        Args:
            audio_data: Input audio data
            sample_rate: Audio sample rate
            chunk_duration: Duration of each chunk in seconds
            overlap: Overlap between chunks (0.0 to 1.0)
            
        Returns:
            List of audio chunks
        """
        chunk_samples = int(chunk_duration * sample_rate)
        overlap_samples = int(overlap * chunk_samples)
        step_samples = chunk_samples - overlap_samples
        
        chunks = []
        chunk_id = 0
        
        for start_sample in range(0, len(audio_data), step_samples):
            end_sample = min(start_sample + chunk_samples, len(audio_data))
            
            if end_sample - start_sample < chunk_samples // 2:  # Skip very short chunks
                continue
            
            chunk_audio = audio_data[start_sample:end_sample]
            start_time = start_sample / sample_rate
            end_time = end_sample / sample_rate
            duration = end_time - start_time
            
            # Calculate chunk quality
            chunk_metrics = self._calculate_audio_metrics(chunk_audio, sample_rate)
            
            chunk = AudioChunk(
                chunk_id=f"chunk_{chunk_id:04d}",
                audio_data=chunk_audio,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                text_transcript="",  # Will be filled by STT service
                quality_score=chunk_metrics.quality_score
            )
            
            chunks.append(chunk)
            chunk_id += 1
        
        return chunks
    
    def _load_audio_file(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file from path"""
        audio_data, sample_rate = librosa.load(file_path, sr=None)
        return audio_data, sample_rate
    
    def _load_audio_bytes(self, audio_bytes: bytes, 
                          file_format: str) -> Tuple[np.ndarray, int]:
        """Load audio from bytes"""
        with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_file.flush()
            
            try:
                audio_data, sample_rate = librosa.load(temp_file.name, sr=None)
            finally:
                os.unlink(temp_file.name)
        
        return audio_data, sample_rate
    
    def _calculate_audio_metrics(self, audio_data: np.ndarray, 
                                sample_rate: int) -> AudioMetrics:
        """Calculate comprehensive audio quality metrics"""
        duration = len(audio_data) / sample_rate
        channels = 1 if len(audio_data.shape) == 1 else audio_data.shape[1]
        
        # Calculate SNR
        signal_power = np.mean(audio_data ** 2)
        noise_power = np.var(audio_data)
        snr_db = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else float('inf')
        
        # Calculate clipping percentage
        clipping_threshold = 0.95
        clipping_samples = np.sum(np.abs(audio_data) > clipping_threshold)
        clipping_percentage = (clipping_samples / len(audio_data)) * 100
        
        # Calculate silence percentage
        silence_threshold = 0.01
        silence_samples = np.sum(np.abs(audio_data) < silence_threshold)
        silence_percentage = (silence_samples / len(audio_data)) * 100
        
        # Calculate RMS volume
        volume_rms = np.sqrt(np.mean(audio_data ** 2))
        
        # Calculate quality score (0-100)
        quality_score = self._calculate_quality_score(
            snr_db, clipping_percentage, silence_percentage, duration
        )
        
        # Determine quality level
        quality_level = self._determine_quality_level(quality_score)
        
        return AudioMetrics(
            duration=duration,
            sample_rate=sample_rate,
            channels=channels,
            bit_depth=16,  # Assuming 16-bit
            snr_db=snr_db,
            clipping_percentage=clipping_percentage,
            silence_percentage=silence_percentage,
            volume_rms=volume_rms,
            quality_score=quality_score,
            quality_level=quality_level
        )
    
    def _validate_audio_quality(self, metrics: AudioMetrics) -> Tuple[bool, str]:
        """Validate audio meets quality requirements"""
        errors = []
        
        if metrics.duration < self.min_duration:
            errors.append(f"Audio too short: {metrics.duration:.1f}s < {self.min_duration}s")
        
        if metrics.duration > self.max_duration:
            errors.append(f"Audio too long: {metrics.duration:.1f}s > {self.max_duration}s")
        
        if metrics.snr_db < self.min_snr:
            errors.append(f"SNR too low: {metrics.snr_db:.1f}dB < {self.min_snr}dB")
        
        if metrics.clipping_percentage > self.max_clipping:
            errors.append(f"Too much clipping: {metrics.clipping_percentage:.1f}% > {self.max_clipping}%")
        
        if metrics.silence_percentage > self.min_silence:
            errors.append(f"Too much silence: {metrics.silence_percentage:.1f}% > {self.min_silence}%")
        
        if metrics.quality_score < 60:
            errors.append(f"Quality score too low: {metrics.quality_score:.1f} < 60")
        
        is_valid = len(errors) == 0
        error_message = "; ".join(errors) if errors else ""
        
        return is_valid, error_message
    
    def _calculate_quality_score(self, snr_db: float, clipping_percentage: float,
                                silence_percentage: float, duration: float) -> float:
        """Calculate overall quality score (0-100)"""
        # SNR score (0-40 points)
        snr_score = min(40, max(0, (snr_db - 10) * 2))
        
        # Clipping score (0-25 points)
        clipping_score = max(0, 25 - (clipping_percentage * 5))
        
        # Silence score (0-20 points)
        silence_score = max(0, 20 - (silence_percentage * 2))
        
        # Duration score (0-15 points)
        if 5 <= duration <= 15:
            duration_score = 15
        elif 1 <= duration < 5 or 15 < duration <= 30:
            duration_score = 10
        else:
            duration_score = 5
        
        return snr_score + clipping_score + silence_score + duration_score
    
    def _determine_quality_level(self, quality_score: float) -> AudioQuality:
        """Determine quality level based on score"""
        if quality_score >= 90:
            return AudioQuality.EXCELLENT
        elif quality_score >= 80:
            return AudioQuality.GOOD
        elif quality_score >= 70:
            return AudioQuality.ACCEPTABLE
        elif quality_score >= 60:
            return AudioQuality.POOR
        else:
            return AudioQuality.REJECTED
    
    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio volume"""
        max_amplitude = np.max(np.abs(audio_data))
        if max_amplitude > 0:
            target_amplitude = 0.8
            audio_data = audio_data * (target_amplitude / max_amplitude)
        return audio_data
    
    def _remove_silence(self, audio_data: np.ndarray, 
                        threshold: float = 0.01) -> np.ndarray:
        """Remove leading and trailing silence"""
        # Find non-silent regions
        non_silent = np.abs(audio_data) > threshold
        
        if np.any(non_silent):
            start = np.argmax(non_silent)
            end = len(audio_data) - np.argmax(non_silent[::-1])
            return audio_data[start:end]
        
        return audio_data
    
    def _reduce_noise(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply basic noise reduction"""
        # Simple high-pass filter to remove low-frequency noise
        cutoff_freq = 80  # Hz
        nyquist = self.target_sample_rate / 2
        normalized_cutoff = cutoff_freq / nyquist
        
        # Apply butterworth filter
        from scipy.signal import butter, filtfilt
        b, a = butter(4, normalized_cutoff, btype='high')
        audio_data = filtfilt(b, a, audio_data)
        
        return audio_data
    
    def save_audio_chunk(self, chunk: AudioChunk, 
                         output_path: str, 
                         format: str = 'wav') -> bool:
        """Save audio chunk to file"""
        try:
            if format.lower() == 'wav':
                sf.write(output_path, chunk.audio_data, self.target_sample_rate)
            elif format.lower() == 'mp3':
                import pydub
                audio_segment = pydub.AudioSegment(
                    chunk.audio_data.tobytes(),
                    frame_rate=self.target_sample_rate,
                    sample_width=2,
                    channels=1
                )
                audio_segment.export(output_path, format='mp3')
            else:
                logger.error(f"Unsupported format: {format}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving audio chunk: {str(e)}")
            return False
