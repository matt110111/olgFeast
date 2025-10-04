from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from .core.config import settings
from .api.v1.auth import router as auth_router
from .api.v1.menu import router as menu_router
from .api.v1.cart import router as cart_router
from .api.v1.orders import router as orders_router
from .api.v1.operations import router as operations_router
from .core.database import engine, Base

# Import models to register them with SQLAlchemy
from .models import user, menu, cart, order

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Modern restaurant order management system with real-time updates",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["authentication"]
)

app.include_router(
    menu_router,
    prefix="/api/v1/menu",
    tags=["menu"]
)

app.include_router(
    cart_router,
    prefix="/api/v1/cart",
    tags=["shopping-cart"]
)

app.include_router(
    orders_router,
    prefix="/api/v1/orders",
    tags=["orders"]
)

app.include_router(
    operations_router,
    prefix="/api/v1/operations",
    tags=["operations"]
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to olgFeast API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.APP_VERSION}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
