"""
Voice Enrollment HTTP Trigger Function
Handles voice enrollment requests and queues them for processing
"""
import logging
import json
import azure.functions as func
from typing import Dict, Any
from datetime import datetime
import uuid
import os

from ..shared.auth import get_current_user_from_token

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceEnrollmentRequest:
    """Voice enrollment request model"""
    
    def __init__(self, data: Dict[str, Any]):
        self.user_id = data.get("user_id")
        self.voice_name = data.get("voice_name")
        self.language = data.get("language", "en-US")
        self.audio_files = data.get("audio_files", [])
        self.consent_given = data.get("consent_given", False)
        self.consent_text = data.get("consent_text")
        self.consent_signature = data.get("consent_signature")
        self.metadata = data.get("metadata", {})
    
    def validate(self) -> tuple[bool, str]:
        """Validate the enrollment request"""
        if not self.user_id:
            return False, "user_id is required"
        
        if not self.voice_name:
            return False, "voice_name is required"
        
        if not self.audio_files:
            return False, "At least one audio file is required"
        
        if not self.consent_given:
            return False, "Consent must be given for voice enrollment"
        
        if not self.consent_text:
            return False, "consent_text is required"
        
        if not self.consent_signature:
            return False, "consent_signature is required"
        
        return True, ""

async def main(req: func.HttpRequest, enrollmentQueue: func.Out[str]) -> func.HttpResponse:
    """
    Main function for voice enrollment HTTP trigger
    """
    try:
        logger.info("Voice enrollment function triggered")
        
        # Get request method
        if req.method != "POST":
            return func.HttpResponse(
                json.dumps({
                    "error": "Method not allowed",
                    "message": "Only POST method is supported"
                }),
                status_code=405,
                mimetype="application/json"
            )
        
        # Get authorization header
        auth_header = req.headers.get("authorization")
        if not auth_header:
            return func.HttpResponse(
                json.dumps({
                    "error": "Unauthorized",
                    "message": "Authorization header is required"
                }),
                status_code=401,
                mimetype="application/json"
            )
        
        # Validate user token
        user = await get_current_user_from_token(auth_header)
        if not user:
            return func.HttpResponse(
                json.dumps({
                    "error": "Unauthorized",
                    "message": "Invalid or expired token"
                }),
                status_code=401,
                mimetype="application/json"
            )
        
        # Parse request body
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({
                    "error": "Bad Request",
                    "message": "Invalid JSON in request body"
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Create enrollment request
        enrollment_req = VoiceEnrollmentRequest(req_body)
        
        # Validate request
        is_valid, error_message = enrollment_req.validate()
        if not is_valid:
            return func.HttpResponse(
                json.dumps({
                    "error": "Bad Request",
                    "message": error_message
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Generate enrollment ID
        enrollment_id = str(uuid.uuid4())
        
        # Create enrollment message for queue
        enrollment_message = {
            "enrollment_id": enrollment_id,
            "user_id": user["id"],
            "user_email": user["email"],
            "voice_name": enrollment_req.voice_name,
            "language": enrollment_req.language,
            "audio_files": enrollment_req.audio_files,
            "consent_given": enrollment_req.consent_given,
            "consent_text": enrollment_req.consent_text,
            "consent_signature": enrollment_req.consent_signature,
            "metadata": enrollment_req.metadata,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending",
            "function_name": "voice-enrollment",
            "request_id": req.headers.get("x-request-id", "unknown")
        }
        
        # Add message to queue
        enrollmentQueue.set(json.dumps(enrollment_message))
        
        logger.info(f"Voice enrollment {enrollment_id} queued for user {user['id']}")
        
        # Return success response
        response_data = {
            "enrollment_id": enrollment_id,
            "message": "Voice enrollment request received and queued for processing",
            "status": "pending",
            "estimated_processing_time": "5-10 minutes",
            "created_at": enrollment_message["created_at"]
        }
        
        return func.HttpResponse(
            json.dumps(response_data),
            status_code=202,  # Accepted
            mimetype="application/json",
            headers={
                "X-Enrollment-ID": enrollment_id,
                "X-Request-ID": req.headers.get("x-request-id", "unknown"),
                "Location": f"/api/enrollment/{enrollment_id}/status"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in voice enrollment function: {str(e)}")
        
        return func.HttpResponse(
            json.dumps({
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "request_id": req.headers.get("x-request-id", "unknown")
            }),
            status_code=500,
            mimetype="application/json"
        )
