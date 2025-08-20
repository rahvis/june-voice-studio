"""
Authentication utilities for Azure Functions
"""
import os
import logging
from typing import Optional, Dict, Any
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
import jwt
import requests

logger = logging.getLogger(__name__)

class AzureFunctionAuth:
    """Authentication handler for Azure Functions"""
    
    def __init__(self):
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.audience = os.getenv("AZURE_AUDIENCE", "api://your-api-identifier")
        
        # Initialize Azure credentials
        try:
            # Try managed identity first (for production)
            self.credential = ManagedIdentityCredential()
            logger.info("Using managed identity for authentication")
        except Exception:
            # Fallback to default credential (for development)
            self.credential = DefaultAzureCredential()
            logger.info("Using default credential for authentication")
        
        # Initialize Key Vault client if available
        self.key_vault_url = os.getenv("AZURE_KEY_VAULT_URL")
        if self.key_vault_url:
            self.secret_client = SecretClient(
                vault_url=self.key_vault_url,
                credential=self.credential
            )
        else:
            self.secret_client = None
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token from Azure Entra ID"""
        try:
            # Get JWKS from Azure AD
            jwks_url = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
            response = requests.get(jwks_url)
            response.raise_for_status()
            jwks = response.json()
            
            # Decode token header to get key ID
            header = jwt.get_unverified_header(token)
            key_id = header.get("kid")
            
            if not key_id:
                logger.warning("Token header missing key ID")
                return None
            
            # Find the signing key
            signing_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == key_id:
                    signing_key = key
                    break
            
            if not signing_key:
                logger.warning(f"Signing key not found for key ID: {key_id}")
                return None
            
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
                import time
                if time.time() > payload["exp"]:
                    logger.warning("Token has expired")
                    return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Microsoft Graph API"""
        try:
            # Get user info from Microsoft Graph
            graph_url = "https://graph.microsoft.com/v1.0/me"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(graph_url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get user info: {str(e)}")
            return None
    
    async def get_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from Azure Key Vault"""
        if not self.secret_client:
            return None
        
        try:
            secret = self.secret_client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {str(e)}")
            return None

# Global auth instance
auth_handler = AzureFunctionAuth()

async def get_current_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token"""
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Validate token
        payload = await auth_handler.validate_token(token)
        if not payload:
            return None
        
        # Get user information
        user_info = await auth_handler.get_user_info(token)
        if not user_info:
            return None
        
        # Create user object
        user = {
            "id": payload.get("oid") or payload.get("sub"),
            "email": user_info.get("mail") or user_info.get("userPrincipalName"),
            "display_name": user_info.get("displayName"),
            "given_name": user_info.get("givenName"),
            "surname": user_info.get("surname"),
            "tenant_id": payload.get("tid"),
            "client_id": payload.get("aud"),
            "token_claims": payload
        }
        
        return user
        
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return None
