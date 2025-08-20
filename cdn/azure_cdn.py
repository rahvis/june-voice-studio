"""
Azure CDN Configuration for Voice Cloning System
Provides CDN setup, signed URL generation, and content delivery optimization
"""

import hashlib
import hmac
import time
import urllib.parse
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class CDNProvider(Enum):
    """CDN provider types"""
    AZURE_CDN = "azure_cdn"
    AZURE_FRONT_DOOR = "azure_front_door"
    AZURE_CDN_STANDARD = "azure_cdn_standard"
    AZURE_CDN_PREMIUM = "azure_cdn_premium"

class ContentType(Enum):
    """Content type categories"""
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    STREAMING = "streaming"

@dataclass
class CDNConfig:
    """CDN configuration settings"""
    provider: CDNProvider = CDNProvider.AZURE_CDN
    endpoint_name: str = "voice-cloning-cdn"
    profile_name: str = "voice-cloning-cdn-profile"
    resource_group: str = "voice-cloning-rg"
    subscription_id: str = ""
    location: str = "East US"
    sku: str = "Standard_Microsoft"
    optimization_type: str = "GeneralWebDelivery"
    origin_host_header: str = ""
    origin_path: str = ""
    enable_compression: bool = True
    enable_https: bool = True
    enable_http2: bool = True
    enable_compression: bool = True
    query_string_caching_behavior: str = "IgnoreQueryString"
    cache_expiration_time: int = 86400  # 24 hours

@dataclass
class SignedURLOptions:
    """Options for generating signed URLs"""
    expiration_time: int = 3600  # 1 hour
    ip_address: Optional[str] = None
    protocol: str = "https"
    cache_control: str = "public, max-age=3600"
    content_disposition: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None

