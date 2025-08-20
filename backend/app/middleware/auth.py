from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
import requests
import logging
from datetime import datetime, timedelta
import os

# Configure logging
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

class AzureEntraIDAuth:
    """Azure Entra ID (Azure AD) authentication handler"""
    
    def __init__(self):
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.audience = os.getenv("AZURE_AUDIENCE", "api://your-api-identifier")
        
        # Azure AD endpoints
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.token_endpoint = f"{self.authority}/oauth2/v2.0/token"
        self.jwks_endpoint = f"{self.authority}/discovery/v2.0/keys"
        
        # JWT validation settings
        self.jwks = None
        self.jwks_last_updated = None
        self.jwks_cache_duration = timedelta(hours=1)
        
        # User cache
        self.user_cache = {}
        self.user_cache_duration = timedelta(minutes=30)
    
    async def get_jwks(self):
        """Get JSON Web Key Set from Azure AD"""
        try:
            # Check if we need to refresh the JWKS
            if (self.jwks is None or 
                self.jwks_last_updated is None or 
                datetime.utcnow() - self.jwks_last_updated > self.jwks_cache_duration):
                
                logger.info("Fetching JWKS from Azure AD")
                response = requests.get(self.jwks_endpoint)
                response.raise_for_status()
                
                self.jwks = response.json()
                self.jwks_last_updated = datetime.utcnow()
                
                logger.info("JWKS updated successfully")
            
            return self.jwks
            
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service unavailable"
            )
    
    def get_signing_key(self, token_header):
        """Get the signing key for a JWT token"""
        try:
            jwks = self.jwks
            if not jwks:
                raise Exception("JWKS not available")
            
            # Find the key that matches the token's key ID
            key_id = token_header.get("kid")
            if not key_id:
                raise Exception("Token header missing key ID")
            
            for key in jwks.get("keys", []):
                if key.get("kid") == key_id:
                    return key
            
            raise Exception(f"Signing key not found for key ID: {key_id}")
            
        except Exception as e:
            logger.error(f"Failed to get signing key: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    async def validate_token(self, token: str) -> dict:
        """Validate JWT token from Azure AD"""
        try:
            # Decode token header to get algorithm and key ID
            header = jwt.get_unverified_header(token)
            
            # Get the signing key
            signing_key = self.get_signing_key(header)
            
            # Decode and validate the token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"
            )
            
            # Validate token expiration
            if "exp" in payload:
                exp_timestamp = payload["exp"]
                if datetime.utcnow().timestamp() > exp_timestamp:
                    raise Exception("Token has expired")
            
            # Validate token not before
            if "nbf" in payload:
                nbf_timestamp = payload["nbf"]
                if datetime.utcnow().timestamp() < nbf_timestamp:
                    raise Exception("Token not yet valid")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
            )
    
    async def get_user_info(self, access_token: str) -> dict:
        """Get user information from Microsoft Graph API"""
        try:
            # Check cache first
            cache_key = access_token[-20:]  # Use last 20 chars as cache key
            if cache_key in self.user_cache:
                cached_user, cached_time = self.user_cache[cache_key]
                if datetime.utcnow() - cached_time < self.user_cache_duration:
                    return cached_user
            
            # Get user info from Microsoft Graph
            graph_url = "https://graph.microsoft.com/v1.0/me"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(graph_url, headers=headers)
            response.raise_for_status()
            
            user_info = response.json()
            
            # Cache the user info
            self.user_cache[cache_key] = (user_info, datetime.utcnow())
            
            return user_info
            
        except Exception as e:
            logger.error(f"Failed to get user info: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user information"
            )
    
    async def get_user_roles(self, access_token: str) -> list:
        """Get user roles from Microsoft Graph API"""
        try:
            # Get app roles from token claims
            # In a real implementation, you might need to call the Microsoft Graph API
            # to get detailed role information
            
            # For now, return basic roles based on token claims
            # This is a simplified implementation
            return ["user"]  # Default role
            
        except Exception as e:
            logger.error(f"Failed to get user roles: {str(e)}")
            return ["user"]  # Default fallback

# Initialize authentication handler
auth_handler = AzureEntraIDAuth()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> dict:
    """Get current authenticated user"""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication credentials"
            )
        
        token = credentials.credentials
        
        # Validate the token
        payload = await auth_handler.validate_token(token)
        
        # Get user information
        user_info = await auth_handler.get_user_info(token)
        
        # Get user roles
        roles = await auth_handler.get_user_roles(token)
        
        # Create user object
        user = {
            "id": payload.get("oid") or payload.get("sub"),  # Object ID or Subject
            "email": user_info.get("mail") or user_info.get("userPrincipalName"),
            "display_name": user_info.get("displayName"),
            "given_name": user_info.get("givenName"),
            "surname": user_info.get("surname"),
            "roles": roles,
            "tenant_id": payload.get("tid"),  # Tenant ID
            "client_id": payload.get("aud"),  # Client ID
            "token_claims": payload
        }
        
        # Log successful authentication
        logger.info(f"User authenticated: {user['id']} ({user['email']})")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def require_role(required_roles: list):
    """Dependency to require specific user roles"""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        
        # Check if user has any of the required roles
        if not any(role in user_roles for role in required_roles):
            logger.warning(f"User {current_user['id']} lacks required roles: {required_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return role_checker

async def require_admin(current_user: dict = Depends(get_current_user)):
    """Dependency to require admin role"""
    return await require_role(["admin"])(current_user)

async def require_moderator(current_user: dict = Depends(get_current_user)):
    """Dependency to require moderator role"""
    return await require_role(["admin", "moderator"])(current_user)

# Utility functions for role checking
def has_role(user: dict, role: str) -> bool:
    """Check if user has a specific role"""
    return role in user.get("roles", [])

def has_any_role(user: dict, roles: list) -> bool:
    """Check if user has any of the specified roles"""
    user_roles = user.get("roles", [])
    return any(role in user_roles for role in roles)

def has_all_roles(user: dict, roles: list) -> bool:
    """Check if user has all of the specified roles"""
    user_roles = user.get("roles", [])
    return all(role in user_roles for role in roles)
