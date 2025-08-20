"""
Webhook Handler HTTP Trigger Function
Handles webhooks from Azure services and external systems
"""
import logging
import json
import azure.functions as func
from typing import Dict, Any
from datetime import datetime
import uuid
import os
import hmac
import hashlib

from ..shared.auth import get_current_user_from_token

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookHandler:
    """Webhook handler for different webhook types"""
    
    def __init__(self):
        self.webhook_secret = os.getenv("WEBHOOK_SECRET", "")
        self.supported_types = {
            "azure-speech": self.handle_azure_speech_webhook,
            "azure-translator": self.handle_azure_translator_webhook,
            "azure-openai": self.handle_azure_openai_webhook,
            "voice-training": self.handle_voice_training_webhook,
            "synthesis-complete": self.handle_synthesis_complete_webhook,
            "error-notification": self.handle_error_notification_webhook
        }
    
    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify webhook signature for security"""
        if not secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True
        
        try:
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    async def handle_webhook(self, webhook_type: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Route webhook to appropriate handler"""
        
        if webhook_type not in self.supported_types:
            logger.warning(f"Unsupported webhook type: {webhook_type}")
            return {
                "error": "Unsupported webhook type",
                "message": f"Webhook type '{webhook_type}' is not supported"
            }
        
        # Get the handler function
        handler = self.supported_types[webhook_type]
        
        try:
            # Call the appropriate handler
            result = await handler(payload, headers)
            return result
        except Exception as e:
            logger.error(f"Error handling webhook {webhook_type}: {str(e)}")
            return {
                "error": "Webhook processing failed",
                "message": str(e)
            }
    
    async def handle_azure_speech_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle Azure Speech Service webhooks"""
        logger.info("Processing Azure Speech Service webhook")
        
        # Extract relevant information
        event_type = payload.get("eventType")
        resource_id = payload.get("resourceId")
        status = payload.get("status")
        
        if event_type == "VoiceTrainingCompleted":
            return await self.handle_voice_training_completion(payload)
        elif event_type == "SynthesisCompleted":
            return await self.handle_synthesis_completion(payload)
        else:
            logger.info(f"Unhandled Azure Speech event: {event_type}")
            return {"status": "ignored", "message": f"Event type {event_type} not handled"}
    
    async def handle_azure_translator_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle Azure Translator webhooks"""
        logger.info("Processing Azure Translator webhook")
        
        # Extract relevant information
        event_type = payload.get("eventType")
        resource_id = payload.get("resourceId")
        
        if event_type == "TranslationCompleted":
            return await self.handle_translation_completion(payload)
        else:
            logger.info(f"Unhandled Azure Translator event: {event_type}")
            return {"status": "ignored", "message": f"Event type {event_type} not handled"}
    
    async def handle_azure_openai_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle Azure OpenAI webhooks"""
        logger.info("Processing Azure OpenAI webhook")
        
        # Extract relevant information
        event_type = payload.get("eventType")
        resource_id = payload.get("resourceId")
        
        if event_type == "TextToSpeechCompleted":
            return await self.handle_openai_tts_completion(payload)
        else:
            logger.info(f"Unhandled Azure OpenAI event: {event_type}")
            return {"status": "ignored", "message": f"Event type {event_type} not handled"}
    
    async def handle_voice_training_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle voice training webhooks"""
        logger.info("Processing voice training webhook")
        
        training_id = payload.get("training_id")
        status = payload.get("status")
        progress = payload.get("progress", 0)
        
        # Process training status update
        if status == "completed":
            return await self.handle_training_completion(payload)
        elif status == "failed":
            return await self.handle_training_failure(payload)
        elif status == "in_progress":
            return await self.handle_training_progress(payload)
        else:
            return {"status": "processed", "message": f"Training {training_id} status: {status}"}
    
    async def handle_synthesis_complete_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle synthesis completion webhooks"""
        logger.info("Processing synthesis completion webhook")
        
        synthesis_id = payload.get("synthesis_id")
        status = payload.get("status")
        audio_url = payload.get("audio_url")
        
        if status == "completed":
            return await self.handle_synthesis_success(payload)
        elif status == "failed":
            return await self.handle_synthesis_failure(payload)
        else:
            return {"status": "processed", "message": f"Synthesis {synthesis_id} status: {status}"}
    
    async def handle_error_notification_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle error notification webhooks"""
        logger.info("Processing error notification webhook")
        
        error_type = payload.get("error_type")
        error_message = payload.get("error_message")
        resource_id = payload.get("resource_id")
        severity = payload.get("severity", "medium")
        
        # Process error notification
        return await self.handle_error_notification(payload)
    
    async def handle_voice_training_completion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle voice training completion"""
        # Implementation for voice training completion
        return {"status": "processed", "message": "Voice training completed"}
    
    async def handle_synthesis_completion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle synthesis completion"""
        # Implementation for synthesis completion
        return {"status": "processed", "message": "Synthesis completed"}
    
    async def handle_translation_completion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle translation completion"""
        # Implementation for translation completion
        return {"status": "processed", "message": "Translation completed"}
    
    async def handle_openai_tts_completion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle OpenAI TTS completion"""
        # Implementation for OpenAI TTS completion
        return {"status": "processed", "message": "OpenAI TTS completed"}
    
    async def handle_training_completion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle training completion"""
        # Implementation for training completion
        return {"status": "processed", "message": "Training completed"}
    
    async def handle_training_failure(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle training failure"""
        # Implementation for training failure
        return {"status": "processed", "message": "Training failed"}
    
    async def handle_training_progress(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle training progress"""
        # Implementation for training progress
        return {"status": "processed", "message": "Training progress updated"}
    
    async def handle_synthesis_success(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle synthesis success"""
        # Implementation for synthesis success
        return {"status": "processed", "message": "Synthesis successful"}
    
    async def handle_synthesis_failure(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle synthesis failure"""
        # Implementation for synthesis failure
        return {"status": "processed", "message": "Synthesis failed"}
    
    async def handle_error_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle error notification"""
        # Implementation for error notification
        return {"status": "processed", "message": "Error notification processed"}

# Global webhook handler instance
webhook_handler = WebhookHandler()

async def main(req: func.HttpRequest, webhook_type: str, notificationQueue: func.Out[str]) -> func.HttpResponse:
    """
    Main function for webhook handler HTTP trigger
    """
    try:
        logger.info(f"Webhook handler function triggered for type: {webhook_type}")
        
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
        
        # Get webhook signature for verification
        signature = req.headers.get("x-webhook-signature", "")
        
        # Get request body
        try:
            payload = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({
                    "error": "Bad Request",
                    "message": "Invalid JSON in request body"
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Verify webhook signature
        if not webhook_handler.verify_signature(
            json.dumps(payload, sort_keys=True),
            signature,
            webhook_handler.webhook_secret
        ):
            logger.warning("Webhook signature verification failed")
            return func.HttpResponse(
                json.dumps({
                    "error": "Unauthorized",
                    "message": "Invalid webhook signature"
                }),
                status_code=401,
                mimetype="application/json"
            )
        
        # Process webhook
        result = await webhook_handler.handle_webhook(webhook_type, payload, dict(req.headers))
        
        # Generate webhook ID
        webhook_id = str(uuid.uuid4())
        
        # Create notification message for queue
        notification_message = {
            "webhook_id": webhook_id,
            "webhook_type": webhook_type,
            "payload": payload,
            "result": result,
            "processed_at": datetime.utcnow().isoformat(),
            "status": "processed",
            "function_name": "webhook-handler"
        }
        
        # Add message to queue
        notificationQueue.set(json.dumps(notification_message))
        
        logger.info(f"Webhook {webhook_id} processed successfully for type {webhook_type}")
        
        # Return success response
        return func.HttpResponse(
            json.dumps({
                "webhook_id": webhook_id,
                "status": "processed",
                "message": "Webhook processed successfully",
                "result": result,
                "processed_at": notification_message["processed_at"]
            }),
            status_code=200,
            mimetype="application/json",
            headers={
                "X-Webhook-ID": webhook_id,
                "X-Webhook-Type": webhook_type
            }
        )
        
    except Exception as e:
        logger.error(f"Error in webhook handler function: {str(e)}")
        
        return func.HttpResponse(
            json.dumps({
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "webhook_type": webhook_type
            }),
            status_code=500,
            mimetype="application/json"
        )
