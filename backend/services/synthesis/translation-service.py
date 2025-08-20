"""
Azure AI Translator Service Integration

This module integrates with Azure AI Translator service to provide
multi-language translation capabilities for voice synthesis.
"""

import requests
import json
import hashlib
import time
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime, timedelta
import uuid
import re

logger = logging.getLogger(__name__)

class TranslationStatus(Enum):
    """Translation status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"

class TranslationQuality(Enum):
    """Translation quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNUSABLE = "unusable"

@dataclass
class TranslationRequest:
    """Translation request data structure"""
    request_id: str
    source_text: str
    source_language: str
    target_language: str
    status: TranslationStatus
    created_at: datetime
    completed_at: Optional[datetime]
    translated_text: Optional[str]
    confidence: Optional[float]
    quality: Optional[TranslationQuality]
    metadata: Dict[str, any]

@dataclass
class TranslationResult:
    """Translation result data structure"""
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    quality: TranslationQuality
    alternatives: List[str]
    detected_language: Optional[str]
    detected_confidence: Optional[float]
    metadata: Dict[str, any]

class AzureTranslatorService:
    """Azure AI Translator service integration"""
    
    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.translator_key = config['translator_key']
        self.translator_region = config['translator_region']
        self.endpoint = f"https://{self.translator_region}.api.cognitive.microsoft.com"
        self.headers = {
            'Ocp-Apim-Subscription-Key': self.translator_key,
            'Content-Type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        self.cache_client = config.get('cache_client')
        self.rate_limiter = config.get('rate_limiter')
        
        # Supported language pairs
        self.supported_languages = self._load_supported_languages()
        
    def _load_supported_languages(self) -> Dict[str, Dict[str, any]]:
        """Load supported language configurations"""
        return {
            "en": {"name": "English", "native_name": "English", "dir": "ltr"},
            "de": {"name": "German", "native_name": "Deutsch", "dir": "ltr"},
            "fr": {"name": "French", "native_name": "Français", "dir": "ltr"},
            "es": {"name": "Spanish", "native_name": "Español", "dir": "ltr"},
            "it": {"name": "Italian", "native_name": "Italiano", "dir": "ltr"},
            "ja": {"name": "Japanese", "native_name": "日本語", "dir": "ltr"},
            "ko": {"name": "Korean", "native_name": "한국어", "dir": "ltr"},
            "zh": {"name": "Chinese", "native_name": "中文", "dir": "ltr"},
            "pt": {"name": "Portuguese", "native_name": "Português", "dir": "ltr"},
            "ru": {"name": "Russian", "native_name": "Русский", "dir": "ltr"},
            "nl": {"name": "Dutch", "native_name": "Nederlands", "dir": "ltr"},
            "sv": {"name": "Swedish", "native_name": "Svenska", "dir": "ltr"},
            "no": {"name": "Norwegian", "native_name": "Norsk", "dir": "ltr"},
            "da": {"name": "Danish", "native_name": "Dansk", "dir": "ltr"},
            "fi": {"name": "Finnish", "native_name": "Suomi", "dir": "ltr"},
            "pl": {"name": "Polish", "native_name": "Polski", "dir": "ltr"},
            "cs": {"name": "Czech", "native_name": "Čeština", "dir": "ltr"},
            "hu": {"name": "Hungarian", "native_name": "Magyar", "dir": "ltr"},
            "ar": {"name": "Arabic", "native_name": "العربية", "dir": "rtl"},
            "he": {"name": "Hebrew", "native_name": "עברית", "dir": "rtl"},
            "hi": {"name": "Hindi", "native_name": "हिन्दी", "dir": "ltr"},
            "th": {"name": "Thai", "native_name": "ไทย", "dir": "ltr"},
            "vi": {"name": "Vietnamese", "native_name": "Tiếng Việt", "dir": "ltr"}
        }
    
    async def translate_text(self, 
                           text: str,
                           target_language: str,
                           source_language: Optional[str] = None,
                           request_id: Optional[str] = None) -> TranslationResult:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (auto-detected if None)
            request_id: Optional request identifier
            
        Returns:
            Translation result
        """
        try:
            # Validate inputs
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            if target_language not in self.supported_languages:
                raise ValueError(f"Unsupported target language: {target_language}")
            
            # Check cache first
            cache_key = self._generate_cache_key(text, target_language, source_language)
            cached_result = await self._get_cached_translation(cache_key)
            
            if cached_result:
                logger.info(f"Translation found in cache for request {request_id}")
                return cached_result
            
            # Auto-detect source language if not provided
            if not source_language:
                source_language = await self.detect_language(text)
                logger.info(f"Detected source language: {source_language} for request {request_id}")
            
            # Validate source language
            if source_language not in self.supported_languages:
                raise ValueError(f"Unsupported source language: {source_language}")
            
            # Check if translation is needed
            if source_language == target_language:
                logger.info(f"Source and target languages are the same for request {request_id}")
                return TranslationResult(
                    translated_text=text,
                    source_language=source_language,
                    target_language=target_language,
                    confidence=1.0,
                    quality=TranslationQuality.EXCELLENT,
                    alternatives=[],
                    detected_language=source_language,
                    detected_confidence=1.0,
                    metadata={"no_translation_needed": True}
                )
            
            # Perform translation
            translation_result = await self._perform_translation(
                text, source_language, target_language
            )
            
            # Cache the result
            await self._cache_translation(cache_key, translation_result)
            
            logger.info(f"Translation completed for request {request_id}")
            return translation_result
            
        except Exception as e:
            logger.error(f"Translation failed for request {request_id}: {str(e)}")
            raise
    
    async def translate_multiple_texts(self, 
                                     texts: List[str],
                                     target_language: str,
                                     source_language: Optional[str] = None) -> List[TranslationResult]:
        """
        Translate multiple texts to target language
        
        Args:
            texts: List of texts to translate
            target_language: Target language code
            source_language: Source language code (auto-detected if None)
            
        Returns:
            List of translation results
        """
        if not texts:
            return []
        
        # Process translations concurrently
        tasks = []
        for text in texts:
            task = self.translate_text(text, target_language, source_language)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for result in results:
            if isinstance(result, TranslationResult):
                valid_results.append(result)
            else:
                logger.error(f"Translation task failed: {result}")
        
        return valid_results
    
    async def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of input text
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (detected_language, confidence)
        """
        try:
            if not text or len(text.strip()) < 10:
                return "en", 0.5
            
            # Use Azure Translator's language detection
            request_url = f"{self.endpoint}/translator/text/v3.0/detect"
            
            request_body = [{"text": text}]
            
            response = requests.post(
                request_url,
                headers=self.headers,
                json=request_body
            )
            
            if response.status_code == 200:
                detection_results = response.json()
                
                if detection_results and len(detection_results) > 0:
                    result = detection_results[0]
                    detected_lang = result.get('language', 'en')
                    confidence = result.get('score', 0.0)
                    
                    # Map to supported language code
                    mapped_lang = self._map_language_code(detected_lang)
                    
                    return mapped_lang, confidence
            
            # Fallback to pattern matching
            return self._detect_by_patterns(text), 0.7
            
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return "en", 0.1
    
    def _map_language_code(self, detected_lang: str) -> str:
        """Map detected language to supported language code"""
        # Azure Translator uses different language codes than our system
        lang_mapping = {
            "en": "en",
            "de": "de",
            "fr": "fr",
            "es": "es",
            "it": "it",
            "ja": "ja",
            "ko": "ko",
            "zh-Hans": "zh",
            "zh-Hant": "zh",
            "pt": "pt",
            "ru": "ru",
            "nl": "nl",
            "sv": "sv",
            "no": "no",
            "da": "da",
            "fi": "fi",
            "pl": "pl",
            "cs": "cs",
            "hu": "hu",
            "ar": "ar",
            "he": "he",
            "hi": "hi",
            "th": "th",
            "vi": "vi"
        }
        
        return lang_mapping.get(detected_lang, "en")
    
    def _detect_by_patterns(self, text: str) -> str:
        """Detect language using pattern matching as fallback"""
        text_lower = text.lower()
        
        # Simple pattern matching for common languages
        patterns = {
            "de": [r'\bder\b', r'\bdie\b', r'\bdas\b', r'\bund\b'],
            "fr": [r'\ble\b', r'\bla\b', r'\bles\b', r'\bet\b'],
            "es": [r'\bel\b', r'\bla\b', r'\blos\b', r'\blas\b'],
            "it": [r'\bil\b', r'\bla\b', r'\bi\b', r'\ble\b"],
            "ja": [r'[あ-ん]', r'[ア-ン]', r'[一-龯]'],
            "ko": [r'[가-힣]', r'[ㄱ-ㅎ]', r'[ㅏ-ㅣ]'],
            "zh": [r'[一-龯]'],
            "ru": [r'[а-я]', r'[А-Я]'],
            "ar": [r'[ء-ي]'],
            "he": [r'[א-ת]']
        }
        
        for lang_code, lang_patterns in patterns.items():
            pattern_count = sum(len(re.findall(pattern, text_lower)) for pattern in lang_patterns)
            if pattern_count > 0:
                return lang_code
        
        return "en"
    
    async def _perform_translation(self, 
                                 text: str,
                                 source_language: str,
                                 target_language: str) -> TranslationResult:
        """Perform the actual translation using Azure Translator"""
        try:
            # Check rate limits
            if self.rate_limiter:
                await self.rate_limiter.wait_for_permission()
            
            # Prepare translation request
            request_url = f"{self.endpoint}/translator/text/v3.0/translate"
            
            params = {
                'api-version': '3.0',
                'from': source_language,
                'to': target_language
            }
            
            request_body = [{"text": text}]
            
            # Make translation request
            response = requests.post(
                request_url,
                headers=self.headers,
                params=params,
                json=request_body
            )
            
            if response.status_code == 200:
                translation_results = response.json()
                
                if translation_results and len(translation_results) > 0:
                    result = translation_results[0]
                    
                    # Extract translation
                    translated_text = result.get('translations', [{}])[0].get('text', '')
                    
                    # Get alternatives if available
                    alternatives = []
                    for translation in result.get('translations', []):
                        if translation.get('text') != translated_text:
                            alternatives.append(translation.get('text', ''))
                    
                    # Calculate quality score
                    quality = self._calculate_translation_quality(text, translated_text)
                    
                    # Create result
                    translation_result = TranslationResult(
                        translated_text=translated_text,
                        source_language=source_language,
                        target_language=target_language,
                        confidence=0.9,  # Azure Translator confidence
                        quality=quality,
                        alternatives=alternatives,
                        detected_language=source_language,
                        detected_confidence=1.0,
                        metadata={
                            "azure_translation": True,
                            "response_time": response.elapsed.total_seconds()
                        }
                    )
                    
                    return translation_result
                else:
                    raise ValueError("Empty translation response from Azure")
            else:
                error_message = f"Azure Translator error: {response.status_code} - {response.text}"
                logger.error(error_message)
                raise Exception(error_message)
                
        except Exception as e:
            logger.error(f"Translation request failed: {str(e)}")
            raise
    
    def _calculate_translation_quality(self, source_text: str, translated_text: str) -> TranslationQuality:
        """Calculate translation quality based on various factors"""
        if not source_text or not translated_text:
            return TranslationQuality.UNUSABLE
        
        # Simple quality heuristics
        source_words = len(source_text.split())
        translated_words = len(translated_text.split())
        
        # Check word count ratio
        if source_words > 0:
            word_ratio = translated_words / source_words
            
            if 0.8 <= word_ratio <= 1.2:
                return TranslationQuality.EXCELLENT
            elif 0.6 <= word_ratio <= 1.4:
                return TranslationQuality.GOOD
            elif 0.4 <= word_ratio <= 1.6:
                return TranslationQuality.ACCEPTABLE
            else:
                return TranslationQuality.POOR
        
        return TranslationQuality.ACCEPTABLE
    
    def _generate_cache_key(self, text: str, target_language: str, source_language: Optional[str]) -> str:
        """Generate cache key for translation"""
        content = f"{text}:{target_language}:{source_language or 'auto'}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def _get_cached_translation(self, cache_key: str) -> Optional[TranslationResult]:
        """Get cached translation result"""
        if not self.cache_client:
            return None
        
        try:
            cached_data = await self.cache_client.get(f"translation:{cache_key}")
            if cached_data:
                # Parse cached data back to TranslationResult
                data = json.loads(cached_data)
                return TranslationResult(**data)
        except Exception as e:
            logger.warning(f"Error retrieving cached translation: {str(e)}")
        
        return None
    
    async def _cache_translation(self, cache_key: str, translation_result: TranslationResult):
        """Cache translation result"""
        if not self.cache_client:
            return
        
        try:
            # Convert to JSON-serializable format
            cache_data = {
                "translated_text": translation_result.translated_text,
                "source_language": translation_result.source_language,
                "target_language": translation_result.target_language,
                "confidence": translation_result.confidence,
                "quality": translation_result.quality.value,
                "alternatives": translation_result.alternatives,
                "detected_language": translation_result.detected_language,
                "detected_confidence": translation_result.detected_confidence,
                "metadata": translation_result.metadata
            }
            
            # Cache for 24 hours
            await self.cache_client.set(
                f"translation:{cache_key}",
                json.dumps(cache_data),
                expire=86400
            )
            
        except Exception as e:
            logger.warning(f"Error caching translation: {str(e)}")
    
    def validate_language_pair(self, source_language: str, target_language: str) -> Tuple[bool, str]:
        """
        Validate if translation between languages is supported
        
        Args:
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []
        
        if source_language not in self.supported_languages:
            errors.append(f"Unsupported source language: {source_language}")
        
        if target_language not in self.supported_languages:
            errors.append(f"Unsupported target language: {target_language}")
        
        if source_language == target_language:
            errors.append("Source and target languages cannot be the same")
        
        is_valid = len(errors) == 0
        error_message = "; ".join(errors) if errors else ""
        
        return is_valid, error_message
    
    def get_supported_languages(self) -> List[Dict[str, any]]:
        """Get list of supported languages"""
        return [
            {
                "code": lang_code,
                "name": lang_info["name"],
                "native_name": lang_info["native_name"],
                "direction": lang_info["dir"]
            }
            for lang_code, lang_info in self.supported_languages.items()
        ]
    
    def get_translation_statistics(self) -> Dict[str, any]:
        """Get translation service statistics"""
        return {
            "supported_languages": len(self.supported_languages),
            "total_language_pairs": len(self.supported_languages) * (len(self.supported_languages) - 1),
            "cache_enabled": self.cache_client is not None,
            "rate_limiting_enabled": self.rate_limiter is not None,
            "service_endpoint": self.endpoint,
            "service_region": self.translator_region
        }
    
    async def health_check(self) -> Dict[str, any]:
        """Perform health check on the translation service"""
        try:
            # Test with a simple translation
            test_text = "Hello"
            test_result = await self.translate_text(test_text, "es", "en")
            
            return {
                "status": "healthy",
                "response_time": test_result.metadata.get("response_time", 0),
                "last_check": datetime.utcnow().isoformat(),
                "test_translation": test_result.translated_text
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
