"""
FastAPI application entry point
"""
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text

from .config import settings
from .database import engine, Base
from .redis_client import RedisClient
from .services.ml_analyzer import get_ml_analyzer
from .models.ml_analysis import (
    AnalyzeSMSRequest,
    AnalyzeSMSResponse,
    HealthCheckResponse,
)

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting up application...")
    
    # Initialize Redis connection (non-blocking)
    try:
        await RedisClient.get_client()
        logger.info("Redis connection pool initialized")
    except Exception as e:
        # Redis is optional - only log at debug level
        logger.debug(f"Redis connection failed during startup: {e}. Health check will show Redis as unavailable.")
    
    # Test database connection (non-blocking)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.warning(f"Database connection failed during startup: {e}. Health check will show database as unavailable.")

    # Load ML models
    try:
        ml_analyzer = get_ml_analyzer()
        ml_analyzer.load_models()
        logger.info("ML models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load ML models: {e}. ML analysis will not be available.")

    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        await RedisClient.close()
    except Exception as e:
        logger.warning(f"Error closing Redis: {e}")
    
    try:
        await engine.dispose()
    except Exception as e:
        logger.warning(f"Error disposing database engine: {e}")
    
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Error handling middleware
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(f"Validation error: {exc.errors()} - {request.url}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "status_code": 422,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check database connection
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["services"]["database"] = "connected"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        health_status["services"]["database"] = "disconnected"
        health_status["status"] = "degraded"
    
    # Check Redis connection
    try:
        redis_client = await RedisClient.get_client()
        await redis_client.ping()
        health_status["services"]["redis"] = "connected"
    except Exception as e:
        # Only log at debug level - Redis is optional for development
        logger.debug(f"Redis health check failed: {e}")
        health_status["services"]["redis"] = "disconnected"
        health_status["status"] = "degraded"
    
    # Return 200 if at least one service is available, 503 if all are down
    if all(status == "disconnected" for status in health_status["services"].values()):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status,
        )
    
    return health_status


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
    }


@app.get("/favicon.ico")
async def favicon():
    """Favicon endpoint - returns 204 No Content"""
    from fastapi.responses import Response
    return Response(status_code=204)


# ML Analysis Endpoints
@app.post("/analyze_sms", response_model=AnalyzeSMSResponse)
async def analyze_sms(request: AnalyzeSMSRequest):
    """
    Analyze an SMS message for scam/phishing indicators.

    Uses an ensemble of ML models and rule-based detection to assess risk.
    Returns a risk score (0-1), risk level (low/medium/high), and human-readable reasons.
    """
    try:
        ml_analyzer = get_ml_analyzer()
        result = await ml_analyzer.analyze_sms(
            message_id=request.message_id,
            text=request.text,
            sender=request.sender,
            received_ts=request.received_ts,
        )
        return result
    except ValueError as e:
        logger.warning(f"Validation error in analyze_sms: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": str(e), "status_code": 400},
        )
    except Exception as e:
        logger.error(f"Error analyzing SMS: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Analysis failed", "status_code": 500},
        )


@app.get("/ml_health", response_model=HealthCheckResponse)
async def ml_health_check():
    """
    Health check endpoint for ML service.

    Returns status of ML models and inference capabilities.
    """
    try:
        ml_analyzer = get_ml_analyzer()
        device = "GPU" if ml_analyzer.device == 0 else "CPU"

        return {
            "status": "ok" if ml_analyzer._models_loaded else "degraded",
            "models_loaded": ml_analyzer._models_loaded,
            "device": device,
        }
    except Exception as e:
        logger.error(f"ML health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "models_loaded": False,
                "device": "unknown",
            },
        )

