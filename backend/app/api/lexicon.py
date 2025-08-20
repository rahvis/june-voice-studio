from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid
import logging
import json

from ..services.text_processing import TextProcessor
from ..services.translation_service import AzureTranslatorService
from ..models.database import LexiconEntry, User
from ..database import get_db
from ..auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/lexicon", tags=["Lexicon Management"])

# Security
security = HTTPBearer()

# Pydantic models for API requests/responses
class LexiconEntryRequest(BaseModel):
    word: str
    pronunciation: str
    language: str
    part_of_speech: Optional[str] = None
    definition: Optional[str] = None
    context: Optional[str] = None
    priority: Optional[str] = "normal"  # low, normal, high
    is_active: Optional[bool] = True

class LexiconEntryResponse(BaseModel):
    id: str
    word: str
    pronunciation: str
    language: str
    part_of_speech: Optional[str] = None
    definition: Optional[str] = None
    context: Optional[str] = None
    priority: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    usage_count: int

class LexiconListResponse(BaseModel):
    entries: List[LexiconEntryResponse]
    total_count: int
    page: int
    page_size: int

class LexiconUpdateRequest(BaseModel):
    pronunciation: Optional[str] = None
    part_of_speech: Optional[str] = None
    definition: Optional[str] = None
    context: Optional[str] = None
    priority: Optional[str] = None
    is_active: Optional[bool] = None

class LexiconBulkUploadRequest(BaseModel):
    language: str
    entries: List[Dict[str, Any]]
    overwrite_existing: Optional[bool] = False

class LexiconBulkUploadResponse(BaseModel):
    upload_id: str
    total_entries: int
    successful_entries: int
    failed_entries: int
    errors: List[Dict[str, Any]]
    created_at: datetime

class LexiconValidationRequest(BaseModel):
    text: str
    language: str
    voice_id: Optional[str] = None

class LexiconValidationResponse(BaseModel):
    text: str
    language: str
    total_words: int
    matched_entries: int
    unmatched_words: List[str]
    suggestions: List[Dict[str, Any]]
    validation_score: float

class LexiconExportRequest(BaseModel):
    language: str
    format: str = "json"  # json, csv, xml
    include_inactive: Optional[bool] = False
    filters: Optional[Dict[str, Any]] = None

# Initialize services
text_processor = TextProcessor({})
translator_service = AzureTranslatorService({})

