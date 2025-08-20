"""
Speech-to-Text Integration Service

This module integrates with Azure Speech-to-Text service to provide
audio transcription, text alignment, and quality validation for
voice enrollment training data.
"""

import azure.cognitiveservices.speech as speechsdk
import azure.cognitiveservices.speech.audio as audio
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging
import json
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np

logger = logging.getLogger(__name__)

class TranscriptionStatus(Enum):
    """Transcription status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class TranscriptionQuality(Enum):
    """Transcription quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNUSABLE = "unusable"

@dataclass
class TranscriptionResult:
    """Transcription result data structure"""
    transcript_id: str
    audio_chunk_id: str
    text: str
    confidence: float
    start_time: float
    end_time: float
    duration: float
    language: str
    status: TranscriptionStatus
    quality: TranscriptionQuality
    word_timings: List[Dict[str, any]]
    metadata: Dict[str, any]

@dataclass
class TextAlignmentResult:
    """Text-audio alignment result"""
    alignment_id: str
    transcript_id: str
    audio_chunk_id: str
    alignment_score: float
    word_alignments: List[Dict[str, any]]
    phoneme_alignments: List[Dict[str, any]]
    is_aligned: bool
    confidence: float

class SpeechToTextService:
    """Azure Speech-to-Text service integration"""
    
    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.speech_key = config['speech_key']
        self.speech_region = config['speech_region']
        self.speech_config = self._create_speech_config()
        self.executor = ThreadPoolExecutor(max_workers=config.get('max_workers', 4))
        
    def _create_speech_config(self) -> speechsdk.SpeechConfig:
        """Create Azure Speech configuration"""
        speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, 
            region=self.speech_region
        )
        
        # Configure for high accuracy transcription
        speech_config.speech_recognition_language = "en-US"
        speech_config.enable_dictation()
        speech_config.enable_audio_logging()
        
        # Enable word-level timing
        speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_EnableWordLevelTimestamps, 
            "true"
        )
        
        # Enable detailed results
        speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceResponse_RequestWordLevelTimestamps, 
            "true"
        )
        
        # Enable profanity filtering
        speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceResponse_ProfanityFilterMode, 
            "1"
        )
        
        return speech_config
    
    async def transcribe_audio_chunk(self, 
                                   audio_data: np.ndarray,
                                   sample_rate: int,
                                   chunk_id: str,
                                   language: str = "en-US") -> TranscriptionResult:
        """
        Transcribe audio chunk asynchronously
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Audio sample rate
            chunk_id: Unique identifier for the chunk
            language: Language code for transcription
            
        Returns:
            Transcription result
        """
        try:
            # Update language for this transcription
            self.speech_config.speech_recognition_language = language
            
            # Convert audio data to format expected by Azure
            audio_bytes = self._convert_audio_to_bytes(audio_data, sample_rate)
            
            # Create audio config
            audio_config = audio.AudioConfig(stream=audio.PushAudioInputStream())
            
            # Create recognizer
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # Start transcription
            future = self.executor.submit(
                self._perform_transcription,
                recognizer,
                audio_bytes,
                chunk_id,
                language
            )
            
            # Wait for completion
            result = await asyncio.get_event_loop().run_in_executor(
                None, future.result
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing audio chunk {chunk_id}: {str(e)}")
            return TranscriptionResult(
                transcript_id=f"transcript_{chunk_id}",
                audio_chunk_id=chunk_id,
                text="",
                confidence=0.0,
                start_time=0.0,
                end_time=0.0,
                duration=0.0,
                language=language,
                status=TranscriptionStatus.FAILED,
                quality=TranscriptionQuality.UNUSABLE,
                word_timings=[],
                metadata={"error": str(e)}
            )
    
    def _perform_transcription(self, 
                             recognizer: speechsdk.SpeechRecognizer,
                             audio_bytes: bytes,
                             chunk_id: str,
                             language: str) -> TranscriptionResult:
        """Perform the actual transcription"""
        try:
            # Push audio data to stream
            audio_stream = recognizer.audio_config.get_stream()
            audio_stream.write(audio_bytes)
            audio_stream.close()
            
            # Start recognition
            result = recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return self._process_successful_result(result, chunk_id, language)
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return self._process_no_match_result(result, chunk_id, language)
            else:
                return self._process_failed_result(result, chunk_id, language)
                
        except Exception as e:
            logger.error(f"Transcription failed for chunk {chunk_id}: {str(e)}")
            raise
    
    def _process_successful_result(self, 
                                 result: speechsdk.SpeechRecognitionResult,
                                 chunk_id: str,
                                 language: str) -> TranscriptionResult:
        """Process successful transcription result"""
        text = result.text
        confidence = result.properties.get(
            speechsdk.PropertyId.SpeechServiceResponse_JsonResult, 
            "{}"
        )
        
        # Parse confidence from JSON result
        try:
            confidence_data = json.loads(confidence)
            confidence_score = confidence_data.get('NBest', [{}])[0].get('Confidence', 0.0)
        except:
            confidence_score = 0.0
        
        # Extract word timings if available
        word_timings = self._extract_word_timings(result)
        
        # Calculate quality score
        quality = self._calculate_transcription_quality(confidence_score, text)
        
        return TranscriptionResult(
            transcript_id=f"transcript_{chunk_id}_{int(time.time())}",
            audio_chunk_id=chunk_id,
            text=text,
            confidence=confidence_score,
            start_time=0.0,  # Will be updated with alignment
            end_time=0.0,    # Will be updated with alignment
            duration=0.0,     # Will be updated with alignment
            language=language,
            status=TranscriptionStatus.COMPLETED,
            quality=quality,
            word_timings=word_timings,
            metadata={
                "result_reason": str(result.reason),
                "offset": result.offset,
                "duration": result.duration
            }
        )
    
    def _process_no_match_result(self, 
                               result: speechsdk.SpeechRecognitionResult,
                               chunk_id: str,
                               language: str) -> TranscriptionResult:
        """Process no-match transcription result"""
        return TranscriptionResult(
            transcript_id=f"transcript_{chunk_id}_{int(time.time())}",
            audio_chunk_id=chunk_id,
            text="",
            confidence=0.0,
            start_time=0.0,
            end_time=0.0,
            duration=0.0,
            language=language,
            status=TranscriptionStatus.FAILED,
            quality=TranscriptionQuality.UNUSABLE,
            word_timings=[],
            metadata={
                "result_reason": str(result.reason),
                "no_match_details": result.no_match_details
            }
        )
    
    def _process_failed_result(self, 
                             result: speechsdk.SpeechRecognitionResult,
                             chunk_id: str,
                             language: str) -> TranscriptionResult:
        """Process failed transcription result"""
        return TranscriptionResult(
            transcript_id=f"transcript_{chunk_id}_{int(time.time())}",
            audio_chunk_id=chunk_id,
            text="",
            confidence=0.0,
            start_time=0.0,
            end_time=0.0,
            duration=0.0,
            language=language,
            status=TranscriptionStatus.FAILED,
            quality=TranscriptionQuality.UNUSABLE,
            word_timings=[],
            metadata={
                "result_reason": str(result.reason),
                "cancellation_reason": str(result.cancellation_details.reason),
                "cancellation_details": str(result.cancellation_details)
            }
        )
    
    def _extract_word_timings(self, result: speechsdk.SpeechRecognitionResult) -> List[Dict[str, any]]:
        """Extract word-level timing information"""
        word_timings = []
        
        try:
            # Get detailed result with word timings
            detailed_result = result.properties.get(
                speechsdk.PropertyId.SpeechServiceResponse_JsonResult
            )
            
            if detailed_result:
                result_data = json.loads(detailed_result)
                words = result_data.get('NBest', [{}])[0].get('Words', [])
                
                for word in words:
                    word_timings.append({
                        "word": word.get('Word', ''),
                        "start_time": word.get('Offset', 0) / 10000000,  # Convert to seconds
                        "end_time": (word.get('Offset', 0) + word.get('Duration', 0)) / 10000000,
                        "duration": word.get('Duration', 0) / 10000000,
                        "confidence": word.get('Confidence', 0.0)
                    })
        except Exception as e:
            logger.warning(f"Could not extract word timings: {str(e)}")
        
        return word_timings
    
    def _calculate_transcription_quality(self, confidence: float, text: str) -> TranscriptionQuality:
        """Calculate transcription quality based on confidence and text"""
        if not text or len(text.strip()) == 0:
            return TranscriptionQuality.UNUSABLE
        
        if confidence >= 0.9:
            return TranscriptionQuality.EXCELLENT
        elif confidence >= 0.8:
            return TranscriptionQuality.GOOD
        elif confidence >= 0.7:
            return TranscriptionQuality.ACCEPTABLE
        elif confidence >= 0.6:
            return TranscriptionQuality.POOR
        else:
            return TranscriptionQuality.UNUSABLE
    
    def _convert_audio_to_bytes(self, audio_data: np.ndarray, sample_rate: int) -> bytes:
        """Convert numpy audio array to bytes for Azure Speech SDK"""
        # Ensure audio is in the correct format (16-bit PCM)
        if audio_data.dtype != np.int16:
            # Normalize to [-1, 1] range
            audio_normalized = audio_data.astype(np.float32)
            audio_normalized = np.clip(audio_normalized, -1.0, 1.0)
            
            # Convert to 16-bit PCM
            audio_data = (audio_normalized * 32767).astype(np.int16)
        
        return audio_data.tobytes()
    
    async def transcribe_multiple_chunks(self, 
                                       audio_chunks: List[Tuple[str, np.ndarray, int]],
                                       language: str = "en-US") -> List[TranscriptionResult]:
        """Transcribe multiple audio chunks concurrently"""
        tasks = []
        
        for chunk_id, audio_data, sample_rate in audio_chunks:
            task = self.transcribe_audio_chunk(audio_data, sample_rate, chunk_id, language)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for result in results:
            if isinstance(result, TranscriptionResult):
                valid_results.append(result)
            else:
                logger.error(f"Transcription task failed: {result}")
        
        return valid_results
    
    def validate_transcription_quality(self, transcriptions: List[TranscriptionResult]) -> Tuple[bool, List[str]]:
        """
        Validate overall transcription quality
        
        Args:
            transcriptions: List of transcription results
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check minimum confidence threshold
        min_confidence = self.config.get('min_confidence', 0.7)
        low_confidence = [t for t in transcriptions if t.confidence < min_confidence]
        
        if low_confidence:
            errors.append(f"{len(low_confidence)} transcriptions below confidence threshold {min_confidence}")
        
        # Check for failed transcriptions
        failed = [t for t in transcriptions if t.status == TranscriptionStatus.FAILED]
        if failed:
            errors.append(f"{len(failed)} transcription failures")
        
        # Check for poor quality transcriptions
        poor_quality = [t for t in transcriptions if t.quality in [TranscriptionQuality.POOR, TranscriptionQuality.UNUSABLE]]
        if poor_quality:
            errors.append(f"{len(poor_quality)} poor quality transcriptions")
        
        # Check minimum text length
        min_text_length = self.config.get('min_text_length', 3)
        short_texts = [t for t in transcriptions if len(t.text.strip().split()) < min_text_length]
        if short_texts:
            errors.append(f"{len(short_texts)} transcriptions with insufficient text content")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def create_text_alignment(self, 
                            transcription: TranscriptionResult,
                            audio_duration: float) -> TextAlignmentResult:
        """
        Create text-audio alignment for training data
        
        Args:
            transcription: Transcription result
            audio_duration: Duration of the audio chunk
            
        Returns:
            Text alignment result
        """
        try:
            # Use word timings if available
            if transcription.word_timings:
                word_alignments = transcription.word_timings
                alignment_score = self._calculate_alignment_score(word_alignments, audio_duration)
                is_aligned = alignment_score > 0.8
            else:
                # Fallback: estimate timing based on audio duration
                word_alignments = self._estimate_word_timings(transcription.text, audio_duration)
                alignment_score = 0.5  # Lower score for estimated alignments
                is_aligned = False
            
            # Create phoneme alignments (simplified)
            phoneme_alignments = self._create_phoneme_alignments(word_alignments)
            
            return TextAlignmentResult(
                alignment_id=f"alignment_{transcription.transcript_id}",
                transcript_id=transcription.transcript_id,
                audio_chunk_id=transcription.audio_chunk_id,
                alignment_score=alignment_score,
                word_alignments=word_alignments,
                phoneme_alignments=phoneme_alignments,
                is_aligned=is_aligned,
                confidence=transcription.confidence
            )
            
        except Exception as e:
            logger.error(f"Error creating text alignment: {str(e)}")
            return TextAlignmentResult(
                alignment_id=f"alignment_{transcription.transcript_id}",
                transcript_id=transcription.transcript_id,
                audio_chunk_id=transcription.audio_chunk_id,
                alignment_score=0.0,
                word_alignments=[],
                phoneme_alignments=[],
                is_aligned=False,
                confidence=0.0
            )
    
    def _calculate_alignment_score(self, word_alignments: List[Dict[str, any]], 
                                 audio_duration: float) -> float:
        """Calculate alignment quality score"""
        if not word_alignments:
            return 0.0
        
        # Check if word timings span the full audio duration
        first_word_time = word_alignments[0]['start_time']
        last_word_time = word_alignments[-1]['end_time']
        
        # Calculate coverage
        coverage = min(1.0, (last_word_time - first_word_time) / audio_duration)
        
        # Check for gaps in timing
        gaps = 0
        for i in range(1, len(word_alignments)):
            gap = word_alignments[i]['start_time'] - word_alignments[i-1]['end_time']
            if gap > 0.5:  # Gap larger than 0.5 seconds
                gaps += 1
        
        gap_penalty = min(0.3, gaps * 0.1)
        
        return max(0.0, coverage - gap_penalty)
    
    def _estimate_word_timings(self, text: str, audio_duration: float) -> List[Dict[str, any]]:
        """Estimate word timings when not provided by Azure"""
        words = text.strip().split()
        if not words:
            return []
        
        # Simple linear distribution
        word_duration = audio_duration / len(words)
        word_alignments = []
        
        for i, word in enumerate(words):
            start_time = i * word_duration
            end_time = (i + 1) * word_duration
            
            word_alignments.append({
                "word": word,
                "start_time": start_time,
                "end_time": end_time,
                "duration": word_duration,
                "confidence": 0.5  # Low confidence for estimated timings
            })
        
        return word_alignments
    
    def _create_phoneme_alignments(self, word_alignments: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Create simplified phoneme alignments"""
        phoneme_alignments = []
        
        for word_align in word_alignments:
            # Simple phoneme breakdown (this would be enhanced with actual phoneme analysis)
            word = word_align['word']
            start_time = word_align['start_time']
            end_time = word_align['end_time']
            
            # Estimate phoneme timing
            phoneme_count = len(word)  # Simplified: one phoneme per character
            if phoneme_count > 0:
                phoneme_duration = (end_time - start_time) / phoneme_count
                
                for i, char in enumerate(word):
                    phoneme_start = start_time + (i * phoneme_duration)
                    phoneme_end = start_time + ((i + 1) * phoneme_duration)
                    
                    phoneme_alignments.append({
                        "phoneme": char,
                        "start_time": phoneme_start,
                        "end_time": phoneme_end,
                        "duration": phoneme_duration,
                        "word": word,
                        "position": i
                    })
        
        return phoneme_alignments
