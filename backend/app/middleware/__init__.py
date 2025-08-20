# Middleware package for Azure Voice Cloning API

from .auth import (
    get_current_user,
    require_role,
    require_admin,
    require_moderator,
    has_role,
    has_any_role,
    has_all_roles,
    AzureEntraIDAuth
)

from .logging import (
    LoggingMiddleware,
    StructuredLoggingMiddleware
)

from .rate_limiting import (
    RateLimitingMiddleware,
    AdaptiveRateLimitingMiddleware
)

from .error_handling import (
    ErrorHandlingMiddleware,
    DetailedErrorHandlingMiddleware
)

__all__ = [
    # Authentication
    "get_current_user",
    "require_role",
    "require_admin",
    "require_moderator",
    "has_role",
    "has_any_role",
    "has_all_roles",
    "AzureEntraIDAuth",
    
    # Logging
    "LoggingMiddleware",
    "StructuredLoggingMiddleware",
    
    # Rate Limiting
    "RateLimitingMiddleware",
    "AdaptiveRateLimitingMiddleware",
    
    # Error Handling
    "ErrorHandlingMiddleware",
    "DetailedErrorHandlingMiddleware"
]
