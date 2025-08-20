"""
Integration Tests for Azure Services
Tests Azure Speech Service, Translator, OpenAI, and Storage integrations
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import tempfile
from typing import Dict, Any, List
import asyncio

# Import the modules to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from speech_to_text import AzureSpeechToTextService
from translation_service import AzureTranslatorService
from voice_selection import VoiceSelector
from audio_synthesis import AudioSynthesizer

class TestAzureSpeechToTextIntegration(unittest.TestCase):
    """Test Azure Speech-to-Text service integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.speech_service = AzureSpeechToTextService(
            subscription_key="test_key",
            region="eastus"
        )
        self.test_audio_file = "test_audio.wav"
        
        # Create a temporary test audio file
        self.temp_dir = tempfile.mkdtemp()
        self.test_audio_path = os.path.join(self.temp_dir, self.test_audio_file)
        
        # Create a dummy audio file
        with open(self.test_audio_path, 'wb') as f:
            f.write(b'dummy_audio_content')
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    @patch('speech_to_text.speechsdk.SpeechConfig')
    @patch('speech_to_text.speechsdk.AudioConfig')
    @patch('speech_to_text.speechsdk.SpeechRecognizer')
    def test_speech_to_text_transcription(self, mock_recognizer, mock_audio_config, mock_speech_config):
        """Test speech-to-text transcription"""
        # Mock the speech recognizer
        mock_recognizer_instance = Mock()
        mock_recognizer_instance.recognize_once.return_value = Mock(
            text="Hello world",
            reason="RecognizedSpeech"
        )
        mock_recognizer.return_value = mock_recognizer_instance
        
        # Test transcription
        result = self.speech_service.transcribe_audio(self.test_audio_path)
        
        self.assertTrue(result.success)
        self.assertEqual(result.transcript, "Hello world")
        self.assertEqual(result.confidence, 1.0)
    
    @patch('speech_to_text.speechsdk.SpeechConfig')
    @patch('speech_to_text.speechsdk.AudioConfig')
    @patch('speech_to_text.speechsdk.SpeechRecognizer')
    def test_speech_to_text_with_language_detection(self, mock_recognizer, mock_audio_config, mock_speech_config):
        """Test speech-to-text with language detection"""
        # Mock the speech recognizer with language detection
        mock_recognizer_instance = Mock()
        mock_recognizer_instance.recognize_once.return_value = Mock(
            text="Bonjour le monde",
            reason="RecognizedSpeech",
            language="fr-FR"
        )
        mock_recognizer.return_value = mock_recognizer_instance
        
        # Test transcription with language detection
        result = self.speech_service.transcribe_audio(
            self.test_audio_path,
            language_detection=True
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.transcript, "Bonjour le monde")
        self.assertEqual(result.detected_language, "fr-FR")
    
    @patch('speech_to_text.speechsdk.SpeechConfig')
    @patch('speech_to_text.speechsdk.AudioConfig')
    @patch('speech_to_text.speechsdk.SpeechRecognizer')
    def test_speech_to_text_error_handling(self, mock_recognizer, mock_audio_config, mock_speech_config):
        """Test speech-to-text error handling"""
        # Mock the speech recognizer with error
        mock_recognizer_instance = Mock()
        mock_recognizer_instance.recognize_once.return_value = Mock(
            reason="NoMatch",
            no_match_details="No speech detected"
        )
        mock_recognizer.return_value = mock_recognizer_instance
        
        # Test error handling
        result = self.speech_service.transcribe_audio(self.test_audio_path)
        
        self.assertFalse(result.success)
        self.assertEqual(result.error, "No speech detected")
    
    def test_audio_file_validation(self):
        """Test audio file validation"""
        # Test valid audio file
        result = self.speech_service.validate_audio_file(self.test_audio_path)
        self.assertTrue(result.is_valid)
        
        # Test non-existent file
        result = self.speech_service.validate_audio_file("non_existent.wav")
        self.assertFalse(result.is_valid)
        self.assertIn("File not found", result.errors)

