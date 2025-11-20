"""API routes for the application."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import uuid

from src.database import get_db, Event
from src.etl import run_etl
from src.agents import get_agent

router = APIRouter()


# Pydantic models for requests/responses
class ETLRequest(BaseModel):
    """Request model for ETL endpoint."""
    location: str = "portugal--lisbon"
    max_results: int = 50
    fetch_descriptions: bool = True


class ETLResponse(BaseModel):
    """Response model for ETL endpoint."""
    status: str
    message: str
    events_stored: Optional[int] = None


class EventResponse(BaseModel):
    """Response model for event data."""
    id: int
    title: str
    description: Optional[str]
    location: Optional[str]
    address: Optional[str]
    date: Optional[str]
    time: Optional[str]
    url: Optional[str]
    source: str
    category: Optional[str]
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    session_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with the event recommendation agent.
    
    Args:
        request: Chat request with user message
        
    Returns:
        Agent's response
    """
    try:
        agent = get_agent()
        
        # Validate and handle session ID
        # Reject placeholder values and generate a new one if needed
        session_id = request.session_id
        if not session_id or session_id in ["string", "null", "undefined", ""]:
            session_id = str(uuid.uuid4())
            print(f"🔄 Generated new session ID: {session_id}")
        else:
            print(f"♻️  Using existing session ID: {session_id}")
        
        # Pass session ID to maintain conversation history
        response = await agent.chat(request.message, session_id=session_id)
        
        # Extract response text
        response_text = agent.print_response(response)
        
        return ChatResponse(
            response=response_text,
            session_id=session_id  # Return the session ID to the client
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/etl/run", response_model=ETLResponse)
async def trigger_etl(request: ETLRequest = ETLRequest()):
    """
    Manually trigger the ETL pipeline to fetch events from Eventbrite.
    
    Args:
        request: ETL request with location, max_results, and fetch_descriptions
        
    Returns:
        ETL response with status and number of events stored
    """
    try:
        events_stored = await run_etl(
            location=request.location,
            max_results=request.max_results,
            fetch_descriptions=request.fetch_descriptions
        )
        
        return ETLResponse(
            status="success",
            message=f"ETL completed successfully for {request.location}",
            events_stored=events_stored
        )
    
    except ValueError as e:
        return ETLResponse(
            status="error",
            message=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ETL failed: {str(e)}")


@router.get("/events", response_model=List[EventResponse])
async def get_events(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    location: Optional[str] = None
):
    """
    Get list of events from the database.
    
    Args:
        db: Database session
        skip: Number of events to skip (for pagination)
        limit: Maximum number of events to return
        category: Filter by category
        location: Filter by location (partial match)
        
    Returns:
        List of events
    """
    query = db.query(Event)
    
    if category:
        query = query.filter(Event.category.ilike(f"%{category}%"))
    
    if location:
        query = query.filter(Event.location.ilike(f"%{location}%"))
    
    events = query.order_by(Event.date.desc()).offset(skip).limit(limit).all()
    return events


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """
    Get a specific event by ID.
    
    Args:
        event_id: Event ID
        db: Database session
        
    Returns:
        Event details
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event


@router.get("/events/stats/summary")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get summary statistics about events in the database.
    
    Args:
        db: Database session
        
    Returns:
        Statistics summary
    """
    total_events = db.query(Event).count()
    
    # Get category breakdown
    categories = db.query(Event.category).distinct().all()
    category_counts = {}
    for (cat,) in categories:
        if cat:
            count = db.query(Event).filter(Event.category == cat).count()
            category_counts[cat] = count
    
    # Get source breakdown
    sources = db.query(Event.source).distinct().all()
    source_counts = {}
    for (source,) in sources:
        count = db.query(Event).filter(Event.source == source).count()
        source_counts[source] = count
    
    return {
        "total_events": total_events,
        "categories": category_counts,
        "sources": source_counts
    }