@router.post("/", response_model=LexiconEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_lexicon_entry(
    request: LexiconEntryRequest,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new lexicon entry for custom pronunciation
    """
    try:
        logger.info(f"Creating lexicon entry for user {current_user.id}")
        
        # Validate input
        if not request.word.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Word cannot be empty"
            )
        
        if not request.pronunciation.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pronunciation cannot be empty"
            )
        
        if not request.language:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Language is required"
            )
        
        # Validate language support
        supported_languages = text_processor.get_supported_languages()
        language_codes = [lang["code"] for lang in supported_languages]
        
        if request.language not in language_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language. Supported: {', '.join(language_codes[:10])}"
            )
        
        # Validate priority
        valid_priorities = ["low", "normal", "high"]
        if request.priority not in valid_priorities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority. Valid options: {', '.join(valid_priorities)}"
            )
        
        # Check if entry already exists
        # In real implementation, check database
        # existing_entry = db.query(LexiconEntry).filter(
        #     LexiconEntry.word == request.word,
        #     LexiconEntry.language == request.language,
        #     LexiconEntry.user_id == current_user.id
        # ).first()
        
        # if existing_entry:
        #     raise HTTPException(
        #         status_code=status.HTTP_409_CONFLICT,
        #         detail="Lexicon entry already exists for this word and language"
        #     )
        
        # Create lexicon entry
        entry_id = str(uuid.uuid4())
        lexicon_entry = LexiconEntry(
            id=entry_id,
            user_id=current_user.id,
            word=request.word.strip().lower(),
            pronunciation=request.pronunciation.strip(),
            language=request.language,
            part_of_speech=request.part_of_speech,
            definition=request.definition,
            context=request.context,
            priority=request.priority,
            is_active=request.is_active,
            usage_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # In real implementation, save to database
        # db.add(lexicon_entry)
        # db.commit()
        
        logger.info(f"Lexicon entry {entry_id} created successfully")
        
        return LexiconEntryResponse(
            id=lexicon_entry.id,
            word=lexicon_entry.word,
            pronunciation=lexicon_entry.pronunciation,
            language=lexicon_entry.language,
            part_of_speech=lexicon_entry.part_of_speech,
            definition=lexicon_entry.definition,
            context=lexicon_entry.context,
            priority=lexicon_entry.priority,
            is_active=lexicon_entry.is_active,
            created_at=lexicon_entry.created_at,
            updated_at=lexicon_entry.updated_at,
            usage_count=lexicon_entry.usage_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating lexicon entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lexicon entry"
        )

@router.get("/{entry_id}", response_model=LexiconEntryResponse)
async def get_lexicon_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get a specific lexicon entry
    """
    try:
        logger.info(f"Getting lexicon entry {entry_id}")
        
        # In real implementation, fetch from database
        # lexicon_entry = db.query(LexiconEntry).filter(
        #     LexiconEntry.id == entry_id,
        #     LexiconEntry.user_id == current_user.id
        # ).first()
        
        # Mock lexicon entry for demonstration
        lexicon_entry = LexiconEntry(
            id=entry_id,
            user_id=current_user.id,
            word="example",
            pronunciation="ɪɡˈzæmpəl",
            language="en-US",
            part_of_speech="noun",
            definition="A representative form or pattern",
            context="This is an example sentence.",
            priority="normal",
            is_active=True,
            usage_count=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if not lexicon_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lexicon entry not found"
            )
        
        # Check if user owns this entry
        if lexicon_entry.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this lexicon entry"
            )
        
        return LexiconEntryResponse(
            id=lexicon_entry.id,
            word=lexicon_entry.word,
            pronunciation=lexicon_entry.pronunciation,
            language=lexicon_entry.language,
            part_of_speech=lexicon_entry.part_of_speech,
            definition=lexicon_entry.definition,
            context=lexicon_entry.context,
            priority=lexicon_entry.priority,
            is_active=lexicon_entry.is_active,
            created_at=lexicon_entry.created_at,
            updated_at=lexicon_entry.updated_at,
            usage_count=lexicon_entry.usage_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lexicon entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get lexicon entry"
        )

@router.get("/", response_model=LexiconListResponse)
async def list_lexicon_entries(
    page: int = 1,
    page_size: int = 20,
    language: Optional[str] = None,
    word_filter: Optional[str] = None,
    part_of_speech: Optional[str] = None,
    priority: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    List lexicon entries with filtering and pagination
    """
    try:
        logger.info(f"Listing lexicon entries for user {current_user.id}")
        
        # In real implementation, fetch from database with filters
        # query = db.query(LexiconEntry).filter(LexiconEntry.user_id == current_user.id)
        
        # if language:
        #     query = query.filter(LexiconEntry.language == language)
        # if word_filter:
        #     query = query.filter(LexiconEntry.word.contains(word_filter))
        # if part_of_speech:
        #     query = query.filter(LexiconEntry.part_of_speech == part_of_speech)
        # if priority:
        #     query = query.filter(LexiconEntry.priority == priority)
        # if is_active is not None:
        #     query = query.filter(LexiconEntry.is_active == is_active)
        
        # total_count = query.count()
        # entries = query.order_by(LexiconEntry.word).offset((page - 1) * page_size).limit(page_size).all()
        
        # Mock entries for demonstration
        mock_entries = [
            LexiconEntry(
                id=f"entry-{i}",
                user_id=current_user.id,
                word=f"word{i}",
                pronunciation=f"prəˌnʌnsiˈeɪʃən{i}",
                language="en-US",
                part_of_speech="noun" if i % 2 == 0 else "verb",
                definition=f"Definition for word {i}",
                context=f"Context for word {i}",
                priority="normal" if i % 3 == 0 else "high" if i % 3 == 1 else "low",
                is_active=True,
                usage_count=i * 2,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            for i in range(1, 21)
        ]
        
        # Apply filters
        if language:
            mock_entries = [e for e in mock_entries if e.language == language]
        if word_filter:
            mock_entries = [e for e in mock_entries if word_filter.lower() in e.word.lower()]
        if part_of_speech:
            mock_entries = [e for e in mock_entries if e.part_of_speech == part_of_speech]
        if priority:
            mock_entries = [e for e in mock_entries if e.priority == priority]
        if is_active is not None:
            mock_entries = [e for e in mock_entries if e.is_active == is_active]
        
        total_count = len(mock_entries)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_entries = mock_entries[start_idx:end_idx]
        
        entry_responses = [
            LexiconEntryResponse(
                id=entry.id,
                word=entry.word,
                pronunciation=entry.pronunciation,
                language=entry.language,
                part_of_speech=entry.part_of_speech,
                definition=entry.definition,
                context=entry.context,
                priority=entry.priority,
                is_active=entry.is_active,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
                usage_count=entry.usage_count
            )
            for entry in paginated_entries
        ]
        
        return LexiconListResponse(
            entries=entry_responses,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error listing lexicon entries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list lexicon entries"
        )

@router.put("/{entry_id}", response_model=LexiconEntryResponse)
async def update_lexicon_entry(
    entry_id: str,
    request: LexiconUpdateRequest,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update a lexicon entry
    """
    try:
        logger.info(f"Updating lexicon entry {entry_id}")
        
        # In real implementation, fetch from database
        # lexicon_entry = db.query(LexiconEntry).filter(
        #     LexiconEntry.id == entry_id,
        #     LexiconEntry.user_id == current_user.id
        # ).first()
        
        # Mock lexicon entry for demonstration
        lexicon_entry = LexiconEntry(
            id=entry_id,
            user_id=current_user.id,
            word="example",
            pronunciation="ɪɡˈzæmpəl",
            language="en-US",
            part_of_speech="noun",
            definition="A representative form or pattern",
            context="This is an example sentence.",
            priority="normal",
            is_active=True,
            usage_count=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if not lexicon_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lexicon entry not found"
            )
        
        # Check if user owns this entry
        if lexicon_entry.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this lexicon entry"
            )
        
        # Update fields
        if request.pronunciation is not None:
            lexicon_entry.pronunciation = request.pronunciation.strip()
        if request.part_of_speech is not None:
            lexicon_entry.part_of_speech = request.part_of_speech
        if request.definition is not None:
            lexicon_entry.definition = request.definition
        if request.context is not None:
            lexicon_entry.context = request.context
        if request.priority is not None:
            # Validate priority
            valid_priorities = ["low", "normal", "high"]
            if request.priority not in valid_priorities:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid priority. Valid options: {', '.join(valid_priorities)}"
                )
            lexicon_entry.priority = request.priority
        if request.is_active is not None:
            lexicon_entry.is_active = request.is_active
        
        lexicon_entry.updated_at = datetime.utcnow()
        
        # In real implementation, save to database
        # db.commit()
        
        logger.info(f"Lexicon entry {entry_id} updated successfully")
        
        return LexiconEntryResponse(
            id=lexicon_entry.id,
            word=lexicon_entry.word,
            pronunciation=lexicon_entry.pronunciation,
            language=lexicon_entry.language,
            part_of_speech=lexicon_entry.part_of_speech,
            definition=lexicon_entry.definition,
            context=lexicon_entry.context,
            priority=lexicon_entry.priority,
            is_active=lexicon_entry.is_active,
            created_at=lexicon_entry.created_at,
            updated_at=lexicon_entry.updated_at,
            usage_count=lexicon_entry.usage_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lexicon entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lexicon entry"
        )

