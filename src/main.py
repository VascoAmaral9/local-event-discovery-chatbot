"""Main FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import init_db, close_db
from src.api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    init_db()
    print("✅ Database initialized successfully")
    yield
    # Shutdown
    close_db()
    print("✅ Database connections closed successfully")


# Initialize FastAPI app
app = FastAPI(
    title="Local Event Discovery Chatbot",
    description="A conversational API for discovering local events",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["events"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Local Event Discovery Chatbot API",
        "version": "0.1.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "chat": "/api/chat",
            "events": "/api/events",
            "etl": "/api/etl/run",
            "stats": "/api/events/stats/summary"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
