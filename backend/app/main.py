from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from datetime import datetime

# Import routers
from .api.routers import voice_management, synthesis, lexicon

# Import middleware and utilities
from .middleware.auth import get_current_user
from .middleware.logging import LoggingMiddleware
from .middleware.rate_limiting import RateLimitingMiddleware
from .middleware.error_handling import ErrorHandlingMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Azure Voice Cloning API...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Version: {os.getenv('APP_VERSION', '1.0.0')}")
    
    # Initialize services
    try:
        # Initialize Azure services
        logger.info("Initializing Azure services...")
        
        # Initialize database connections
        logger.info("Initializing database connections...")
        
        # Initialize caches
        logger.info("Initializing caches...")
        
        logger.info("Azure Voice Cloning API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Azure Voice Cloning API...")
    
    try:
        # Close database connections
        logger.info("Closing database connections...")
        
        # Close Azure service connections
        logger.info("Closing Azure service connections...")
        
        logger.info("Azure Voice Cloning API shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Create FastAPI application
app = FastAPI(
    title="Azure Voice Cloning API",
    description="A comprehensive API for Azure Open AI voice cloning services",
    version=os.getenv("APP_VERSION", "1.0.0"),
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT", "development") == "development" else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(",")
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Include routers
app.include_router(
    voice_management.router,
    prefix="/api/v1",
    tags=["Voice Management"]
)

app.include_router(
    synthesis.router,
    prefix="/api/v1",
    tags=["Voice Synthesis"]
)

app.include_router(
    lexicon.router,
    prefix="/api/v1",
    tags=["Lexicon Management"]
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Azure Voice Cloning API",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "description": "A comprehensive API for Azure Open AI voice cloning services",
        "documentation": "/docs",
        "health": "/health",
        "timestamp": datetime.utcnow().isoformat()
    }

# API info endpoint
@app.get("/api/info", tags=["API Info"])
async def api_info():
    """API information and capabilities"""
    return {
        "name": "Azure Voice Cloning API",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "description": "A comprehensive API for Azure Open AI voice cloning services",
        "features": [
            "Voice Model Training and Management",
            "Real-time Voice Synthesis",
            "Batch Voice Synthesis",
            "Custom Lexicon Management",
            "Multi-language Support",
            "Azure AI Services Integration",
            "Secure Authentication",
            "Rate Limiting",
            "Comprehensive Logging"
        ],
        "endpoints": {
            "voice_management": "/api/v1/voices",
            "synthesis": "/api/v1/synthesis",
            "lexicon": "/api/v1/lexicon"
        },
        "authentication": "Bearer Token (Azure Entra ID)",
        "rate_limits": {
            "default": "100 requests per minute",
            "synthesis": "50 requests per minute",
            "training": "10 requests per minute"
        },
        "supported_languages": [
            "en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "ja-JP", "ko-KR", "zh-CN"
        ],
        "audio_formats": ["wav", "mp3", "ogg", "flac"],
        "timestamp": datetime.utcnow().isoformat()
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "code": 500,
                "message": "An internal server error occurred",
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path
            }
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Azure Voice Cloning API startup event triggered")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Azure Voice Cloning API shutdown event triggered")

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
