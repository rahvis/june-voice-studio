from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import traceback
import json
from datetime import datetime
from typing import Dict, Any, Optional
import os

# Configure logging
logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for consistent error handling and response formatting"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Error handling configuration
        self.include_traceback = os.getenv("ERROR_INCLUDE_TRACEBACK", "false").lower() == "true"
        self.log_errors = os.getenv("ERROR_LOG_ERRORS", "true").lower() == "true"
        self.log_level = os.getenv("ERROR_LOG_LEVEL", "ERROR").upper()
        
        # Error mapping for common exceptions
        self.error_mapping = {
            "ValidationError": {
                "status_code": 400,
                "error_type": "ValidationError",
                "message": "Request validation failed"
            },
            "AuthenticationError": {
                "status_code": 401,
                "error_type": "AuthenticationError",
                "message": "Authentication failed"
            },
            "AuthorizationError": {
                "status_code": 403,
                "error_type": "AuthorizationError",
                "message": "Access denied"
            },
            "NotFoundError": {
                "status_code": 404,
                "error_type": "NotFoundError",
                "message": "Resource not found"
            },
            "ConflictError": {
                "status_code": 409,
                "error_type": "ConflictError",
                "message": "Resource conflict"
            },
            "RateLimitError": {
                "status_code": 429,
                "error_type": "RateLimitError",
                "message": "Rate limit exceeded"
            },
            "InternalServerError": {
                "status_code": 500,
                "error_type": "InternalServerError",
                "message": "Internal server error"
            },
            "ServiceUnavailableError": {
                "status_code": 503,
                "error_type": "ServiceUnavailableError",
                "message": "Service temporarily unavailable"
            }
        }
        
        # Custom error handlers
        self.custom_handlers = {}
        
        logger.info(f"Error handling middleware initialized - Log level: {self.log_level}")
    
    async def dispatch(self, request: Request, call_next):
        """Process the request with error handling"""
        try:
            # Process request
            response = await call_next(request)
            return response
            
        except Exception as exc:
            # Handle the exception
            return await self._handle_exception(request, exc)
    
    async def _handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle exceptions and return formatted error response"""
        try:
            # Get error details
            error_info = await self._get_error_info(request, exc)
            
            # Log the error
            if self.log_errors:
                await self._log_error(request, exc, error_info)
            
            # Create error response
            error_response = await self._create_error_response(request, exc, error_info)
            
            return error_response
            
        except Exception as e:
            # Fallback error handling
            logger.error(f"Error in error handler: {str(e)}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": "InternalServerError",
                        "code": 500,
                        "message": "An unexpected error occurred",
                        "timestamp": datetime.utcnow().isoformat(),
                        "request_id": getattr(request.state, "request_id", "unknown")
                    }
                }
            )
    
    async def _get_error_info(self, request: Request, exc: Exception) -> Dict[str, Any]:
        """Extract error information from exception"""
        error_info = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "request_path": request.url.path,
            "request_method": request.method,
            "request_id": getattr(request.state, "request_id", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Handle specific exception types
        if isinstance(exc, HTTPException):
            error_info.update({
                "status_code": exc.status_code,
                "error_type": self._get_error_type(exc.status_code),
                "message": exc.detail,
                "headers": dict(exc.headers) if exc.headers else {}
            })
        else:
            # Map exception to standard error info
            mapped_error = self._get_mapped_error(exc)
            error_info.update(mapped_error)
        
        # Add traceback if enabled
        if self.include_traceback:
            error_info["traceback"] = traceback.format_exc()
        
        return error_info
    
    def _get_error_type(self, status_code: int) -> str:
        """Get error type based on HTTP status code"""
        if status_code >= 500:
            return "InternalServerError"
        elif status_code == 429:
            return "RateLimitError"
        elif status_code == 409:
            return "ConflictError"
        elif status_code == 404:
            return "NotFoundError"
        elif status_code == 403:
            return "AuthorizationError"
        elif status_code == 401:
            return "AuthenticationError"
        elif status_code >= 400:
            return "ValidationError"
        else:
            return "UnknownError"
    
    def _get_mapped_error(self, exc: Exception) -> Dict[str, Any]:
        """Get mapped error information for custom exceptions"""
        exception_name = type(exc).__name__
        
        # Check custom error mapping
        if exception_name in self.error_mapping:
            return self.error_mapping[exception_name]
        
        # Check custom handlers
        if exception_name in self.custom_handlers:
            handler = self.custom_handlers[exception_name]
            return handler(exc)
        
        # Default error mapping
        return {
            "status_code": 500,
            "error_type": "InternalServerError",
            "message": "An unexpected error occurred"
        }
    
    async def _log_error(self, request: Request, exc: Exception, error_info: Dict[str, Any]):
        """Log error information"""
        try:
            # Determine log level
            log_level = self._get_log_level(error_info.get("status_code", 500))
            
            # Create log message
            log_message = (
                f"Error {error_info['request_id']}: "
                f"{error_info['request_method']} {error_info['request_path']} - "
                f"{error_info['error_type']} ({error_info['status_code']}): "
                f"{error_info['exception_message']}"
            )
            
            # Log based on level
            if log_level == "DEBUG":
                logger.debug(log_message)
                if self.include_traceback:
                    logger.debug(f"Traceback: {error_info.get('traceback', 'N/A')}")
            elif log_level == "INFO":
                logger.info(log_message)
            elif log_level == "WARNING":
                logger.warning(log_message)
            else:  # ERROR
                logger.error(log_message)
                if self.include_traceback:
                    logger.error(f"Traceback: {error_info.get('traceback', 'N/A')}")
            
            # Additional context logging
            if log_level == "DEBUG":
                logger.debug(f"Error context: {json.dumps(error_info, indent=2)}")
                
        except Exception as e:
            logger.error(f"Error logging error: {str(e)}")
    
    def _get_log_level(self, status_code: int) -> str:
        """Determine log level based on status code"""
        if status_code >= 500:
            return "ERROR"
        elif status_code == 429:
            return "WARNING"
        elif status_code >= 400:
            return "INFO"
        else:
            return "DEBUG"
    
    async def _create_error_response(self, request: Request, exc: Exception, error_info: Dict[str, Any]) -> JSONResponse:
        """Create formatted error response"""
        # Get status code
        status_code = error_info.get("status_code", 500)
        
        # Create response content
        response_content = {
            "error": {
                "type": error_info.get("error_type", "InternalServerError"),
                "code": status_code,
                "message": error_info.get("message", "An error occurred"),
                "timestamp": error_info["timestamp"],
                "request_id": error_info["request_id"],
                "path": error_info["request_path"],
                "method": error_info["request_method"]
            }
        }
        
        # Add additional error details for development
        if os.getenv("ENVIRONMENT", "production") == "development":
            response_content["error"]["details"] = {
                "exception_type": error_info["exception_type"],
                "exception_message": error_info["exception_message"]
            }
            
            if self.include_traceback:
                response_content["error"]["traceback"] = error_info.get("traceback")
        
        # Add headers
        headers = {
            "X-Request-ID": error_info["request_id"],
            "X-Error-Type": error_info.get("error_type", "InternalServerError")
        }
        
        # Add retry-after header for rate limiting
        if status_code == 429:
            retry_after = error_info.get("headers", {}).get("Retry-After", "60")
            headers["Retry-After"] = str(retry_after)
        
        return JSONResponse(
            status_code=status_code,
            content=response_content,
            headers=headers
        )
    
    def add_custom_handler(self, exception_type: str, handler):
        """Add custom exception handler"""
        self.custom_handlers[exception_type] = handler
        logger.info(f"Added custom handler for {exception_type}")
    
    def add_error_mapping(self, exception_type: str, mapping: Dict[str, Any]):
        """Add custom error mapping"""
        self.error_mapping[exception_type] = mapping
        logger.info(f"Added error mapping for {exception_type}")

class DetailedErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Enhanced error handling with detailed error categorization and recovery suggestions"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Error categorization
        self.error_categories = {
            "client": [400, 401, 403, 404, 409, 422, 429],
            "server": [500, 502, 503, 504],
            "network": [502, 503, 504],
            "authentication": [401, 403],
            "validation": [400, 422],
            "rate_limiting": [429],
            "not_found": [404],
            "conflict": [409]
        }
        
        # Recovery suggestions
        self.recovery_suggestions = {
            400: "Check your request format and parameters",
            401: "Verify your authentication credentials",
            403: "Ensure you have the required permissions",
            404: "Verify the resource exists and the URL is correct",
            409: "Check for conflicts with existing resources",
            422: "Validate your request data format",
            429: "Wait before making additional requests",
            500: "Try again later or contact support",
            502: "Service temporarily unavailable, try again later",
            503: "Service under maintenance, try again later",
            504: "Request timeout, try again later"
        }
        
        # Error correlation
        self.error_correlation = {}
        
        logger.info("Detailed error handling middleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """Process request with detailed error handling"""
        try:
            response = await call_next(request)
            return response
            
        except Exception as exc:
            return await self._handle_detailed_exception(request, exc)
    
    async def _handle_detailed_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle exceptions with detailed information and recovery suggestions"""
        try:
            # Get detailed error info
            error_info = await self._get_detailed_error_info(request, exc)
            
            # Add error correlation
            await self._add_error_correlation(request, exc, error_info)
            
            # Create detailed error response
            error_response = await self._create_detailed_error_response(request, exc, error_info)
            
            return error_response
            
        except Exception as e:
            logger.error(f"Error in detailed error handler: {str(e)}")
            
            # Fallback to basic error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": "InternalServerError",
                        "code": 500,
                        "message": "An unexpected error occurred",
                        "timestamp": datetime.utcnow().isoformat(),
                        "request_id": getattr(request.state, "request_id", "unknown")
                    }
                }
            )
    
    async def _get_detailed_error_info(self, request: Request, exc: Exception) -> Dict[str, Any]:
        """Extract detailed error information"""
        # Get basic error info
        basic_info = await self._get_error_info(request, exc)
        
        # Add detailed categorization
        status_code = basic_info.get("status_code", 500)
        
        detailed_info = {
            **basic_info,
            "category": self._get_error_category(status_code),
            "recovery_suggestion": self.recovery_suggestions.get(status_code, "Try again later"),
            "user_actionable": self._is_user_actionable(status_code),
            "retryable": self._is_retryable(status_code),
            "correlation_id": self._generate_correlation_id()
        }
        
        # Add specific error details
        if isinstance(exc, HTTPException):
            detailed_info["http_error"] = True
            detailed_info["headers"] = dict(exc.headers) if exc.headers else {}
        else:
            detailed_info["http_error"] = False
        
        return detailed_info
    
    def _get_error_category(self, status_code: int) -> str:
        """Get error category based on status code"""
        for category, codes in self.error_categories.items():
            if status_code in codes:
                return category
        
        return "unknown"
    
    def _is_user_actionable(self, status_code: int) -> bool:
        """Determine if the error is user-actionable"""
        return status_code in [400, 401, 403, 404, 409, 422, 429]
    
    def _is_retryable(self, status_code: int) -> bool:
        """Determine if the error is retryable"""
        return status_code in [429, 500, 502, 503, 504]
    
    def _generate_correlation_id(self) -> str:
        """Generate correlation ID for error tracking"""
        import uuid
        return str(uuid.uuid4())
    
    async def _add_error_correlation(self, request: Request, exc: Exception, error_info: Dict[str, Any]):
        """Add error correlation information"""
        correlation_id = error_info["correlation_id"]
        
        # Store error correlation
        self.error_correlation[correlation_id] = {
            "timestamp": error_info["timestamp"],
            "error_type": error_info["error_type"],
            "status_code": error_info["status_code"],
            "path": error_info["request_path"],
            "method": error_info["request_method"],
            "request_id": error_info["request_id"]
        }
        
        # Clean up old correlations (keep last 1000)
        if len(self.error_correlation) > 1000:
            # Remove oldest entries
            sorted_correlations = sorted(
                self.error_correlation.items(),
                key=lambda x: x[1]["timestamp"]
            )
            for key, _ in sorted_correlations[:-1000]:
                del self.error_correlation[key]
    
    async def _create_detailed_error_response(self, request: Request, exc: Exception, error_info: Dict[str, Any]) -> JSONResponse:
        """Create detailed error response with recovery information"""
        status_code = error_info.get("status_code", 500)
        
        # Create response content
        response_content = {
            "error": {
                "type": error_info.get("error_type", "InternalServerError"),
                "code": status_code,
                "message": error_info.get("message", "An error occurred"),
                "timestamp": error_info["timestamp"],
                "request_id": error_info["request_id"],
                "correlation_id": error_info["correlation_id"],
                "path": error_info["request_path"],
                "method": error_info["request_method"],
                "category": error_info["category"],
                "recovery_suggestion": error_info["recovery_suggestion"],
                "user_actionable": error_info["user_actionable"],
                "retryable": error_info["retryable"]
            }
        }
        
        # Add development details
        if os.getenv("ENVIRONMENT", "production") == "development":
            response_content["error"]["development"] = {
                "exception_type": error_info["exception_type"],
                "exception_message": error_info["exception_message"],
                "traceback": error_info.get("traceback")
            }
        
        # Add headers
        headers = {
            "X-Request-ID": error_info["request_id"],
            "X-Correlation-ID": error_info["correlation_id"],
            "X-Error-Type": error_info.get("error_type", "InternalServerError"),
            "X-Error-Category": error_info["category"],
            "X-User-Actionable": str(error_info["user_actionable"]).lower(),
            "X-Retryable": str(error_info["retryable"]).lower()
        }
        
        # Add retry headers
        if error_info["retryable"]:
            if status_code == 429:
                retry_after = error_info.get("headers", {}).get("Retry-After", "60")
                headers["Retry-After"] = str(retry_after)
            else:
                headers["Retry-After"] = "30"  # Default retry after 30 seconds
        
        return JSONResponse(
            status_code=status_code,
            content=response_content,
            headers=headers
        )
    
    async def _get_error_info(self, request: Request, exc: Exception) -> Dict[str, Any]:
        """Get basic error information (reuse from base class)"""
        # This would typically call the base class method
        # For now, implement a simplified version
        return {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "request_path": request.url.path,
            "request_method": request.method,
            "request_id": getattr(request.state, "request_id", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": getattr(exc, "status_code", 500),
            "error_type": "InternalServerError",
            "message": str(exc)
        }
