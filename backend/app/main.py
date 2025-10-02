from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging_config import setup_logging
from app.middleware import RequestLoggingMiddleware
from app.routes import auth, users
import logging

# Configure logging
setup_logging(
    log_level=getattr(settings, "LOG_LEVEL", "INFO"),
    log_file=getattr(settings, "LOG_FILE", "logs/app.log"),
    console_logs=True
)

logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

logger.info("Application startup", extra={"environment": getattr(settings, "ENVIRONMENT", "development")})

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Welcome to Vehicle Check API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
