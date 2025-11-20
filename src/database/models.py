"""Database models for events."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from src.database.connection import Base


class Event(Base):
    """Event model for storing local events."""
    
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    date = Column(String(50), nullable=True)  # Store as string for flexibility
    time = Column(String(50), nullable=True)
    url = Column(String(500), nullable=True)
    source = Column(String(100), nullable=False)  # Which API/website it came from
    category = Column(String(100), nullable=True)  # Event category (music, sports, etc.)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}', date='{self.date}')>"
    
    def to_dict(self):
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "address": self.address,
            "date": self.date,
            "time": self.time,
            "url": self.url,
            "source": self.source,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
