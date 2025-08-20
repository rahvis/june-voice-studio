"""
Voice Selection and Fallback Logic Service

This module handles voice selection algorithms, fallback mechanisms,
and voice availability checking for the synthesis service.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VoiceType(Enum):
    """Voice type enumeration"""
    CUSTOM_NEURAL = "custom_neural"
    STOCK_NEURAL = "stock_neural"
    OPENAI_TTS = "openai_tts"
    FALLBACK = "fallback"

class VoiceStatus(Enum):
    """Voice status enumeration"""
    AVAILABLE = "available"
    TRAINING = "training"
    FAILED = "failed"
    EXPIRED = "expired"
    UNAVAILABLE = "unavailable"

class VoiceQuality(Enum):
    """Voice quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"

@dataclass
class VoiceInfo:
    """Voice information data structure"""
    voice_id: str
    voice_name: str
    voice_type: VoiceType
    status: VoiceStatus
    language: str
    gender: str
    quality: VoiceQuality
    created_at: datetime
    last_used: Optional[datetime]
    usage_count: int
    metadata: Dict[str, any]

@dataclass
class VoiceSelectionResult:
    """Voice selection result"""
    selected_voice: VoiceInfo
    fallback_used: bool
    fallback_reason: Optional[str]
    confidence: float
    alternatives: List[VoiceInfo]
    metadata: Dict[str, any]

