"""
Unit Tests for Consent Management System
Tests consent capture, verification, digital signatures, and audit trails
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import hashlib
from typing import Dict, Any

# Import the modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from consent_management import ConsentManager, ConsentRecord, DigitalSignature, ConsentStatus

class TestConsentRecord(unittest.TestCase):
    """Test ConsentRecord class"""
    
    def setUp(self):
        """Set up test data"""
        self.consent_data = {
            'user_id': 'test_user_123',
            'consent_type': 'voice_cloning',
            'purpose': 'Create custom voice model for text-to-speech',
            'data_usage': ['audio_processing', 'voice_training', 'synthesis'],
            'retention_period': 730,  # 2 years
            'third_party_sharing': False,
            'withdrawal_rights': True
        }
    
    def test_consent_record_creation(self):
        """Test creating a consent record"""
        record = ConsentRecord(**self.consent_data)
        
        self.assertEqual(record.user_id, 'test_user_123')
        self.assertEqual(record.consent_type, 'voice_cloning')
        self.assertEqual(record.purpose, 'Create custom voice model for text-to-speech')
        self.assertEqual(record.status, ConsentStatus.PENDING)
        self.assertIsNotNone(record.record_id)
        self.assertIsNotNone(record.created_at)
    
    def test_consent_record_validation(self):
        """Test consent record validation"""
        # Test with missing required fields
        invalid_data = self.consent_data.copy()
        del invalid_data['user_id']
        
        with self.assertRaises(ValueError):
            ConsentRecord(**invalid_data)
    
    def test_consent_record_expiration(self):
        """Test consent record expiration logic"""
        record = ConsentRecord(**self.consent_data)
        
        # Test not expired
        self.assertFalse(record.is_expired())
        
        # Test expired
        record.created_at = datetime.now() - timedelta(days=800)
        self.assertTrue(record.is_expired())

class TestDigitalSignature(unittest.TestCase):
    """Test DigitalSignature class"""
    
    def setUp(self):
        """Set up test data"""
        self.private_key = "test_private_key_12345"
        self.public_key = "test_public_key_67890"
        self.data = "test_consent_data"
    
    def test_signature_creation(self):
        """Test creating a digital signature"""
        signature = DigitalSignature.create_signature(self.data, self.private_key)
        
        self.assertIsNotNone(signature.signature_hash)
        self.assertEqual(signature.data_hash, hashlib.sha256(self.data.encode()).hexdigest())
        self.assertIsNotNone(signature.timestamp)
    
    def test_signature_verification(self):
        """Test signature verification"""
        signature = DigitalSignature.create_signature(self.data, self.private_key)
        
        # Test valid signature
        self.assertTrue(signature.verify_signature(self.data, self.public_key))
        
        # Test invalid data
        self.assertFalse(signature.verify_signature("modified_data", self.public_key))
    
    def test_signature_tampering_detection(self):
        """Test detection of signature tampering"""
        signature = DigitalSignature.create_signature(self.data, self.private_key)
        
        # Modify the signature hash
        signature.signature_hash = "modified_hash"
        
        self.assertFalse(signature.verify_signature(self.data, self.public_key))

class TestConsentManager(unittest.TestCase):
    """Test ConsentManager class"""
    
    def setUp(self):
        """Set up test environment"""
        self.consent_manager = ConsentManager()
        self.test_consent_data = {
            'user_id': 'test_user_123',
            'consent_type': 'voice_cloning',
            'purpose': 'Create custom voice model',
            'data_usage': ['audio_processing'],
            'retention_period': 365,
            'third_party_sharing': False,
            'withdrawal_rights': True
        }
    
    @patch('consent_management.ConsentManager._save_to_database')
    def test_capture_consent(self, mock_save):
        """Test capturing user consent"""
        mock_save.return_value = True
        
        result = self.consent_manager.capture_consent(**self.test_consent_data)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.consent_id)
        self.assertEqual(result.status, ConsentStatus.ACTIVE)
        
        # Verify save was called
        mock_save.assert_called_once()
    
    @patch('consent_management.ConsentManager._load_from_database')
    def test_verify_consent(self, mock_load):
        """Test consent verification"""
        # Mock database response
        mock_consent = ConsentRecord(**self.test_consent_data)
        mock_consent.status = ConsentStatus.ACTIVE
        mock_consent.created_at = datetime.now()
        mock_load.return_value = mock_consent
        
        result = self.consent_manager.verify_consent('test_consent_id')
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.consent_type, 'voice_cloning')
    
    def test_verify_consent_not_found(self):
        """Test consent verification when consent not found"""
        with patch('consent_management.ConsentManager._load_from_database', return_value=None):
            result = self.consent_manager.verify_consent('non_existent_id')
            
            self.assertFalse(result.is_valid)
            self.assertEqual(result.status, 'not_found')
    
    def test_verify_consent_expired(self):
        """Test consent verification for expired consent"""
        expired_consent = ConsentRecord(**self.test_consent_data)
        expired_consent.created_at = datetime.now() - timedelta(days=400)
        expired_consent.status = ConsentStatus.ACTIVE
        
        with patch('consent_management.ConsentManager._load_from_database', return_value=expired_consent):
            result = self.consent_manager.verify_consent('expired_consent_id')
            
            self.assertFalse(result.is_valid)
            self.assertEqual(result.status, 'expired')
    
    @patch('consent_management.ConsentManager._save_to_database')
    def test_withdraw_consent(self, mock_save):
        """Test consent withdrawal"""
        mock_save.return_value = True
        
        result = self.consent_manager.withdraw_consent('test_consent_id', 'test_user_123')
        
        self.assertTrue(result.success)
        self.assertEqual(result.status, 'withdrawn')
        
        # Verify save was called
        mock_save.assert_called_once()
    
    def test_withdraw_consent_unauthorized(self):
        """Test consent withdrawal by unauthorized user"""
        result = self.consent_manager.withdraw_consent('test_consent_id', 'unauthorized_user')
        
        self.assertFalse(result.success)
        self.assertEqual(result.status, 'unauthorized')
    
    @patch('consent_management.ConsentManager._load_from_database')
    def test_get_consent_history(self, mock_load):
        """Test retrieving consent history"""
        # Mock multiple consent records
        mock_records = [
            ConsentRecord(**self.test_consent_data),
            ConsentRecord(**self.test_consent_data)
        ]
        mock_load.return_value = mock_records
        
        history = self.consent_manager.get_consent_history('test_user_123')
        
        self.assertEqual(len(history), 2)
        self.assertIsInstance(history[0], ConsentRecord)
    
    def test_consent_audit_trail(self):
        """Test consent audit trail functionality"""
        # Capture consent
        with patch('consent_management.ConsentManager._save_to_database', return_value=True):
            consent_result = self.consent_manager.capture_consent(**self.test_consent_data)
        
        # Get audit trail
        audit_trail = self.consent_manager.get_audit_trail(consent_result.consent_id)
        
        self.assertIsNotNone(audit_trail)
        self.assertIn('consent_captured', [event['action'] for event in audit_trail])

class TestConsentValidation(unittest.TestCase):
    """Test consent validation logic"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_consent = {
            'user_id': 'test_user_123',
            'consent_type': 'voice_cloning',
            'purpose': 'Create custom voice model',
            'data_usage': ['audio_processing'],
            'retention_period': 365,
            'third_party_sharing': False,
            'withdrawal_rights': True
        }
    
    def test_valid_consent_data(self):
        """Test validation of valid consent data"""
        consent_manager = ConsentManager()
        
        # This should not raise any exceptions
        result = consent_manager.validate_consent_data(self.valid_consent)
        self.assertTrue(result.is_valid)
    
    def test_invalid_consent_data(self):
        """Test validation of invalid consent data"""
        consent_manager = ConsentManager()
        
        # Test missing required fields
        invalid_consent = self.valid_consent.copy()
        del invalid_consent['user_id']
        
        result = consent_manager.validate_consent_data(invalid_consent)
        self.assertFalse(result.is_valid)
        self.assertIn('user_id', result.errors)
    
    def test_invalid_retention_period(self):
        """Test validation of retention period"""
        consent_manager = ConsentManager()
        
        # Test negative retention period
        invalid_consent = self.valid_consent.copy()
        invalid_consent['retention_period'] = -10
        
        result = consent_manager.validate_consent_data(invalid_consent)
        self.assertFalse(result.is_valid)
        self.assertIn('retention_period', result.errors)
    
    def test_invalid_data_usage(self):
        """Test validation of data usage array"""
        consent_manager = ConsentManager()
        
        # Test empty data usage array
        invalid_consent = self.valid_consent.copy()
        invalid_consent['data_usage'] = []
        
        result = consent_manager.validate_consent_data(invalid_consent)
        self.assertFalse(result.is_valid)
        self.assertIn('data_usage', result.errors)