@router.delete("/{entry_id}")
async def delete_lexicon_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a lexicon entry
    """
    try:
        logger.info(f"Deleting lexicon entry {entry_id}")
        
        # In real implementation, fetch from database
        # lexicon_entry = db.query(LexiconEntry).filter(
        #     LexiconEntry.id == entry_id,
        #     LexiconEntry.user_id == current_user.id
        # ).first()
        
        # Mock lexicon entry for demonstration
        lexicon_entry = LexiconEntry(
            id=entry_id,
            user_id=current_user.id,
            word="example",
            pronunciation="ɪɡˈzæmpəl",
            language="en-US",
            part_of_speech="noun",
            definition="A representative form or pattern",
            context="This is an example sentence.",
            priority="normal",
            is_active=True,
            usage_count=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if not lexicon_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lexicon entry not found"
            )
        
        # Check if user owns this entry
        if lexicon_entry.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this lexicon entry"
            )
        
        # In real implementation, delete from database
        # db.delete(lexicon_entry)
        # db.commit()
        
        logger.info(f"Lexicon entry {entry_id} deleted successfully")
        
        return {
            "entry_id": entry_id,
            "message": "Lexicon entry deleted successfully",
            "deleted_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lexicon entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete lexicon entry"
        )

@router.post("/bulk-upload", response_model=LexiconBulkUploadResponse)
async def bulk_upload_lexicon(
    request: LexiconBulkUploadRequest,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Bulk upload lexicon entries from file or data
    """
    try:
        logger.info(f"Bulk uploading lexicon entries for user {current_user.id}")
        
        # Validate input
        if not request.entries or len(request.entries) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one entry is required"
            )
        
        if len(request.entries) > 1000:  # Limit batch size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 1000 entries allowed per upload"
            )
        
        # Validate language support
        supported_languages = text_processor.get_supported_languages()
        language_codes = [lang["code"] for lang in supported_languages]
        
        if request.language not in language_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language. Supported: {', '.join(language_codes[:10])}"
            )
        
        upload_id = str(uuid.uuid4())
        successful_entries = 0
        failed_entries = 0
        errors = []
        
        # Process each entry
        for i, entry_data in enumerate(request.entries):
            try:
                # Validate entry data
                if not entry_data.get("word") or not entry_data.get("pronunciation"):
                    errors.append({
                        "index": i,
                        "error": "Missing required fields: word and pronunciation",
                        "data": entry_data
                    })
                    failed_entries += 1
                    continue
                
                # Check if entry already exists
                if not request.overwrite_existing:
                    # In real implementation, check database
                    # existing_entry = db.query(LexiconEntry).filter(
                    #     LexiconEntry.word == entry_data["word"],
                    #     LexiconEntry.language == request.language,
                    #     LexiconEntry.user_id == current_user.id
                    # ).first()
                    
                    # if existing_entry:
                    #     errors.append({
                    #         "index": i,
                    #         "error": "Entry already exists",
                    #         "data": entry_data
                    #     })
                    #     failed_entries += 1
                    #     continue
                    pass
                
                # Create lexicon entry
                entry_id = str(uuid.uuid4())
                lexicon_entry = LexiconEntry(
                    id=entry_id,
                    user_id=current_user.id,
                    word=entry_data["word"].strip().lower(),
                    pronunciation=entry_data["pronunciation"].strip(),
                    language=request.language,
                    part_of_speech=entry_data.get("part_of_speech"),
                    definition=entry_data.get("definition"),
                    context=entry_data.get("context"),
                    priority=entry_data.get("priority", "normal"),
                    is_active=entry_data.get("is_active", True),
                    usage_count=0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                # In real implementation, save to database
                # db.add(lexicon_entry)
                
                successful_entries += 1
                
            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e),
                    "data": entry_data
                })
                failed_entries += 1
        
        # In real implementation, commit all successful entries
        # db.commit()
        
        logger.info(f"Bulk upload completed: {successful_entries} successful, {failed_entries} failed")
        
        return LexiconBulkUploadResponse(
            upload_id=upload_id,
            total_entries=len(request.entries),
            successful_entries=successful_entries,
            failed_entries=failed_entries,
            errors=errors,
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk upload failed"
        )