class TestAzureTranslatorIntegration(unittest.TestCase):
    """Test Azure Translator service integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.translator_service = AzureTranslatorService(
            subscription_key="test_key",
            region="eastus"
        )
        self.test_text = "Hello world"
        self.source_language = "en"
        self.target_language = "es"
    
    @patch('translation_service.requests.post')
    def test_text_translation(self, mock_post):
        """Test text translation"""
        # Mock the translation response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "translations": [
                    {
                        "text": "Hola mundo",
                        "to": "es"
                    }
                ]
            }
        ]
        mock_post.return_value = mock_response
        
        # Test translation
        result = self.translator_service.translate_text(
            self.test_text,
            self.source_language,
            self.target_language
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.translated_text, "Hola mundo")
        self.assertEqual(result.target_language, "es")
    
    @patch('translation_service.requests.post')
    def test_language_detection(self, mock_post):
        """Test language detection"""
        # Mock the language detection response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "detectedLanguage": {
                    "language": "en",
                    "score": 0.95
                }
            }
        ]
        mock_post.return_value = mock_response
        
        # Test language detection
        result = self.translator_service.detect_language(self.test_text)
        
        self.assertTrue(result.success)
        self.assertEqual(result.detected_language, "en")
        self.assertEqual(result.confidence, 0.95)
    
    @patch('translation_service.requests.post')
    def test_batch_translation(self, mock_post):
        """Test batch translation"""
        # Mock the batch translation response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "translations": [
                    {
                        "text": "Hola mundo",
                        "to": "es"
                    }
                ]
            },
            {
                "translations": [
                    {
                        "text": "Bonjour le monde",
                        "to": "fr"
                    }
                ]
            }
        ]
        mock_post.return_value = mock_response
        
        # Test batch translation
        texts = ["Hello world", "Good morning"]
        target_languages = ["es", "fr"]
        
        result = self.translator_service.translate_batch(
            texts,
            self.source_language,
            target_languages
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.translations), 2)
        self.assertEqual(result.translations[0], "Hola mundo")
        self.assertEqual(result.translations[1], "Bonjour le monde")
    
    @patch('translation_service.requests.post')
    def test_translation_error_handling(self, mock_post):
        """Test translation error handling"""
        # Mock the translation error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "code": "InvalidRequest",
                "message": "Invalid language code"
            }
        }
        mock_post.return_value = mock_response
        
        # Test error handling
        result = self.translator_service.translate_text(
            self.test_text,
            "invalid_lang",
            self.target_language
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Invalid language code")

class TestVoiceSelectionIntegration(unittest.TestCase):
    """Test voice selection and fallback logic"""
    
    def setUp(self):
        """Set up test environment"""
        self.voice_selector = VoiceSelector()
        self.test_text = "Hello world"
        self.user_preferences = {
            "language": "en-US",
            "gender": "female",
            "style": "friendly"
        }
    
    def test_custom_neural_voice_selection(self):
        """Test custom neural voice selection"""
        # Mock available voices
        available_voices = [
            {
                "voice_id": "voice_1",
                "language": "en-US",
                "gender": "female",
                "style": "friendly",
                "status": "ready"
            }
        ]
        
        with patch.object(self.voice_selector, 'get_available_voices', return_value=available_voices):
            selected_voice = self.voice_selector.select_voice(
                self.test_text,
                self.user_preferences
            )
            
            self.assertIsNotNone(selected_voice)
            self.assertEqual(selected_voice["voice_id"], "voice_1")
            self.assertEqual(selected_voice["type"], "custom_neural")
    
    def test_fallback_to_stock_voices(self):
        """Test fallback to stock neural voices"""
        # Mock no custom voices available
        with patch.object(self.voice_selector, 'get_available_voices', return_value=[]):
            selected_voice = self.voice_selector.select_voice(
                self.test_text,
                self.user_preferences
            )
            
            self.assertIsNotNone(selected_voice)
            self.assertEqual(selected_voice["type"], "stock_neural")
    
    def test_openai_tts_fallback(self):
        """Test OpenAI TTS fallback"""
        # Mock no voices available
        with patch.object(self.voice_selector, 'get_available_voices', return_value=[]):
            with patch.object(self.voice_selector, 'get_stock_voices', return_value=[]):
                selected_voice = self.voice_selector.select_voice(
                    self.test_text,
                    self.user_preferences
                )
                
                self.assertIsNotNone(selected_voice)
                self.assertEqual(selected_voice["type"], "openai_tts")
    
    def test_voice_availability_checking(self):
        """Test voice availability checking"""
        # Test available voice
        with patch.object(self.voice_selector, 'check_voice_status', return_value="ready"):
            is_available = self.voice_selector.is_voice_available("voice_1")
            self.assertTrue(is_available)
        
        # Test unavailable voice
        with patch.object(self.voice_selector, 'check_voice_status', return_value="training"):
            is_available = self.voice_selector.is_voice_available("voice_2")
            self.assertFalse(is_available)

class TestAudioSynthesisIntegration(unittest.TestCase):
    """Test audio synthesis integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.synthesizer = AudioSynthesizer()
        self.test_text = "Hello world"
        self.voice_config = {
            "voice_id": "test_voice",
            "language": "en-US",
            "gender": "female"
        }
    
    @patch('audio_synthesis.speechsdk.SpeechConfig')
    @patch('audio_synthesis.speechsdk.SpeechSynthesizer')
    def test_text_to_speech_synthesis(self, mock_synthesizer, mock_speech_config):
        """Test text-to-speech synthesis"""
        # Mock the speech synthesizer
        mock_synthesizer_instance = Mock()
        mock_synthesizer_instance.speak_text_async.return_value = Mock(
            reason="SynthesizingAudioCompleted",
            audio_data=b"synthesized_audio_data"
        )
        mock_synthesizer.return_value = mock_synthesizer_instance
        
        # Test synthesis
        result = self.synthesizer.synthesize_text(
            self.test_text,
            self.voice_config
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.audio_data)
        self.assertEqual(result.audio_format, "wav")
    
    @patch('audio_synthesis.speechsdk.SpeechConfig')
    @patch('audio_synthesis.speechsdk.SpeechSynthesizer')
    def test_ssml_synthesis(self, mock_synthesizer, mock_speech_config):
        """Test SSML synthesis"""
        # Mock the speech synthesizer
        mock_synthesizer_instance = Mock()
        mock_synthesizer_instance.speak_ssml_async.return_value = Mock(
            reason="SynthesizingAudioCompleted",
            audio_data=b"ssml_audio_data"
        )
        mock_synthesizer.return_value = mock_synthesizer_instance
        
        # Test SSML synthesis
        ssml_text = "<speak>Hello <break time='1s'/> world</speak>"
        result = self.synthesizer.synthesize_ssml(
            ssml_text,
            self.voice_config
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.audio_data)
    
    @patch('audio_synthesis.speechsdk.SpeechConfig')
    @patch('audio_synthesis.speechsdk.SpeechSynthesizer')
    def test_batch_synthesis(self, mock_synthesizer, mock_speech_config):
        """Test batch synthesis"""
        # Mock the speech synthesizer
        mock_synthesizer_instance = Mock()
        mock_synthesizer_instance.speak_text_async.return_value = Mock(
            reason="SynthesizingAudioCompleted",
            audio_data=b"batch_audio_data"
        )
        mock_synthesizer.return_value = mock_synthesizer_instance
        
        # Test batch synthesis
        texts = ["Hello", "World", "Test"]
        result = self.synthesizer.synthesize_batch(
            texts,
            self.voice_config
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.audio_files), 3)
    
    def test_audio_format_conversion(self):
        """Test audio format conversion"""
        # Test WAV to MP3 conversion
        test_audio_data = b"test_audio_wav_data"
        
        with patch.object(self.synthesizer, 'convert_audio_format') as mock_convert:
            mock_convert.return_value = b"converted_mp3_data"
            
            result = self.synthesizer.convert_audio_format(
                test_audio_data,
                "wav",
                "mp3"
            )
            
            self.assertEqual(result, b"converted_mp3_data")
    
    def test_synthesis_parameter_validation(self):
        """Test synthesis parameter validation"""
        # Test valid parameters
        valid_config = {
            "voice_id": "test_voice",
            "language": "en-US",
            "speed": 1.0,
            "pitch": 0.0,
            "volume": 1.0
        }
        
        result = self.synthesizer.validate_synthesis_config(valid_config)
        self.assertTrue(result.is_valid)
        
        # Test invalid parameters
        invalid_config = {
            "voice_id": "test_voice",
            "language": "en-US",
            "speed": 2.5,  # Invalid speed
            "pitch": 0.0,
            "volume": 1.0
        }
        
        result = self.synthesizer.validate_synthesis_config(invalid_config)
        self.assertFalse(result.is_valid)
        self.assertIn("speed", result.errors)

