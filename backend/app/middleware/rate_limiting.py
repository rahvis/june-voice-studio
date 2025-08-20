from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from typing import Dict, Tuple, Optional
from collections import defaultdict, deque
import os

# Configure logging
logger = logging.getLogger(__name__)

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Rate limiting configuration
        self.enabled = os.getenv("RATE_LIMITING_ENABLED", "true").lower() == "true"
        self.default_limit = int(os.getenv("RATE_LIMIT_DEFAULT", "100"))  # requests per minute
        self.burst_limit = int(os.getenv("RATE_LIMIT_BURST", "200"))  # burst requests per minute
        
        # Specific endpoint limits
        self.endpoint_limits = {
            "/api/v1/synthesis/speak": int(os.getenv("RATE_LIMIT_SYNTHESIS", "50")),
            "/api/v1/synthesis/batch": int(os.getenv("RATE_LIMIT_BATCH_SYNTHESIS", "20")),
            "/api/v1/voices/train": int(os.getenv("RATE_LIMIT_TRAINING", "10")),
            "/api/v1/lexicon/bulk-upload": int(os.getenv("RATE_LIMIT_BULK_UPLOAD", "5")),
        }
        
        # Rate limiting storage
        self.rate_limit_store: Dict[str, deque] = defaultdict(lambda: deque())
        self.cleanup_interval = 60  # Clean up old entries every 60 seconds
        self.last_cleanup = time.time()
        
        # IP-based rate limiting
        self.ip_based = os.getenv("RATE_LIMIT_IP_BASED", "true").lower() == "true"
        self.ip_limit = int(os.getenv("RATE_LIMIT_IP", "1000"))  # requests per minute per IP
        
        # User-based rate limiting
        self.user_based = os.getenv("RATE_LIMIT_USER_BASED", "true").lower() == "true"
        self.user_limit = int(os.getenv("RATE_LIMIT_USER", "500"))  # requests per minute per user
        
        # Rate limiting headers
        self.include_headers = os.getenv("RATE_LIMIT_HEADERS", "true").lower() == "true"
        
        # Sliding window configuration
        self.window_size = 60  # 60 seconds
        
        logger.info(f"Rate limiting middleware initialized - Enabled: {self.enabled}")
        if self.enabled:
            logger.info(f"Default limit: {self.default_limit} req/min, Burst: {self.burst_limit} req/min")
    
    async def dispatch(self, request: Request, call_next):
        """Process the request with rate limiting"""
        if not self.enabled:
            return await call_next(request)
        
        # Clean up old entries periodically
        await self._cleanup_old_entries()
        
        # Get rate limit key
        rate_limit_key = await self._get_rate_limit_key(request)
        
        # Check rate limits
        if not await self._check_rate_limit(rate_limit_key, request):
            await self._handle_rate_limit_exceeded(request, rate_limit_key)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limiting headers
        if self.include_headers:
            await self._add_rate_limit_headers(response, rate_limit_key)
        
        return response
    
    async def _get_rate_limit_key(self, request: Request) -> str:
        """Get the rate limiting key for the request"""
        # Get endpoint path
        path = request.url.path
        
        # Get client identifier
        client_id = await self._get_client_identifier(request)
        
        # Create rate limit key
        return f"{client_id}:{path}"
    
    async def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        identifiers = []
        
        # IP-based identification
        if self.ip_based:
            client_ip = self._get_client_ip(request)
            identifiers.append(f"ip:{client_ip}")
        
        # User-based identification (if authenticated)
        if self.user_based:
            user_id = await self._get_user_id(request)
            if user_id:
                identifiers.append(f"user:{user_id}")
        
        # Fallback to IP if no user ID
        if not identifiers:
            client_ip = self._get_client_ip(request)
            identifiers.append(f"ip:{client_ip}")
        
        return "|".join(identifiers)
    
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
        return request.client.host if request.client else "unknown"
    
    async def _get_user_id(self, request: Request) -> Optional[str]:
        """Get user ID from request (if authenticated)"""
        try:
            # Check if user is authenticated
            # This would typically come from the auth middleware
            if hasattr(request.state, "user"):
                return request.state.user.get("id")
            
            # Check authorization header
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # In a real implementation, you might decode the token here
                # For now, return None to indicate no user ID
                return None
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting user ID: {str(e)}")
            return None
    
    async def _check_rate_limit(self, rate_limit_key: str, request: Request) -> bool:
        """Check if the request is within rate limits"""
        try:
            current_time = time.time()
            path = request.url.path
            
            # Get the appropriate limit for this endpoint
            limit = self.endpoint_limits.get(path, self.default_limit)
            
            # Get current request count for this key
            request_times = self.rate_limit_store[rate_limit_key]
            
            # Remove old entries outside the window
            while request_times and current_time - request_times[0] > self.window_size:
                request_times.popleft()
            
            # Check if adding this request would exceed the limit
            if len(request_times) >= limit:
                logger.warning(f"Rate limit exceeded for {rate_limit_key}: {len(request_times)} >= {limit}")
                return False
            
            # Add current request time
            request_times.append(current_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            # Allow request on error (fail open)
            return True
    
    async def _handle_rate_limit_exceeded(self, request: Request, rate_limit_key: str):
        """Handle rate limit exceeded"""
        path = request.url.path
        limit = self.endpoint_limits.get(path, self.default_limit)
        
        # Get current count
        request_times = self.rate_limit_store[rate_limit_key]
        current_count = len(request_times)
        
        # Calculate retry after time
        if request_times:
            oldest_request = request_times[0]
            retry_after = int(self.window_size - (time.time() - oldest_request))
        else:
            retry_after = self.window_size
        
        # Log rate limit exceeded
        logger.warning(
            f"Rate limit exceeded for {rate_limit_key}: "
            f"{current_count} requests in {self.window_size}s (limit: {limit})"
        )
        
        # Raise HTTP exception
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {limit} per minute",
                "retry_after": retry_after,
                "current_count": current_count,
                "limit": limit,
                "window_size": self.window_size
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + retry_after))
            }
        )
    
    async def _add_rate_limit_headers(self, response, rate_limit_key: str):
        """Add rate limiting headers to response"""
        try:
            current_time = time.time()
            request_times = self.rate_limit_store[rate_limit_key]
            
            # Remove old entries
            while request_times and current_time - request_times[0] > self.window_size:
                request_times.popleft()
            
            # Get current count and limit
            current_count = len(request_times)
            path = rate_limit_key.split(":", 1)[1] if ":" in rate_limit_key else "/"
            limit = self.endpoint_limits.get(path, self.default_limit)
            
            # Calculate remaining requests
            remaining = max(0, limit - current_count)
            
            # Calculate reset time
            if request_times:
                oldest_request = request_times[0]
                reset_time = int(oldest_request + self.window_size)
            else:
                reset_time = int(current_time + self.window_size)
            
            # Add headers
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            response.headers["X-RateLimit-Window"] = str(self.window_size)
            
        except Exception as e:
            logger.error(f"Error adding rate limit headers: {str(e)}")
    
    async def _cleanup_old_entries(self):
        """Clean up old rate limiting entries"""
        try:
            current_time = time.time()
            
            # Only cleanup periodically
            if current_time - self.last_cleanup < self.cleanup_interval:
                return
            
            self.last_cleanup = current_time
            
            # Remove old entries from all rate limit stores
            keys_to_remove = []
            
            for key, request_times in self.rate_limit_store.items():
                # Remove old entries
                while request_times and current_time - request_times[0] > self.window_size:
                    request_times.popleft()
                
                # Remove empty keys
                if not request_times:
                    keys_to_remove.append(key)
            
            # Remove empty keys
            for key in keys_to_remove:
                del self.rate_limit_store[key]
            
            # Log cleanup if there were entries to clean
            if keys_to_remove:
                logger.debug(f"Cleaned up {len(keys_to_remove)} empty rate limit entries")
                
        except Exception as e:
            logger.error(f"Error during rate limit cleanup: {str(e)}")

class AdaptiveRateLimitingMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting with adaptive limits based on system load"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Adaptive rate limiting configuration
        self.base_limit = int(os.getenv("ADAPTIVE_RATE_LIMIT_BASE", "100"))
        self.min_limit = int(os.getenv("ADAPTIVE_RATE_LIMIT_MIN", "10"))
        self.max_limit = int(os.getenv("ADAPTIVE_RATE_LIMIT_MAX", "1000"))
        
        # System load thresholds
        self.cpu_threshold = float(os.getenv("ADAPTIVE_CPU_THRESHOLD", "0.8"))
        self.memory_threshold = float(os.getenv("ADAPTIVE_MEMORY_THRESHOLD", "0.8"))
        
        # Load history for smoothing
        self.load_history = deque(maxlen=10)
        self.last_adaptation = time.time()
        self.adaptation_interval = 30  # Adapt every 30 seconds
        
        # Current adaptive limit
        self.current_limit = self.base_limit
        
        logger.info(f"Adaptive rate limiting initialized - Base: {self.base_limit}, Range: {self.min_limit}-{self.max_limit}")
    
    async def dispatch(self, request: Request, call_next):
        """Process request with adaptive rate limiting"""
        # Adapt limits based on system load
        await self._adapt_limits()
        
        # Use current adaptive limit
        # This would integrate with the main rate limiting middleware
        return await call_next(request)
    
    async def _adapt_limits(self):
        """Adapt rate limits based on system load"""
        try:
            current_time = time.time()
            
            # Only adapt periodically
            if current_time - self.last_adaptation < self.adaptation_interval:
                return
            
            self.last_adaptation = current_time
            
            # Get current system load
            cpu_load = await self._get_cpu_load()
            memory_load = await self._get_memory_load()
            
            # Calculate overall load
            overall_load = max(cpu_load, memory_load)
            self.load_history.append(overall_load)
            
            # Calculate average load
            if self.load_history:
                avg_load = sum(self.load_history) / len(self.load_history)
            else:
                avg_load = overall_load
            
            # Adjust rate limit based on load
            if avg_load > self.cpu_threshold:
                # High load - reduce rate limit
                reduction_factor = min(0.5, avg_load - self.cpu_threshold)
                new_limit = max(self.min_limit, int(self.current_limit * (1 - reduction_factor)))
                
                if new_limit < self.current_limit:
                    logger.info(f"Reducing rate limit from {self.current_limit} to {new_limit} due to high load ({avg_load:.2f})")
                    self.current_limit = new_limit
                    
            elif avg_load < self.cpu_threshold * 0.5:
                # Low load - increase rate limit
                increase_factor = min(0.2, (self.cpu_threshold * 0.5) - avg_load)
                new_limit = min(self.max_limit, int(self.current_limit * (1 + increase_factor)))
                
                if new_limit > self.current_limit:
                    logger.info(f"Increasing rate limit from {self.current_limit} to {new_limit} due to low load ({avg_load:.2f})")
                    self.current_limit = new_limit
            
        except Exception as e:
            logger.error(f"Error adapting rate limits: {str(e)}")
    
    async def _get_cpu_load(self) -> float:
        """Get current CPU load (0.0 to 1.0)"""
        try:
            # This is a simplified implementation
            # In production, you'd use psutil or similar
            import psutil
            return psutil.cpu_percent(interval=1) / 100.0
        except ImportError:
            # Fallback to mock data
            return 0.5
    
    async def _get_memory_load(self) -> float:
        """Get current memory load (0.0 to 1.0)"""
        try:
            # This is a simplified implementation
            # In production, you'd use psutil or similar
            import psutil
            memory = psutil.virtual_memory()
            return memory.percent / 100.0
        except ImportError:
            # Fallback to mock data
            return 0.6
