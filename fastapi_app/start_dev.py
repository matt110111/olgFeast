#!/usr/bin/env python3
"""
Development server startup script for olgFeast FastAPI application
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print("🚀 Starting olgFeast FastAPI Development Server")
    print("=" * 50)
    print(f"📖 API Documentation: http://localhost:8000/docs")
    print(f"📚 ReDoc Documentation: http://localhost:8000/redoc")
    print(f"🏥 Health Check: http://localhost:8000/health")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
