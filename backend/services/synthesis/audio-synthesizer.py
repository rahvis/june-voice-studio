"""
Audio Synthesis Engine

This module handles real-time text-to-speech synthesis using Azure Speech SDK,
batch synthesis workflows, and audio format conversion for various output formats.
"""

import azure.cognitiveservices.speech as speechsdk
import azure.cognitiveservices.speech.audio as audio
import numpy as np
import io
import wave
import tempfile
import os
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Union, BinaryIO
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class SynthesisMode(Enum):
    """Synthesis mode enumeration"""
    REAL_TIME = "real_time"
    BATCH = "batch"
    STREAMING = "streaming"

class AudioFormat(Enum):
    """Audio output format enumeration"""
    WAV = "wav"
    MP3 = "mp3"
    OPUS = "opus"
    PCM = "pcm"
    FLAC = "flac"

class SynthesisStatus(Enum):
    """Synthesis status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class SynthesisRequest:
    """Synthesis request data structure"""
    request_id: str
    text: str
    ssml: str
    voice_name: str
    language: str
    mode: SynthesisMode
    output_format: AudioFormat
    sample_rate: int
    channels: int
    bit_depth: int
    prosody: Optional[Dict[str, any]]
    metadata: Dict[str, any]

@dataclass
class SynthesisResult:
    """Synthesis result data structure"""
    request_id: str
    status: SynthesisStatus
    audio_data: Optional[bytes]
    audio_url: Optional[str]
    duration: Optional[float]
    sample_rate: int
    channels: int
    bit_depth: int
    format: AudioFormat
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    metadata: Dict[str, any]

@dataclass
class StreamingChunk:
    """Streaming audio chunk"""
    chunk_id: str
    audio_data: bytes
    timestamp: float
    is_final: bool
    metadata: Dict[str, any]

class AudioSynthesizer:
    """Azure Speech SDK-based audio synthesis engine"""
    
    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.speech_key = config['speech_key']
        self.speech_region = config['speech_region']
        self.speech_config = self._create_speech_config()
        self.storage_client = config.get('storage_client')
        self.cache_client = config.get('cache_client')
        
        # Audio format configurations
        self.audio_configs = self._load_audio_configs()
        
    def _create_speech_config(self) -> speechsdk.SpeechConfig:
        """Create Azure Speech configuration"""
        speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, 
            region=self.speech_region
        )
        
        # Configure for high-quality synthesis
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm
        )
        
        # Enable audio logging for debugging
        speech_config.enable_audio_logging()
        
        # Set default voice
        speech_config.speech_synthesis_voice_name = "en-US-AriaNeural"
        
        return speech_config
    
    def _load_audio_configs(self) -> Dict[str, Dict[str, any]]:
        """Load audio format configurations"""
        return {
            AudioFormat.WAV.value: {
                "mime_type": "audio/wav",
                "extension": ".wav",
                "supported_sample_rates": [8000, 16000, 22050, 44100, 48000],
                "supported_channels": [1, 2],
                "supported_bit_depths": [16, 24, 32]
            },
            AudioFormat.MP3.value: {
                "mime_type": "audio/mpeg",
                "extension": ".mp3",
                "supported_sample_rates": [8000, 16000, 22050, 44100, 48000],
                "supported_channels": [1, 2],
                "supported_bit_depths": [16]
            },
            AudioFormat.OPUS.value: {
                "mime_type": "audio/opus",
                "extension": ".opus",
                "supported_sample_rates": [8000, 16000, 22050, 44100, 48000],
                "supported_channels": [1, 2],
                "supported_bit_depths": [16]
            },
            AudioFormat.PCM.value: {
                "mime_type": "audio/pcm",
                "extension": ".pcm",
                "supported_sample_rates": [8000, 16000, 22050, 44100, 48000],
                "supported_channels": [1, 2],
                "supported_bit_depths": [16, 24, 32]
            },
            AudioFormat.FLAC.value: {
                "mime_type": "audio/flac",
                "extension": ".flac",
                "supported_sample_rates": [8000, 16000, 22050, 44100, 48000],
                "supported_channels": [1, 2],
                "supported_bit_depths": [16, 24, 32]
            }
        }
    
    async def synthesize_text(self, 
                            request: SynthesisRequest) -> SynthesisResult:
        """
        Synthesize text to speech
        
        Args:
            request: Synthesis request
            
        Returns:
            Synthesis result
        """
        try:
            # Validate request
            validation_result = self._validate_synthesis_request(request)
            if not validation_result[0]:
                return SynthesisResult(
                    request_id=request.request_id,
                    status=SynthesisStatus.FAILED,
                    audio_data=None,
                    audio_url=None,
                    duration=None,
                    sample_rate=request.sample_rate,
                    channels=request.channels,
                    bit_depth=request.bit_depth,
                    format=request.output_format,
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message=validation_result[1],
                    metadata={"validation_failed": True}
                )
            
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = await self._get_cached_synthesis(cache_key)
            
            if cached_result:
                logger.info(f"Synthesis found in cache for request {request.request_id}")
                return cached_result
            
            # Update speech config for this request
            self._update_speech_config(request)
            
            # Perform synthesis based on mode
            if request.mode == SynthesisMode.REAL_TIME:
                result = await self._synthesize_real_time(request)
            elif request.mode == SynthesisMode.BATCH:
                result = await self._synthesize_batch(request)
            elif request.mode == SynthesisMode.STREAMING:
                result = await self._synthesize_streaming(request)
            else:
                raise ValueError(f"Unsupported synthesis mode: {request.mode}")
            
            # Cache the result
            await self._cache_synthesis(cache_key, result)
            
            # Update voice usage statistics
            await self._update_voice_usage(request.voice_name)
            
            return result
            
        except Exception as e:
            logger.error(f"Error synthesizing text for request {request.request_id}: {str(e)}")
            return SynthesisResult(
                request_id=request.request_id,
                status=SynthesisStatus.FAILED,
                audio_data=None,
                audio_url=None,
                duration=None,
                sample_rate=request.sample_rate,
                channels=request.channels,
                bit_depth=request.bit_depth,
                format=request.output_format,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                error_message=str(e),
                metadata={"error": str(e)}
            )
    
    def _validate_synthesis_request(self, request: SynthesisRequest) -> Tuple[bool, str]:
        """Validate synthesis request parameters"""
        errors = []
        
        # Check text content
        if not request.text and not request.ssml:
            errors.append("Either text or SSML must be provided")
        
        # Check voice name
        if not request.voice_name:
            errors.append("Voice name is required")
        
        # Check language
        if not request.language:
            errors.append("Language is required")
        
        # Check output format
        if request.output_format not in self.audio_configs:
            errors.append(f"Unsupported output format: {request.output_format}")
        
        # Check sample rate
        format_config = self.audio_configs.get(request.output_format.value, {})
        supported_rates = format_config.get("supported_sample_rates", [])
        if request.sample_rate not in supported_rates:
            errors.append(f"Unsupported sample rate {request.sample_rate} for format {request.output_format}")
        
        # Check channels
        supported_channels = format_config.get("supported_channels", [])
        if request.channels not in supported_channels:
            errors.append(f"Unsupported channel count {request.channels} for format {request.output_format}")
        
        # Check bit depth
        supported_bit_depths = format_config.get("supported_bit_depths", [])
        if request.bit_depth not in supported_bit_depths:
            errors.append(f"Unsupported bit depth {request.bit_depth} for format {request.output_format}")
        
        is_valid = len(errors) == 0
        error_message = "; ".join(errors) if errors else ""
        
        return is_valid, error_message
    
    def _update_speech_config(self, request: SynthesisRequest):
        """Update speech configuration for the request"""
        # Set voice
        self.speech_config.speech_synthesis_voice_name = request.voice_name
        
        # Set output format based on requirements
        if request.output_format == AudioFormat.WAV:
            self.speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm
            )
        elif request.output_format == AudioFormat.MP3:
            self.speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
            )
        elif request.output_format == AudioFormat.OPUS:
            self.speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm
            )
        else:
            # Default to PCM
            self.speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm
            )
    
    async def _synthesize_real_time(self, request: SynthesisRequest) -> SynthesisResult:
        """Perform real-time synthesis"""
        try:
            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config
            )
            
            # Start synthesis
            if request.ssml:
                result = synthesizer.speak_ssml_async(request.ssml).get()
            else:
                result = synthesizer.speak_text_async(request.text).get()
            
            # Check result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Get audio data
                audio_data = result.audio_data
                
                # Convert to requested format
                converted_audio = await self._convert_audio_format(
                    audio_data, request.output_format, request.sample_rate, 
                    request.channels, request.bit_depth
                )
                
                # Calculate duration
                duration = self._calculate_audio_duration(
                    converted_audio, request.sample_rate, request.channels, request.bit_depth
                )
                
                return SynthesisResult(
                    request_id=request.request_id,
                    status=SynthesisStatus.COMPLETED,
                    audio_data=converted_audio,
                    audio_url=None,
                    duration=duration,
                    sample_rate=request.sample_rate,
                    channels=request.channels,
                    bit_depth=request.bit_depth,
                    format=request.output_format,
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message=None,
                    metadata={
                        "synthesis_mode": "real_time",
                        "original_audio_size": len(audio_data),
                        "converted_audio_size": len(converted_audio)
                    }
                )
            else:
                error_message = f"Synthesis failed: {result.reason}"
                if result.cancellation_details:
                    error_message += f" - {result.cancellation_details.reason}"
                
                return SynthesisResult(
                    request_id=request.request_id,
                    status=SynthesisStatus.FAILED,
                    audio_data=None,
                    audio_url=None,
                    duration=None,
                    sample_rate=request.sample_rate,
                    channels=request.channels,
                    bit_depth=request.bit_depth,
                    format=request.output_format,
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message=error_message,
                    metadata={"synthesis_mode": "real_time", "failure_reason": str(result.reason)}
                )
                
        except Exception as e:
            logger.error(f"Real-time synthesis failed: {str(e)}")
            raise
    
    async def _synthesize_batch(self, request: SynthesisRequest) -> SynthesisResult:
        """Perform batch synthesis for long content"""
        try:
            # For batch synthesis, we'll use the same approach but with progress tracking
            # In a real implementation, this would use Azure's Batch Synthesis API
            
            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config
            )
            
            # Start synthesis
            if request.ssml:
                result = synthesizer.speak_ssml_async(request.ssml).get()
            else:
                result = synthesizer.speak_text_async(request.text).get()
            
            # Check result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Get audio data
                audio_data = result.audio_data
                
                # Convert to requested format
                converted_audio = await self._convert_audio_format(
                    audio_data, request.output_format, request.sample_rate, 
                    request.channels, request.bit_depth
                )
                
                # Calculate duration
                duration = self._calculate_audio_duration(
                    converted_audio, request.sample_rate, request.channels, request.bit_depth
                )
                
                # Store to storage if available
                audio_url = None
                if self.storage_client:
                    audio_url = await self._store_audio_file(
                        converted_audio, request.request_id, request.output_format
                    )
                
                return SynthesisResult(
                    request_id=request.request_id,
                    status=SynthesisStatus.COMPLETED,
                    audio_data=converted_audio,
                    audio_url=audio_url,
                    duration=duration,
                    sample_rate=request.sample_rate,
                    channels=request.channels,
                    bit_depth=request.bit_depth,
                    format=request.output_format,
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message=None,
                    metadata={
                        "synthesis_mode": "batch",
                        "original_audio_size": len(audio_data),
                        "converted_audio_size": len(converted_audio),
                        "stored_to_storage": audio_url is not None
                    }
                )
            else:
                error_message = f"Batch synthesis failed: {result.reason}"
                if result.cancellation_details:
                    error_message += f" - {result.cancellation_details.reason}"
                
                return SynthesisResult(
                    request_id=request.request_id,
                    status=SynthesisStatus.FAILED,
                    audio_data=None,
                    audio_url=None,
                    duration=None,
                    sample_rate=request.sample_rate,
                    channels=request.channels,
                    bit_depth=request.bit_depth,
                    format=request.output_format,
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message=error_message,
                    metadata={"synthesis_mode": "batch", "failure_reason": str(result.reason)}
                )
                
        except Exception as e:
            logger.error(f"Batch synthesis failed: {str(e)}")
            raise
    
    async def _synthesize_streaming(self, request: SynthesisRequest) -> SynthesisResult:
        """Perform streaming synthesis"""
        try:
            # For streaming, we'll use the same approach but return audio data immediately
            # In a real implementation, this would use Azure's Streaming Synthesis API
            
            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config
            )
            
            # Start synthesis
            if request.ssml:
                result = synthesizer.speak_ssml_async(request.ssml).get()
            else:
                result = synthesizer.speak_text_async(request.text).get()
            
            # Check result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Get audio data
                audio_data = result.audio_data
                
                # Convert to requested format
                converted_audio = await self._convert_audio_format(
                    audio_data, request.output_format, request.sample_rate, 
                    request.channels, request.bit_depth
                )
                
                # Calculate duration
                duration = self._calculate_audio_duration(
                    converted_audio, request.sample_rate, request.channels, request.bit_depth
                )
                
                return SynthesisResult(
                    request_id=request.request_id,
                    status=SynthesisStatus.COMPLETED,
                    audio_data=converted_audio,
                    audio_url=None,
                    duration=duration,
                    sample_rate=request.sample_rate,
                    channels=request.channels,
                    bit_depth=request.bit_depth,
                    format=request.output_format,
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message=None,
                    metadata={
                        "synthesis_mode": "streaming",
                        "original_audio_size": len(audio_data),
                        "converted_audio_size": len(converted_audio)
                    }
                )
            else:
                error_message = f"Streaming synthesis failed: {result.reason}"
                if result.cancellation_details:
                    error_message += f" - {result.cancellation_details.reason}"
                
                return SynthesisResult(
                    request_id=request.request_id,
                    status=SynthesisStatus.FAILED,
                    audio_data=None,
                    audio_url=None,
                    duration=None,
                    sample_rate=request.sample_rate,
                    channels=request.channels,
                    bit_depth=request.bit_depth,
                    format=request.output_format,
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message=error_message,
                    metadata={"synthesis_mode": "streaming", "failure_reason": str(result.reason)}
                )
                
        except Exception as e:
            logger.error(f"Streaming synthesis failed: {str(e)}")
            raise
    
    async def _convert_audio_format(self, 
                                  audio_data: bytes,
                                  target_format: AudioFormat,
                                  sample_rate: int,
                                  channels: int,
                                  bit_depth: int) -> bytes:
        """Convert audio to target format"""
        try:
            if target_format == AudioFormat.WAV:
                return self._convert_to_wav(audio_data, sample_rate, channels, bit_depth)
            elif target_format == AudioFormat.MP3:
                return await self._convert_to_mp3(audio_data, sample_rate, channels, bit_depth)
            elif target_format == AudioFormat.OPUS:
                return await self._convert_to_opus(audio_data, sample_rate, channels, bit_depth)
            elif target_format == AudioFormat.FLAC:
                return await self._convert_to_flac(audio_data, sample_rate, channels, bit_depth)
            else:
                # Return as PCM
                return audio_data
                
        except Exception as e:
            logger.error(f"Audio format conversion failed: {str(e)}")
            # Return original audio data as fallback
            return audio_data
    
    def _convert_to_wav(self, audio_data: bytes, sample_rate: int, channels: int, bit_depth: int) -> bytes:
        """Convert audio to WAV format"""
        try:
            # Create WAV file in memory
            with io.BytesIO() as wav_buffer:
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(channels)
                    wav_file.setsampwidth(bit_depth // 8)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data)
                
                return wav_buffer.getvalue()
                
        except Exception as e:
            logger.error(f"WAV conversion failed: {str(e)}")
            raise
    
    async def _convert_to_mp3(self, audio_data: bytes, sample_rate: int, channels: int, bit_depth: int) -> bytes:
        """Convert audio to MP3 format"""
        try:
            # This would use a library like pydub or ffmpeg
            # For now, return the original audio data
            logger.warning("MP3 conversion not implemented, returning original audio")
            return audio_data
            
        except Exception as e:
            logger.error(f"MP3 conversion failed: {str(e)}")
            raise
    
    async def _convert_to_opus(self, audio_data: bytes, sample_rate: int, channels: int, bit_depth: int) -> bytes:
        """Convert audio to Opus format"""
        try:
            # This would use a library like opuslib
            # For now, return the original audio data
            logger.warning("Opus conversion not implemented, returning original audio")
            return audio_data
            
        except Exception as e:
            logger.error(f"Opus conversion failed: {str(e)}")
            raise
    
    async def _convert_to_flac(self, audio_data: bytes, sample_rate: int, channels: int, bit_depth: int) -> bytes:
        """Convert audio to FLAC format"""
        try:
            # This would use a library like soundfile
            # For now, return the original audio data
            logger.warning("FLAC conversion not implemented, returning original audio")
            return audio_data
            
        except Exception as e:
            logger.error(f"FLAC conversion failed: {str(e)}")
            raise
    
    def _calculate_audio_duration(self, audio_data: bytes, sample_rate: int, channels: int, bit_depth: int) -> float:
        """Calculate audio duration in seconds"""
        try:
            bytes_per_sample = bit_depth // 8
            total_samples = len(audio_data) // (channels * bytes_per_sample)
            duration = total_samples / sample_rate
            return round(duration, 3)
            
        except Exception as e:
            logger.error(f"Duration calculation failed: {str(e)}")
            return 0.0
    
    async def _store_audio_file(self, audio_data: bytes, request_id: str, format: AudioFormat) -> Optional[str]:
        """Store audio file to storage and return URL"""
        try:
            if not self.storage_client:
                return None
            
            # Generate filename
            filename = f"audio/{request_id}{format.value}"
            
            # Store file
            await self.storage_client.store_file(filename, audio_data)
            
            # Generate URL
            audio_url = await self.storage_client.get_file_url(filename)
            
            return audio_url
            
        except Exception as e:
            logger.error(f"Failed to store audio file: {str(e)}")
            return None
    
    def _generate_cache_key(self, request: SynthesisRequest) -> str:
        """Generate cache key for synthesis request"""
        import hashlib
        
        # Create content hash
        content = f"{request.text}:{request.ssml}:{request.voice_name}:{request.language}:{request.output_format.value}:{request.sample_rate}:{request.channels}:{request.bit_depth}"
        
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def _get_cached_synthesis(self, cache_key: str) -> Optional[SynthesisResult]:
        """Get cached synthesis result"""
        if not self.cache_client:
            return None
        
        try:
            cached_data = await self.cache_client.get(f"synthesis:{cache_key}")
            if cached_data:
                # Parse cached data back to SynthesisResult
                data = json.loads(cached_data)
                return SynthesisResult(**data)
        except Exception as e:
            logger.warning(f"Error retrieving cached synthesis: {str(e)}")
        
        return None
    
    async def _cache_synthesis(self, cache_key: str, result: SynthesisResult):
        """Cache synthesis result"""
        if not self.cache_client:
            return
        
        try:
            # Convert to JSON-serializable format
            cache_data = {
                "request_id": result.request_id,
                "status": result.status.value,
                "audio_data": result.audio_data.hex() if result.audio_data else None,
                "audio_url": result.audio_url,
                "duration": result.duration,
                "sample_rate": result.sample_rate,
                "channels": result.channels,
                "bit_depth": result.bit_depth,
                "format": result.format.value,
                "created_at": result.created_at.isoformat(),
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "error_message": result.error_message,
                "metadata": result.metadata
            }
            
            # Cache for 1 hour
            await self.cache_client.set(
                f"synthesis:{cache_key}",
                json.dumps(cache_data),
                expire=3600
            )
            
        except Exception as e:
            logger.warning(f"Error caching synthesis: {str(e)}")
    
    async def _update_voice_usage(self, voice_name: str):
        """Update voice usage statistics"""
        try:
            # This would update voice usage in the voice registry
            # For now, just log the usage
            logger.info(f"Voice usage updated for: {voice_name}")
            
        except Exception as e:
            logger.error(f"Error updating voice usage: {str(e)}")
    
    def get_supported_formats(self) -> List[Dict[str, any]]:
        """Get list of supported audio formats"""
        return [
            {
                "format": format_name,
                "mime_type": config["mime_type"],
                "extension": config["extension"],
                "supported_sample_rates": config["supported_sample_rates"],
                "supported_channels": config["supported_channels"],
                "supported_bit_depths": config["supported_bit_depths"]
            }
            for format_name, config in self.audio_configs.items()
        ]
    
    def get_synthesis_statistics(self) -> Dict[str, any]:
        """Get synthesis service statistics"""
        return {
            "supported_formats": len(self.audio_configs),
            "cache_enabled": self.cache_client is not None,
            "storage_enabled": self.storage_client is not None,
            "azure_speech_region": self.speech_region,
            "total_synthesis_modes": len(SynthesisMode),
            "total_synthesis_statuses": len(SynthesisStatus)
        }
    
    async def health_check(self) -> Dict[str, any]:
        """Perform health check on the synthesis service"""
        try:
            # Test with a simple synthesis
            test_request = SynthesisRequest(
                request_id="health_check",
                text="Hello world",
                ssml="",
                voice_name="en-US-AriaNeural",
                language="en-US",
                mode=SynthesisMode.REAL_TIME,
                output_format=AudioFormat.WAV,
                sample_rate=16000,
                channels=1,
                bit_depth=16,
                prosody=None,
                metadata={}
            )
            
            result = await self.synthesize_text(test_request)
            
            return {
                "status": "healthy" if result.status == SynthesisStatus.COMPLETED else "unhealthy",
                "test_synthesis_successful": result.status == SynthesisStatus.COMPLETED,
                "last_check": datetime.utcnow().isoformat(),
                "test_duration": result.duration
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