class VoiceSelector:
    """Voice selection and fallback logic service"""
    
    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.voice_registry = config.get('voice_registry')
        self.fallback_strategy = config.get('fallback_strategy', 'graceful')
        self.preferred_voice_types = config.get('preferred_voice_types', [
            VoiceType.CUSTOM_NEURAL,
            VoiceType.STOCK_NEURAL,
            VoiceType.OPENAI_TTS
        ])
        
    async def select_voice(self, 
                          user_id: str,
                          language: str,
                          gender: Optional[str] = None,
                          voice_preference: Optional[str] = None,
                          quality_threshold: Optional[VoiceQuality] = None) -> VoiceSelectionResult:
        """
        Select the best available voice for synthesis
        
        Args:
            user_id: User identifier
            language: Target language code
            gender: Preferred gender (optional)
            voice_preference: Specific voice preference (optional)
            quality_threshold: Minimum quality threshold (optional)
            
        Returns:
            Voice selection result
        """
        try:
            # Get available voices for the user and language
            available_voices = await self._get_available_voices(user_id, language, gender)
            
            if not available_voices:
                # No voices available, use fallback
                fallback_voice = await self._get_fallback_voice(language, gender)
                return VoiceSelectionResult(
                    selected_voice=fallback_voice,
                    fallback_used=True,
                    fallback_reason="No voices available for user and language",
                    confidence=0.5,
                    alternatives=[],
                    metadata={"fallback_type": "no_voices_available"}
                )
            
            # Apply quality threshold if specified
            if quality_threshold:
                available_voices = self._filter_by_quality(available_voices, quality_threshold)
            
            # Sort voices by priority
            sorted_voices = self._sort_voices_by_priority(available_voices, voice_preference)
            
            # Select the best voice
            selected_voice = sorted_voices[0] if sorted_voices else None
            
            if not selected_voice:
                # No voices meet quality threshold, use fallback
                fallback_voice = await self._get_fallback_voice(language, gender)
                return VoiceSelectionResult(
                    selected_voice=fallback_voice,
                    fallback_used=True,
                    fallback_reason=f"No voices meet quality threshold: {quality_threshold}",
                    confidence=0.5,
                    alternatives=[],
                    metadata={"fallback_type": "quality_threshold_not_met"}
                )
            
            # Check if fallback is needed
            fallback_used = selected_voice.voice_type != VoiceType.CUSTOM_NEURAL
            fallback_reason = None
            
            if fallback_used:
                fallback_reason = f"Using {selected_voice.voice_type.value} instead of custom neural voice"
            
            # Get alternative voices
            alternatives = sorted_voices[1:4] if len(sorted_voices) > 1 else []
            
            # Calculate confidence based on voice quality and type
            confidence = self._calculate_voice_confidence(selected_voice)
            
            return VoiceSelectionResult(
                selected_voice=selected_voice,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
                confidence=confidence,
                alternatives=alternatives,
                metadata={
                    "total_available_voices": len(available_voices),
                    "voice_selection_algorithm": "priority_based"
                }
            )
            
        except Exception as e:
            logger.error(f"Error selecting voice: {str(e)}")
            # Return fallback voice on error
            fallback_voice = await self._get_fallback_voice(language, gender)
            return VoiceSelectionResult(
                selected_voice=fallback_voice,
                fallback_used=True,
                fallback_reason=f"Error in voice selection: {str(e)}",
                confidence=0.3,
                alternatives=[],
                metadata={"error": str(e)}
            )
    
    async def _get_available_voices(self, user_id: str, language: str, gender: Optional[str] = None) -> List[VoiceInfo]:
        """Get available voices for user and language"""
        available_voices = []
        
        try:
            # Get user's custom neural voices
            if self.voice_registry:
                custom_voices = await self.voice_registry.get_user_voices(user_id, language)
                available_voices.extend(custom_voices)
            
            # Get stock neural voices for the language
            stock_voices = await self._get_stock_neural_voices(language, gender)
            available_voices.extend(stock_voices)
            
            # Get OpenAI TTS voices for the language
            openai_voices = await self._get_openai_tts_voices(language, gender)
            available_voices.extend(openai_voices)
            
            # Filter by availability and status
            available_voices = [v for v in available_voices if v.status == VoiceStatus.AVAILABLE]
            
            return available_voices
            
        except Exception as e:
            logger.error(f"Error getting available voices: {str(e)}")
            return []
    
    async def _get_stock_neural_voices(self, language: str, gender: Optional[str] = None) -> List[VoiceInfo]:
        """Get stock neural voices for the language"""
        # This would integrate with Azure Speech Service to get available stock voices
        stock_voices = []
        
        # Common stock voices for major languages
        stock_voice_map = {
            "en-US": [
                {"name": "en-US-AriaNeural", "gender": "Female"},
                {"name": "en-US-GuyNeural", "gender": "Male"},
                {"name": "en-US-JennyNeural", "gender": "Female"},
                {"name": "en-US-TonyNeural", "gender": "Male"}
            ],
            "de-DE": [
                {"name": "de-DE-KatjaNeural", "gender": "Female"},
                {"name": "de-DE-ConradNeural", "gender": "Male"}
            ],
            "fr-FR": [
                {"name": "fr-FR-DeniseNeural", "gender": "Female"},
                {"name": "fr-FR-HenriNeural", "gender": "Male"}
            ],
            "es-ES": [
                {"name": "es-ES-ElviraNeural", "gender": "Female"},
                {"name": "es-ES-AlvaroNeural", "gender": "Male"}
            ],
            "ja-JP": [
                {"name": "ja-JP-NanamiNeural", "gender": "Female"},
                {"name": "ja-JP-KeitaNeural", "gender": "Male"}
            ]
        }
        
        if language in stock_voice_map:
            for voice_info in stock_voice_map[language]:
                if not gender or voice_info["gender"] == gender:
                    stock_voices.append(VoiceInfo(
                        voice_id=f"stock_{voice_info['name']}",
                        voice_name=voice_info["name"],
                        voice_type=VoiceType.STOCK_NEURAL,
                        status=VoiceStatus.AVAILABLE,
                        language=language,
                        gender=voice_info["gender"],
                        quality=VoiceQuality.GOOD,
                        created_at=datetime.utcnow(),
                        last_used=None,
                        usage_count=0,
                        metadata={"stock_voice": True}
                    ))
        
        return stock_voices
    
    async def _get_openai_tts_voices(self, language: str, gender: Optional[str] = None) -> List[VoiceInfo]:
        """Get OpenAI TTS voices for the language"""
        # This would integrate with Azure OpenAI Service
        openai_voices = []
        
        # OpenAI TTS supports multiple languages
        supported_languages = ["en", "de", "fr", "es", "it", "ja", "ko", "zh", "pt", "ru"]
        
        if language.split("-")[0] in supported_languages:
            openai_voices.append(VoiceInfo(
                voice_id="openai_tts_default",
                voice_name="gpt-4o-mini-tts",
                voice_type=VoiceType.OPENAI_TTS,
                status=VoiceStatus.AVAILABLE,
                language=language,
                gender="neutral",
                quality=VoiceQuality.GOOD,
                created_at=datetime.utcnow(),
                last_used=None,
                usage_count=0,
                metadata={
                    "openai_model": "gpt-4o-mini-tts",
                    "fallback_voice": True
                }
            ))
        
        return openai_voices
    
    async def _get_fallback_voice(self, language: str, gender: Optional[str] = None) -> VoiceInfo:
        """Get fallback voice when no preferred voices are available"""
        try:
            # Try to get a stock neural voice as fallback
            fallback_voices = await self._get_stock_neural_voices(language, gender)
            
            if fallback_voices:
                return fallback_voices[0]
            
            # If no stock voices, create a generic fallback
            return VoiceInfo(
                voice_id="fallback_generic",
                voice_name="fallback-voice",
                voice_type=VoiceType.FALLBACK,
                status=VoiceStatus.AVAILABLE,
                language=language,
                gender=gender or "neutral",
                quality=VoiceQuality.ACCEPTABLE,
                created_at=datetime.utcnow(),
                last_used=None,
                usage_count=0,
                metadata={"fallback_type": "generic", "emergency": True}
            )
            
        except Exception as e:
            logger.error(f"Error getting fallback voice: {str(e)}")
            # Return emergency fallback
            return VoiceInfo(
                voice_id="emergency_fallback",
                voice_name="emergency-voice",
                voice_type=VoiceType.FALLBACK,
                status=VoiceStatus.AVAILABLE,
                language="en-US",
                gender="neutral",
                quality=VoiceQuality.POOR,
                created_at=datetime.utcnow(),
                last_used=None,
                usage_count=0,
                metadata={"fallback_type": "emergency", "error": str(e)}
            )
    
    def _filter_by_quality(self, voices: List[VoiceInfo], quality_threshold: VoiceQuality) -> List[VoiceInfo]:
        """Filter voices by quality threshold"""
        quality_order = {
            VoiceQuality.EXCELLENT: 4,
            VoiceQuality.GOOD: 3,
            VoiceQuality.ACCEPTABLE: 2,
            VoiceQuality.POOR: 1
        }
        
        threshold_level = quality_order.get(quality_threshold, 1)
        
        return [
            voice for voice in voices
            if quality_order.get(voice.quality, 0) >= threshold_level
        ]
    
    def _sort_voices_by_priority(self, voices: List[VoiceInfo], voice_preference: Optional[str] = None) -> List[VoiceInfo]:
        """Sort voices by priority order"""
        if not voices:
            return []
        
        # If specific voice preference is provided, prioritize it
        if voice_preference:
            preferred_voices = [v for v in voices if v.voice_name == voice_preference]
            other_voices = [v for v in voices if v.voice_name != voice_preference]
            voices = preferred_voices + other_voices
        
        # Sort by voice type priority
        type_priority = {
            VoiceType.CUSTOM_NEURAL: 1,
            VoiceType.STOCK_NEURAL: 2,
            VoiceType.OPENAI_TTS: 3,
            VoiceType.FALLBACK: 4
        }
        
        # Sort by multiple criteria
        sorted_voices = sorted(voices, key=lambda v: (
            type_priority.get(v.voice_type, 5),  # Voice type priority
            -quality_order.get(v.quality, 0),    # Quality (higher is better)
            -v.usage_count,                      # Usage count (lower is better)
            v.last_used or datetime.min          # Last used (older is better)
        ))
        
        return sorted_voices
    
    def _calculate_voice_confidence(self, voice: VoiceInfo) -> float:
        """Calculate confidence score for voice selection"""
        base_confidence = 0.8
        
        # Adjust based on voice type
        type_confidence = {
            VoiceType.CUSTOM_NEURAL: 1.0,
            VoiceType.STOCK_NEURAL: 0.9,
            VoiceType.OPENAI_TTS: 0.8,
            VoiceType.FALLBACK: 0.6
        }
        
        type_multiplier = type_confidence.get(voice.voice_type, 0.7)
        
        # Adjust based on quality
        quality_confidence = {
            VoiceQuality.EXCELLENT: 1.0,
            VoiceQuality.GOOD: 0.9,
            VoiceQuality.ACCEPTABLE: 0.8,
            VoiceQuality.POOR: 0.6
        }
        
        quality_multiplier = quality_confidence.get(voice.quality, 0.7)
        
        # Adjust based on usage count (prefer less used voices)
        usage_multiplier = max(0.8, 1.0 - (voice.usage_count * 0.01))
        
        # Calculate final confidence
        confidence = base_confidence * type_multiplier * quality_multiplier * usage_multiplier
        
        return min(1.0, max(0.0, confidence))
    
    async def check_voice_availability(self, voice_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a specific voice is available
        
        Args:
            voice_id: Voice identifier to check
            
        Returns:
            Tuple of (is_available, error_message)
        """
        try:
            if not self.voice_registry:
                return False, "Voice registry not available"
            
            voice_info = await self.voice_registry.get_voice(voice_id)
            
            if not voice_info:
                return False, "Voice not found"
            
            if voice_info.status != VoiceStatus.AVAILABLE:
                return False, f"Voice status: {voice_info.status.value}"
            
            # Check if voice is expired
            if voice_info.metadata.get("expires_at"):
                expires_at = datetime.fromisoformat(voice_info.metadata["expires_at"])
                if datetime.utcnow() > expires_at:
                    return False, "Voice has expired"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking voice availability: {str(e)}")
            return False, f"Error: {str(e)}"
    
    async def get_voice_recommendations(self, 
                                      user_id: str,
                                      language: str,
                                      context: Optional[str] = None) -> List[VoiceInfo]:
        """
        Get voice recommendations for user
        
        Args:
            user_id: User identifier
            language: Target language
            context: Usage context (e.g., "business", "casual", "narration")
            
        Returns:
            List of recommended voices
        """
        try:
            # Get available voices
            available_voices = await self._get_available_voices(user_id, language)
            
            if not available_voices:
                return []
            
            # Apply context-based filtering
            if context:
                available_voices = self._filter_by_context(available_voices, context)
            
            # Sort by recommendation score
            recommended_voices = sorted(
                available_voices,
                key=lambda v: self._calculate_recommendation_score(v, user_id, context),
                reverse=True
            )
            
            return recommended_voices[:5]  # Return top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error getting voice recommendations: {str(e)}")
            return []
    
    def _filter_by_context(self, voices: List[VoiceInfo], context: str) -> List[VoiceInfo]:
        """Filter voices by usage context"""
        context_filters = {
            "business": lambda v: v.gender in ["Male", "Female"] and v.quality in [VoiceQuality.EXCELLENT, VoiceQuality.GOOD],
            "casual": lambda v: True,  # Accept all voices
            "narration": lambda v: v.voice_type in [VoiceType.CUSTOM_NEURAL, VoiceType.STOCK_NEURAL],
            "accessibility": lambda v: v.quality in [VoiceQuality.EXCELLENT, VoiceQuality.GOOD]
        }
        
        filter_func = context_filters.get(context.lower(), lambda v: True)
        return [v for v in voices if filter_func(v)]
    
    def _calculate_recommendation_score(self, voice: VoiceInfo, user_id: str, context: Optional[str] = None) -> float:
        """Calculate recommendation score for a voice"""
        score = 0.0
        
        # Base score from quality
        quality_scores = {
            VoiceQuality.EXCELLENT: 10.0,
            VoiceQuality.GOOD: 8.0,
            VoiceQuality.ACCEPTABLE: 6.0,
            VoiceQuality.POOR: 4.0
        }
        score += quality_scores.get(voice.quality, 5.0)
        
        # Bonus for custom neural voices
        if voice.voice_type == VoiceType.CUSTOM_NEURAL:
            score += 5.0
        
        # Bonus for stock neural voices
        elif voice.voice_type == VoiceType.STOCK_NEURAL:
            score += 3.0
        
        # Penalty for high usage (prefer less used voices)
        usage_penalty = min(2.0, voice.usage_count * 0.1)
        score -= usage_penalty
        
        # Context-specific adjustments
        if context == "business":
            if voice.quality in [VoiceQuality.EXCELLENT, VoiceQuality.GOOD]:
                score += 2.0
        
        elif context == "narration":
            if voice.voice_type in [VoiceType.CUSTOM_NEURAL, VoiceType.STOCK_NEURAL]:
                score += 3.0
        
        return max(0.0, score)
    
    async def update_voice_usage(self, voice_id: str):
        """Update voice usage statistics"""
        try:
            if self.voice_registry:
                await self.voice_registry.increment_usage_count(voice_id)
                await self.voice_registry.update_last_used(voice_id, datetime.utcnow())
                
        except Exception as e:
            logger.error(f"Error updating voice usage: {str(e)}")
    
    def get_voice_statistics(self) -> Dict[str, any]:
        """Get voice selection service statistics"""
        return {
            "fallback_strategy": self.fallback_strategy,
            "preferred_voice_types": [vt.value for vt in self.preferred_voice_types],
            "voice_registry_available": self.voice_registry is not None,
            "total_voice_types": len(VoiceType),
            "total_voice_statuses": len(VoiceStatus),
            "total_voice_qualities": len(VoiceQuality)
        }
