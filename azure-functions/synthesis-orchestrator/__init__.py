"""
Synthesis Orchestrator HTTP Trigger Function
Orchestrates voice synthesis requests and routes them to appropriate queues
"""
import logging
import json
import azure.functions as func
from typing import Dict, Any, List
from datetime import datetime
import uuid
import os

from ..shared.auth import get_current_user_from_token

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SynthesisRequest:
    """Synthesis request model"""
    
    def __init__(self, data: Dict[str, Any]):
        self.text = data.get("text")
        self.voice_id = data.get("voice_id")
        self.language = data.get("language", "en-US")
        self.output_format = data.get("output_format", "wav")
        self.speed = data.get("speed", 1.0)
        self.pitch = data.get("pitch", 0.0)
        self.volume = data.get("volume", 1.0)
        self.ssml = data.get("ssml")
        self.metadata = data.get("metadata", {})
    
    def validate(self) -> tuple[bool, str]:
        """Validate the synthesis request"""
        if not self.text and not self.ssml:
            return False, "Either text or SSML is required"
        
        if not self.voice_id:
            return False, "voice_id is required"
        
        if self.speed < 0.5 or self.speed > 2.0:
            return False, "Speed must be between 0.5 and 2.0"
        
        if self.pitch < -12 or self.pitch > 12:
            return False, "Pitch must be between -12 and 12"
        
        if self.volume < 0.0 or self.volume > 2.0:
            return False, "Volume must be between 0.0 and 2.0"
        
        return True, ""

class BatchSynthesisRequest:
    """Batch synthesis request model"""
    
    def __init__(self, data: Dict[str, Any]):
        self.requests = data.get("requests", [])
        self.voice_id = data.get("voice_id")
        self.language = data.get("language", "en-US")
        self.output_format = data.get("output_format", "wav")
        self.priority = data.get("priority", "normal")
        self.metadata = data.get("metadata", {})
    
    def validate(self) -> tuple[bool, str]:
        """Validate the batch synthesis request"""
        if not self.requests:
            return False, "At least one synthesis request is required"
        
        if len(self.requests) > 100:
            return False, "Maximum 100 requests allowed per batch"
        
        if not self.voice_id:
            return False, "voice_id is required"
        
        # Validate individual requests
        for i, req in enumerate(self.requests):
            synthesis_req = SynthesisRequest(req)
            is_valid, error_message = synthesis_req.validate()
            if not is_valid:
                return False, f"Request {i+1}: {error_message}"
        
        return True, ""

async def main(req: func.HttpRequest, synthesisQueue: func.Out[str], batchQueue: func.Out[str]) -> func.HttpResponse:
    """
    Main function for synthesis orchestrator HTTP trigger
    """
    try:
        logger.info("Synthesis orchestrator function triggered")
        
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
        
        # Determine request type
        request_type = req_body.get("type", "single")
        
        if request_type == "batch":
            # Handle batch synthesis request
            return await handle_batch_synthesis(
                req_body, user, batchQueue, req.headers.get("x-request-id", "unknown")
            )
        else:
            # Handle single synthesis request
            return await handle_single_synthesis(
                req_body, user, synthesisQueue, req.headers.get("x-request-id", "unknown")
            )
        
    except Exception as e:
        logger.error(f"Error in synthesis orchestrator function: {str(e)}")
        
        return func.HttpResponse(
            json.dumps({
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "request_id": req.headers.get("x-request-id", "unknown")
            }),
            status_code=500,
            mimetype="application/json"
        )

async def handle_single_synthesis(
    req_body: Dict[str, Any], 
    user: Dict[str, Any], 
    synthesisQueue: func.Out[str],
    request_id: str
) -> func.HttpResponse:
    """Handle single synthesis request"""
    
    # Create synthesis request
    synthesis_req = SynthesisRequest(req_body)
    
    # Validate request
    is_valid, error_message = synthesis_req.validate()
    if not is_valid:
        return func.HttpResponse(
            json.dumps({
                "error": "Bad Request",
                "message": error_message
            }),
            status_code=400,
            mimetype="application/json"
        )
    
    # Generate synthesis ID
    synthesis_id = str(uuid.uuid4())
    
    # Create synthesis message for queue
    synthesis_message = {
        "synthesis_id": synthesis_id,
        "user_id": user["id"],
        "user_email": user["email"],
        "text": synthesis_req.text,
        "voice_id": synthesis_req.voice_id,
        "language": synthesis_req.language,
        "output_format": synthesis_req.output_format,
        "speed": synthesis_req.speed,
        "pitch": synthesis_req.pitch,
        "volume": synthesis_req.volume,
        "ssml": synthesis_req.ssml,
        "metadata": synthesis_req.metadata,
        "created_at": datetime.utcnow().isoformat(),
        "status": "queued",
        "type": "single",
        "function_name": "synthesis-orchestrator",
        "request_id": request_id
    }
    
    # Add message to queue
    synthesisQueue.set(json.dumps(synthesis_message))
    
    logger.info(f"Single synthesis {synthesis_id} queued for user {user['id']}")
    
    # Return success response
    response_data = {
        "synthesis_id": synthesis_id,
        "message": "Synthesis request received and queued for processing",
        "status": "queued",
        "estimated_processing_time": "1-2 minutes",
        "created_at": synthesis_message["created_at"]
    }
    
    return func.HttpResponse(
        json.dumps(response_data),
        status_code=202,  # Accepted
        mimetype="application/json",
        headers={
            "X-Synthesis-ID": synthesis_id,
            "X-Request-ID": request_id,
            "Location": f"/api/synthesis/{synthesis_id}/status"
        }
    )

async def handle_batch_synthesis(
    req_body: Dict[str, Any], 
    user: Dict[str, Any], 
    batchQueue: func.Out[str],
    request_id: str
) -> func.HttpResponse:
    """Handle batch synthesis request"""
    
    # Create batch synthesis request
    batch_req = BatchSynthesisRequest(req_body)
    
    # Validate request
    is_valid, error_message = batch_req.validate()
    if not is_valid:
        return func.HttpResponse(
            json.dumps({
                "error": "Bad Request",
                "message": error_message
            }),
            status_code=400,
            mimetype="application/json"
        )
    
    # Generate batch ID
    batch_id = str(uuid.uuid4())
    
    # Create batch synthesis message for queue
    batch_message = {
        "batch_id": batch_id,
        "user_id": user["id"],
        "user_email": user["email"],
        "requests": batch_req.requests,
        "voice_id": batch_req.voice_id,
        "language": batch_req.language,
        "output_format": batch_req.output_format,
        "priority": batch_req.priority,
        "metadata": batch_req.metadata,
        "total_requests": len(batch_req.requests),
        "created_at": datetime.utcnow().isoformat(),
        "status": "queued",
        "type": "batch",
        "function_name": "synthesis-orchestrator",
        "request_id": request_id
    }
    
    # Add message to queue
    batchQueue.set(json.dumps(batch_message))
    
    logger.info(f"Batch synthesis {batch_id} queued for user {user['id']} with {len(batch_req.requests)} requests")
    
    # Return success response
    response_data = {
        "batch_id": batch_id,
        "message": "Batch synthesis request received and queued for processing",
        "status": "queued",
        "total_requests": len(batch_req.requests),
        "estimated_processing_time": f"{len(batch_req.requests) * 2}-{len(batch_req.requests) * 3} minutes",
        "created_at": batch_message["created_at"]
    }
    
    return func.HttpResponse(
        json.dumps(response_data),
        status_code=202,  # Accepted
        mimetype="application/json",
        headers={
            "X-Batch-ID": batch_id,
            "X-Request-ID": request_id,
            "Location": f"/api/batch-synthesis/{batch_id}/status"
        }
    )
