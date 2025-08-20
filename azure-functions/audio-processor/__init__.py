"""
Audio File Processing Blob Storage Trigger Function
Processes uploaded audio files for voice cloning
"""
import logging
import json
import azure.functions as func
from typing import Dict, Any
from datetime import datetime
import os
import uuid
import tempfile
import io

# Audio processing imports
try:
    import librosa
    import soundfile as sf
    import numpy as np
    from pydub import AudioSegment
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    AUDIO_PROCESSING_AVAILABLE = False
    logging.warning("Audio processing libraries not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioProcessor:
    """Audio file processor for voice cloning"""
    
    def __init__(self):
        self.supported_formats = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
        self.max_duration_seconds = 300  # 5 minutes
        self.min_duration_seconds = 1     # 1 second
        self.target_sample_rate = 22050   # Target sample rate for processing
        self.target_channels = 1          # Mono audio
        
    def validate_audio_file(self, audio_data: bytes, filename: str) -> tuple[bool, str]:
        """Validate uploaded audio file"""
        try:
            # Check file extension
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in self.supported_formats:
                return False, f"Unsupported audio format: {file_ext}"
            
            # Check file size (max 100MB)
            if len(audio_data) > 100 * 1024 * 1024:
                return False, "File size exceeds 100MB limit"
            
            # Check if audio processing is available
            if not AUDIO_PROCESSING_AVAILABLE:
                return False, "Audio processing libraries not available"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error validating audio file: {str(e)}"
    
    async def process_audio_file(self, audio_data: bytes, filename: str) -> Dict[str, Any]:
        """Process audio file for voice cloning"""
        try:
            # Create temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Load audio file
                audio_info = await self._analyze_audio(temp_file_path)
                
                # Validate duration
                if audio_info["duration"] > self.max_duration_seconds:
                    return {
                        "success": False,
                        "error": f"Audio duration ({audio_info['duration']:.1f}s) exceeds maximum limit ({self.max_duration_seconds}s)"
                    }
                
                if audio_info["duration"] < self.min_duration_seconds:
                    return {
                        "success": False,
                        "error": f"Audio duration ({audio_info['duration']:.1f}s) is below minimum limit ({self.min_duration_seconds}s)"
                    }
                
                # Process audio
                processed_audio = await self._process_audio(temp_file_path, audio_info)
                
                # Generate processing metadata
                processing_metadata = {
                    "original_filename": filename,
                    "original_format": audio_info["format"],
                    "original_sample_rate": audio_info["sample_rate"],
                    "original_channels": audio_info["channels"],
                    "original_duration": audio_info["duration"],
                    "processed_sample_rate": self.target_sample_rate,
                    "processed_channels": self.target_channels,
                    "processing_timestamp": datetime.utcnow().isoformat(),
                    "processing_version": "1.0.0"
                }
                
                return {
                    "success": True,
                    "processed_audio": processed_audio,
                    "metadata": processing_metadata,
                    "audio_info": audio_info
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error processing audio file {filename}: {str(e)}")
            return {
                "success": False,
                "error": f"Audio processing failed: {str(e)}"
            }
    
    async def _analyze_audio(self, file_path: str) -> Dict[str, Any]:
        """Analyze audio file properties"""
        try:
            # Load audio with librosa
            y, sr = librosa.load(file_path, sr=None, mono=False)
            
            # Get duration
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Get format info
            format_info = sf.info(file_path)
            
            return {
                "duration": duration,
                "sample_rate": sr,
                "channels": format_info.channels,
                "format": format_info.format,
                "frames": format_info.frames,
                "sections": format_info.sections
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audio file: {str(e)}")
            raise
    
    async def _process_audio(self, file_path: str, audio_info: Dict[str, Any]) -> bytes:
        """Process audio file for voice cloning"""
        try:
            # Load audio with pydub for easier processing
            audio = AudioSegment.from_file(file_path)
            
            # Convert to mono if needed
            if audio.channels > 1:
                audio = audio.set_channels(1)
                logger.info("Converted audio to mono")
            
            # Resample to target sample rate if needed
            if audio.frame_rate != self.target_sample_rate:
                audio = audio.set_frame_rate(self.target_sample_rate)
                logger.info(f"Resampled audio from {audio_info['sample_rate']}Hz to {self.target_sample_rate}Hz")
            
            # Normalize audio levels
            audio = audio.normalize()
            
            # Export as WAV (uncompressed for processing)
            output_buffer = io.BytesIO()
            audio.export(output_buffer, format="wav")
            processed_audio = output_buffer.getvalue()
            output_buffer.close()
            
            logger.info("Audio processing completed successfully")
            return processed_audio
            
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise
    
    async def create_audio_chunks(self, audio_data: bytes, chunk_duration: int = 10) -> list[bytes]:
        """Split audio into chunks for training"""
        try:
            # Load audio from bytes
            audio = AudioSegment.from_wav(io.BytesIO(audio_data))
            
            # Calculate chunk size in milliseconds
            chunk_size_ms = chunk_duration * 1000
            
            # Split audio into chunks
            chunks = []
            for i in range(0, len(audio), chunk_size_ms):
                chunk = audio[i:i + chunk_size_ms]
                
                # Export chunk
                chunk_buffer = io.BytesIO()
                chunk.export(chunk_buffer, format="wav")
                chunks.append(chunk_buffer.getvalue())
                chunk_buffer.close()
            
            logger.info(f"Created {len(chunks)} audio chunks of {chunk_duration}s each")
            return chunks
            
        except Exception as e:
            logger.error(f"Error creating audio chunks: {str(e)}")
            raise

# Global audio processor instance
audio_processor = AudioProcessor()

async def main(myblob: func.InputStream, processedAudio: func.Out[bytes], processingQueue: func.Out[str]) -> None:
    """
    Main function for audio file processing blob storage trigger
    """
    try:
        # Get blob information
        blob_name = myblob.name
        blob_size = myblob.length
        blob_uri = myblob.uri
        
        logger.info(f"Audio file processing triggered for blob: {blob_name} (size: {blob_size} bytes)")
        
        # Read blob content
        audio_data = myblob.read()
        
        # Validate audio file
        is_valid, error_message = audio_processor.validate_audio_file(audio_data, blob_name)
        if not is_valid:
            logger.error(f"Audio file validation failed for {blob_name}: {error_message}")
            
            # Add error to processing queue
            error_message = {
                "type": "audio_processing_error",
                "blob_name": blob_name,
                "blob_uri": blob_uri,
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat(),
                "function_name": "audio-processor"
            }
            
            processingQueue.set(json.dumps(error_message))
            return
        
        # Process audio file
        processing_result = await audio_processor.process_audio_file(audio_data, blob_name)
        
        if processing_result["success"]:
            # Store processed audio
            processed_audio.set(processing_result["processed_audio"])
            
            # Create audio chunks for training
            try:
                audio_chunks = await audio_processor.create_audio_chunks(
                    processing_result["processed_audio"],
                    chunk_duration=10
                )
                
                # Add processing result to queue
                success_message = {
                    "type": "audio_processing_success",
                    "blob_name": blob_name,
                    "blob_uri": blob_uri,
                    "processed_audio_uri": f"voice-cloning/processed-audio/{blob_name}",
                    "metadata": processing_result["metadata"],
                    "audio_info": processing_result["audio_info"],
                    "chunk_count": len(audio_chunks),
                    "chunk_duration": 10,
                    "timestamp": datetime.utcnow().isoformat(),
                    "function_name": "audio-processor"
                }
                
                processingQueue.set(json.dumps(success_message))
                
                logger.info(f"Audio file {blob_name} processed successfully. Created {len(audio_chunks)} chunks.")
                
            except Exception as e:
                logger.error(f"Error creating audio chunks for {blob_name}: {str(e)}")
                
                # Add chunking error to queue
                chunking_error = {
                    "type": "audio_chunking_error",
                    "blob_name": blob_name,
                    "blob_uri": blob_uri,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                    "function_name": "audio-processor"
                }
                
                processingQueue.set(json.dumps(chunking_error))
        else:
            # Processing failed
            logger.error(f"Audio processing failed for {blob_name}: {processing_result['error']}")
            
            # Add processing error to queue
            processing_error = {
                "type": "audio_processing_error",
                "blob_name": blob_name,
                "blob_uri": blob_uri,
                "error": processing_result["error"],
                "timestamp": datetime.utcnow().isoformat(),
                "function_name": "audio-processor"
            }
            
            processingQueue.set(json.dumps(processing_error))
        
    except Exception as e:
        logger.error(f"Error in audio file processing function: {str(e)}")
        
        # Add general error to queue
        general_error = {
            "type": "audio_processing_general_error",
            "blob_name": getattr(myblob, 'name', 'unknown'),
            "blob_uri": getattr(myblob, 'uri', 'unknown'),
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "function_name": "audio-processor"
        }
        
        processingQueue.set(json.dumps(general_error))
