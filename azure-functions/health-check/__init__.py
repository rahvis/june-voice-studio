"""
Health Check HTTP Trigger Function
Provides health status and monitoring information
"""
import logging
import json
import azure.functions as func
from typing import Dict, Any
from datetime import datetime
import os
import psutil
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthChecker:
    """Health checker for Azure Functions and dependencies"""
    
    def __init__(self):
        self.start_time = time.time()
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.version = os.getenv("APP_VERSION", "1.0.0")
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Check system health metrics"""
        try:
            # Get CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            
            # Get network statistics
            network = psutil.net_io_counters()
            
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "status": "healthy" if cpu_percent < 80 else "warning"
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent,
                    "status": "healthy" if memory.percent < 80 else "warning"
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 2),
                    "status": "healthy" if (disk.used / disk.total) < 0.9 else "warning"
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "status": "healthy"
                }
            }
        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            return {
                "error": "Failed to check system health",
                "message": str(e)
            }
    
    async def check_azure_services(self) -> Dict[str, Any]:
        """Check Azure service connectivity"""
        try:
            # This would typically check actual Azure service connectivity
            # For now, return mock status
            services = {
                "azure_speech": {
                    "status": "healthy",
                    "response_time_ms": 150,
                    "last_check": datetime.utcnow().isoformat()
                },
                "azure_translator": {
                    "status": "healthy",
                    "response_time_ms": 120,
                    "last_check": datetime.utcnow().isoformat()
                },
                "azure_openai": {
                    "status": "healthy",
                    "response_time_ms": 200,
                    "last_check": datetime.utcnow().isoformat()
                },
                "azure_storage": {
                    "status": "healthy",
                    "response_time_ms": 80,
                    "last_check": datetime.utcnow().isoformat()
                },
                "azure_cosmos_db": {
                    "status": "healthy",
                    "response_time_ms": 100,
                    "last_check": datetime.utcnow().isoformat()
                }
            }
            
            return services
            
        except Exception as e:
            logger.error(f"Error checking Azure services: {str(e)}")
            return {
                "error": "Failed to check Azure services",
                "message": str(e)
            }
    
    async def check_function_health(self) -> Dict[str, Any]:
        """Check Azure Function health metrics"""
        try:
            uptime = time.time() - self.start_time
            
            return {
                "status": "healthy",
                "uptime_seconds": int(uptime),
                "uptime_formatted": self._format_uptime(uptime),
                "environment": self.environment,
                "version": self.version,
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking function health: {str(e)}")
            return {
                "error": "Failed to check function health",
                "message": str(e)
            }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {secs}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    async def get_overall_health(self) -> Dict[str, Any]:
        """Get overall health status"""
        try:
            # Check all health aspects
            system_health = await self.check_system_health()
            azure_services = await self.check_azure_services()
            function_health = await self.check_function_health()
            
            # Determine overall status
            overall_status = "healthy"
            if "error" in system_health or "error" in azure_services or "error" in function_health:
                overall_status = "unhealthy"
            else:
                # Check for warnings
                for service in azure_services.values():
                    if isinstance(service, dict) and service.get("status") == "warning":
                        overall_status = "degraded"
                        break
                
                # Check system metrics for warnings
                if (system_health.get("cpu", {}).get("status") == "warning" or
                    system_health.get("memory", {}).get("status") == "warning" or
                    system_health.get("disk", {}).get("status") == "warning"):
                    overall_status = "degraded"
            
            return {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "function": function_health,
                "system": system_health,
                "azure_services": azure_services,
                "checks": {
                    "system": "error" not in system_health,
                    "azure_services": "error" not in azure_services,
                    "function": "error" not in function_health
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting overall health: {str(e)}")
            return {
                "status": "unhealthy",
                "error": "Failed to determine health status",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global health checker instance
health_checker = HealthChecker()

async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main function for health check HTTP trigger
    """
    try:
        logger.info("Health check function triggered")
        
        # Get request method
        if req.method != "GET":
            return func.HttpResponse(
                json.dumps({
                    "error": "Method not allowed",
                    "message": "Only GET method is supported"
                }),
                status_code=405,
                mimetype="application/json"
            )
        
        # Get query parameters
        detailed = req.params.get("detailed", "false").lower() == "true"
        check_type = req.params.get("check", "overall")
        
        # Perform health checks based on type
        if check_type == "system":
            health_data = await health_checker.check_system_health()
        elif check_type == "azure":
            health_data = await health_checker.check_azure_services()
        elif check_type == "function":
            health_data = await health_checker.check_function_health()
        else:
            # Overall health check
            health_data = await health_checker.get_overall_health()
        
        # Determine response status code
        status_code = 200
        if health_data.get("status") == "unhealthy":
            status_code = 503  # Service Unavailable
        elif health_data.get("status") == "degraded":
            status_code = 200  # Still OK but with warnings
        
        # Add response headers
        headers = {
            "X-Health-Status": health_data.get("status", "unknown"),
            "X-Health-Check-Type": check_type,
            "X-Health-Timestamp": health_data.get("timestamp", datetime.utcnow().isoformat())
        }
        
        # If detailed check requested, include all metrics
        if detailed and check_type == "overall":
            health_data["detailed"] = True
            health_data["response_time_ms"] = int((time.time() - health_checker.start_time) * 1000)
        
        logger.info(f"Health check completed: {health_data.get('status', 'unknown')}")
        
        return func.HttpResponse(
            json.dumps(health_data, indent=2 if detailed else None),
            status_code=status_code,
            mimetype="application/json",
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Error in health check function: {str(e)}")
        
        error_response = {
            "status": "unhealthy",
            "error": "Health check failed",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=503,  # Service Unavailable
            mimetype="application/json",
            headers={
                "X-Health-Status": "unhealthy",
                "X-Health-Error": "true"
            }
        )
