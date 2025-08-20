"""
Application Insights Integration for Voice Cloning System
Provides custom telemetry collection, performance monitoring, error tracking, and user behavior analytics
"""

import logging
import time
import json
import uuid
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import traceback
import asyncio
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class TelemetryType(Enum):
    """Telemetry types"""
    EVENT = "event"
    METRIC = "metric"
    TRACE = "trace"
    EXCEPTION = "exception"
    REQUEST = "request"
    DEPENDENCY = "dependency"
    PAGE_VIEW = "page_view"
    USER_ACTION = "user_action"

class SeverityLevel(Enum):
    """Severity levels for telemetry"""
    VERBOSE = 0
    INFORMATION = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

@dataclass
class TelemetryContext:
    """Telemetry context information"""
    session_id: str
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    application_version: str = "1.0.0"
    cloud_role_name: str = "voice-cloning-api"
    cloud_role_instance: str = "api-instance-1"
    operation_id: Optional[str] = None
    parent_operation_id: Optional[str] = None

@dataclass
class CustomEvent:
    """Custom event telemetry"""
    name: str
    properties: Dict[str, Any]
    measurements: Optional[Dict[str, float]] = None
    timestamp: Optional[datetime] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None

@dataclass
class CustomMetric:
    """Custom metric telemetry"""
    name: str
    value: float
    count: int = 1
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    standard_deviation: Optional[float] = None
    properties: Optional[Dict[str, Any]] = None