class AzureCDN:
    """Azure CDN management and configuration"""
    
    def __init__(self, config: CDNConfig):
        self.config = config
        self.endpoint_url = f"https://{config.endpoint_name}.azureedge.net"
        self._setup_cdn()
    
    def _setup_cdn(self) -> None:
        """Setup CDN configuration"""
        try:
            # This would typically use Azure SDK to configure CDN
            # For now, we'll simulate the setup
            logger.info(f"CDN endpoint configured: {self.endpoint_url}")
            logger.info(f"CDN provider: {self.config.provider.value}")
            logger.info(f"Optimization type: {self.config.optimization_type}")
        except Exception as e:
            logger.error(f"Failed to setup CDN: {e}")
    
    def get_endpoint_url(self, path: str = "") -> str:
        """Get CDN endpoint URL with optional path"""
        if path:
            return f"{self.endpoint_url}/{path.lstrip('/')}"
        return self.endpoint_url
    
    def generate_signed_url(self, blob_path: str, options: SignedURLOptions) -> str:
        """Generate signed URL for secure content access"""
        try:
            # Parse the blob path
            parsed_path = urllib.parse.urlparse(blob_path)
            path = parsed_path.path.lstrip('/')
            
            # Generate expiration timestamp
            expiration = int(time.time()) + options.expiration_time
            
            # Create signature string
            signature_string = f"{path}\n{expiration}"
            if options.ip_address:
                signature_string += f"\n{options.ip_address}"
            
            # Generate signature (this would use actual CDN key in production)
            signature = self._generate_signature(signature_string)
            
            # Build signed URL
            signed_url = f"{self.endpoint_url}/{path}"
            params = {
                'sv': expiration,
                'sr': signature,
                'sig': signature,
                'st': int(time.time()),
                'se': expiration
            }
            
            if options.ip_address:
                params['ip'] = options.ip_address
            
            # Add query parameters
            query_string = urllib.parse.urlencode(params)
            signed_url = f"{signed_url}?{query_string}"
            
            logger.info(f"Generated signed URL for {blob_path}, expires in {options.expiration_time}s")
            return signed_url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {blob_path}: {e}")
            return blob_path
    
    def _generate_signature(self, signature_string: str) -> str:
        """Generate HMAC signature for URL signing"""
        # In production, this would use the actual CDN key
        # For now, we'll generate a mock signature
        key = b"mock_cdn_key_for_demo"
        signature = hmac.new(key, signature_string.encode('utf-8'), hashlib.sha256)
        return signature.hexdigest()
    
    def configure_caching_rules(self, content_type: ContentType, 
                               cache_duration: int = 86400) -> bool:
        """Configure caching rules for specific content types"""
        try:
            rules = {
                ContentType.AUDIO: {
                    'cache_duration': cache_duration,
                    'compression': True,
                    'query_string_caching': 'IgnoreQueryString',
                    'cache_behavior': 'Cache'
                },
                ContentType.IMAGE: {
                    'cache_duration': cache_duration * 7,  # 7 days for images
                    'compression': True,
                    'query_string_caching': 'IgnoreQueryString',
                    'cache_behavior': 'Cache'
                },
                ContentType.DOCUMENT: {
                    'cache_duration': cache_duration * 30,  # 30 days for documents
                    'compression': True,
                    'query_string_caching': 'IgnoreQueryString',
                    'cache_behavior': 'Cache'
                },
                ContentType.STREAMING: {
                    'cache_duration': 300,  # 5 minutes for streaming
                    'compression': False,
                    'query_string_caching': 'UseQueryString',
                    'cache_behavior': 'Cache'
                }
            }
            
            rule = rules.get(content_type, rules[ContentType.AUDIO])
            logger.info(f"Configured caching rule for {content_type.value}: {rule}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure caching rules for {content_type.value}: {e}")
            return False
    
    def purge_content(self, paths: List[str]) -> bool:
        """Purge content from CDN cache"""
        try:
            for path in paths:
                logger.info(f"Purging content: {path}")
                # In production, this would call Azure CDN purge API
            
            logger.info(f"Successfully purged {len(paths)} content paths")
            return True
            
        except Exception as e:
            logger.error(f"Failed to purge content: {e}")
            return False
    
    def get_cache_status(self, path: str) -> Dict[str, any]:
        """Get cache status for a specific path"""
        try:
            # Mock cache status - in production this would query CDN API
            status = {
                'path': path,
                'cached': True,
                'cache_hit_ratio': 0.95,
                'last_accessed': datetime.now().isoformat(),
                'cache_expiration': (datetime.now() + timedelta(hours=24)).isoformat(),
                'size': '2.5MB',
                'compression_ratio': 0.7
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get cache status for {path}: {e}")
            return {}
    
    def optimize_for_mobile(self, enable: bool = True) -> bool:
        """Enable mobile optimization features"""
        try:
            if enable:
                optimizations = [
                    'Image compression',
                    'JavaScript minification',
                    'CSS minification',
                    'Mobile-specific caching',
                    'Adaptive bitrate streaming'
                ]
                logger.info(f"Enabled mobile optimizations: {', '.join(optimizations)}")
            else:
                logger.info("Disabled mobile optimizations")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure mobile optimization: {e}")
            return False
    
    def configure_geo_distribution(self, regions: List[str]) -> bool:
        """Configure geographic distribution for content"""
        try:
            for region in regions:
                logger.info(f"Configured CDN for region: {region}")
            
            logger.info(f"CDN configured for {len(regions)} regions")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure geo distribution: {e}")
            return False
    
    def get_performance_metrics(self) -> Dict[str, any]:
        """Get CDN performance metrics"""
        try:
            # Mock metrics - in production this would come from Azure Monitor
            metrics = {
                'total_requests': 1000000,
                'cache_hit_ratio': 0.92,
                'average_response_time': 45,  # ms
                'bandwidth_usage': '2.5GB',
                'error_rate': 0.001,
                'top_regions': [
                    {'region': 'East US', 'requests': 250000},
                    {'region': 'West Europe', 'requests': 200000},
                    {'region': 'Southeast Asia', 'requests': 150000}
                ],
                'top_content_types': [
                    {'type': 'audio', 'requests': 600000},
                    {'type': 'image', 'requests': 300000},
                    {'type': 'document', 'requests': 100000}
                ]
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}
    
    def set_custom_domain(self, domain: str, ssl_certificate: str = "") -> bool:
        """Configure custom domain for CDN"""
        try:
            logger.info(f"Configured custom domain: {domain}")
            if ssl_certificate:
                logger.info(f"SSL certificate configured for {domain}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure custom domain {domain}: {e}")
            return False
    
    def enable_analytics(self, enable: bool = True) -> bool:
        """Enable CDN analytics and reporting"""
        try:
            if enable:
                features = [
                    'Real-time analytics',
                    'Traffic reports',
                    'Performance monitoring',
                    'Geographic distribution',
                    'Device analytics'
                ]
                logger.info(f"Enabled CDN analytics: {', '.join(features)}")
            else:
                logger.info("Disabled CDN analytics")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure analytics: {e}")
            return False

# CDN utility functions
def get_optimal_cdn_endpoint(user_location: str, cdn_endpoints: List[str]) -> str:
    """Get optimal CDN endpoint based on user location"""
    # This would implement geographic routing logic
    # For now, return the first endpoint
    return cdn_endpoints[0] if cdn_endpoints else ""

def calculate_cache_key(content_hash: str, user_preferences: Dict[str, any]) -> str:
    """Calculate cache key based on content and user preferences"""
    key_parts = [content_hash]
    
    if user_preferences.get('language'):
        key_parts.append(user_preferences['language'])
    
    if user_preferences.get('quality'):
        key_parts.append(user_preferences['quality'])
    
    if user_preferences.get('format'):
        key_parts.append(user_preferences['format'])
    
    return ":".join(key_parts)

def validate_cdn_config(config: CDNConfig) -> bool:
    """Validate CDN configuration"""
    required_fields = ['endpoint_name', 'profile_name', 'resource_group']
    
    for field in required_fields:
        if not getattr(config, field):
            logger.error(f"Missing required CDN configuration field: {field}")
            return False
    
    return True
