from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import logging

from ..services.consent_management import ConsentManager
from ..services.audio_processing import AudioProcessor
from ..services.speech_to_text import SpeechToTextService
from ..services.cnv_training_orchestration import CNVTrainingService
from ..services.voice_selection import VoiceSelector
from ..models.database import VoiceModel, TrainingJob, User
from ..database import get_db
from ..auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/voices", tags=["Voice Management"])

# Security
security = HTTPBearer()

# Pydantic models for API requests/responses
class VoiceTrainingRequest(BaseModel):
    name: str
    language: str
    gender: Optional[str] = "neutral"
    description: Optional[str] = None
    audio_files: List[str]  # List of audio file URLs
    training_config: Optional[dict] = None

class VoiceTrainingResponse(BaseModel):
    job_id: str
    voice_id: str
    status: str
    message: str
    estimated_completion: Optional[datetime] = None

class VoiceStatusResponse(BaseModel):
    voice_id: str
    name: str
    status: str
    language: str
    gender: str
    quality: str
    training_progress: Optional[float] = None
    created_at: datetime
    last_updated: datetime
    total_synthesis: int
    total_duration: float
    metadata: dict

class VoiceListResponse(BaseModel):
    voices: List[VoiceStatusResponse]
    total_count: int
    page: int
    page_size: int

class VoiceUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class VoiceDeleteResponse(BaseModel):
    voice_id: str
    message: str
    deleted_at: datetime

# Initialize services
consent_manager = ConsentManager()
audio_processor = AudioProcessor({})
speech_to_text = SpeechToTextService({})
cnv_training = CNVTrainingService({})
voice_selector = VoiceSelector({})

@router.post("/train", response_model=VoiceTrainingResponse, status_code=status.HTTP_202_ACCEPTED)
async def train_voice(
    request: VoiceTrainingRequest,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Start training a new custom voice model
    """
    try:
        logger.info(f"Starting voice training for user {current_user.id}")
        
        # Verify user consent for voice cloning
        has_consent, consent_record = consent_manager.verify_consent(
            current_user.id, 
            consent_manager.ConsentType.VOICE_CLONING
        )
        
        if not has_consent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voice cloning consent not provided or expired"
            )
        
        # Validate audio files
        if not request.audio_files or len(request.audio_files) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 3 audio files are required for training"
            )
        
        # Create voice model record
        voice_id = str(uuid.uuid4())
        voice_model = VoiceModel(
            id=voice_id,
            user_id=current_user.id,
            name=request.name,
            language=request.language,
            gender=request.gender,
            description=request.description,
            status="training",
            quality="pending",
            training_progress=0.0,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            total_synthesis=0,
            total_duration=0.0,
            metadata=request.training_config or {}
        )
        
        # Create training job
        job_id = str(uuid.uuid4())
        training_job = TrainingJob(
            id=job_id,
            voice_id=voice_id,
            user_id=current_user.id,
            status="submitted",
            audio_files=request.audio_files,
            training_config=request.training_config or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database (simplified - in real implementation, use proper DB session)
        # db.add(voice_model)
        # db.add(training_job)
        # db.commit()
        
        # Start training process asynchronously
        await cnv_training.create_training_job(
            user_id=current_user.id,
            audio_files=request.audio_files,
            transcriptions=[],  # Will be generated during training
            training_config=request.training_config or {}
        )
        
        logger.info(f"Voice training job {job_id} created successfully for voice {voice_id}")
        
        return VoiceTrainingResponse(
            job_id=job_id,
            voice_id=voice_id,
            status="submitted",
            message="Voice training job submitted successfully",
            estimated_completion=datetime.utcnow()  # In real implementation, calculate based on audio length
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating voice training job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create voice training job"
        )

@router.get("/{voice_id}", response_model=VoiceStatusResponse)
async def get_voice_status(
    voice_id: str,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get the status and details of a specific voice model
    """
    try:
        logger.info(f"Getting voice status for voice {voice_id}")
        
        # In real implementation, fetch from database
        # voice_model = db.query(VoiceModel).filter(
        #     VoiceModel.id == voice_id,
        #     VoiceModel.user_id == current_user.id
        # ).first()
        
        # Mock voice model for demonstration
        voice_model = VoiceModel(
            id=voice_id,
            user_id=current_user.id,
            name="Sample Voice",
            language="en-US",
            gender="neutral",
            status="ready",
            quality="high",
            training_progress=100.0,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            total_synthesis=25,
            total_duration=1200.0,
            metadata={"accent": "neutral", "age_group": "adult"}
        )
        
        if not voice_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice model not found"
            )
        
        # Check if user owns this voice model
        if voice_model.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this voice model"
            )
        
        return VoiceStatusResponse(
            voice_id=voice_model.id,
            name=voice_model.name,
            status=voice_model.status,
            language=voice_model.language,
            gender=voice_model.gender,
            quality=voice_model.quality,
            training_progress=voice_model.training_progress,
            created_at=voice_model.created_at,
            last_updated=voice_model.last_updated,
            total_synthesis=voice_model.total_synthesis,
            total_duration=voice_model.total_duration,
            metadata=voice_model.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get voice status"
        )

