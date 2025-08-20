"""
Business Intelligence Module for Voice Cloning System
Provides usage analytics, cost tracking, quality metrics monitoring, and compliance reporting
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid
import csv
from pathlib import Path

logger = logging.getLogger(__name__)

class ReportType(Enum):
    """Report types"""
    USAGE_ANALYTICS = "usage_analytics"
    COST_ANALYSIS = "cost_analysis"
    QUALITY_METRICS = "quality_metrics"
    COMPLIANCE_AUDIT = "compliance_audit"
    PERFORMANCE_REPORT = "performance_report"
    USER_BEHAVIOR = "user_behavior"

class MetricCategory(Enum):
    """Metric categories"""
    OPERATIONAL = "operational"
    BUSINESS = "business"
    TECHNICAL = "technical"
    COMPLIANCE = "compliance"
    COST = "cost"

@dataclass
class UsageMetric:
    """Usage metric data"""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    user_id: Optional[str] = None
    voice_id: Optional[str] = None
    language: Optional[str] = None
    region: Optional[str] = None
    device_type: Optional[str] = None

@dataclass
class CostMetric:
    """Cost metric data"""
    service_name: str
    resource_type: str
    cost_amount: float
    currency: str = "USD"
    timestamp: datetime = None
    region: Optional[str] = None
    usage_quantity: Optional[float] = None
    usage_unit: Optional[str] = None

@dataclass
class QualityMetric:
    """Quality metric data"""
    metric_name: str
    value: float
    threshold: float
    status: str  # "good", "warning", "critical"
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

@dataclass
class ComplianceRecord:
    """Compliance record data"""
    requirement_id: str
    requirement_name: str
    status: str  # "compliant", "non_compliant", "pending"
    last_checked: datetime
    next_check: datetime
    details: Optional[Dict[str, Any]] = None
    evidence: Optional[List[str]] = None

class BusinessIntelligenceEngine:
    """Business intelligence and analytics engine"""
    
    def __init__(self):
        self.usage_metrics = []
        self.cost_metrics = []
        self.quality_metrics = []
        self.compliance_records = []
        self.reports_cache = {}
        self._setup_bi_engine()
    
    def _setup_bi_engine(self) -> None:
        """Setup business intelligence engine"""
        try:
            logger.info("Business Intelligence engine initialized")
            
            # Initialize default metrics and records
            self._setup_default_metrics()
            self._setup_compliance_framework()
            
        except Exception as e:
            logger.error(f"Failed to setup BI engine: {e}")
    
    def _setup_default_metrics(self) -> None:
        """Setup default metrics for tracking"""
        try:
            # Add some sample usage metrics
            sample_usage = [
                UsageMetric(
                    metric_name="daily_active_users",
                    value=150,
                    unit="users",
                    timestamp=datetime.now(),
                    region="East US"
                ),
                UsageMetric(
                    metric_name="voice_synthesis_requests",
                    value=2500,
                    unit="requests",
                    timestamp=datetime.now(),
                    region="East US"
                )
            ]
            
            self.usage_metrics.extend(sample_usage)
            
            # Add sample cost metrics
            sample_costs = [
                CostMetric(
                    service_name="Azure Speech Service",
                    resource_type="Custom Neural Voice",
                    cost_amount=45.50,
                    timestamp=datetime.now(),
                    region="East US",
                    usage_quantity=100,
                    usage_unit="hours"
                ),
                CostMetric(
                    service_name="Azure Functions",
                    resource_type="Consumption Plan",
                    cost_amount=12.30,
                    timestamp=datetime.now(),
                    region="East US",
                    usage_quantity=50000,
                    usage_unit="executions"
                )
            ]
            
            self.cost_metrics.extend(sample_costs)
            
            logger.info("Default metrics setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup default metrics: {e}")
    
    def _setup_compliance_framework(self) -> None:
        """Setup compliance framework"""
        try:
            compliance_requirements = [
                ComplianceRecord(
                    requirement_id="GDPR_001",
                    requirement_name="Data Processing Consent",
                    status="compliant",
                    last_checked=datetime.now(),
                    next_check=datetime.now() + timedelta(days=30),
                    details={"consent_mechanism": "explicit_opt_in", "audit_trail": "enabled"}
                ),
                ComplianceRecord(
                    requirement_id="GDPR_002",
                    requirement_name="Data Retention Policy",
                    status="compliant",
                    last_checked=datetime.now(),
                    next_check=datetime.now() + timedelta(days=30),
                    details={"retention_period": "2_years", "auto_deletion": "enabled"}
                ),
                ComplianceRecord(
                    requirement_id="SOC2_001",
                    requirement_name="Access Control",
                    status="compliant",
                    last_checked=datetime.now(),
                    next_check=datetime.now() + timedelta(days=90),
                    details={"mfa_enabled": True, "role_based_access": "enabled"}
                )
            ]
            
            self.compliance_records.extend(compliance_requirements)
            logger.info("Compliance framework setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup compliance framework: {e}")
    
    def record_usage_metric(self, metric: UsageMetric) -> bool:
        """Record usage metric"""
        try:
            self.usage_metrics.append(metric)
            logger.debug(f"Recorded usage metric: {metric.metric_name} = {metric.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record usage metric: {e}")
            return False
    
    def record_cost_metric(self, cost: CostMetric) -> bool:
        """Record cost metric"""
        try:
            if not cost.timestamp:
                cost.timestamp = datetime.now()
            
            self.cost_metrics.append(cost)
            logger.debug(f"Recorded cost metric: {cost.service_name} = {cost.cost_amount} {cost.currency}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record cost metric: {e}")
            return False
    
    def record_quality_metric(self, metric: QualityMetric) -> bool:
        """Record quality metric"""
        try:
            self.quality_metrics.append(metric)
            logger.debug(f"Recorded quality metric: {metric.metric_name} = {metric.value} ({metric.status})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record quality metric: {e}")
            return False
    
    def update_compliance_record(self, requirement_id: str, status: str, 
                               details: Optional[Dict[str, Any]] = None) -> bool:
        """Update compliance record"""
        try:
            for record in self.compliance_records:
                if record.requirement_id == requirement_id:
                    record.status = status
                    record.last_checked = datetime.now()
                    if details:
                        record.details = details
                    logger.info(f"Updated compliance record: {requirement_id} = {status}")
                    return True
            
            logger.warning(f"Compliance requirement not found: {requirement_id}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to update compliance record: {e}")
            return False
    
    def generate_usage_analytics_report(self, time_range: str = "PT24H") -> Dict[str, Any]:
        """Generate usage analytics report"""
        try:
            end_time = datetime.now()
            
            if time_range == "PT24H":
                start_time = end_time - timedelta(hours=24)
            elif time_range == "PT7D":
                start_time = end_time - timedelta(days=7)
            elif time_range == "PT30D":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(hours=1)
            
            # Filter metrics by time range
            filtered_metrics = [
                m for m in self.usage_metrics 
                if start_time <= m.timestamp <= end_time
            ]
            
            # Group by metric name
            metrics_by_name = {}
            for metric in filtered_metrics:
                if metric.metric_name not in metrics_by_name:
                    metrics_by_name[metric.metric_name] = []
                metrics_by_name[metric.metric_name].append(metric)
            
            # Calculate analytics
            analytics = {
                'report_type': 'usage_analytics',
                'time_range': time_range,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_metrics': len(filtered_metrics),
                'metrics_summary': {},
                'trends': {},
                'top_users': [],
                'top_voices': [],
                'regional_distribution': {}
            }
            
            for metric_name, metrics in metrics_by_name.items():
                values = [m.value for m in metrics]
                analytics['metrics_summary'][metric_name] = {
                    'total': sum(values),
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(metrics)
                }
            
            logger.info(f"Generated usage analytics report for {time_range}")
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to generate usage analytics report: {e}")
            return {}
    
    def generate_cost_analysis_report(self, time_range: str = "PT30D") -> Dict[str, Any]:
        """Generate cost analysis report"""
        try:
            end_time = datetime.now()
            
            if time_range == "PT7D":
                start_time = end_time - timedelta(days=7)
            elif time_range == "PT30D":
                start_time = end_time - timedelta(days=30)
            elif time_range == "PT90D":
                start_time = end_time - timedelta(days=90)
            else:
                start_time = end_time - timedelta(days=30)
            
            # Filter costs by time range
            filtered_costs = [
                c for c in self.cost_metrics 
                if start_time <= c.timestamp <= end_time
            ]
            
            # Group by service
            costs_by_service = {}
            total_cost = 0
            
            for cost in filtered_costs:
                if cost.service_name not in costs_by_service:
                    costs_by_service[cost.service_name] = []
                costs_by_service[cost.service_name].append(cost)
                total_cost += cost.cost_amount
            
            # Calculate cost breakdown
            cost_analysis = {
                'report_type': 'cost_analysis',
                'time_range': time_range,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_cost': total_cost,
                'currency': 'USD',
                'cost_breakdown': {},
                'cost_trends': {},
                'cost_optimization_recommendations': []
            }
            
            for service_name, costs in costs_by_service.items():
                service_total = sum(c.cost_amount for c in costs)
                cost_analysis['cost_breakdown'][service_name] = {
                    'total_cost': service_total,
                    'percentage': (service_total / total_cost) * 100 if total_cost > 0 else 0,
                    'cost_count': len(costs)
                }
            
            # Generate optimization recommendations
            if total_cost > 100:  # If monthly cost > $100
                cost_analysis['cost_optimization_recommendations'].extend([
                    "Consider reserved instances for predictable workloads",
                    "Review and optimize Azure Functions execution",
                    "Implement cost alerts for budget management"
                ])
            
            logger.info(f"Generated cost analysis report for {time_range}")
            return cost_analysis
            
        except Exception as e:
            logger.error(f"Failed to generate cost analysis report: {e}")
            return {}
    
    def generate_quality_metrics_report(self) -> Dict[str, Any]:
        """Generate quality metrics report"""
        try:
            # Get recent quality metrics
            recent_metrics = [
                m for m in self.quality_metrics 
                if m.timestamp >= datetime.now() - timedelta(hours=24)
            ]
            
            # Group by status
            metrics_by_status = {}
            for metric in recent_metrics:
                if metric.status not in metrics_by_status:
                    metrics_by_status[metric.status] = []
                metrics_by_status[metric.status].append(metric)
            
            # Calculate quality scores
            total_metrics = len(recent_metrics)
            good_metrics = len(metrics_by_status.get('good', []))
            warning_metrics = len(metrics_by_status.get('warning', []))
            critical_metrics = len(metrics_by_status.get('critical', []))
            
            quality_score = (good_metrics / total_metrics * 100) if total_metrics > 0 else 0
            
            quality_report = {
                'report_type': 'quality_metrics',
                'timestamp': datetime.now().isoformat(),
                'quality_score': quality_score,
                'total_metrics': total_metrics,
                'metrics_by_status': {
                    'good': good_metrics,
                    'warning': warning_metrics,
                    'critical': critical_metrics
                },
                'status_distribution': {
                    'good_percentage': (good_metrics / total_metrics * 100) if total_metrics > 0 else 0,
                    'warning_percentage': (warning_metrics / total_metrics * 100) if total_metrics > 0 else 0,
                    'critical_percentage': (critical_metrics / total_metrics * 100) if total_metrics > 0 else 0
                },
                'critical_issues': [
                    m for m in recent_metrics if m.status == 'critical'
                ],
                'recommendations': []
            }
            
            # Generate recommendations based on quality issues
            if critical_metrics > 0:
                quality_report['recommendations'].append(
                    "Immediate attention required for critical quality issues"
                )
            
            if warning_metrics > (total_metrics * 0.2):  # More than 20% warnings
                quality_report['recommendations'].append(
                    "Review processes to reduce warning-level quality issues"
                )
            
            if quality_score < 90:
                quality_report['recommendations'].append(
                    "Implement quality improvement initiatives"
                )
            
            logger.info("Generated quality metrics report")
            return quality_report
            
        except Exception as e:
            logger.error(f"Failed to generate quality metrics report: {e}")
            return {}
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report"""
        try:
            total_requirements = len(self.compliance_records)
            compliant_requirements = len([r for r in self.compliance_records if r.status == 'compliant'])
            non_compliant_requirements = len([r for r in self.compliance_records if r.status == 'non_compliant'])
            pending_requirements = len([r for r in self.compliance_records if r.status == 'pending'])
            
            compliance_score = (compliant_requirements / total_requirements * 100) if total_requirements > 0 else 0
            
            compliance_report = {
                'report_type': 'compliance_audit',
                'timestamp': datetime.now().isoformat(),
                'compliance_score': compliance_score,
                'total_requirements': total_requirements,
                'compliant_requirements': compliant_requirements,
                'non_compliant_requirements': non_compliant_requirements,
                'pending_requirements': pending_requirements,
                'compliance_status': 'compliant' if compliance_score >= 95 else 'needs_attention',
                'requirements_by_status': {
                    'compliant': [r for r in self.compliance_records if r.status == 'compliant'],
                    'non_compliant': [r for r in self.compliance_records if r.status == 'non_compliant'],
                    'pending': [r for r in self.compliance_records if r.status == 'pending']
                },
                'upcoming_checks': [
                    r for r in self.compliance_records 
                    if r.next_check <= datetime.now() + timedelta(days=7)
                ],
                'recommendations': []
            }
            
            # Generate compliance recommendations
            if non_compliant_requirements > 0:
                compliance_report['recommendations'].append(
                    "Address non-compliant requirements immediately"
                )
            
            if pending_requirements > 0:
                compliance_report['recommendations'].append(
                    "Complete pending compliance checks"
                )
            
            if compliance_score < 100:
                compliance_report['recommendations'].append(
                    "Implement continuous compliance monitoring"
                )
            
            logger.info("Generated compliance report")
            return compliance_report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {}
    
    def export_report_to_csv(self, report: Dict[str, Any], file_path: str) -> bool:
        """Export report to CSV format"""
        try:
            if not report:
                logger.warning("No report data to export")
                return False
            
            # Create directory if it doesn't exist
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                if report['report_type'] == 'usage_analytics':
                    self._export_usage_analytics_csv(report, csvfile)
                elif report['report_type'] == 'cost_analysis':
                    self._export_cost_analysis_csv(report, csvfile)
                elif report['report_type'] == 'quality_metrics':
                    self._export_quality_metrics_csv(report, csvfile)
                elif report['report_type'] == 'compliance_audit':
                    self._export_compliance_audit_csv(report, csvfile)
                else:
                    logger.warning(f"Unknown report type: {report['report_type']}")
                    return False
            
            logger.info(f"Report exported to CSV: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export report to CSV: {e}")
            return False
    
    def _export_usage_analytics_csv(self, report: Dict[str, Any], csvfile) -> None:
        """Export usage analytics to CSV"""
        writer = csv.writer(csvfile)
        writer.writerow(['Metric Name', 'Total', 'Average', 'Min', 'Max', 'Count'])
        
        for metric_name, summary in report['metrics_summary'].items():
            writer.writerow([
                metric_name,
                summary['total'],
                summary['average'],
                summary['min'],
                summary['max'],
                summary['count']
            ])
    
    def _export_cost_analysis_csv(self, report: Dict[str, Any], csvfile) -> None:
        """Export cost analysis to CSV"""
        writer = csv.writer(csvfile)
        writer.writerow(['Service Name', 'Total Cost', 'Percentage', 'Cost Count'])
        
        for service_name, breakdown in report['cost_breakdown'].items():
            writer.writerow([
                service_name,
                breakdown['total_cost'],
                f"{breakdown['percentage']:.2f}%",
                breakdown['cost_count']
            ])
    
    def _export_quality_metrics_csv(self, report: Dict[str, Any], csvfile) -> None:
        """Export quality metrics to CSV"""
        writer = csv.writer(csvfile)
        writer.writerow(['Status', 'Count', 'Percentage'])
        
        for status, count in report['metrics_by_status'].items():
            percentage = report['status_distribution'][f'{status}_percentage']
            writer.writerow([status, count, f"{percentage:.2f}%"])
    
    def _export_compliance_audit_csv(self, report: Dict[str, Any], csvfile) -> None:
        """Export compliance audit to CSV"""
        writer = csv.writer(csvfile)
        writer.writerow(['Requirement ID', 'Requirement Name', 'Status', 'Last Checked', 'Next Check'])
        
        for status, requirements in report['requirements_by_status'].items():
            for req in requirements:
                writer.writerow([
                    req.requirement_id,
                    req.requirement_name,
                    req.status,
                    req.last_checked.isoformat(),
                    req.next_check.isoformat()
                ])
    
    def get_bi_summary(self) -> Dict[str, Any]:
        """Get business intelligence summary"""
        try:
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_usage_metrics': len(self.usage_metrics),
                'total_cost_metrics': len(self.cost_metrics),
                'total_quality_metrics': len(self.quality_metrics),
                'total_compliance_records': len(self.compliance_records),
                'recent_reports': list(self.reports_cache.keys()),
                'system_health': 'healthy' if len(self.quality_metrics) > 0 else 'unknown'
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get BI summary: {e}")
            return {}

# Utility functions
def create_sample_usage_data() -> List[UsageMetric]:
    """Create sample usage data for testing"""
    return [
        UsageMetric(
            metric_name="voice_synthesis_requests",
            value=150,
            unit="requests",
            timestamp=datetime.now(),
            user_id="user_123",
            voice_id="voice_456",
            language="en-US",
            region="East US"
        ),
        UsageMetric(
            metric_name="voice_enrollment_requests",
            value=25,
            unit="requests",
            timestamp=datetime.now(),
            user_id="user_123",
            region="East US"
        )
    ]

def create_sample_cost_data() -> List[CostMetric]:
    """Create sample cost data for testing"""
    return [
        CostMetric(
            service_name="Azure Speech Service",
            resource_type="Custom Neural Voice",
            cost_amount=25.75,
            region="East US",
            usage_quantity=50,
            usage_unit="hours"
        ),
        CostMetric(
            service_name="Azure Storage",
            resource_type="Blob Storage",
            cost_amount=8.45,
            region="East US",
            usage_quantity=100,
            usage_unit="GB"
        )
    ]

def validate_usage_metric(metric: UsageMetric) -> bool:
    """Validate usage metric"""
    if not metric.metric_name or metric.value < 0:
        return False
    
    if not metric.timestamp:
        return False
    
    return True
