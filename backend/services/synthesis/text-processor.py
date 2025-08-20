"""
Text Processing Engine for Voice Synthesis

This module handles text preprocessing, language detection, SSML generation,
and prosody controls for the voice synthesis service.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import langdetect
from langdetect import DetectorFactory
import unicodedata

logger = logging.getLogger(__name__)

# Set seed for consistent language detection
DetectorFactory.seed = 0

class LanguageCode(Enum):
    """Supported language codes"""
    ENGLISH_US = "en-US"
    ENGLISH_GB = "en-GB"
    ENGLISH_AU = "en-AU"
    GERMAN = "de-DE"
    FRENCH = "fr-FR"
    SPANISH = "es-ES"
    ITALIAN = "it-IT"
    JAPANESE = "ja-JP"
    KOREAN = "ko-KR"
    CHINESE_SIMPLIFIED = "zh-CN"
    PORTUGUESE_BRAZIL = "pt-BR"
    RUSSIAN = "ru-RU"
    DUTCH = "nl-NL"
    SWEDISH = "sv-SE"
    NORWEGIAN = "no-NO"
    DANISH = "da-DK"
    FINNISH = "fi-FI"
    POLISH = "pl-PL"
    CZECH = "cs-CZ"
    HUNGARIAN = "hu-HU"

class ProsodyType(Enum):
    """Prosody modification types"""
    RATE = "rate"
    PITCH = "pitch"
    VOLUME = "volume"
    PAUSE = "pause"

@dataclass
class TextSegment:
    """Text segment with metadata"""
    text: str
    language: str
    start_position: int
    end_position: int
    confidence: float
    metadata: Dict[str, any]

@dataclass
class SSMLSegment:
    """SSML segment with prosody controls"""
    text: str
    language: str
    prosody: Dict[str, any]
    voice_name: Optional[str]
    metadata: Dict[str, any]

class TextProcessor:
    """Text processing and SSML generation engine"""
    
    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.supported_languages = self._load_supported_languages()
        self.language_patterns = self._load_language_patterns()
        self.prosody_presets = self._load_prosody_presets()
        
    def _load_supported_languages(self) -> Dict[str, Dict[str, any]]:
        """Load supported language configurations"""
        return {
            "en-US": {"name": "English (US)", "locale": "en-US", "gender": "neutral"},
            "en-GB": {"name": "English (UK)", "locale": "en-GB", "gender": "neutral"},
            "en-AU": {"name": "English (Australia)", "locale": "en-AU", "gender": "neutral"},
            "de-DE": {"name": "German", "locale": "de-DE", "gender": "neutral"},
            "fr-FR": {"name": "French", "locale": "fr-FR", "gender": "neutral"},
            "es-ES": {"name": "Spanish", "locale": "es-ES", "gender": "neutral"},
            "it-IT": {"name": "Italian", "locale": "it-IT", "gender": "neutral"},
            "ja-JP": {"name": "Japanese", "locale": "ja-JP", "gender": "neutral"},
            "ko-KR": {"name": "Korean", "locale": "ko-KR", "gender": "neutral"},
            "zh-CN": {"name": "Chinese (Simplified)", "locale": "zh-CN", "gender": "neutral"},
            "pt-BR": {"name": "Portuguese (Brazil)", "locale": "pt-BR", "gender": "neutral"},
            "ru-RU": {"name": "Russian", "locale": "ru-RU", "gender": "neutral"}
        }
    
    def _load_language_patterns(self) -> Dict[str, List[str]]:
        """Load language-specific text patterns"""
        return {
            "en-US": [r'\bthe\b', r'\band\b', r'\bor\b', r'\bof\b', r'\bto\b'],
            "de-DE": [r'\bder\b', r'\bdie\b', r'\bdas\b', r'\bund\b', r'\boder\b'],
            "fr-FR": [r'\ble\b', r'\bla\b', r'\bles\b', r'\bet\b', r'\bou\b'],
            "es-ES": [r'\bel\b', r'\bla\b', r'\blos\b', r'\blas\b', r'\by\b'],
            "it-IT": [r'\bil\b', r'\bla\b', r'\bi\b', r'\ble\b', r'\bo\b"],
            "ja-JP": [r'[あ-ん]', r'[ア-ン]', r'[一-龯]'],
            "ko-KR": [r'[가-힣]', r'[ㄱ-ㅎ]', r'[ㅏ-ㅣ]'],
            "zh-CN": [r'[一-龯]', r'[一-龯]', r'[一-龯]'],
            "pt-BR": [r'\bo\b', r'\ba\b', r'\bos\b', r'\bas\b', r'\be\b'],
            "ru-RU": [r'\bи\b', r'\bв\b', r'\bна\b', r'\bс\b', r'\bпо\b']
        }
    
    def _load_prosody_presets(self) -> Dict[str, Dict[str, any]]:
        """Load prosody modification presets"""
        return {
            "excited": {
                "rate": "+20%",
                "pitch": "+2st",
                "volume": "+10%"
            },
            "calm": {
                "rate": "-10%",
                "pitch": "-1st",
                "volume": "-5%"
            },
            "emphasized": {
                "rate": "0%",
                "pitch": "+1st",
                "volume": "+15%"
            },
            "whisper": {
                "rate": "-20%",
                "pitch": "-2st",
                "volume": "-20%"
            },
            "slow": {
                "rate": "-30%",
                "pitch": "0st",
                "volume": "0%"
            },
            "fast": {
                "rate": "+30%",
                "pitch": "0st",
                "volume": "0%"
            }
        }
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess and clean input text
        
        Args:
            text: Input text to process
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Normalize unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Clean up punctuation
        text = re.sub(r'([.!?])\1+', r'\1', text)
        text = re.sub(r'([,;:])\1+', r'\1', text)
        
        # Fix common text issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
        
        # Trim whitespace
        text = text.strip()
        
        return text
    
    def detect_language(self, text: str, fallback_language: str = "en-US") -> Tuple[str, float]:
        """
        Detect the language of input text
        
        Args:
            text: Text to analyze
            fallback_language: Fallback language if detection fails
            
        Returns:
            Tuple of (detected_language, confidence)
        """
        try:
            if not text or len(text.strip()) < 10:
                return fallback_language, 0.5
            
            # Use langdetect for primary detection
            detected_langs = langdetect.detect_langs(text)
            
            if detected_langs:
                primary_lang = detected_langs[0]
                lang_code = primary_lang.lang
                confidence = primary_lang.prob
                
                # Map to supported language codes
                mapped_lang = self._map_language_code(lang_code)
                
                if mapped_lang:
                    return mapped_lang, confidence
                
                # Try pattern matching as fallback
                pattern_lang = self._detect_by_patterns(text)
                if pattern_lang:
                    return pattern_lang, 0.7
            
            # Use fallback language
            return fallback_language, 0.3
            
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return fallback_language, 0.1
    
    def _map_language_code(self, detected_lang: str) -> Optional[str]:
        """Map detected language to supported language code"""
        lang_mapping = {
            "en": "en-US",
            "de": "de-DE",
            "fr": "fr-FR",
            "es": "es-ES",
            "it": "it-IT",
            "ja": "ja-JP",
            "ko": "ko-KR",
            "zh": "zh-CN",
            "pt": "pt-BR",
            "ru": "ru-RU",
            "nl": "nl-NL",
            "sv": "sv-SE",
            "no": "no-NO",
            "da": "da-DK",
            "fi": "fi-FI",
            "pl": "pl-PL",
            "cs": "cs-CZ",
            "hu": "hu-HU"
        }
        
        return lang_mapping.get(detected_lang)
    
    def _detect_by_patterns(self, text: str) -> Optional[str]:
        """Detect language using pattern matching"""
        text_lower = text.lower()
        
        for lang_code, patterns in self.language_patterns.items():
            pattern_count = sum(len(re.findall(pattern, text_lower)) for pattern in patterns)
            if pattern_count > 0:
                return lang_code
        
        return None
    
    def segment_text(self, text: str, max_segment_length: int = 500) -> List[TextSegment]:
        """
        Segment text into manageable chunks
        
        Args:
            text: Text to segment
            max_segment_length: Maximum length of each segment
            
        Returns:
            List of text segments
        """
        if not text:
            return []
        
        segments = []
        sentences = self._split_into_sentences(text)
        
        current_segment = ""
        start_position = 0
        
        for sentence in sentences:
            # Check if adding this sentence would exceed limit
            if len(current_segment) + len(sentence) > max_segment_length and current_segment:
                # Create segment
                segment = TextSegment(
                    text=current_segment.strip(),
                    language=self.detect_language(current_segment)[0],
                    start_position=start_position,
                    end_position=start_position + len(current_segment),
                    confidence=0.8,
                    metadata={"type": "sentence_group"}
                )
                segments.append(segment)
                
                # Start new segment
                current_segment = sentence
                start_position = start_position + len(current_segment)
            else:
                current_segment += " " + sentence if current_segment else sentence
        
        # Add final segment
        if current_segment:
            segment = TextSegment(
                text=current_segment.strip(),
                language=self.detect_language(current_segment)[0],
                start_position=start_position,
                end_position=start_position + len(current_segment),
                confidence=0.8,
                metadata={"type": "sentence_group"}
            )
            segments.append(segment)
        
        return segments
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be enhanced with NLP libraries)
        sentence_endings = r'[.!?]+'
        sentences = re.split(sentence_endings, text)
        
        # Clean up sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def generate_ssml(self, 
                      text: str, 
                      voice_name: str,
                      language: str,
                      prosody: Optional[Dict[str, any]] = None,
                      metadata: Optional[Dict[str, any]] = None) -> str:
        """
        Generate SSML markup for text synthesis
        
        Args:
            text: Text to synthesize
            voice_name: Name of the voice to use
            language: Language code
            prosody: Prosody modifications
            metadata: Additional metadata
            
        Returns:
            SSML markup string
        """
        try:
            # Clean and validate text
            clean_text = self.preprocess_text(text)
            if not clean_text:
                return ""
            
            # Validate language
            if language not in self.supported_languages:
                logger.warning(f"Unsupported language: {language}, using en-US")
                language = "en-US"
            
            # Apply prosody modifications
            prosody_attrs = self._build_prosody_attributes(prosody or {})
            
            # Generate SSML
            ssml = f'<speak version="1.0" xml:lang="{language}">\n'
            ssml += f'  <voice name="{voice_name}">\n'
            
            if prosody_attrs:
                ssml += f'    <prosody {prosody_attrs}>\n'
                ssml += f'      {clean_text}\n'
                ssml += '    </prosody>\n'
            else:
                ssml += f'    {clean_text}\n'
            
            ssml += '  </voice>\n'
            ssml += '</speak>'
            
            return ssml
            
        except Exception as e:
            logger.error(f"Error generating SSML: {str(e)}")
            # Return minimal SSML as fallback
            return f'<speak version="1.0" xml:lang="{language}"><voice name="{voice_name}">{text}</voice></speak>'
    
    def _build_prosody_attributes(self, prosody: Dict[str, any]) -> str:
        """Build prosody attributes string"""
        if not prosody:
            return ""
        
        attributes = []
        
        # Rate modification
        if "rate" in prosody:
            rate_value = prosody["rate"]
            if isinstance(rate_value, (int, float)):
                if rate_value > 0:
                    attributes.append(f'rate="+{rate_value}%"')
                else:
                    attributes.append(f'rate="{rate_value}%"')
            else:
                attributes.append(f'rate="{rate_value}"')
        
        # Pitch modification
        if "pitch" in prosody:
            pitch_value = prosody["pitch"]
            if isinstance(pitch_value, (int, float)):
                if pitch_value > 0:
                    attributes.append(f'pitch="+{pitch_value}st"')
                else:
                    attributes.append(f'pitch="{pitch_value}st"')
            else:
                attributes.append(f'pitch="{pitch_value}"')
        
        # Volume modification
        if "volume" in prosody:
            volume_value = prosody["volume"]
            if isinstance(volume_value, (int, float)):
                if volume_value > 0:
                    attributes.append(f'volume="+{volume_value}%"')
                else:
                    attributes.append(f'volume="{volume_value}%"')
            else:
                attributes.append(f'volume="{volume_value}"')
        
        return " ".join(attributes)
    
    def apply_prosody_preset(self, text: str, preset_name: str) -> str:
        """
        Apply a prosody preset to text
        
        Args:
            text: Text to modify
            preset_name: Name of the prosody preset
            
        Returns:
            Text with prosody markup
        """
        if preset_name not in self.prosody_presets:
            logger.warning(f"Unknown prosody preset: {preset_name}")
            return text
        
        preset = self.prosody_presets[preset_name]
        
        # Create prosody markup
        prosody_attrs = self._build_prosody_attributes(preset)
        
        if prosody_attrs:
            return f'<prosody {prosody_attrs}>{text}</prosody>'
        
        return text
    
    def create_pronunciation_guide(self, text: str, language: str) -> str:
        """
        Create pronunciation guide for text
        
        Args:
            text: Text to create guide for
            language: Language code
            
        Returns:
            Pronunciation guide SSML
        """
        # This is a simplified implementation
        # In production, you would integrate with pronunciation services
        
        if language.startswith("en"):
            # English pronunciation rules
            pronunciation_map = {
                "hello": "həˈloʊ",
                "world": "wɜːld",
                "computer": "kəmˈpjuːtər",
                "technology": "tekˈnɒlədʒi"
            }
            
            for word, pronunciation in pronunciation_map.items():
                if word.lower() in text.lower():
                    text = text.replace(word, f'<phoneme ph="{pronunciation}">{word}</phoneme>')
        
        return text
    
    def validate_ssml(self, ssml: str) -> Tuple[bool, List[str]]:
        """
        Validate SSML markup
        
        Args:
            ssml: SSML to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check for required tags
        if "<speak" not in ssml:
            errors.append("Missing <speak> tag")
        
        if "<voice" not in ssml:
            errors.append("Missing <voice> tag")
        
        if "</speak>" not in ssml:
            errors.append("Missing </speak> tag")
        
        if "</voice>" not in ssml:
            errors.append("Missing </voice> tag")
        
        # Check for balanced tags
        open_tags = len(re.findall(r'<[^/][^>]*>', ssml))
        close_tags = len(re.findall(r'</[^>]*>', ssml))
        
        if open_tags != close_tags:
            errors.append(f"Unbalanced tags: {open_tags} open, {close_tags} close")
        
        # Check for valid language attribute
        lang_match = re.search(r'xml:lang="([^"]+)"', ssml)
        if lang_match:
            lang_code = lang_match.group(1)
            if lang_code not in self.supported_languages:
                errors.append(f"Unsupported language code: {lang_code}")
        
        # Check for valid voice name
        voice_match = re.search(r'name="([^"]+)"', ssml)
        if not voice_match:
            errors.append("Missing voice name attribute")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def get_supported_languages(self) -> List[Dict[str, any]]:
        """Get list of supported languages"""
        return [
            {
                "code": lang_code,
                "name": lang_info["name"],
                "locale": lang_info["locale"],
                "gender": lang_info["gender"]
            }
            for lang_code, lang_info in self.supported_languages.items()
        ]
    
    def get_prosody_presets(self) -> List[str]:
        """Get available prosody presets"""
        return list(self.prosody_presets.keys())
    
    def get_text_statistics(self, text: str) -> Dict[str, any]:
        """
        Get text statistics
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of text statistics
        """
        if not text:
            return {}
        
        # Basic statistics
        char_count = len(text)
        word_count = len(text.split())
        sentence_count = len(self._split_into_sentences(text))
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # Language detection
        detected_lang, confidence = self.detect_language(text)
        
        # Readability metrics (simplified)
        avg_word_length = char_count / word_count if word_count > 0 else 0
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        return {
            "characters": char_count,
            "words": word_count,
            "sentences": sentence_count,
            "paragraphs": paragraph_count,
            "detected_language": detected_lang,
            "language_confidence": confidence,
            "average_word_length": round(avg_word_length, 2),
            "average_sentence_length": round(avg_sentence_length, 2),
            "estimated_reading_time": round(word_count / 200, 1)  # Assuming 200 WPM
        }
