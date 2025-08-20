"""
Azure Monitor Configuration for Voice Cloning System
Provides metric collection, alert rules, log analytics queries, and automated scaling policies
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "Critical"
    ERROR = "Error"
    WARNING = "Warning"
    INFORMATION = "Information"

class ScalingPolicy(Enum):
    """Scaling policy types"""
    CPU_BASED = "cpu_based"
    MEMORY_BASED = "memory_based"
    QUEUE_BASED = "queue_based"
    CUSTOM_METRIC = "custom_metric"
    SCHEDULE_BASED = "schedule_based"

@dataclass
class MetricDefinition:
    """Metric definition"""
    name: str
    display_name: str
    description: str
    unit: str
    metric_type: MetricType
    aggregation_type: str = "Average"
    time_grain: str = "PT1M"  # 1 minute
    category: str = "general"
    dimensions: Optional[List[str]] = None

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    description: str
    severity: AlertSeverity
    metric_name: str
    threshold: float
    operator: str  # GreaterThan, LessThan, etc.
    time_window: str = "PT5M"  # 5 minutes
    frequency: str = "PT1M"    # 1 minute
    action_groups: List[str] = None
    enabled: bool = True

@dataclass
class ScalingRule:
    """Scaling rule configuration"""
    name: str
    metric_name: str
    threshold: float
    operator: str
    scale_out_cooldown: int = 300  # 5 minutes
    scale_in_cooldown: int = 300   # 5 minutes
    scale_out_increment: int = 1
    scale_in_increment: int = 1
    min_instances: int = 1
    max_instances: int = 10

class AzureMonitorClient:
    """Azure Monitor client for metrics and alerts"""
    
    def __init__(self, subscription_id: str, resource_group: str):
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.metrics = {}
        self.alert_rules = {}
        self.scaling_rules = {}
        self._setup_monitoring()
    
    def _setup_monitoring(self) -> None:
        """Setup Azure Monitor configuration"""
        try:
            logger.info(f"Azure Monitor client initialized for subscription: {self.subscription_id}")
            logger.info(f"Resource group: {self.resource_group}")
            
            # Initialize default metrics
            self._setup_default_metrics()
            
            # Initialize default alert rules
            self._setup_default_alerts()
            
            # Initialize scaling policies
            self._setup_scaling_policies()
            
        except Exception as e:
            logger.error(f"Failed to setup Azure Monitor: {e}")
    
    def _setup_default_metrics(self) -> None:
        """Setup default metrics for voice cloning system"""
        default_metrics = [
            MetricDefinition(
                name="VoiceSynthesisRequests",
                display_name="Voice Synthesis Requests",
                description="Total number of voice synthesis requests",
                unit="Count",
                metric_type=MetricType.COUNTER,
                category="voice_synthesis"
            ),
            MetricDefinition(
                name="VoiceEnrollmentRequests",
                display_name="Voice Enrollment Requests",
                description="Total number of voice enrollment requests",
                unit="Count",
                metric_type=MetricType.COUNTER,
                category="voice_enrollment"
            ),
            MetricDefinition(
                name="SynthesisLatency",
                display_name="Synthesis Latency",
                description="Average latency for voice synthesis",
                unit="Milliseconds",
                metric_type=MetricType.GAUGE,
                category="performance"
            ),
            MetricDefinition(
                name="ActiveUsers",
                display_name="Active Users",
                description="Number of active users",
                unit="Count",
                metric_type=MetricType.GAUGE,
                category="user_activity"
            ),
            MetricDefinition(
                name="ErrorRate",
                display_name="Error Rate",
                description="Percentage of failed requests",
                unit="Percent",
                metric_type=MetricType.GAUGE,
                category="reliability"
            ),
            MetricDefinition(
                name="CacheHitRatio",
                display_name="Cache Hit Ratio",
                description="Percentage of cache hits",
                unit="Percent",
                metric_type=MetricType.GAUGE,
                category="performance"
            )
        ]
        
        for metric in default_metrics:
            self.metrics[metric.name] = metric
        
        logger.info(f"Setup {len(default_metrics)} default metrics")
    
    def _setup_default_alerts(self) -> None:
        """Setup default alert rules"""
        default_alerts = [
            AlertRule(
                name="HighErrorRate",
                description="Alert when error rate exceeds threshold",
                severity=AlertSeverity.CRITICAL,
                metric_name="ErrorRate",
                threshold=5.0,
                operator="GreaterThan",
                time_window="PT5M"
            ),
            AlertRule(
                name="HighLatency",
                description="Alert when synthesis latency is too high",
                severity=AlertSeverity.WARNING,
                metric_name="SynthesisLatency",
                threshold=2000.0,
                operator="GreaterThan",
                time_window="PT5M"
            ),
            AlertRule(
                name="LowCacheHitRatio",
                description="Alert when cache hit ratio is low",
                severity=AlertSeverity.WARNING,
                metric_name="CacheHitRatio",
                threshold=70.0,
                operator="LessThan",
                time_window="PT10M"
            ),
            AlertRule(
                name="HighCPUUsage",
                description="Alert when CPU usage is high",
                severity=AlertSeverity.WARNING,
                metric_name="CPUPercentage",
                threshold=80.0,
                operator="GreaterThan",
                time_window="PT5M"
            ),
            AlertRule(
                name="HighMemoryUsage",
                description="Alert when memory usage is high",
                severity=AlertSeverity.WARNING,
                metric_name="MemoryPercentage",
                threshold=85.0,
                operator="GreaterThan",
                time_window="PT5M"
            )
        ]
        
        for alert in default_alerts:
            self.alert_rules[alert.name] = alert
        
        logger.info(f"Setup {len(default_alerts)} default alert rules")
    
    def _setup_scaling_policies(self) -> None:
        """Setup scaling policies"""
        scaling_policies = [
            ScalingRule(
                name="CPUBasedScaling",
                metric_name="CPUPercentage",
                threshold=70.0,
                operator="GreaterThan",
                scale_out_cooldown=300,
                scale_in_cooldown=600,
                min_instances=2,
                max_instances=10
            ),
            ScalingRule(
                name="QueueBasedScaling",
                metric_name="QueueLength",
                threshold=100,
                operator="GreaterThan",
                scale_out_cooldown=180,
                scale_in_cooldown=300,
                min_instances=1,
                max_instances=8
            ),
            ScalingRule(
                name="LatencyBasedScaling",
                metric_name="SynthesisLatency",
                threshold=1500.0,
                operator="GreaterThan",
                scale_out_cooldown=240,
                scale_in_cooldown=480,
                min_instances=2,
                max_instances=12
            )
        ]
        
        for policy in scaling_policies:
            self.scaling_rules[policy.name] = policy
        
        logger.info(f"Setup {len(scaling_policies)} scaling policies")
    
    def create_custom_metric(self, metric: MetricDefinition) -> bool:
        """Create custom metric"""
        try:
            self.metrics[metric.name] = metric
            logger.info(f"Created custom metric: {metric.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create custom metric {metric.name}: {e}")
            return False
    
    def create_alert_rule(self, alert: AlertRule) -> bool:
        """Create alert rule"""
        try:
            self.alert_rules[alert.name] = alert
            logger.info(f"Created alert rule: {alert.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create alert rule {alert.name}: {e}")
            return False
    
    def create_scaling_rule(self, rule: ScalingRule) -> bool:
        """Create scaling rule"""
        try:
            self.scaling_rules[rule.name] = rule
            logger.info(f"Created scaling rule: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create scaling rule {rule.name}: {e}")
            return False
    
    def emit_metric(self, metric_name: str, value: float, 
                   dimensions: Optional[Dict[str, str]] = None) -> bool:
        """Emit metric to Azure Monitor"""
        try:
            if metric_name not in self.metrics:
                logger.warning(f"Unknown metric: {metric_name}")
                return False
            
            # In production, this would send to Azure Monitor
            metric_data = {
                'name': metric_name,
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'dimensions': dimensions or {},
                'category': self.metrics[metric_name].category
            }
            
            logger.debug(f"Emitted metric: {metric_data}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to emit metric {metric_name}: {e}")
            return False
    
    def emit_batch_metrics(self, metrics: List[Dict[str, Any]]) -> bool:
        """Emit multiple metrics in batch"""
        try:
            success_count = 0
            
            for metric_data in metrics:
                if self.emit_metric(
                    metric_data['name'],
                    metric_data['value'],
                    metric_data.get('dimensions')
                ):
                    success_count += 1
            
            logger.info(f"Emitted {success_count}/{len(metrics)} metrics successfully")
            return success_count == len(metrics)
            
        except Exception as e:
            logger.error(f"Failed to emit batch metrics: {e}")
            return False
    
    def get_metric_definition(self, metric_name: str) -> Optional[MetricDefinition]:
        """Get metric definition"""
        return self.metrics.get(metric_name)
    
    def list_metrics(self, category: Optional[str] = None) -> List[MetricDefinition]:
        """List available metrics"""
        if category:
            return [metric for metric in self.metrics.values() if metric.category == category]
        return list(self.metrics.values())
    
    def get_alert_rules(self, severity: Optional[AlertSeverity] = None) -> List[AlertRule]:
        """Get alert rules"""
        if severity:
            return [rule for rule in self.alert_rules.values() if rule.severity == severity]
        return list(self.alert_rules.values())
    
    def get_scaling_rules(self) -> List[ScalingRule]:
        """Get scaling rules"""
        return list(self.scaling_rules.values())
    
    def evaluate_alerts(self, current_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Evaluate alert rules against current metrics"""
        triggered_alerts = []
        
        try:
            for rule_name, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                
                if rule.metric_name in current_metrics:
                    current_value = current_metrics[rule.metric_name]
                    triggered = False
                    
                    if rule.operator == "GreaterThan" and current_value > rule.threshold:
                        triggered = True
                    elif rule.operator == "LessThan" and current_value < rule.threshold:
                        triggered = True
                    elif rule.operator == "GreaterThanOrEqual" and current_value >= rule.threshold:
                        triggered = True
                    elif rule.operator == "LessThanOrEqual" and current_value <= rule.threshold:
                        triggered = True
                    elif rule.operator == "Equal" and current_value == rule.threshold:
                        triggered = True
                    
                    if triggered:
                        alert_info = {
                            'rule_name': rule_name,
                            'metric_name': rule.metric_name,
                            'current_value': current_value,
                            'threshold': rule.threshold,
                            'operator': rule.operator,
                            'severity': rule.severity.value,
                            'timestamp': datetime.now().isoformat(),
                            'description': rule.description
                        }
                        triggered_alerts.append(alert_info)
                        
                        logger.warning(f"Alert triggered: {rule_name} - {rule.metric_name} = {current_value}")
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Failed to evaluate alerts: {e}")
            return []
    
    def generate_log_analytics_query(self, metric_name: str, 
                                   time_range: str = "PT1H") -> str:
        """Generate Log Analytics query for metric"""
        try:
            if metric_name not in self.metrics:
                return ""
            
            metric = self.metrics[metric_name]
            
            query = f"""
            {metric.name}
            | where TimeGenerated >= ago({time_range})
            | summarize 
                avg({metric.name}) as Average,
                min({metric.name}) as Minimum,
                max({metric.name}) as Maximum,
                count() as Count
                by bin(TimeGenerated, {metric.time_grain})
            | order by TimeGenerated asc
            """
            
            return query.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate Log Analytics query: {e}")
            return ""
    
    def create_dashboard_config(self) -> Dict[str, Any]:
        """Create dashboard configuration"""
        try:
            dashboard = {
                'name': 'Voice Cloning System Dashboard',
                'description': 'Comprehensive monitoring dashboard for voice cloning system',
                'subscription_id': self.subscription_id,
                'resource_group': self.resource_group,
                'location': 'East US',
                'tags': {
                    'Environment': 'Production',
                    'Component': 'Voice Cloning',
                    'ManagedBy': 'Bicep'
                },
                'lenses': [
                    {
                        'order': 1,
                        'parts': [
                            {
                                'position': {'x': 0, 'y': 0, 'colSpan': 6, 'rowSpan': 4},
                                'metadata': {
                                    'inputs': [],
                                    'type': 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart',
                                    'settings': {
                                        'content': {
                                            'Query': self.generate_log_analytics_query("VoiceSynthesisRequests", "PT24H"),
                                            'PartTitle': "Voice Synthesis Requests (24h)"
                                        }
                                    }
                                }
                            },
                            {
                                'position': {'x': 6, 'y': 0, 'colSpan': 6, 'rowSpan': 4},
                                'metadata': {
                                    'inputs': [],
                                    'type': 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart',
                                    'settings': {
                                        'content': {
                                            'Query': self.generate_log_analytics_query("SynthesisLatency", "PT24H"),
                                            'PartTitle': "Synthesis Latency (24h)"
                                        }
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Failed to create dashboard config: {e}")
            return {}
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        try:
            summary = {
                'timestamp': datetime.now().isoformat(),
                'subscription_id': self.subscription_id,
                'resource_group': self.resource_group,
                'metrics_count': len(self.metrics),
                'alert_rules_count': len(self.alert_rules),
                'scaling_rules_count': len(self.scaling_rules),
                'metrics_by_category': {},
                'alerts_by_severity': {},
                'recent_alerts': []
            }
            
            # Group metrics by category
            for metric in self.metrics.values():
                category = metric.category
                if category not in summary['metrics_by_category']:
                    summary['metrics_by_category'][category] = []
                summary['metrics_by_category'][category].append(metric.name)
            
            # Group alerts by severity
            for rule in self.alert_rules.values():
                severity = rule.severity.value
                if severity not in summary['alerts_by_severity']:
                    summary['alerts_by_severity'][severity] = []
                summary['alerts_by_severity'][severity].append(rule.name)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get monitoring summary: {e}")
            return {}

# Utility functions
def create_voice_cloning_metrics() -> List[MetricDefinition]:
    """Create comprehensive metrics for voice cloning system"""
    return [
        MetricDefinition(
            name="VoiceModelsTrained",
            display_name="Voice Models Trained",
            description="Total number of voice models successfully trained",
            unit="Count",
            metric_type=MetricType.COUNTER,
            category="voice_training"
        ),
        MetricDefinition(
            name="TrainingSuccessRate",
            display_name="Training Success Rate",
            description="Percentage of successful voice model training",
            unit="Percent",
            metric_type=MetricType.GAUGE,
            category="voice_training"
        ),
        MetricDefinition(
            name="AudioProcessingTime",
            display_name="Audio Processing Time",
            description="Average time to process audio files",
            unit="Milliseconds",
            metric_type=MetricType.GAUGE,
            category="audio_processing"
        ),
        MetricDefinition(
            name="TranslationRequests",
            display_name="Translation Requests",
            description="Total number of translation requests",
            unit="Count",
            metric_type=MetricType.COUNTER,
            category="translation"
        ),
        MetricDefinition(
            name="CacheEvictions",
            display_name="Cache Evictions",
            description="Number of cache entries evicted",
            unit="Count",
            metric_type=MetricType.COUNTER,
            category="performance"
        )
    ]

def create_performance_alerts() -> List[AlertRule]:
    """Create performance-focused alert rules"""
    return [
        AlertRule(
            name="TrainingFailureRate",
            description="Alert when voice training failure rate is high",
            severity=AlertSeverity.ERROR,
            metric_name="TrainingSuccessRate",
            threshold=85.0,
            operator="LessThan",
            time_window="PT30M"
        ),
        AlertRule(
            name="HighAudioProcessingTime",
            description="Alert when audio processing takes too long",
            severity=AlertSeverity.WARNING,
            metric_name="AudioProcessingTime",
            threshold=5000.0,
            operator="GreaterThan",
            time_window="PT10M"
        ),
        AlertRule(
            name="CachePerformanceDegradation",
            description="Alert when cache performance degrades",
            severity=AlertSeverity.WARNING,
            metric_name="CacheEvictions",
            threshold=1000,
            operator="GreaterThan",
            time_window="PT15M"
        )
    ]

def validate_metric_definition(metric: MetricDefinition) -> bool:
    """Validate metric definition"""
    if not metric.name or not metric.display_name:
        return False
    
    if metric.threshold < 0:
        return False
    
    return True
