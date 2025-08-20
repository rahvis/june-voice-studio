"""
Consent Management System for Voice Enrollment

This module handles consent capture, verification, digital signatures,
audit trails, and consent expiration/renewal for voice cloning.
"""

import json
import hashlib
import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ConsentStatus(Enum):
    """Consent status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    RENEWED = "renewed"

class ConsentType(Enum):
    """Type of consent"""
    VOICE_CLONING = "voice_cloning"
    DATA_PROCESSING = "data_processing"
    THIRD_PARTY_SHARING = "third_party_sharing"
    RESEARCH_USE = "research_use"

@dataclass
class ConsentRecord:
    """Consent record data structure"""
    consent_id: str
    user_id: str
    consent_type: ConsentType
    status: ConsentStatus
    created_at: datetime.datetime
    expires_at: Optional[datetime.datetime]
    revoked_at: Optional[datetime.datetime]
    digital_signature: str
    consent_text: str
    user_ip: str
    user_agent: str
    metadata: Dict[str, any]
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['consent_type'] = self.consent_type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        if self.revoked_at:
            data['revoked_at'] = self.revoked_at.isoformat()
        return data

class ConsentManager:
    """Manages consent operations for voice enrollment"""
    
    def __init__(self, storage_client, audit_logger):
        self.storage_client = storage_client
        self.audit_logger = audit_logger
        self.consent_texts = self._load_consent_texts()
    
    def _load_consent_texts(self) -> Dict[str, str]:
        """Load consent text templates"""
        return {
            ConsentType.VOICE_CLONING.value: """
            VOICE CLONING CONSENT AGREEMENT
            
            I, the undersigned, hereby provide my explicit consent for the creation 
            and use of a custom neural voice model based on my voice recordings.
            
            I understand that:
            1. My voice will be recorded and processed to create a digital voice model
            2. This model may be used to synthesize speech in multiple languages
            3. I retain the right to revoke this consent at any time
            4. My voice data will be processed in accordance with privacy regulations
            5. I am the rightful owner of this voice and have authority to grant this consent
            
            I acknowledge that I have read and understood this agreement and voluntarily 
            consent to the voice cloning process.
            """,
            
            ConsentType.DATA_PROCESSING.value: """
            DATA PROCESSING CONSENT
            
            I consent to the processing of my personal data, including voice recordings,
            for the purpose of creating and using a custom neural voice model.
            
            This consent covers:
            - Audio recording and processing
            - Text transcription and alignment
            - Model training and optimization
            - Quality assurance and testing
            """,
            
            ConsentType.THIRD_PARTY_SHARING.value: """
            THIRD PARTY SHARING CONSENT
            
            I consent to the sharing of my voice model with authorized third-party
            services for the purpose of text-to-speech synthesis.
            
            This includes:
            - Azure AI Speech Services
            - Translation services
            - Audio processing services
            """
        }
    
    def create_consent(self, 
                       user_id: str, 
                       consent_types: List[ConsentType],
                       user_ip: str,
                       user_agent: str,
                       metadata: Optional[Dict[str, any]] = None) -> List[ConsentRecord]:
        """
        Create new consent records for a user
        
        Args:
            user_id: Unique identifier for the user
            consent_types: List of consent types to create
            user_ip: IP address of the user
            user_agent: User agent string
            metadata: Additional metadata
            
        Returns:
            List of created consent records
        """
        consent_records = []
        
        for consent_type in consent_types:
            consent_id = self._generate_consent_id(user_id, consent_type)
            consent_text = self.consent_texts[consent_type.value]
            
            # Create digital signature
            digital_signature = self._create_digital_signature(
                user_id, consent_type, consent_text, user_ip
            )
            
            # Set expiration (default 1 year)
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=365)
            
            consent_record = ConsentRecord(
                consent_id=consent_id,
                user_id=user_id,
                consent_type=consent_type,
                status=ConsentStatus.ACTIVE,
                created_at=datetime.datetime.utcnow(),
                expires_at=expires_at,
                revoked_at=None,
                digital_signature=digital_signature,
                consent_text=consent_text,
                user_ip=user_ip,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            # Store consent record
            self._store_consent(consent_record)
            
            # Log consent creation
            self.audit_logger.log_consent_created(consent_record)
            
            consent_records.append(consent_record)
            
            logger.info(f"Created consent {consent_id} for user {user_id}")
        
        return consent_records
    
    def verify_consent(self, user_id: str, consent_type: ConsentType) -> Tuple[bool, Optional[ConsentRecord]]:
        """
        Verify if user has valid consent for a specific type
        
        Args:
            user_id: User identifier
            consent_type: Type of consent to verify
            
        Returns:
            Tuple of (is_valid, consent_record)
        """
        consent_record = self._get_active_consent(user_id, consent_type)
        
        if not consent_record:
            return False, None
        
        # Check if consent is expired
        if consent_record.expires_at and consent_record.expires_at < datetime.datetime.utcnow():
            self._expire_consent(consent_record.consent_id)
            return False, None
        
        # Verify digital signature
        if not self._verify_digital_signature(consent_record):
            logger.warning(f"Invalid digital signature for consent {consent_record.consent_id}")
            return False, None
        
        return True, consent_record
    
    def revoke_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        """
        Revoke user consent
        
        Args:
            user_id: User identifier
            consent_type: Type of consent to revoke
            
        Returns:
            True if consent was revoked successfully
        """
        consent_record = self._get_active_consent(user_id, consent_type)
        
        if not consent_record:
            logger.warning(f"No active consent found for user {user_id} and type {consent_type}")
            return False
        
        # Update consent status
        consent_record.status = ConsentStatus.REVOKED
        consent_record.revoked_at = datetime.datetime.utcnow()
        
        # Store updated consent
        self._store_consent(consent_record)
        
        # Log consent revocation
        self.audit_logger.log_consent_revoked(consent_record)
        
        logger.info(f"Revoked consent {consent_record.consent_id} for user {user_id}")
        return True
    
    def renew_consent(self, user_id: str, consent_type: ConsentType) -> Optional[ConsentRecord]:
        """
        Renew expired consent
        
        Args:
            user_id: User identifier
            consent_type: Type of consent to renew
            
        Returns:
            New consent record if renewal successful
        """
        expired_consent = self._get_expired_consent(user_id, consent_type)
        
        if not expired_consent:
            logger.warning(f"No expired consent found for user {user_id} and type {consent_type}")
            return None
        
        # Create new consent record
        new_consent = self.create_consent(
            user_id=user_id,
            consent_types=[consent_type],
            user_ip=expired_consent.user_ip,
            user_agent=expired_consent.user_agent,
            metadata=expired_consent.metadata
        )[0]
        
        # Mark old consent as renewed
        expired_consent.status = ConsentStatus.RENEWED
        self._store_consent(expired_consent)
        
        logger.info(f"Renewed consent for user {user_id} and type {consent_type}")
        return new_consent
    
    def get_consent_history(self, user_id: str) -> List[ConsentRecord]:
        """
        Get consent history for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of consent records
        """
        return self._get_user_consents(user_id)
    
    def _generate_consent_id(self, user_id: str, consent_type: ConsentType) -> str:
        """Generate unique consent ID"""
        timestamp = datetime.datetime.utcnow().isoformat()
        content = f"{user_id}:{consent_type.value}:{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _create_digital_signature(self, user_id: str, consent_type: ConsentType, 
                                 consent_text: str, user_ip: str) -> str:
        """Create digital signature for consent"""
        content = f"{user_id}:{consent_type.value}:{consent_text}:{user_ip}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _verify_digital_signature(self, consent_record: ConsentRecord) -> bool:
        """Verify digital signature of consent"""
        expected_signature = self._create_digital_signature(
            consent_record.user_id,
            consent_record.consent_type,
            consent_record.consent_text,
            consent_record.user_ip
        )
        return consent_record.digital_signature == expected_signature
    
    def _store_consent(self, consent_record: ConsentRecord):
        """Store consent record in storage"""
        self.storage_client.store_consent(consent_record)
    
    def _get_active_consent(self, user_id: str, consent_type: ConsentType) -> Optional[ConsentRecord]:
        """Get active consent for user and type"""
        return self.storage_client.get_active_consent(user_id, consent_type.value)
    
    def _get_expired_consent(self, user_id: str, consent_type: ConsentType) -> Optional[ConsentRecord]:
        """Get expired consent for user and type"""
        return self.storage_client.get_expired_consent(user_id, consent_type.value)
    
    def _get_user_consents(self, user_id: str) -> List[ConsentRecord]:
        """Get all consents for a user"""
        return self.storage_client.get_user_consents(user_id)
    
    def _expire_consent(self, consent_id: str):
        """Mark consent as expired"""
        self.storage_client.expire_consent(consent_id)
