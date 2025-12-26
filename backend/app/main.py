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