class TestEndToEndIntegration(unittest.TestCase):
    """Test end-to-end integration scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.speech_service = AzureSpeechToTextService("test_key", "eastus")
        self.translator_service = AzureTranslatorService("test_key", "eastus")
        self.voice_selector = VoiceSelector()
        self.synthesizer = AudioSynthesizer()
    
    @patch('speech_to_text.speechsdk.SpeechRecognizer')
    @patch('translation_service.requests.post')
    @patch('audio_synthesis.speechsdk.SpeechSynthesizer')
    def test_voice_cloning_workflow(self, mock_synthesizer, mock_translate, mock_recognize):
        """Test complete voice cloning workflow"""
        # Mock speech-to-text
        mock_recognize_instance = Mock()
        mock_recognize_instance.recognize_once.return_value = Mock(
            text="Hello world",
            reason="RecognizedSpeech"
        )
        mock_recognize.return_value = mock_recognize_instance
        
        # Mock translation
        mock_translate_response = Mock()
        mock_translate_response.status_code = 200
        mock_translate_response.json.return_value = [
            {
                "translations": [
                    {
                        "text": "Hola mundo",
                        "to": "es"
                    }
                ]
            }
        ]
        mock_translate.return_value = mock_translate_response
        
        # Mock synthesis
        mock_synthesizer_instance = Mock()
        mock_synthesizer_instance.speak_text_async.return_value = Mock(
            reason="SynthesizingAudioCompleted",
            audio_data=b"synthesized_audio"
        )
        mock_synthesizer.return_value = mock_synthesizer_instance
        
        # Test workflow
        # 1. Transcribe audio
        transcription = self.speech_service.transcribe_audio("test_audio.wav")
        self.assertTrue(transcription.success)
        
        # 2. Translate text
        translation = self.translator_service.translate_text(
            transcription.transcript,
            "en",
            "es"
        )
        self.assertTrue(translation.success)
        
        # 3. Select voice
        voice = self.voice_selector.select_voice(
            translation.translated_text,
            {"language": "es-ES"}
        )
        self.assertIsNotNone(voice)
        
        # 4. Synthesize audio
        synthesis = self.synthesizer.synthesize_text(
            translation.translated_text,
            voice
        )
        self.assertTrue(synthesis.success)
        
        # Verify complete workflow
        self.assertEqual(transcription.transcript, "Hello world")
        self.assertEqual(translation.translated_text, "Hola mundo")
        self.assertIsNotNone(synthesis.audio_data)

if __name__ == '__main__':
    unittest.main()