@router.post("/validate", response_model=LexiconValidationResponse)
async def validate_text_with_lexicon(
    request: LexiconValidationRequest,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Validate text against user's lexicon and provide suggestions
    """
    try:
        logger.info(f"Validating text with lexicon for user {current_user.id}")
        
        # Validate input
        if not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty"
            )
        
        if not request.language:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Language is required"
            )
        
        # Process text
        processed_text = text_processor.preprocess_text(request.text)
        words = processed_text.split()
        total_words = len(words)
        
        # In real implementation, fetch user's lexicon entries
        # user_lexicon = db.query(LexiconEntry).filter(
        #     LexiconEntry.user_id == current_user.id,
        #     LexiconEntry.language == request.language,
        #     LexiconEntry.is_active == True
        # ).all()
        
        # Mock lexicon entries for demonstration
        mock_lexicon = [
            {"word": "example", "pronunciation": "ɪɡˈzæmpəl"},
            {"word": "pronunciation", "pronunciation": "prəˌnʌnsiˈeɪʃən"},
            {"word": "lexicon", "pronunciation": "ˈlɛksɪkən"}
        ]
        
        # Check which words are in the lexicon
        matched_entries = []
        unmatched_words = []
        suggestions = []
        
        for word in words:
            word_lower = word.lower().strip(".,!?;:")
            found = False
            
            for entry in mock_lexicon:
                if entry["word"] == word_lower:
                    matched_entries.append(entry)
                    found = True
                    break
            
            if not found:
                unmatched_words.append(word_lower)
                
                # Generate suggestions (in real implementation, use more sophisticated algorithms)
                if len(word_lower) > 3:
                    suggestions.append({
                        "word": word_lower,
                        "suggestions": [
                            f"Add pronunciation for '{word_lower}'",
                            f"Check spelling of '{word_lower}'",
                            f"Consider adding '{word_lower}' to your lexicon"
                        ]
                    })
        
        # Calculate validation score
        validation_score = (len(matched_entries) / total_words) * 100 if total_words > 0 else 0
        
        logger.info(f"Text validation completed: {len(matched_entries)} matched, {len(unmatched_words)} unmatched")
        
        return LexiconValidationResponse(
            text=request.text,
            language=request.language,
            total_words=total_words,
            matched_entries=len(matched_entries),
            unmatched_words=unmatched_words,
            suggestions=suggestions,
            validation_score=validation_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Text validation failed"
        )

@router.post("/export")
async def export_lexicon(
    request: LexiconExportRequest,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Export lexicon entries in various formats
    """
    try:
        logger.info(f"Exporting lexicon for user {current_user.id}")
        
        # Validate format
        supported_formats = ["json", "csv", "xml"]
        if request.format not in supported_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format. Supported: {', '.join(supported_formats)}"
            )
        
        # In real implementation, fetch lexicon entries with filters
        # query = db.query(LexiconEntry).filter(LexiconEntry.user_id == current_user.id)
        
        # if request.language:
        #     query = query.filter(LexiconEntry.language == request.language)
        # if not request.include_inactive:
        #     query = query.filter(LexiconEntry.is_active == True)
        
        # if request.filters:
        #     # Apply additional filters
        #     pass
        
        # entries = query.order_by(LexiconEntry.word).all()
        
        # Mock entries for demonstration
        mock_entries = [
            {
                "word": "example",
                "pronunciation": "ɪɡˈzæmpəl",
                "language": "en-US",
                "part_of_speech": "noun",
                "definition": "A representative form or pattern",
                "context": "This is an example sentence.",
                "priority": "normal",
                "is_active": True
            }
        ]
        
        # Generate export data based on format
        if request.format == "json":
            export_data = json.dumps(mock_entries, indent=2, default=str)
            media_type = "application/json"
            filename = f"lexicon_{request.language}_{datetime.utcnow().strftime('%Y%m%d')}.json"
        elif request.format == "csv":
            # Generate CSV format
            csv_lines = ["word,pronunciation,language,part_of_speech,definition,context,priority,is_active"]
            for entry in mock_entries:
                csv_lines.append(f"{entry['word']},{entry['pronunciation']},{entry['language']},{entry['part_of_speech'] or ''},{entry['definition'] or ''},{entry['context'] or ''},{entry['priority']},{entry['is_active']}")
            export_data = "\n".join(csv_lines)
            media_type = "text/csv"
            filename = f"lexicon_{request.language}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        else:  # xml
            # Generate XML format
            xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<lexicon>']
            for entry in mock_entries:
                xml_lines.append('  <entry>')
                xml_lines.append(f'    <word>{entry["word"]}</word>')
                xml_lines.append(f'    <pronunciation>{entry["pronunciation"]}</pronunciation>')
                xml_lines.append(f'    <language>{entry["language"]}</language>')
                if entry["part_of_speech"]:
                    xml_lines.append(f'    <part_of_speech>{entry["part_of_speech"]}</part_of_speech>')
                if entry["definition"]:
                    xml_lines.append(f'    <definition>{entry["definition"]}</definition>')
                if entry["context"]:
                    xml_lines.append(f'    <context>{entry["context"]}</context>')
                xml_lines.append(f'    <priority>{entry["priority"]}</priority>')
                xml_lines.append(f'    <is_active>{entry["is_active"]}</is_active>')
                xml_lines.append('  </entry>')
            xml_lines.append('</lexicon>')
            export_data = "\n".join(xml_lines)
            media_type = "application/xml"
            filename = f"lexicon_{request.language}_{datetime.utcnow().strftime('%Y%m%d')}.xml"
        
        # Return file response
        from fastapi.responses import Response
        return Response(
            content=export_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(export_data.encode('utf-8')))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting lexicon: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lexicon export failed"
        )

