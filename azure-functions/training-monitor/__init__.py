"""
Training Job Monitoring Timer Trigger Function
Monitors voice training jobs and updates their status
"""
import logging
import json
import azure.functions as func
from typing import Dict, Any, List
from datetime import datetime, timedelta
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainingJobMonitor:
    """Monitor for voice training jobs"""
    
    def __init__(self):
        self.azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.azure_speech_region = os.getenv("AZURE_SPEECH_REGION")
        self.check_interval_minutes = 5
        
    async def get_active_training_jobs(self) -> List[Dict[str, Any]]:
        """Get list of active training jobs from database/storage"""
        try:
            # In a real implementation, this would query the database
            # For now, return mock data
            mock_jobs = [
                {
                    "job_id": "training-001",
                    "user_id": "user-001",
                    "voice_name": "John Doe Voice",
                    "status": "running",
                    "progress": 65,
                    "started_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "estimated_completion": (datetime.utcnow() + timedelta(hours=1)).isoformat()
                },
                {
                    "job_id": "training-002",
                    "user_id": "user-002",
                    "voice_name": "Jane Smith Voice",
                    "status": "queued",
                    "progress": 0,
                    "started_at": None,
                    "estimated_completion": None
                }
            ]
            
            return mock_jobs
            
        except Exception as e:
            logger.error(f"Error getting active training jobs: {str(e)}")
            return []
    
    async def check_job_status(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Check the status of a specific training job"""
        try:
            job_id = job["job_id"]
            current_status = job["status"]
            
            # In a real implementation, this would call Azure Speech Service API
            # to check the actual job status
            if current_status == "running":
                # Simulate checking Azure Speech Service
                await self._simulate_azure_check(job_id)
                
                # Update progress (mock)
                new_progress = min(100, job["progress"] + 5)
                job["progress"] = new_progress
                
                if new_progress >= 100:
                    job["status"] = "completed"
                    job["completed_at"] = datetime.utcnow().isoformat()
                    logger.info(f"Training job {job_id} completed")
                else:
                    logger.info(f"Training job {job_id} progress: {new_progress}%")
                    
            elif current_status == "queued":
                # Check if it's time to start this job
                if await self._should_start_job(job):
                    job["status"] = "running"
                    job["started_at"] = datetime.utcnow().isoformat()
                    job["estimated_completion"] = (datetime.utcnow() + timedelta(hours=3)).isoformat()
                    logger.info(f"Training job {job_id} started")
            
            return job
            
        except Exception as e:
            logger.error(f"Error checking job status for {job.get('job_id', 'unknown')}: {str(e)}")
            job["status"] = "error"
            job["error_message"] = str(e)
            return job
    
    async def _simulate_azure_check(self, job_id: str):
        """Simulate checking Azure Speech Service (replace with real API call)"""
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # In real implementation, this would be:
        # from azure.cognitiveservices.speech import SpeechConfig, CustomVoiceClient
        # client = CustomVoiceClient(endpoint, credential)
        # job_status = client.get_voice_training_job(job_id)
        
        logger.debug(f"Checked Azure Speech Service for job {job_id}")
    
    async def _should_start_job(self, job: Dict[str, Any]) -> bool:
        """Determine if a queued job should be started"""
        try:
            # Check if there are available resources
            # In a real implementation, this would check Azure quotas and current load
            
            # For now, start jobs that have been queued for more than 1 minute
            if job.get("queued_at"):
                queued_time = datetime.fromisoformat(job["queued_at"])
                if datetime.utcnow() - queued_time > timedelta(minutes=1):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining if job should start: {str(e)}")
            return False
    
    async def update_job_status(self, job: Dict[str, Any]) -> bool:
        """Update job status in database/storage"""
        try:
            # In a real implementation, this would update the database
            # For now, just log the update
            logger.info(f"Updated job {job['job_id']} status to {job['status']}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating job status: {str(e)}")
            return False
    
    async def send_notifications(self, job: Dict[str, Any]) -> None:
        """Send notifications for job status changes"""
        try:
            if job["status"] in ["completed", "failed", "error"]:
                # Send completion notification
                notification = {
                    "type": "training_completion",
                    "job_id": job["job_id"],
                    "user_id": job["user_id"],
                    "status": job["status"],
                    "voice_name": job["voice_name"],
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if job["status"] == "completed":
                    notification["message"] = f"Voice training for '{job['voice_name']}' has completed successfully!"
                elif job["status"] == "failed":
                    notification["message"] = f"Voice training for '{job['voice_name']}' has failed. Please check the logs."
                elif job["status"] == "error":
                    notification["message"] = f"Voice training for '{job['voice_name']}' encountered an error: {job.get('error_message', 'Unknown error')}"
                
                logger.info(f"Notification prepared for job {job['job_id']}: {notification['message']}")
                
        except Exception as e:
            logger.error(f"Error sending notification for job {job.get('job_id', 'unknown')}: {str(e)}")
    
    async def monitor_training_jobs(self) -> Dict[str, Any]:
        """Main monitoring function"""
        try:
            start_time = time.time()
            logger.info("Starting training job monitoring cycle")
            
            # Get active training jobs
            active_jobs = await self.get_active_training_jobs()
            logger.info(f"Found {len(active_jobs)} active training jobs")
            
            # Check each job
            updated_jobs = []
            completed_jobs = []
            failed_jobs = []
            
            for job in active_jobs:
                # Check job status
                updated_job = await self.check_job_status(job)
                
                # Update job in database
                if await self.update_job_status(updated_job):
                    updated_jobs.append(updated_job)
                    
                    # Track completed/failed jobs
                    if updated_job["status"] == "completed":
                        completed_jobs.append(updated_job)
                    elif updated_job["status"] in ["failed", "error"]:
                        failed_jobs.append(updated_job)
                    
                    # Send notifications
                    await self.send_notifications(updated_job)
            
            # Calculate monitoring statistics
            monitoring_stats = {
                "total_jobs_checked": len(active_jobs),
                "jobs_updated": len(updated_jobs),
                "jobs_completed": len(completed_jobs),
                "jobs_failed": len(failed_jobs),
                "monitoring_duration_ms": int((time.time() - start_time) * 1000),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Training job monitoring completed: {monitoring_stats}")
            return monitoring_stats
            
        except Exception as e:
            logger.error(f"Error in training job monitoring: {str(e)}")
            return {
                "error": "Training job monitoring failed",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global monitor instance
training_monitor = TrainingJobMonitor()

async def main(mytimer: func.TimerRequest, notificationQueue: func.Out[str]) -> None:
    """
    Main function for training job monitoring timer trigger
    """
    try:
        # Check if timer is past due
        if mytimer.past_due:
            logger.warning("Training job monitoring timer is past due")
        
        # Run monitoring
        monitoring_result = await training_monitor.monitor_training_jobs()
        
        # Add monitoring result to notification queue
        if "error" not in monitoring_result:
            notification_message = {
                "type": "training_monitoring_summary",
                "data": monitoring_result,
                "timestamp": datetime.utcnow().isoformat(),
                "function_name": "training-monitor"
            }
            
            notificationQueue.set(json.dumps(notification_message))
            logger.info("Training monitoring summary added to notification queue")
        
    except Exception as e:
        logger.error(f"Error in training job monitoring function: {str(e)}")
        
        # Add error notification to queue
        error_notification = {
            "type": "training_monitoring_error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "function_name": "training-monitor"
        }
        
        notificationQueue.set(json.dumps(error_notification))
        logger.info("Training monitoring error notification added to queue")

# Import asyncio for async operations
import asyncio
