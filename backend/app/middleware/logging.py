from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import time
import json
import uuid
from datetime import datetime
from typing import Dict, Any
import os

# Configure logging
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_requests = os.getenv("LOG_REQUESTS", "true").lower() == "true"
        self.log_responses = os.getenv("LOG_RESPONSES", "true").lower() == "true"
        self.log_request_body = os.getenv("LOG_REQUEST_BODY", "false").lower() == "true"
        self.log_response_body = os.getenv("LOG_RESPONSE_BODY", "false").lower() == "true"
        self.log_headers = os.getenv("LOG_HEADERS", "false").lower() == "true"
        self.max_body_size = int(os.getenv("MAX_LOG_BODY_SIZE", "1024"))  # Max bytes to log
        
        # Sensitive headers to mask
        self.sensitive_headers = {
            "authorization", "cookie", "x-api-key", "x-auth-token",
            "x-forwarded-for", "x-real-ip", "x-client-ip"
        }
        
        # Sensitive query parameters to mask
        self.sensitive_params = {
            "token", "key", "secret", "password", "api_key", "auth"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and response"""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        if self.log_requests:
            await self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log response
            if self.log_responses:
                await self._log_response(response, request_id, process_time)
            
            return response
            
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            await self._log_error(request, request_id, e, process_time)
            
            # Re-raise the exception
            raise
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details"""
        try:
            # Get client information
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "Unknown")
            
            # Get request details
            method = request.method
            url = str(request.url)
            path = request.url.path
            query_params = dict(request.query_params)
            
            # Mask sensitive query parameters
            masked_params = self._mask_sensitive_data(query_params, self.sensitive_params)
            
            # Get headers (masked if enabled)
            headers = {}
            if self.log_headers:
                headers = self._mask_sensitive_data(dict(request.headers), self.sensitive_headers)
            
            # Get request body (if enabled and available)
            body = None
            if self.log_request_body and method in ["POST", "PUT", "PATCH"]:
                body = await self._get_request_body(request)
            
            # Create log entry
            log_data = {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "request",
                "method": method,
                "url": url,
                "path": path,
                "query_params": masked_params,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "headers": headers,
                "body": body
            }
            
            # Log based on level
            if self.log_level == "DEBUG":
                logger.debug(f"Request: {json.dumps(log_data, indent=2)}")
            else:
                logger.info(f"Request {request_id}: {method} {path} from {client_ip}")
                
        except Exception as e:
            logger.error(f"Error logging request: {str(e)}")
    
    async def _log_response(self, response: Response, request_id: str, process_time: float):
        """Log outgoing response details"""
        try:
            # Get response details
            status_code = response.status_code
            headers = {}
            if self.log_headers:
                headers = dict(response.headers)
            
            # Get response body (if enabled)
            body = None
            if self.log_response_body:
                body = await self._get_response_body(response)
            
            # Create log entry
            log_data = {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "response",
                "status_code": status_code,
                "process_time": process_time,
                "headers": headers,
                "body": body
            }
            
            # Log based on level and status code
            if status_code >= 400:
                if self.log_level == "DEBUG":
                    logger.error(f"Response: {json.dumps(log_data, indent=2)}")
                else:
                    logger.error(f"Response {request_id}: {status_code} in {process_time:.3f}s")
            elif self.log_level == "DEBUG":
                logger.debug(f"Response: {json.dumps(log_data, indent=2)}")
            else:
                logger.info(f"Response {request_id}: {status_code} in {process_time:.3f}s")
                
        except Exception as e:
            logger.error(f"Error logging response: {str(e)}")
    
    async def _log_error(self, request: Request, request_id: str, error: Exception, process_time: float):
        """Log error details"""
        try:
            # Get request details
            method = request.method
            path = request.url.path
            client_ip = self._get_client_ip(request)
            
            # Create error log entry
            log_data = {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "error",
                "method": method,
                "path": path,
                "client_ip": client_ip,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "process_time": process_time
            }
            
            # Log error
            logger.error(f"Error {request_id}: {method} {path} - {type(error).__name__}: {str(error)}")
            
            if self.log_level == "DEBUG":
                logger.debug(f"Error details: {json.dumps(log_data, indent=2)}")
                
        except Exception as e:
            logger.error(f"Error logging error: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get the real client IP address"""
        # Check various headers for real IP
        for header in ["x-forwarded-for", "x-real-ip", "x-client-ip", "cf-connecting-ip"]:
            if header in request.headers:
                ip = request.headers[header]
                # Handle comma-separated IPs (take first)
                if "," in ip:
                    ip = ip.split(",")[0].strip()
                return ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "Unknown"
    
    def _mask_sensitive_data(self, data: Dict[str, Any], sensitive_keys: set) -> Dict[str, Any]:
        """Mask sensitive data in dictionaries"""
        masked_data = {}
        
        for key, value in data.items():
            if key.lower() in sensitive_keys:
                if isinstance(value, str) and len(value) > 0:
                    # Mask the value, keeping first and last character if possible
                    if len(value) <= 2:
                        masked_data[key] = "***"
                    else:
                        masked_data[key] = f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"
                else:
                    masked_data[key] = "***"
            else:
                masked_data[key] = value
        
        return masked_data
    
    async def _get_request_body(self, request: Request) -> str:
        """Get request body content"""
        try:
            # Check content type
            content_type = request.headers.get("content-type", "")
            
            # Only log text-based content types
            if not any(text_type in content_type.lower() for text_type in ["text", "json", "xml", "form"]):
                return "[Binary content - not logged]"
            
            # Get body
            body = await request.body()
            
            # Decode and truncate if necessary
            try:
                body_text = body.decode("utf-8")
                if len(body_text) > self.max_body_size:
                    body_text = body_text[:self.max_body_size] + "... [truncated]"
                return body_text
            except UnicodeDecodeError:
                return "[Binary content - decode failed]"
                
        except Exception as e:
            return f"[Error reading body: {str(e)}]"
    
    async def _get_response_body(self, response: Response) -> str:
        """Get response body content"""
        try:
            # Check if response has body
            if not hasattr(response, "body"):
                return "[No body]"
            
            body = response.body
            
            # Handle different response types
            if isinstance(body, bytes):
                try:
                    body_text = body.decode("utf-8")
                    if len(body_text) > self.max_body_size:
                        body_text = body_text[:self.max_body_size] + "... [truncated]"
                    return body_text
                except UnicodeDecodeError:
                    return "[Binary content - decode failed]"
            elif isinstance(body, str):
                if len(body) > self.max_body_size:
                    body = body[:self.max_body_size] + "... [truncated]"
                return body
            else:
                return f"[{type(body).__name__} content]"
                
        except Exception as e:
            return f"[Error reading body: {str(e)}]"

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured logging in JSON format"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("structured")
        
        # Configure structured logger
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')  # Just the message, no timestamp/level
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # Prevent duplicate logs
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and response with structured logging"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Log request
        await self._log_structured_request(request, request_id)
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            await self._log_structured_response(response, request_id, process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            await self._log_structured_error(request, request_id, e, process_time)
            raise
    
    async def _log_structured_request(self, request: Request, request_id: str):
        """Log request in structured format"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "request_id": request_id,
            "event": "request_started",
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "content_length": request.headers.get("content-length"),
            "content_type": request.headers.get("content-type")
        }
        
        self.logger.info(json.dumps(log_entry))
    
    async def _log_structured_response(self, response: Response, request_id: str, process_time: float):
        """Log response in structured format"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "request_id": request_id,
            "event": "request_completed",
            "status_code": response.status_code,
            "process_time": process_time,
            "content_length": response.headers.get("content-length"),
            "content_type": response.headers.get("content-type")
        }
        
        self.logger.info(json.dumps(log_entry))
    
    async def _log_structured_error(self, request: Request, request_id: str, error: Exception, process_time: float):
        """Log error in structured format"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "request_id": request_id,
            "event": "request_failed",
            "method": request.method,
            "path": request.url.path,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "process_time": process_time
        }
        
        self.logger.error(json.dumps(log_entry))
    
    def _get_client_ip(self, request: Request) -> str:
        """Get the real client IP address"""
        for header in ["x-forwarded-for", "x-real-ip", "x-client-ip", "cf-connecting-ip"]:
            if header in request.headers:
                ip = request.headers[header]
                if "," in ip:
                    ip = ip.split(",")[0].strip()
                return ip
        return request.client.host if request.client else "Unknown"