@router.get("/", response_model=VoiceListResponse)
async def list_user_voices(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    language_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    List all voice models for the current user with pagination and filtering
    """
    try:
        logger.info(f"Listing voices for user {current_user.id}")
        
        # In real implementation, fetch from database with filters
        # query = db.query(VoiceModel).filter(VoiceModel.user_id == current_user.id)
        
        # if status_filter:
        #     query = query.filter(VoiceModel.status == status_filter)
        # if language_filter:
        #     query = query.filter(VoiceModel.language == language_filter)
        
        # total_count = query.count()
        # voices = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # Mock voices for demonstration
        mock_voices = [
            VoiceModel(
                id="voice-1",
                user_id=current_user.id,
                name="John's Voice",
                language="en-US",
                gender="male",
                status="ready",
                quality="high",
                training_progress=100.0,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                total_synthesis=45,
                total_duration=1800.0,
                metadata={"accent": "american", "age_group": "adult"}
            ),
            VoiceModel(
                id="voice-2",
                user_id=current_user.id,
                name="Sarah's Voice",
                language="en-US",
                gender="female",
                status="training",
                quality="high",
                training_progress=75.0,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                total_synthesis=12,
                total_duration=480.0,
                metadata={"accent": "british", "age_group": "young_adult"}
            )
        ]
        
        # Apply filters
        if status_filter:
            mock_voices = [v for v in mock_voices if v.status == status_filter]
        if language_filter:
            mock_voices = [v for v in mock_voices if v.language == language_filter]
        
        total_count = len(mock_voices)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_voices = mock_voices[start_idx:end_idx]
        
        voice_responses = [
            VoiceStatusResponse(
                voice_id=voice.id,
                name=voice.name,
                status=voice.status,
                language=voice.language,
                gender=voice.gender,
                quality=voice.quality,
                training_progress=voice.training_progress,
                created_at=voice.created_at,
                last_updated=voice.last_updated,
                total_synthesis=voice.total_synthesis,
                total_duration=voice.total_duration,
                metadata=voice.metadata
            )
            for voice in paginated_voices
        ]
        
        return VoiceListResponse(
            voices=voice_responses,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list voices"
        )

@router.put("/{voice_id}", response_model=VoiceStatusResponse)
async def update_voice(
    voice_id: str,
    request: VoiceUpdateRequest,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update voice model metadata and settings
    """
    try:
        logger.info(f"Updating voice {voice_id}")
        
        # In real implementation, fetch and update in database
        # voice_model = db.query(VoiceModel).filter(
        #     VoiceModel.id == voice_id,
        #     VoiceModel.user_id == current_user.id
        # ).first()
        
        # Mock voice model for demonstration
        voice_model = VoiceModel(
            id=voice_id,
            user_id=current_user.id,
            name="Sample Voice",
            language="en-US",
            gender="neutral",
            status="ready",
            quality="high",
            training_progress=100.0,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            total_synthesis=25,
            total_duration=1200.0,
            metadata={"accent": "neutral", "age_group": "adult"}
        )
        
        if not voice_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice model not found"
            )
        
        # Check if user owns this voice model
        if voice_model.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this voice model"
            )
        
        # Update fields
        if request.name is not None:
            voice_model.name = request.name
        if request.description is not None:
            voice_model.description = request.description
        if request.is_active is not None:
            voice_model.is_active = request.is_active
        
        voice_model.last_updated = datetime.utcnow()
        
        # In real implementation, save to database
        # db.commit()
        
        return VoiceStatusResponse(
            voice_id=voice_model.id,
            name=voice_model.name,
            status=voice_model.status,
            language=voice_model.language,
            gender=voice_model.gender,
            quality=voice_model.quality,
            training_progress=voice_model.training_progress,
            created_at=voice_model.created_at,
            last_updated=voice_model.last_updated,
            total_synthesis=voice_model.total_synthesis,
            total_duration=voice_model.total_duration,
            metadata=voice_model.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating voice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update voice"
        )

