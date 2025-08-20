from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid
import logging
import io
import tempfile
import os

from ..services.voice_selection import VoiceSelector
from ..services.text_processing import TextProcessor
from ..services.audio_synthesis import AudioSynthesizer
from ..services.translation_service import AzureTranslatorService
from ..models.database import VoiceModel, SynthesisJob, User
from ..database import get_db
from ..auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/synthesis", tags=["Voice Synthesis"])

# Security
security = HTTPBearer()

# Pydantic models for API requests/responses
class SynthesisRequest(BaseModel):
    text: str
    voice_id: str
    language: Optional[str] = "en-US"
    speed: Optional[float] = 1.0
    pitch: Optional[float] = 1.0
    volume: Optional[float] = 1.0
    format: Optional[str] = "wav"
    ssml: Optional[bool] = False
    prosody: Optional[Dict[str, Any]] = None

class SynthesisResponse(BaseModel):
    synthesis_id: str
    status: str
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    word_count: int
    created_at: datetime
    estimated_completion: Optional[datetime] = None

class BatchSynthesisRequest(BaseModel):
    texts: List[str]
    voice_id: str
    language: Optional[str] = "en-US"
    speed: Optional[float] = 1.0
    pitch: Optional[float] = 1.0
    volume: Optional[float] = 1.0
    format: Optional[str] = "wav"
    priority: Optional[str] = "normal"  # low, normal, high

class BatchSynthesisResponse(BaseModel):
    job_id: str
    total_texts: int
    status: str
    message: str
    estimated_completion: Optional[datetime] = None

class SynthesisJobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    completed_count: int
    total_count: int
    results: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class AudioFormatConversionRequest(BaseModel):
    audio_url: str
    target_format: str  # wav, mp3, ogg, flac
    quality: Optional[str] = "high"  # low, medium, high
    sample_rate: Optional[int] = None
    bit_depth: Optional[int] = None

class AudioFormatConversionResponse(BaseModel):
    conversion_id: str
    original_format: str
    target_format: str
    original_url: str
    converted_url: str
    file_size: int
    duration: float
    quality: str
    created_at: datetime

# Initialize services
voice_selector = VoiceSelector({})
text_processor = TextProcessor({})
audio_synthesizer = AudioSynthesizer({})
translator_service = AzureTranslatorService({})

@router.post("/speak", response_model=SynthesisResponse, status_code=status.HTTP_202_ACCEPTED)
async def synthesize_speech(
    request: SynthesisRequest,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Real-time text-to-speech synthesis endpoint
    """
    try:
        logger.info(f"Starting speech synthesis for user {current_user.id}")
        
        # Validate input
        if not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty"
            )
        
        if not request.voice_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voice ID is required"
            )
        
        # Validate parameters
        if not (0.5 <= request.speed <= 2.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Speed must be between 0.5 and 2.0"
            )
        
        if not (0.5 <= request.pitch <= 2.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pitch must be between 0.5 and 2.0"
            )
        
        if not (0.0 <= request.volume <= 1.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Volume must be between 0.0 and 1.0"
            )
        
        # Check voice availability
        is_available, error_message = await voice_selector.check_voice_availability(request.voice_id)
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Voice not available: {error_message}"
            )
        
        # Process text
        processed_text = text_processor.preprocess_text(request.text)
        word_count = len(processed_text.split())
        
        # Generate SSML if requested
        if request.ssml:
            ssml_text = text_processor.generate_ssml(
                text=processed_text,
                voice_name=request.voice_id,
                language=request.language,
                prosody=request.prosody
            )
            # Validate SSML
            is_valid, errors = text_processor.validate_ssml(ssml_text)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid SSML: {', '.join(errors)}"
                )
            processed_text = ssml_text
        
        # Create synthesis request
        synthesis_request = {
            "text": processed_text,
            "voice_id": request.voice_id,
            "language": request.language,
            "speed": request.speed,
            "pitch": request.pitch,
            "volume": request.volume,
            "format": request.format,
            "ssml": request.ssml
        }
        
        # Start synthesis
        synthesis_result = await audio_synthesizer.synthesize_text(synthesis_request)
        
        if synthesis_result.status == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Synthesis failed: {synthesis_result.error_message}"
            )
        
        # Create synthesis record
        synthesis_id = str(uuid.uuid4())
        synthesis_job = SynthesisJob(
            id=synthesis_id,
            user_id=current_user.id,
            voice_id=request.voice_id,
            text=request.text,
            language=request.language,
            status="completed",
            audio_url=synthesis_result.audio_url,
            duration=synthesis_result.duration,
            word_count=word_count,
            format=request.format,
            settings=request.dict(),
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        # In real implementation, save to database
        # db.add(synthesis_job)
        # db.commit()
        
        # Update voice usage statistics
        await voice_selector.update_voice_usage(request.voice_id)
        
        logger.info(f"Speech synthesis completed successfully: {synthesis_id}")
        
        return SynthesisResponse(
            synthesis_id=synthesis_id,
            status="completed",
            audio_url=synthesis_result.audio_url,
            duration=synthesis_result.duration,
            word_count=word_count,
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in speech synthesis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Speech synthesis failed"
        )

@router.post("/speak/stream")
async def synthesize_speech_stream(
    request: SynthesisRequest,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Streaming text-to-speech synthesis endpoint
    """
    try:
        logger.info(f"Starting streaming speech synthesis for user {current_user.id}")
        
        # Validate input (same as regular synthesis)
        if not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty"
            )
        
        # Process text
        processed_text = text_processor.preprocess_text(request.text)
        
        # Create synthesis request for streaming
        synthesis_request = {
            "text": processed_text,
            "voice_id": request.voice_id,
            "language": request.language,
            "speed": request.speed,
            "pitch": request.pitch,
            "volume": request.volume,
            "format": request.format,
            "ssml": request.ssml,
            "streaming": True
        }
        
        # Start streaming synthesis
        async def audio_stream():
            try:
                async for chunk in audio_synthesizer.synthesize_text_streaming(synthesis_request):
                    if chunk.audio_data:
                        yield chunk.audio_data
                    if chunk.status == "completed":
                        break
            except Exception as e:
                logger.error(f"Streaming synthesis error: {str(e)}")
                yield b""  # Send empty chunk on error
        
        # Return streaming response
        return StreamingResponse(
            audio_stream(),
            media_type=f"audio/{request.format}",
            headers={
                "Content-Disposition": f"attachment; filename=synthesis_{uuid.uuid4()}.{request.format}",
                "Cache-Control": "no-cache",
                "X-Synthesis-Status": "streaming"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in streaming speech synthesis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Streaming speech synthesis failed"
        )

@router.post("/batch", response_model=BatchSynthesisResponse, status_code=status.HTTP_202_ACCEPTED)
async def batch_synthesis(
    request: BatchSynthesisRequest,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Batch text-to-speech synthesis endpoint
    """
    try:
        logger.info(f"Starting batch synthesis for user {current_user.id}")
        
        # Validate input
        if not request.texts or len(request.texts) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one text is required"
            )
        
        if len(request.texts) > 100:  # Limit batch size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 texts allowed per batch"
            )
        
        # Check voice availability
        is_available, error_message = await voice_selector.check_voice_availability(request.voice_id)
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Voice not available: {error_message}"
            )
        
        # Create batch synthesis job
        job_id = str(uuid.uuid4())
        batch_job = SynthesisJob(
            id=job_id,
            user_id=current_user.id,
            voice_id=request.voice_id,
            text="",  # Will be populated with individual texts
            language=request.language,
            status="submitted",
            batch_size=len(request.texts),
            priority=request.priority,
            settings=request.dict(),
            created_at=datetime.utcnow()
        )
        
        # In real implementation, save to database
        # db.add(batch_job)
        # db.commit()
        
        # Start batch processing asynchronously
        # This would typically be handled by a background worker
        # For now, we'll simulate the process
        
        logger.info(f"Batch synthesis job {job_id} created successfully")
        
        return BatchSynthesisResponse(
            job_id=job_id,
            total_texts=len(request.texts),
            status="submitted",
            message="Batch synthesis job submitted successfully",
            estimated_completion=datetime.utcnow()  # In real implementation, calculate based on batch size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating batch synthesis job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create batch synthesis job"
        )

@router.get("/batch/{job_id}", response_model=SynthesisJobStatus)
async def get_batch_synthesis_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get batch synthesis job status
    """
    try:
        logger.info(f"Getting batch synthesis status for job {job_id}")
        
        # In real implementation, fetch from database
        # batch_job = db.query(SynthesisJob).filter(
        #     SynthesisJob.id == job_id,
        #     SynthesisJob.user_id == current_user.id
        # ).first()
        
        # Mock batch job for demonstration
        batch_job = SynthesisJob(
            id=job_id,
            user_id=current_user.id,
            voice_id="voice-1",
            text="",
            language="en-US",
            status="processing",
            batch_size=10,
            priority="normal",
            settings={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if not batch_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch synthesis job not found"
            )
        
        # Mock results
        mock_results = [
            {
                "text": f"Sample text {i}",
                "status": "completed" if i < 7 else "processing",
                "audio_url": f"https://example.com/audio_{i}.wav" if i < 7 else None,
                "duration": 2.5 if i < 7 else None,
                "error": None
            }
            for i in range(1, 11)
        ]
        
        completed_count = sum(1 for r in mock_results if r["status"] == "completed")
        progress = (completed_count / len(mock_results)) * 100
        
        return SynthesisJobStatus(
            job_id=job_id,
            status=batch_job.status,
            progress=progress,
            completed_count=completed_count,
            total_count=len(mock_results),
            results=mock_results,
            created_at=batch_job.created_at,
            updated_at=batch_job.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch synthesis status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get batch synthesis status"
        )

@router.post("/convert-audio", response_model=AudioFormatConversionResponse)
async def convert_audio_format(
    request: AudioFormatConversionRequest,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Convert audio format and quality
    """
    try:
        logger.info(f"Converting audio format for user {current_user.id}")
        
        # Validate input
        supported_formats = ["wav", "mp3", "ogg", "flac"]
        if request.target_format not in supported_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported target format. Supported: {', '.join(supported_formats)}"
            )
        
        # Validate quality
        valid_qualities = ["low", "medium", "high"]
        if request.quality not in valid_qualities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid quality. Valid options: {', '.join(valid_qualities)}"
            )
        
        # In real implementation, download audio file and convert
        # For now, we'll simulate the conversion
        
        conversion_id = str(uuid.uuid4())
        
        # Mock conversion result
        converted_url = f"https://example.com/converted_{conversion_id}.{request.target_format}"
        
        logger.info(f"Audio format conversion completed: {conversion_id}")
        
        return AudioFormatConversionResponse(
            conversion_id=conversion_id,
            original_format="wav",  # Would be detected from original file
            target_format=request.target_format,
            original_url=request.audio_url,
            converted_url=converted_url,
            file_size=1024000,  # Mock file size
            duration=30.5,  # Mock duration
            quality=request.quality,
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting audio format: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audio format conversion failed"
        )

@router.get("/history")
async def get_synthesis_history(
    page: int = 1,
    page_size: int = 20,
    voice_id: Optional[str] = None,
    language: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get user's synthesis history with filtering and pagination
    """
    try:
        logger.info(f"Getting synthesis history for user {current_user.id}")
        
        # In real implementation, fetch from database with filters
        # query = db.query(SynthesisJob).filter(SynthesisJob.user_id == current_user.id)
        
        # if voice_id:
        #     query = query.filter(SynthesisJob.voice_id == voice_id)
        # if language:
        #     query = query.filter(SynthesisJob.language == language)
        # if date_from:
        #     query = query.filter(SynthesisJob.created_at >= date_from)
        # if date_to:
        #     query = query.filter(SynthesisJob.created_at <= date_to)
        
        # total_count = query.count()
        # history = query.order_by(SynthesisJob.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        # Mock history for demonstration
        mock_history = [
            {
                "id": f"synth-{i}",
                "voice_id": "voice-1",
                "text": f"Sample synthesis text {i}",
                "language": "en-US",
                "status": "completed",
                "audio_url": f"https://example.com/audio_{i}.wav",
                "duration": 2.5 + i * 0.5,
                "word_count": 10 + i * 2,
                "format": "wav",
                "created_at": datetime.utcnow()
            }
            for i in range(1, 21)
        ]
        
        # Apply filters
        if voice_id:
            mock_history = [h for h in mock_history if h["voice_id"] == voice_id]
        if language:
            mock_history = [h for h in mock_history if h["language"] == language]
        
        total_count = len(mock_history)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_history = mock_history[start_idx:end_idx]
        
        return {
            "history": paginated_history,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
        
    except Exception as e:
        logger.error(f"Error getting synthesis history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get synthesis history"
        )

@router.get("/statistics")
async def get_synthesis_statistics(
    period: str = "30d",  # 7d, 30d, 90d, 1y
    voice_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get synthesis statistics for the user
    """
    try:
        logger.info(f"Getting synthesis statistics for user {current_user.id}")
        
        # In real implementation, calculate from database
        # This would involve complex queries and aggregations
        
        # Mock statistics for demonstration
        mock_stats = {
            "total_synthesis": 156,
            "total_duration": 7200.5,  # seconds
            "total_words": 3120,
            "average_duration": 46.2,  # seconds per synthesis
            "most_used_voice": "voice-1",
            "language_distribution": {
                "en-US": 120,
                "es-ES": 25,
                "fr-FR": 11
            },
            "format_distribution": {
                "wav": 89,
                "mp3": 45,
                "ogg": 22
            },
            "daily_average": 5.2,
            "peak_usage_day": "2024-01-15",
            "peak_usage_count": 12
        }
        
        return mock_stats
        
    except Exception as e:
        logger.error(f"Error getting synthesis statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get synthesis statistics"
        )

@router.delete("/history/{synthesis_id}")
async def delete_synthesis_history(
    synthesis_id: str,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a synthesis history record
    """
    try:
        logger.info(f"Deleting synthesis history {synthesis_id}")
        
        # In real implementation, fetch and delete from database
        # synthesis_record = db.query(SynthesisJob).filter(
        #     SynthesisJob.id == synthesis_id,
        #     SynthesisJob.user_id == current_user.id
        # ).first()
        
        # if not synthesis_record:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Synthesis record not found"
        #     )
        
        # db.delete(synthesis_record)
        # db.commit()
        
        # Also delete associated audio file from storage
        
        logger.info(f"Synthesis history {synthesis_id} deleted successfully")
        
        return {
            "synthesis_id": synthesis_id,
            "message": "Synthesis history deleted successfully",
            "deleted_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting synthesis history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete synthesis history"
        )
