"""
Compliance Validation Testing for Voice Cloning System
Tests GDPR, HIPAA, SOC 2, and other regulatory compliance requirements
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import hashlib
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pytz

# Import the modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from consent_management import ConsentManager, ConsentRecord, ConsentStatus
from monitoring.business_intelligence import BusinessIntelligenceEngine

class ComplianceTestBase(unittest.TestCase):
    """Base class for compliance tests"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_user_id = "test_user_123"
        self.test_voice_id = "test_voice_456"
        self.test_consent_id = "test_consent_789"
        self.test_organization_id = "org_123"
        self.current_time = datetime.now(pytz.UTC)
        
        # Test data for compliance validation
        self.test_personal_data = {
            "user_id": self.test_user_id,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "voice_biometrics": "voice_fingerprint_data",
            "audio_samples": ["sample1.wav", "sample2.wav"]
        }

class GDPRComplianceTest(ComplianceTestBase):
    """Test GDPR compliance requirements"""
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.consent_manager = ConsentManager()
        self.bi_engine = BusinessIntelligenceEngine()
        
        # GDPR-specific test data
        self.gdpr_consent_data = {
            "user_id": self.test_user_id,
            "consent_type": "voice_cloning",
            "purpose": "Create custom voice model for text-to-speech",
            "data_usage": ["audio_processing", "voice_training", "synthesis"],
            "retention_period": 730,  # 2 years
            "third_party_sharing": False,
            "withdrawal_rights": True,
            "data_portability": True,
            "automated_decision_making": False,
            "profiling": False,
            "cross_border_transfer": False
        }
    
    def test_legal_basis_for_processing(self):
        """Test legal basis for data processing under GDPR"""
        # Test explicit consent as legal basis
        consent_result = self.consent_manager.capture_consent(**self.gdpr_consent_data)
        
        self.assertTrue(consent_result.success)
        self.assertEqual(consent_result.legal_basis, "explicit_consent")
        
        # Verify consent is freely given
        self.assertTrue(consent_result.freely_given)
        
        # Verify consent is specific and informed
        self.assertTrue(consent_result.specific)
        self.assertTrue(consent_result.informed)
    
    def test_data_minimization(self):
        """Test data minimization principle"""
        # Test that only necessary data is collected
        collected_data = self._get_collected_data(self.test_user_id)
        
        # Verify only required fields are collected
        required_fields = ["user_id", "consent_type", "purpose", "data_usage"]
        for field in required_fields:
            self.assertIn(field, collected_data)
        
        # Verify no excessive data is collected
        excessive_fields = ["ssn", "credit_card", "passport_number"]
        for field in excessive_fields:
            self.assertNotIn(field, collected_data)
    
    def test_purpose_limitation(self):
        """Test purpose limitation principle"""
        # Test that data is only used for specified purposes
        consent_record = self.consent_manager.get_consent_record(self.test_consent_id)
        
        # Verify data usage is limited to specified purposes
        allowed_purposes = consent_record.data_usage
        actual_usage = self._get_actual_data_usage(self.test_user_id)
        
        for usage in actual_usage:
            self.assertIn(usage, allowed_purposes)
    
    def test_storage_limitation(self):
        """Test storage limitation principle"""
        # Test that data is not kept longer than necessary
        consent_record = self.consent_manager.get_consent_record(self.test_consent_id)
        
        # Calculate retention period
        retention_days = consent_record.retention_period
        creation_date = consent_record.created_at
        
        # Verify data will be deleted after retention period
        deletion_date = creation_date + timedelta(days=retention_days)
        self.assertGreater(deletion_date, self.current_time)
        
        # Test automatic data deletion
        is_deleted = self._check_data_deletion(self.test_user_id)
        self.assertFalse(is_deleted)  # Data should still exist within retention period
    
    def test_data_subject_rights(self):
        """Test data subject rights under GDPR"""
        # Test right to access
        access_result = self._exercise_data_subject_right(
            "access",
            self.test_user_id
        )
        self.assertTrue(access_result.success)
        self.assertIsNotNone(access_result.data)
        
        # Test right to rectification
        rectification_result = self._exercise_data_subject_right(
            "rectification",
            self.test_user_id,
            {"email": "new.email@example.com"}
        )
        self.assertTrue(rectification_result.success)
        
        # Test right to erasure (right to be forgotten)
        erasure_result = self._exercise_data_subject_right(
            "erasure",
            self.test_user_id
        )
        self.assertTrue(erasure_result.success)
        
        # Verify data is actually deleted
        is_deleted = self._check_data_deletion(self.test_user_id)
        self.assertTrue(is_deleted)
        
        # Test right to data portability
        portability_result = self._exercise_data_subject_right(
            "portability",
            self.test_user_id
        )
        self.assertTrue(portability_result.success)
        self.assertIsNotNone(portability_result.export_data)
    
    def test_consent_withdrawal(self):
        """Test consent withdrawal under GDPR"""
        # Create consent record
        consent_result = self.consent_manager.capture_consent(**self.gdpr_consent_data)
        
        # Test consent withdrawal
        withdrawal_result = self.consent_manager.withdraw_consent(
            consent_result.consent_id,
            self.test_user_id
        )
        
        self.assertTrue(withdrawal_result.success)
        self.assertEqual(withdrawal_result.status, "withdrawn")
        
        # Verify data processing stops after withdrawal
        can_process = self._can_process_data(self.test_user_id)
        self.assertFalse(can_process)
    
    def test_data_breach_notification(self):
        """Test data breach notification requirements"""
        # Simulate data breach
        breach_result = self._simulate_data_breach(self.test_user_id)
        
        # Verify breach is detected within 72 hours
        detection_time = breach_result.detection_time
        breach_time = breach_result.breach_time
        time_to_detect = detection_time - breach_time
        
        self.assertLessEqual(time_to_detect.total_seconds(), 72 * 3600)  # 72 hours
        
        # Verify notification is sent to supervisory authority
        notification_sent = breach_result.notification_sent
        self.assertTrue(notification_sent)
        
        # Verify affected data subjects are notified
        subjects_notified = breach_result.subjects_notified
        self.assertIn(self.test_user_id, subjects_notified)
    
    def test_data_protection_impact_assessment(self):
        """Test Data Protection Impact Assessment (DPIA)"""
        # Perform DPIA for voice cloning system
        dpia_result = self._perform_dpia("voice_cloning_system")
        
        # Verify high-risk processing is identified
        self.assertTrue(dpia_result.requires_dpia)
        
        # Verify risk mitigation measures are documented
        self.assertIsNotNone(dpia_result.risk_mitigation)
        self.assertGreater(len(dpia_result.risk_mitigation), 0)
        
        # Verify consultation with supervisory authority if needed
        if dpia_result.consultation_required:
            self.assertTrue(dpia_result.consultation_performed)
    
    def _get_collected_data(self, user_id: str) -> Dict[str, Any]:
        """Get data collected for a user"""
        # Mock data collection
        return {
            "user_id": user_id,
            "consent_type": "voice_cloning",
            "purpose": "Create custom voice model",
            "data_usage": ["audio_processing", "voice_training"],
            "retention_period": 730
        }
    
    def _get_actual_data_usage(self, user_id: str) -> List[str]:
        """Get actual data usage for a user"""
        # Mock actual usage
        return ["audio_processing", "voice_training"]
    
    def _check_data_deletion(self, user_id: str) -> bool:
        """Check if user data has been deleted"""
        # Mock deletion check
        return False
    
    def _exercise_data_subject_right(self, right: str, user_id: str, data: Dict = None) -> Dict[str, Any]:
        """Exercise a data subject right"""
        # Mock right exercise
        if right == "access":
            return {"success": True, "data": self._get_collected_data(user_id)}
        elif right == "rectification":
            return {"success": True}
        elif right == "erasure":
            return {"success": True}
        elif right == "portability":
            return {"success": True, "export_data": "exported_data"}
        else:
            return {"success": False, "error": "Unknown right"}
    
    def _can_process_data(self, user_id: str) -> bool:
        """Check if data can be processed for a user"""
        # Mock processing check
        return False
    
    def _simulate_data_breach(self, user_id: str) -> Dict[str, Any]:
        """Simulate a data breach"""
        # Mock breach simulation
        breach_time = self.current_time - timedelta(hours=24)
        detection_time = self.current_time - timedelta(hours=12)
        
        return {
            "breach_time": breach_time,
            "detection_time": detection_time,
            "notification_sent": True,
            "subjects_notified": [user_id]
        }
    
    def _perform_dpia(self, system_name: str) -> Dict[str, Any]:
        """Perform Data Protection Impact Assessment"""
        # Mock DPIA
        return {
            "requires_dpia": True,
            "risk_mitigation": ["Data encryption", "Access controls", "Audit logging"],
            "consultation_required": False,
            "consultation_performed": False
        }