@dataclass
class PerformanceMetric:
    """Performance metric data"""
    operation_name: str
    duration_ms: float
    success: bool
    properties: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class ApplicationInsightsClient:
    """Application Insights client for telemetry collection"""
    
    def __init__(self, instrumentation_key: str, connection_string: str = ""):
        self.instrumentation_key = instrumentation_key
        self.connection_string = connection_string
        self.telemetry_context = TelemetryContext(
            session_id=str(uuid.uuid4()),
            operation_id=str(uuid.uuid4())
        )
        self._setup_client()
    
    def _setup_client(self) -> None:
        """Setup Application Insights client"""
        try:
            # In production, this would initialize the actual Application Insights SDK
            # For now, we'll simulate the setup
            logger.info(f"Application Insights client initialized with key: {self.instrumentation_key[:8]}...")
            
            # Setup default properties
            self.default_properties = {
                'component': 'voice-cloning-system',
                'environment': 'production',
                'deployment_region': 'East US'
            }
            
        except Exception as e:
            logger.error(f"Failed to setup Application Insights client: {e}")
    
    def track_event(self, event: CustomEvent) -> None:
        """Track custom event"""
        try:
            # Add default properties
            event.properties.update(self.default_properties)
            
            # Add context information
            if not event.session_id:
                event.properties['session_id'] = self.telemetry_context.session_id
            if not event.user_id:
                event.properties['user_id'] = self.telemetry_context.user_id
            
            # Add timestamp
            if not event.timestamp:
                event.properties['timestamp'] = datetime.now().isoformat()
            
            # In production, this would send to Application Insights
            logger.info(f"Tracked event: {event.name} with {len(event.properties)} properties")
            
        except Exception as e:
            logger.error(f"Failed to track event {event.name}: {e}")
    
    def track_metric(self, metric: CustomMetric) -> None:
        """Track custom metric"""
        try:
            # Add default properties
            if metric.properties:
                metric.properties.update(self.default_properties)
            else:
                metric.properties = self.default_properties.copy()
            
            # Add context information
            metric.properties['session_id'] = self.telemetry_context.session_id
            if self.telemetry_context.user_id:
                metric.properties['user_id'] = self.telemetry_context.user_id
            
            # In production, this would send to Application Insights
            logger.info(f"Tracked metric: {metric.name} = {metric.value}")
            
        except Exception as e:
            logger.error(f"Failed to track metric {metric.name}: {e}")
    
    def track_exception(self, exception: Exception, properties: Optional[Dict[str, Any]] = None) -> None:
        """Track exception"""
        try:
            if properties is None:
                properties = {}
            
            # Add default properties
            properties.update(self.default_properties)
            
            # Add exception details
            properties['exception_type'] = type(exception).__name__
            properties['exception_message'] = str(exception)
            properties['stack_trace'] = traceback.format_exc()
            properties['session_id'] = self.telemetry_context.session_id
            properties['timestamp'] = datetime.now().isoformat()
            
            # In production, this would send to Application Insights
            logger.error(f"Tracked exception: {type(exception).__name__}: {str(exception)}")
            
        except Exception as e:
            logger.error(f"Failed to track exception: {e}")
    
    def track_request(self, name: str, url: str, duration_ms: float, 
                     success: bool, response_code: int, properties: Optional[Dict[str, Any]] = None) -> None:
        """Track HTTP request"""
        try:
            if properties is None:
                properties = {}
            
            # Add default properties
            properties.update(self.default_properties)
            
            # Add request details
            properties['request_name'] = name
            properties['request_url'] = url
            properties['duration_ms'] = duration_ms
            properties['success'] = success
            properties['response_code'] = response_code
            properties['session_id'] = self.telemetry_context.session_id
            properties['timestamp'] = datetime.now().isoformat()
            
            # In production, this would send to Application Insights
            logger.info(f"Tracked request: {name} - {response_code} ({duration_ms}ms)")
            
        except Exception as e:
            logger.error(f"Failed to track request {name}: {e}")
    
    def track_dependency(self, name: str, dependency_type: str, target: str,
                        duration_ms: float, success: bool, properties: Optional[Dict[str, Any]] = None) -> None:
        """Track dependency call"""
        try:
            if properties is None:
                properties = {}
            
            # Add default properties
            properties.update(self.default_properties)
            
            # Add dependency details
            properties['dependency_name'] = name
            properties['dependency_type'] = dependency_type
            properties['dependency_target'] = target
            properties['duration_ms'] = duration_ms
            properties['success'] = success
            properties['session_id'] = self.telemetry_context.session_id
            properties['timestamp'] = datetime.now().isoformat()
            
            # In production, this would send to Application Insights
            logger.info(f"Tracked dependency: {name} ({dependency_type}) - {target} ({duration_ms}ms)")
            
        except Exception as e:
            logger.error(f"Failed to track dependency {name}: {e}")
    
    @contextmanager
    def track_operation(self, operation_name: str, properties: Optional[Dict[str, Any]] = None):
        """Context manager for tracking operations"""
        start_time = time.time()
        operation_id = str(uuid.uuid4())
        
        try:
            # Set operation context
            old_operation_id = self.telemetry_context.operation_id
            self.telemetry_context.operation_id = operation_id
            
            # Track operation start
            if properties is None:
                properties = {}
            properties['operation_id'] = operation_id
            properties['operation_start'] = datetime.now().isoformat()
            
            yield operation_id
            
            # Track successful completion
            duration_ms = (time.time() - start_time) * 1000
            self.track_request(operation_name, "", duration_ms, True, 200, properties)
            
        except Exception as e:
            # Track failure
            duration_ms = (time.time() - start_time) * 1000
            if properties is None:
                properties = {}
            properties['operation_id'] = operation_id
            properties['error'] = str(e)
            
            self.track_request(operation_name, "", duration_ms, False, 500, properties)
            self.track_exception(e, properties)
            raise
            
        finally:
            # Restore operation context
            self.telemetry_context.operation_id = old_operation_id
    
    def track_user_action(self, action_name: str, user_id: str, 
                         properties: Optional[Dict[str, Any]] = None) -> None:
        """Track user action"""
        try:
            if properties is None:
                properties = {}
            
            # Add default properties
            properties.update(self.default_properties)
            
            # Add user action details
            properties['action_name'] = action_name
            properties['user_id'] = user_id
            properties['session_id'] = self.telemetry_context.session_id
            properties['timestamp'] = datetime.now().isoformat()
            
            # In production, this would send to Application Insights
            logger.info(f"Tracked user action: {action_name} by user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to track user action {action_name}: {e}")
    
    def track_performance_metric(self, metric: PerformanceMetric) -> None:
        """Track performance metric"""
        try:
            # Add default properties
            if metric.properties:
                metric.properties.update(self.default_properties)
            else:
                metric.properties = self.default_properties.copy()
            
            # Add performance details
            metric.properties['operation_name'] = metric.operation_name
            metric.properties['duration_ms'] = metric.duration_ms
            metric.properties['success'] = metric.success
            metric.properties['session_id'] = self.telemetry_context.session_id
            metric.properties['timestamp'] = datetime.now().isoformat()
            
            # Track as both metric and request
            self.track_metric(CustomMetric(
                name=f"performance.{metric.operation_name}",
                value=metric.duration_ms,
                properties=metric.properties
            ))
            
            self.track_request(
                metric.operation_name,
                "",
                metric.duration_ms,
                metric.success,
                200 if metric.success else 500,
                metric.properties
            )
            
        except Exception as e:
            logger.error(f"Failed to track performance metric: {e}")
    
    def set_user_context(self, user_id: str) -> None:
        """Set user context for telemetry"""
        self.telemetry_context.user_id = user_id
        logger.info(f"User context set: {user_id}")
    
    def set_session_context(self, session_id: str) -> None:
        """Set session context for telemetry"""
        self.telemetry_context.session_id = session_id
        logger.info(f"Session context set: {session_id}")
    
    def set_operation_context(self, operation_id: str, parent_operation_id: Optional[str] = None) -> None:
        """Set operation context for telemetry"""
        self.telemetry_context.operation_id = operation_id
        self.telemetry_context.parent_operation_id = parent_operation_id
        logger.info(f"Operation context set: {operation_id}")
    
    def flush(self) -> None:
        """Flush telemetry data"""
        try:
            # In production, this would flush the telemetry buffer
            logger.info("Telemetry data flushed")
        except Exception as e:
            logger.error(f"Failed to flush telemetry: {e}")

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self, app_insights_client: ApplicationInsightsClient):
        self.app_insights = app_insights_client
        self.metrics_buffer = []
        self.buffer_size = 100
        self.flush_interval = 60  # seconds
    
    def start_monitoring(self) -> None:
        """Start performance monitoring"""
        try:
            logger.info("Performance monitoring started")
            # In production, this would start background monitoring tasks
            
        except Exception as e:
            logger.error(f"Failed to start performance monitoring: {e}")
    
    def record_metric(self, name: str, value: float, category: str = "general") -> None:
        """Record performance metric"""
        try:
            metric = CustomMetric(
                name=f"{category}.{name}",
                value=value,
                properties={'category': category}
            )
            
            self.app_insights.track_metric(metric)
            
            # Add to buffer for batch processing
            self.metrics_buffer.append(metric)
            
            # Flush if buffer is full
            if len(self.metrics_buffer) >= self.buffer_size:
                self.flush_metrics()
                
        except Exception as e:
            logger.error(f"Failed to record metric {name}: {e}")
    
    def flush_metrics(self) -> None:
        """Flush metrics buffer"""
        try:
            if self.metrics_buffer:
                logger.info(f"Flushing {len(self.metrics_buffer)} metrics")
                self.metrics_buffer.clear()
                
        except Exception as e:
            logger.error(f"Failed to flush metrics: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        try:
            # Mock performance summary
            summary = {
                'total_requests': 15000,
                'average_response_time': 125.5,  # ms
                'success_rate': 99.2,  # %
                'error_rate': 0.8,     # %
                'throughput': 250,     # requests per second
                'active_users': 150,
                'peak_concurrent_users': 45
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {}

class UserBehaviorAnalytics:
    """User behavior analytics and insights"""
    
    def __init__(self, app_insights_client: ApplicationInsightsClient):
        self.app_insights = app_insights_client
        self.user_sessions = {}
    
    def track_user_session(self, user_id: str, session_data: Dict[str, Any]) -> None:
        """Track user session data"""
        try:
            session_id = str(uuid.uuid4())
            
            session_info = {
                'session_id': session_id,
                'user_id': user_id,
                'start_time': datetime.now().isoformat(),
                'session_data': session_data
            }
            
            self.user_sessions[session_id] = session_info
            
            # Track session start
            self.app_insights.track_event(CustomEvent(
                name="user_session_started",
                properties={
                    'session_id': session_id,
                    'user_id': user_id,
                    'session_data': json.dumps(session_data)
                }
            ))
            
        except Exception as e:
            logger.error(f"Failed to track user session: {e}")
    
    def track_user_behavior(self, user_id: str, behavior_type: str, 
                           behavior_data: Dict[str, Any]) -> None:
        """Track user behavior patterns"""
        try:
            self.app_insights.track_event(CustomEvent(
                name=f"user_behavior_{behavior_type}",
                properties={
                    'user_id': user_id,
                    'behavior_type': behavior_type,
                    'behavior_data': json.dumps(behavior_data),
                    'timestamp': datetime.now().isoformat()
                }
            ))
            
        except Exception as e:
            logger.error(f"Failed to track user behavior: {e}")
    
    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get user behavior insights"""
        try:
            # Mock user insights
            insights = {
                'user_id': user_id,
                'total_sessions': 25,
                'average_session_duration': 1800,  # seconds
                'favorite_features': ['voice_synthesis', 'voice_enrollment'],
                'usage_patterns': {
                    'peak_hours': ['09:00', '14:00', '19:00'],
                    'preferred_languages': ['en-US', 'es-ES', 'fr-FR'],
                    'device_preferences': ['desktop', 'mobile']
                },
                'engagement_score': 8.5,
                'last_activity': datetime.now().isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get user insights: {e}")
            return {}

# Utility functions
def create_app_insights_client(instrumentation_key: str, connection_string: str = "") -> ApplicationInsightsClient:
    """Create Application Insights client"""
    return ApplicationInsightsClient(instrumentation_key, connection_string)

def track_api_call(app_insights: ApplicationInsightsClient, endpoint: str, 
                  duration_ms: float, success: bool, response_code: int):
    """Track API call performance"""
    app_insights.track_request(
        name=f"API_{endpoint}",
        url=endpoint,
        duration_ms=duration_ms,
        success=success,
        response_code=response_code
    )

def track_voice_synthesis(app_insights: ApplicationInsightsClient, user_id: str, 
                         voice_id: str, text_length: int, duration_ms: float):
    """Track voice synthesis metrics"""
    app_insights.track_event(CustomEvent(
        name="voice_synthesis_completed",
        properties={
            'user_id': user_id,
            'voice_id': voice_id,
            'text_length': text_length,
            'duration_ms': duration_ms
        }
    ))
    
    app_insights.track_metric(CustomMetric(
        name="synthesis_duration",
        value=duration_ms,
        properties={'voice_id': voice_id, 'user_id': user_id}
    ))