@router.delete("/{voice_id}", response_model=VoiceDeleteResponse)
async def delete_voice(
    voice_id: str,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a voice model and all associated data
    """
    try:
        logger.info(f"Deleting voice {voice_id}")
        
        # In real implementation, fetch from database
        # voice_model = db.query(VoiceModel).filter(
        #     VoiceModel.id == voice_id,
        #     VoiceModel.user_id == current_user.id
        # ).first()
        
        # Mock voice model for demonstration
        voice_model = VoiceModel(
            id=voice_id,
            user_id=current_user.id,
            name="Sample Voice",
            language="en-US",
            gender="neutral",
            status="ready",
            quality="high",
            training_progress=100.0,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            total_synthesis=25,
            total_duration=1200.0,
            metadata={}
        )
        
        if not voice_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice model not found"
            )
        
        # Check if user owns this voice model
        if voice_model.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this voice model"
            )
        
        # Check if voice is currently in use
        if voice_model.total_synthesis > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete voice model that has been used for synthesis"
            )
        
        # In real implementation, delete from database and cleanup associated files
        # db.delete(voice_model)
        # db.commit()
        
        # Cleanup training jobs, audio files, etc.
        
        logger.info(f"Voice {voice_id} deleted successfully")
        
        return VoiceDeleteResponse(
            voice_id=voice_id,
            message="Voice model deleted successfully",
            deleted_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting voice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete voice"
        )

@router.get("/{voice_id}/training-status")
async def get_training_status(
    voice_id: str,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get detailed training status for a voice model
    """
    try:
        logger.info(f"Getting training status for voice {voice_id}")
        
        # In real implementation, fetch training job from database
        # training_job = db.query(TrainingJob).filter(
        #     TrainingJob.voice_id == voice_id,
        #     TrainingJob.user_id == current_user.id
        # ).order_by(TrainingJob.created_at.desc()).first()
        
        # Mock training job for demonstration
        training_job = TrainingJob(
            id="job-1",
            voice_id=voice_id,
            user_id=current_user.id,
            status="training",
            audio_files=["audio1.wav", "audio2.wav"],
            training_config={"epochs": 100, "batch_size": 32},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if not training_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training job not found"
            )
        
        # Get detailed status from CNV training service
        job_status = await cnv_training.get_training_job(training_job.id)
        
        if not job_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training job status not found"
            )
        
        return {
            "job_id": training_job.id,
            "voice_id": voice_id,
            "status": job_status.status,
            "progress": job_status.progress,
            "current_step": job_status.current_step,
            "estimated_completion": job_status.estimated_completion,
            "audio_files_count": len(training_job.audio_files),
            "training_config": training_job.training_config,
            "created_at": training_job.created_at,
            "updated_at": training_job.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting training status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get training status"
        )

@router.post("/{voice_id}/cancel-training")
async def cancel_training(
    voice_id: str,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Cancel an ongoing voice training job
    """
    try:
        logger.info(f"Cancelling training for voice {voice_id}")
        
        # In real implementation, fetch training job from database
        # training_job = db.query(TrainingJob).filter(
        #     TrainingJob.voice_id == voice_id,
        #     TrainingJob.user_id == current_user.id,
        #     TrainingJob.status.in_(["submitted", "training"])
        # ).first()
        
        # Mock training job for demonstration
        training_job = TrainingJob(
            id="job-1",
            voice_id=voice_id,
            user_id=current_user.id,
            status="training",
            audio_files=["audio1.wav", "audio2.wav"],
            training_config={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if not training_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active training job not found"
            )
        
        # Cancel training job
        success = await cnv_training.cancel_training_job(training_job.id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel training job"
            )
        
        # Update voice model status
        # voice_model = db.query(VoiceModel).filter(VoiceModel.id == voice_id).first()
        # voice_model.status = "cancelled"
        # voice_model.last_updated = datetime.utcnow()
        # db.commit()
        
        logger.info(f"Training cancelled successfully for voice {voice_id}")
        
        return {
            "voice_id": voice_id,
            "job_id": training_job.id,
            "message": "Training job cancelled successfully",
            "cancelled_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling training: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel training"
        )