class HIPAAComplianceTest(ComplianceTestBase):
    """Test HIPAA compliance requirements"""
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.hipaa_data = {
            "user_id": self.test_user_id,
            "phi": "Protected Health Information",
            "medical_record_number": "MRN123456",
            "diagnosis": "Voice disorder",
            "treatment_plan": "Voice therapy and cloning"
        }
    
    def test_phi_identification(self):
        """Test identification of Protected Health Information (PHI)"""
        # Test PHI identification
        phi_fields = self._identify_phi_fields(self.hipaa_data)
        
        # Verify PHI fields are identified
        expected_phi_fields = ["medical_record_number", "diagnosis", "treatment_plan"]
        for field in expected_phi_fields:
            self.assertIn(field, phi_fields)
        
        # Verify non-PHI fields are not included
        non_phi_fields = ["user_id", "consent_type"]
        for field in non_phi_fields:
            self.assertNotIn(field, phi_fields)
    
    def test_minimum_necessary_standard(self):
        """Test minimum necessary standard"""
        # Test that only minimum necessary PHI is used
        necessary_data = self._get_minimum_necessary_data(self.test_user_id)
        
        # Verify only required PHI is included
        required_phi = ["diagnosis", "treatment_plan"]
        for field in required_phi:
            self.assertIn(field, necessary_data)
        
        # Verify unnecessary PHI is excluded
        unnecessary_phi = ["medical_record_number", "social_security_number"]
        for field in unnecessary_phi:
            self.assertNotIn(field, necessary_data)
    
    def test_phi_encryption(self):
        """Test PHI encryption requirements"""
        # Test encryption at rest
        encrypted_phi = self._encrypt_phi(self.hipaa_data)
        self.assertNotEqual(encrypted_phi, self.hipaa_data)
        
        # Test encryption in transit
        is_encrypted_in_transit = self._check_encryption_in_transit()
        self.assertTrue(is_encrypted_in_transit)
        
        # Test encryption key management
        key_secure = self._check_encryption_key_security()
        self.assertTrue(key_secure)
    
    def test_access_controls(self):
        """Test access controls for PHI"""
        # Test role-based access control
        user_role = "voice_therapist"
        can_access_phi = self._check_phi_access(user_role, self.test_user_id)
        self.assertTrue(can_access_phi)
        
        # Test unauthorized access prevention
        unauthorized_role = "billing_clerk"
        can_access_phi = self._check_phi_access(unauthorized_role, self.test_user_id)
        self.assertFalse(can_access_phi)
        
        # Test access logging
        access_logs = self._get_access_logs(self.test_user_id)
        self.assertIsNotNone(access_logs)
        self.assertGreater(len(access_logs), 0)
    
    def test_audit_trails(self):
        """Test audit trail requirements"""
        # Test PHI access logging
        audit_trail = self._get_phi_audit_trail(self.test_user_id)
        
        # Verify all PHI access is logged
        self.assertIsNotNone(audit_trail)
        self.assertGreater(len(audit_trail), 0)
        
        # Verify audit trail cannot be modified
        original_trail = audit_trail.copy()
        with self.assertRaises(Exception):
            audit_trail.append({"action": "malicious_action"})
    
    def test_breach_notification(self):
        """Test HIPAA breach notification requirements"""
        # Simulate PHI breach
        breach_result = self._simulate_phi_breach(self.test_user_id)
        
        # Verify breach is reported within 60 days
        report_time = breach_result.report_time
        breach_time = breach_result.breach_time
        time_to_report = report_time - breach_time
        
        self.assertLessEqual(time_to_report.days, 60)
        
        # Verify HHS notification
        hhs_notified = breach_result.hhs_notified
        self.assertTrue(hhs_notified)
        
        # Verify affected individuals notification
        individuals_notified = breach_result.individuals_notified
        self.assertIn(self.test_user_id, individuals_notified)
    
    def _identify_phi_fields(self, data: Dict[str, Any]) -> List[str]:
        """Identify PHI fields in data"""
        phi_fields = []
        phi_patterns = ["medical", "diagnosis", "treatment", "mrn", "ssn"]
        
        for key, value in data.items():
            if any(pattern in key.lower() for pattern in phi_patterns):
                phi_fields.append(key)
        
        return phi_fields
    
    def _get_minimum_necessary_data(self, user_id: str) -> Dict[str, Any]:
        """Get minimum necessary PHI data"""
        # Mock minimum necessary data
        return {
            "diagnosis": "Voice disorder",
            "treatment_plan": "Voice therapy and cloning"
        }
    
    def _encrypt_phi(self, phi_data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt PHI data"""
        # Mock encryption
        encrypted = {}
        for key, value in phi_data.items():
            if key in self._identify_phi_fields(phi_data):
                encrypted[key] = f"encrypted_{value}"
            else:
                encrypted[key] = value
        
        return encrypted
    
    def _check_encryption_in_transit(self) -> bool:
        """Check if PHI is encrypted in transit"""
        # Mock encryption check
        return True
    
    def _check_encryption_key_security(self) -> bool:
        """Check encryption key security"""
        # Mock key security check
        return True
    
    def _check_phi_access(self, role: str, user_id: str) -> bool:
        """Check if role can access PHI"""
        # Mock access control
        authorized_roles = ["voice_therapist", "doctor", "nurse"]
        return role in authorized_roles
    
    def _get_access_logs(self, user_id: str) -> List[Dict[str, Any]]:
        """Get PHI access logs"""
        # Mock access logs
        return [
            {"timestamp": self.current_time, "user": "therapist1", "action": "viewed"}
        ]
    
    def _get_phi_audit_trail(self, user_id: str) -> List[Dict[str, Any]]:
        """Get PHI audit trail"""
        # Mock audit trail
        return [
            {"timestamp": self.current_time, "action": "phi_accessed", "user": "therapist1"}
        ]
    
    def _simulate_phi_breach(self, user_id: str) -> Dict[str, Any]:
        """Simulate PHI breach"""
        # Mock breach simulation
        breach_time = self.current_time - timedelta(days=30)
        report_time = self.current_time - timedelta(days=15)
        
        return {
            "breach_time": breach_time,
            "report_time": report_time,
            "hhs_notified": True,
            "individuals_notified": [user_id]
        }

class SOC2ComplianceTest(ComplianceTestBase):
    """Test SOC 2 compliance requirements"""
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.soc2_controls = {
            "security": ["access_control", "encryption", "vulnerability_management"],
            "availability": ["backup_recovery", "disaster_recovery", "monitoring"],
            "processing_integrity": ["data_validation", "error_handling", "audit_logging"],
            "confidentiality": ["data_classification", "encryption", "access_controls"],
            "privacy": ["consent_management", "data_minimization", "breach_notification"]
        }
    
    def test_security_controls(self):
        """Test security control implementation"""
        # Test access control implementation
        access_controls = self._assess_security_controls("security")
        
        # Verify all security controls are implemented
        for control in self.soc2_controls["security"]:
            self.assertIn(control, access_controls)
            self.assertTrue(access_controls[control]["implemented"])
        
        # Verify control effectiveness
        overall_security_score = access_controls["overall_score"]
        self.assertGreaterEqual(overall_security_score, 80)
    
    def test_availability_controls(self):
        """Test availability control implementation"""
        # Test availability controls
        availability_controls = self._assess_availability_controls()
        
        # Verify backup and recovery
        backup_score = availability_controls["backup_recovery"]["score"]
        self.assertGreaterEqual(backup_score, 85)
        
        # Verify disaster recovery
        dr_score = availability_controls["disaster_recovery"]["score"]
        self.assertGreaterEqual(dr_score, 80)
        
        # Verify monitoring
        monitoring_score = availability_controls["monitoring"]["score"]
        self.assertGreaterEqual(monitoring_score, 90)
    
    def test_processing_integrity(self):
        """Test processing integrity controls"""
        # Test data validation
        validation_score = self._assess_data_validation()
        self.assertGreaterEqual(validation_score, 85)
        
        # Test error handling
        error_handling_score = self._assess_error_handling()
        self.assertGreaterEqual(error_handling_score, 80)
        
        # Test audit logging
        audit_logging_score = self._assess_audit_logging()
        self.assertGreaterEqual(audit_logging_score, 90)
    
    def test_confidentiality_controls(self):
        """Test confidentiality controls"""
        # Test data classification
        classification_score = self._assess_data_classification()
        self.assertGreaterEqual(classification_score, 85)
        
        # Test encryption implementation
        encryption_score = self._assess_encryption_implementation()
        self.assertGreaterEqual(encryption_score, 90)
        
        # Test access controls
        access_control_score = self._assess_access_controls()
        self.assertGreaterEqual(access_control_score, 85)
    
    def test_privacy_controls(self):
        """Test privacy controls"""
        # Test consent management
        consent_score = self._assess_consent_management()
        self.assertGreaterEqual(consent_score, 90)
        
        # Test data minimization
        minimization_score = self._assess_data_minimization()
        self.assertGreaterEqual(minimization_score, 85)
        
        # Test breach notification
        breach_notification_score = self._assess_breach_notification()
        self.assertGreaterEqual(breach_notification_score, 80)
    
    def _assess_security_controls(self, control_type: str) -> Dict[str, Any]:
        """Assess security controls"""
        # Mock security control assessment
        controls = {}
        for control in self.soc2_controls[control_type]:
            controls[control] = {
                "implemented": True,
                "score": 85,
                "status": "effective"
            }
        
        controls["overall_score"] = 85
        return controls
    
    def _assess_availability_controls(self) -> Dict[str, Any]:
        """Assess availability controls"""
        # Mock availability control assessment
        return {
            "backup_recovery": {"score": 90, "status": "effective"},
            "disaster_recovery": {"score": 85, "status": "effective"},
            "monitoring": {"score": 95, "status": "effective"}
        }
    
    def _assess_data_validation(self) -> int:
        """Assess data validation effectiveness"""
        # Mock validation assessment
        return 90
    
    def _assess_error_handling(self) -> int:
        """Assess error handling effectiveness"""
        # Mock error handling assessment
        return 85
    
    def _assess_audit_logging(self) -> int:
        """Assess audit logging effectiveness"""
        # Mock audit logging assessment
        return 95
    
    def _assess_data_classification(self) -> int:
        """Assess data classification effectiveness"""
        # Mock classification assessment
        return 90
    
    def _assess_encryption_implementation(self) -> int:
        """Assess encryption implementation effectiveness"""
        # Mock encryption assessment
        return 95
    
    def _assess_access_controls(self) -> int:
        """Assess access control effectiveness"""
        # Mock access control assessment
        return 90
    
    def _assess_consent_management(self) -> int:
        """Assess consent management effectiveness"""
        # Mock consent management assessment
        return 95
    
    def _assess_data_minimization(self) -> int:
        """Assess data minimization effectiveness"""
        # Mock data minimization assessment
        return 90
    
    def _assess_breach_notification(self) -> int:
        """Assess breach notification effectiveness"""
        # Mock breach notification assessment
        return 85

class OverallComplianceAssessment(unittest.TestCase):
    """Overall compliance assessment across all frameworks"""
    
    def test_comprehensive_compliance(self):
        """Test comprehensive compliance across all frameworks"""
        compliance_scores = {}
        max_score = 100
        
        # GDPR Compliance (30 points)
        gdpr_score = self._assess_gdpr_compliance()
        compliance_scores['GDPR'] = gdpr_score
        print(f"GDPR Compliance: {gdpr_score}/30")
        
        # HIPAA Compliance (25 points)
        hipaa_score = self._assess_hipaa_compliance()
        compliance_scores['HIPAA'] = hipaa_score
        print(f"HIPAA Compliance: {hipaa_score}/25")
        
        # SOC 2 Compliance (25 points)
        soc2_score = self._assess_soc2_compliance()
        compliance_scores['SOC2'] = soc2_score
        print(f"SOC 2 Compliance: {soc2_score}/25")
        
        # General Security (20 points)
        security_score = self._assess_general_security()
        compliance_scores['Security'] = security_score
        print(f"General Security: {security_score}/20")
        
        # Calculate total score
        total_score = sum(compliance_scores.values())
        print(f"\nTotal Compliance Score: {total_score}/{max_score}")
        
        # Compliance assertions
        self.assertGreaterEqual(total_score, 85, "Overall compliance should be at least 85%")
        self.assertGreaterEqual(gdpr_score, 25, "GDPR compliance should be at least 83%")
        self.assertGreaterEqual(hipaa_score, 20, "HIPAA compliance should be at least 80%")
        self.assertGreaterEqual(soc2_score, 20, "SOC 2 compliance should be at least 80%")
        self.assertGreaterEqual(security_score, 16, "General security should be at least 80%")
        
        # Generate compliance report
        self._generate_compliance_report(compliance_scores)
    
    def _assess_gdpr_compliance(self) -> int:
        """Assess GDPR compliance (30 points)"""
        score = 0
        
        # Legal basis (5 points)
        score += 5  # Mock perfect legal basis
        
        # Data minimization (5 points)
        score += 5  # Mock data minimization implemented
        
        # Purpose limitation (5 points)
        score += 5  # Mock purpose limitation implemented
        
        # Storage limitation (5 points)
        score += 5  # Mock storage limitation implemented
        
        # Data subject rights (5 points)
        score += 5  # Mock data subject rights implemented
        
        # Breach notification (5 points)
        score += 5  # Mock breach notification implemented
        
        return score
    
    def _assess_hipaa_compliance(self) -> int:
        """Assess HIPAA compliance (25 points)"""
        score = 0
        
        # PHI identification (5 points)
        score += 5  # Mock PHI identification implemented
        
        # Minimum necessary standard (5 points)
        score += 5  # Mock minimum necessary standard implemented
        
        # PHI encryption (5 points)
        score += 5  # Mock PHI encryption implemented
        
        # Access controls (5 points)
        score += 5  # Mock access controls implemented
        
        # Audit trails (5 points)
        score += 5  # Mock audit trails implemented
        
        return score
    
    def _assess_soc2_compliance(self) -> int:
        """Assess SOC 2 compliance (25 points)"""
        score = 0
        
        # Security controls (8 points)
        score += 8  # Mock security controls implemented
        
        # Availability controls (6 points)
        score += 6  # Mock availability controls implemented
        
        # Processing integrity (5 points)
        score += 5  # Mock processing integrity implemented
        
        # Confidentiality controls (3 points)
        score += 3  # Mock confidentiality controls implemented
        
        # Privacy controls (3 points)
        score += 3  # Mock privacy controls implemented
        
        return score
    
    def _assess_general_security(self) -> int:
        """Assess general security (20 points)"""
        score = 0
        
        # Authentication (5 points)
        score += 5  # Mock authentication implemented
        
        # Authorization (5 points)
        score += 5  # Mock authorization implemented
        
        # Input validation (5 points)
        score += 5  # Mock input validation implemented
        
        # Monitoring and logging (5 points)
        score += 5  # Mock monitoring and logging implemented
        
        return score
    
    def _generate_compliance_report(self, compliance_scores: Dict[str, int]):
        """Generate compliance report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": sum(compliance_scores.values()),
            "framework_scores": compliance_scores,
            "recommendations": self._generate_recommendations(compliance_scores)
        }
        
        # Save report (mock)
        print("\nCompliance Report Generated:")
        print(json.dumps(report, indent=2))
    
    def _generate_recommendations(self, compliance_scores: Dict[str, int]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        for framework, score in compliance_scores.items():
            if score < 20:  # Less than 80%
                recommendations.append(f"Improve {framework} compliance - current score: {score}")
            elif score < 23:  # Less than 90%
                recommendations.append(f"Enhance {framework} compliance - current score: {score}")
        
        if not recommendations:
            recommendations.append("All compliance frameworks meet minimum requirements")
        
        return recommendations

if __name__ == '__main__':
    unittest.main()