@router.get("/statistics")
async def get_lexicon_statistics(
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get lexicon statistics for the user
    """
    try:
        logger.info(f"Getting lexicon statistics for user {current_user.id}")
        
        # In real implementation, calculate from database
        # This would involve complex queries and aggregations
        
        # Mock statistics for demonstration
        mock_stats = {
            "total_entries": 156,
            "active_entries": 142,
            "inactive_entries": 14,
            "languages": {
                "en-US": 89,
                "es-ES": 34,
                "fr-FR": 33
            },
            "parts_of_speech": {
                "noun": 67,
                "verb": 45,
                "adjective": 23,
                "adverb": 21
            },
            "priority_distribution": {
                "high": 23,
                "normal": 98,
                "low": 35
            },
            "most_used_words": [
                {"word": "example", "usage_count": 45},
                {"word": "pronunciation", "usage_count": 32},
                {"word": "lexicon", "usage_count": 28}
            ],
            "recent_additions": 12,
            "coverage_score": 78.5  # Percentage of common words covered
        }
        
        # Filter by language if specified
        if language:
            mock_stats["languages"] = {language: mock_stats["languages"].get(language, 0)}
        
        return mock_stats
        
    except Exception as e:
        logger.error(f"Error getting lexicon statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get lexicon statistics"
        )
