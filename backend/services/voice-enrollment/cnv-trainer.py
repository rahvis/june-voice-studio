"""
Custom Neural Voice Training Orchestration Service

This module handles the orchestration of Custom Neural Voice (CNV) training
workflows, including job submission, monitoring, and status tracking.
"""

import requests
import json
import time
import asyncio
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class TrainingStatus(Enum):
    """Training job status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class TrainingType(Enum):
    """Training type enumeration"""
    PROFESSIONAL = "professional"
    NEURAL_CROSS_LINGUAL = "neural_cross_lingual"
    NEURAL_MULTILINGUAL = "neural_multilingual"

@dataclass
class TrainingJob:
    """Training job data structure"""
    job_id: str
    user_id: str
    voice_name: str
    training_type: TrainingType
    status: TrainingStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress_percentage: float
    estimated_completion: Optional[datetime]
    audio_files: List[str]
    transcriptions: List[str]
    model_id: Optional[str]
    voice_id: Optional[str]
    error_message: Optional[str]
    metadata: Dict[str, any]

@dataclass
class TrainingConfig:
    """Training configuration parameters"""
    training_type: TrainingType
    voice_name: str
    description: str
    language: str
    gender: str
    cross_lingual: bool
    multilingual: bool
    audio_format: str
    sample_rate: int
    channels: int
    bit_depth: int
    quality_threshold: float
    min_utterances: int
    max_utterances: int

class CNVTrainingService:
    """Azure Custom Neural Voice training service"""
    
    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.speech_key = config['speech_key']
        self.speech_region = config['speech_region']
        self.endpoint = f"https://{self.speech_region}.api.cognitive.microsoft.com"
        self.headers = {
            'Ocp-Apim-Subscription-Key': self.speech_key,
            'Content-Type': 'application/json'
        }
        self.storage_client = config.get('storage_client')
        self.notification_service = config.get('notification_service')
        
    async def create_training_job(self, 
                                user_id: str,
                                audio_files: List[str],
                                transcriptions: List[str],
                                training_config: TrainingConfig) -> TrainingJob:
        """
        Create and submit a new training job
        
        Args:
            user_id: User identifier
            audio_files: List of audio file paths
            transcriptions: List of transcription file paths
            training_config: Training configuration
            
        Returns:
            Training job instance
        """
        try:
            # Validate inputs
            validation_result = self._validate_training_inputs(
                audio_files, transcriptions, training_config
            )
            
            if not validation_result[0]:
                raise ValueError(f"Training validation failed: {validation_result[1]}")
            
            # Generate unique identifiers
            job_id = str(uuid.uuid4())
            voice_name = f"{training_config.voice_name}-{user_id}-{int(time.time())}"
            
            # Create training job
            training_job = TrainingJob(
                job_id=job_id,
                user_id=user_id,
                voice_name=voice_name,
                training_type=training_config.training_type,
                status=TrainingStatus.PENDING,
                created_at=datetime.utcnow(),
                started_at=None,
                completed_at=None,
                progress_percentage=0.0,
                estimated_completion=None,
                audio_files=audio_files,
                transcriptions=transcriptions,
                model_id=None,
                voice_id=None,
                error_message=None,
                metadata={
                    "training_config": asdict(training_config),
                    "total_audio_duration": 0.0,
                    "total_utterances": len(audio_files)
                }
            )
            
            # Store training job
            await self._store_training_job(training_job)
            
            # Submit to Azure Speech Service
            submission_result = await self._submit_to_azure_speech(training_job, training_config)
            
            if submission_result:
                training_job.status = TrainingStatus.SUBMITTED
                training_job.metadata["azure_job_id"] = submission_result
                await self._store_training_job(training_job)
                
                # Start monitoring
                asyncio.create_task(self._monitor_training_job(training_job.job_id))
                
                logger.info(f"Training job {job_id} submitted successfully")
            else:
                training_job.status = TrainingStatus.FAILED
                training_job.error_message = "Failed to submit to Azure Speech Service"
                await self._store_training_job(training_job)
                
                logger.error(f"Training job {job_id} submission failed")
            
            return training_job
            
        except Exception as e:
            logger.error(f"Error creating training job: {str(e)}")
            raise
    
    async def get_training_job(self, job_id: str) -> Optional[TrainingJob]:
        """Get training job by ID"""
        return await self._get_training_job(job_id)
    
    async def get_user_training_jobs(self, user_id: str) -> List[TrainingJob]:
        """Get all training jobs for a user"""
        return await self._get_user_training_jobs(user_id)
    
    async def cancel_training_job(self, job_id: str, user_id: str) -> bool:
        """
        Cancel a training job
        
        Args:
            job_id: Training job ID
            user_id: User identifier for authorization
            
        Returns:
            True if cancellation successful
        """
        try:
            training_job = await self._get_training_job(job_id)
            
            if not training_job:
                logger.warning(f"Training job {job_id} not found")
                return False
            
            if training_job.user_id != user_id:
                logger.warning(f"User {user_id} not authorized to cancel job {job_id}")
                return False
            
            if training_job.status not in [TrainingStatus.PENDING, TrainingStatus.SUBMITTED, TrainingStatus.RUNNING]:
                logger.warning(f"Cannot cancel job {job_id} in status {training_job.status}")
                return False
            
            # Cancel in Azure if submitted
            if training_job.status in [TrainingStatus.SUBMITTED, TrainingStatus.RUNNING]:
                azure_job_id = training_job.metadata.get("azure_job_id")
                if azure_job_id:
                    await self._cancel_azure_job(azure_job_id)
            
            # Update job status
            training_job.status = TrainingStatus.CANCELLED
            training_job.completed_at = datetime.utcnow()
            await self._store_training_job(training_job)
            
            # Send notification
            if self.notification_service:
                await self.notification_service.send_training_cancelled_notification(training_job)
            
            logger.info(f"Training job {job_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling training job {job_id}: {str(e)}")
            return False
    
    async def _validate_training_inputs(self, 
                                      audio_files: List[str],
                                      transcriptions: List[str],
                                      training_config: TrainingConfig) -> Tuple[bool, str]:
        """Validate training inputs"""
        # Check minimum utterances
        if len(audio_files) < training_config.min_utterances:
            return False, f"Insufficient audio files: {len(audio_files)} < {training_config.min_utterances}"
        
        # Check maximum utterances
        if len(audio_files) > training_config.max_utterances:
            return False, f"Too many audio files: {len(audio_files)} > {training_config.max_utterances}"
        
        # Check file count match
        if len(audio_files) != len(transcriptions):
            return False, f"Audio file count ({len(audio_files)}) doesn't match transcription count ({len(transcriptions)})"
        
        # Validate audio files exist and are accessible
        for audio_file in audio_files:
            if not await self._validate_audio_file(audio_file):
                return False, f"Invalid audio file: {audio_file}"
        
        # Validate transcription files exist and are accessible
        for transcription_file in transcriptions:
            if not await self._validate_transcription_file(transcription_file):
                return False, f"Invalid transcription file: {transcription_file}"
        
        return True, ""
    
    async def _validate_audio_file(self, file_path: str) -> bool:
        """Validate audio file exists and is accessible"""
        try:
            # Check if file exists in storage
            if self.storage_client:
                return await self.storage_client.file_exists(file_path)
            return True  # Assume valid if no storage client
        except Exception as e:
            logger.warning(f"Error validating audio file {file_path}: {str(e)}")
            return False
    
    async def _validate_transcription_file(self, file_path: str) -> bool:
        """Validate transcription file exists and is accessible"""
        try:
            # Check if file exists in storage
            if self.storage_client:
                return await self.storage_client.file_exists(file_path)
            return True  # Assume valid if no storage client
        except Exception as e:
            logger.warning(f"Error validating transcription file {file_path}: {str(e)}")
            return False
    
    async def _submit_to_azure_speech(self, 
                                    training_job: TrainingJob,
                                    training_config: TrainingConfig) -> Optional[str]:
        """Submit training job to Azure Speech Service"""
        try:
            # Prepare training data
            training_data = await self._prepare_training_data(training_job, training_config)
            
            # Create training request
            request_url = f"{self.endpoint}/speechtotext/v3.0/custom/neural/voices"
            
            request_body = {
                "name": training_job.voice_name,
                "description": training_config.description,
                "locale": training_config.language,
                "gender": training_config.gender,
                "trainingData": training_data,
                "properties": {
                    "crossLingual": training_config.cross_lingual,
                    "multilingual": training_config.multilingual,
                    "audioFormat": training_config.audio_format,
                    "sampleRate": training_config.sample_rate,
                    "channels": training_config.channels,
                    "bitDepth": training_config.bit_depth
                }
            }
            
            # Submit request
            response = requests.post(
                request_url,
                headers=self.headers,
                json=request_body
            )
            
            if response.status_code == 202:  # Accepted
                # Extract job ID from response headers
                location_header = response.headers.get('Location')
                if location_header:
                    azure_job_id = location_header.split('/')[-1]
                    return azure_job_id
                else:
                    logger.error("No Location header in response")
                    return None
            else:
                logger.error(f"Azure Speech Service error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error submitting to Azure Speech Service: {str(e)}")
            return None
    
    async def _prepare_training_data(self, 
                                   training_job: TrainingJob,
                                   training_config: TrainingConfig) -> Dict[str, any]:
        """Prepare training data for Azure submission"""
        training_data = {
            "audioFiles": [],
            "transcriptions": []
        }
        
        # Prepare audio files
        for audio_file in training_job.audio_files:
            audio_info = await self._get_audio_file_info(audio_file)
            training_data["audioFiles"].append({
                "fileName": audio_file.split('/')[-1],
                "filePath": audio_file,
                "duration": audio_info.get("duration", 0.0),
                "sampleRate": audio_info.get("sample_rate", training_config.sample_rate),
                "channels": audio_info.get("channels", training_config.channels),
                "bitDepth": audio_info.get("bit_depth", training_config.bit_depth)
            })
        
        # Prepare transcriptions
        for transcription_file in training_job.transcriptions:
            transcription_text = await self._get_transcription_text(transcription_file)
            training_data["transcriptions"].append({
                "fileName": transcription_file.split('/')[-1],
                "filePath": transcription_file,
                "text": transcription_text
            })
        
        return training_data
    
    async def _get_audio_file_info(self, file_path: str) -> Dict[str, any]:
        """Get audio file information"""
        try:
            if self.storage_client:
                # Get metadata from storage
                metadata = await self.storage_client.get_file_metadata(file_path)
                return metadata
            else:
                # Return default values
                return {
                    "duration": 10.0,
                    "sample_rate": 22050,
                    "channels": 1,
                    "bit_depth": 16
                }
        except Exception as e:
            logger.warning(f"Error getting audio file info for {file_path}: {str(e)}")
            return {}
    
    async def _get_transcription_text(self, file_path: str) -> str:
        """Get transcription text from file"""
        try:
            if self.storage_client:
                # Read transcription file
                content = await self.storage_client.read_file(file_path)
                return content.decode('utf-8').strip()
            else:
                # Return placeholder
                return "Transcription text"
        except Exception as e:
            logger.warning(f"Error reading transcription file {file_path}: {str(e)}")
            return ""
    
    async def _monitor_training_job(self, job_id: str):
        """Monitor training job progress"""
        try:
            while True:
                training_job = await self._get_training_job(job_id)
                
                if not training_job:
                    logger.error(f"Training job {job_id} not found during monitoring")
                    break
                
                # Check if job is complete
                if training_job.status in [TrainingStatus.SUCCEEDED, TrainingStatus.FAILED, TrainingStatus.CANCELLED]:
                    logger.info(f"Training job {job_id} completed with status {training_job.status}")
                    break
                
                # Update progress from Azure
                await self._update_job_progress(training_job)
                
                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
        except Exception as e:
            logger.error(f"Error monitoring training job {job_id}: {str(e)}")
    
    async def _update_job_progress(self, training_job: TrainingJob):
        """Update job progress from Azure Speech Service"""
        try:
            azure_job_id = training_job.metadata.get("azure_job_id")
            if not azure_job_id:
                return
            
            # Get job status from Azure
            request_url = f"{self.endpoint}/speechtotext/v3.0/custom/neural/voices/{azure_job_id}"
            response = requests.get(request_url, headers=self.headers)
            
            if response.status_code == 200:
                job_data = response.json()
                
                # Update job status
                azure_status = job_data.get("status", "Unknown")
                training_job.status = self._map_azure_status(azure_status)
                
                # Update progress
                if "progress" in job_data:
                    training_job.progress_percentage = job_data["progress"]
                
                # Update timestamps
                if azure_status == "Running" and not training_job.started_at:
                    training_job.started_at = datetime.utcnow()
                
                if azure_status in ["Succeeded", "Failed"] and not training_job.completed_at:
                    training_job.completed_at = datetime.utcnow()
                
                # Extract model and voice IDs if successful
                if azure_status == "Succeeded":
                    training_job.model_id = job_data.get("modelId")
                    training_job.voice_id = job_data.get("voiceId")
                
                # Store updated job
                await self._store_training_job(training_job)
                
                # Send notifications
                if self.notification_service:
                    if training_job.status == TrainingStatus.SUCCEEDED:
                        await self.notification_service.send_training_completed_notification(training_job)
                    elif training_job.status == TrainingStatus.FAILED:
                        await self.notification_service.send_training_failed_notification(training_job)
                
        except Exception as e:
            logger.error(f"Error updating job progress: {str(e)}")
    
    def _map_azure_status(self, azure_status: str) -> TrainingStatus:
        """Map Azure status to internal status"""
        status_mapping = {
            "NotStarted": TrainingStatus.PENDING,
            "Running": TrainingStatus.RUNNING,
            "Succeeded": TrainingStatus.SUCCEEDED,
            "Failed": TrainingStatus.FAILED,
            "Cancelled": TrainingStatus.CANCELLED
        }
        
        return status_mapping.get(azure_status, TrainingStatus.PENDING)
    
    async def _cancel_azure_job(self, azure_job_id: str) -> bool:
        """Cancel job in Azure Speech Service"""
        try:
            request_url = f"{self.endpoint}/speechtotext/v3.0/custom/neural/voices/{azure_job_id}"
            response = requests.delete(request_url, headers=self.headers)
            
            return response.status_code in [200, 202, 204]
            
        except Exception as e:
            logger.error(f"Error cancelling Azure job {azure_job_id}: {str(e)}")
            return False
    
    async def _store_training_job(self, training_job: TrainingJob):
        """Store training job in storage"""
        if self.storage_client:
            await self.storage_client.store_training_job(training_job)
    
    async def _get_training_job(self, job_id: str) -> Optional[TrainingJob]:
        """Get training job from storage"""
        if self.storage_client:
            return await self.storage_client.get_training_job(job_id)
        return None
    
    async def _get_user_training_jobs(self, user_id: str) -> List[TrainingJob]:
        """Get user training jobs from storage"""
        if self.storage_client:
            return await self.storage_client.get_user_training_jobs(user_id)
        return []
    
    def get_training_requirements(self) -> Dict[str, any]:
        """Get training requirements and recommendations"""
        return {
            "minimum_utterances": 300,
            "recommended_utterances": 1000,
            "minimum_duration": 30,  # minutes
            "recommended_duration": 180,  # minutes
            "audio_formats": ["wav", "mp3", "flac"],
            "sample_rates": [16000, 22050, 44100],
            "channels": [1, 2],
            "bit_depths": [16, 24],
            "quality_thresholds": {
                "min_snr_db": 15.0,
                "max_clipping_percent": 5.0,
                "min_confidence": 0.7
            },
            "supported_languages": [
                "en-US", "en-GB", "en-AU", "de-DE", "fr-FR", "es-ES", "it-IT",
                "ja-JP", "ko-KR", "zh-CN", "pt-BR", "ru-RU"
            ]
        }