class TestConsentExpiration(unittest.TestCase):
    """Test consent expiration handling"""
    
    def setUp(self):
        """Set up test data"""
        self.consent_manager = ConsentManager()
        self.consent_data = {
            'user_id': 'test_user_123',
            'consent_type': 'voice_cloning',
            'purpose': 'Create custom voice model',
            'data_usage': ['audio_processing'],
            'retention_period': 30,  # 30 days
            'third_party_sharing': False,
            'withdrawal_rights': True
        }
    
    def test_consent_expiration_check(self):
        """Test checking if consent is expired"""
        # Create consent with short retention period
        with patch('consent_management.ConsentManager._save_to_database', return_value=True):
            consent_result = self.consent_manager.capture_consent(**self.consent_data)
        
        # Check expiration status
        is_expired = self.consent_manager.is_consent_expired(consent_result.consent_id)
        self.assertFalse(is_expired)
    
    def test_expired_consent_handling(self):
        """Test handling of expired consent"""
        # Create expired consent
        expired_consent = ConsentRecord(**self.consent_data)
        expired_consent.created_at = datetime.now() - timedelta(days=40)
        expired_consent.status = ConsentStatus.ACTIVE
        
        with patch('consent_management.ConsentManager._load_from_database', return_value=expired_consent):
            # Verify expired consent is not valid
            result = self.consent_manager.verify_consent('expired_consent_id')
            self.assertFalse(result.is_valid)
            self.assertEqual(result.status, 'expired')
    
    def test_consent_renewal(self):
        """Test consent renewal functionality"""
        # Create consent
        with patch('consent_management.ConsentManager._save_to_database', return_value=True):
            consent_result = self.consent_manager.capture_consent(**self.consent_data)
        
        # Renew consent
        renewal_result = self.consent_manager.renew_consent(consent_result.consent_id)
        
        self.assertTrue(renewal_result.success)
        self.assertEqual(renewal_result.status, 'renewed')

if __name__ == '__main__':
    unittest.main()
