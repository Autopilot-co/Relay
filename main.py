"""
Relay - AI Assistant for Workflow Automation
Main FastAPI application entry point
"""

from fastapi import FastAPI
from config.settings import settings
from utils.logger import logger

# Log that we're starting up
logger.info(f"Initializing {settings.app_name}...")

# Create the FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    description="AI Assistant for Workflow Automation",
    version="0.1.0",
    debug=settings.debug
)

logger.info(f"{settings.app_name} initialized successfully")


@app.get("/health")
async def health_check():
    """
    Health check endpoint - proves the server is running
    
    Returns:
        dict: Simple status message with config info
    """
    logger.info("Health check endpoint called")
    return {
        "status": "ok",
        "message": f"{settings.app_name} is running",
        "debug": settings.debug,
        "port": settings.port
    }


@app.get("/")
async def root():
    """
    Root endpoint - welcome message
    
    Returns:
        dict: Welcome message
    """
    logger.info("Root endpoint called")
    return {
        "app": settings.app_name,
        "description": "AI Assistant for Workflow Automation",
        "status": "operational",
        "version": "0.1.0"
    }


# Entry point for running with python main.py
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {settings.app_name} server on port {settings.port}...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )

