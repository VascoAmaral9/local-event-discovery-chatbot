"""Agno agent for event recommendations."""
import os
import asyncio
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path
from dotenv import load_dotenv
from agno.agent import Agent
from agno.agent.agent import RunOutput
from agno.db.sqlite import SqliteDb
from sqlalchemy import or_, and_
from src.database import get_db, Event
from src.etl.event_scraper import run_etl

# Load environment variables
load_dotenv()


class EventAgent:
    """Agent for recommending local events using Agno."""
    
    def __init__(self):
        """Initialize the event recommendation agent."""
        # Set up SQLite database for agent conversation history
        project_root = Path(__file__).parent.parent.parent
        agent_db_path = project_root / "data" / "agent_sessions.db"
        
        # Create data directory if it doesn't exist
        agent_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize Agno's SQLite database for conversation storage
        agent_db = SqliteDb(
            db_file=str(agent_db_path),
            session_table="agent_sessions"
        )
        
        self.agent = Agent(
            name="Event Recommendation Agent",
            description="A helpful assistant that recommends local events based on user preferences",
            instructions=[
                "You are a friendly event recommendation assistant.",
                "Help users discover local events in their area.",
                "When users ask about events, search the database and provide personalized recommendations.",
                "Always be enthusiastic and helpful.",
                "If no events match the criteria, suggest alternatives or ask the user to adjust their preferences.",
                "Include event details like date, time, location, and provide the URL when available.",
                "Remember previous conversation context to provide continuity in recommendations.",
                "When a user refers to a specific event (like 'the second event', 'the Afrobeats event', etc.), use the event's title or unique details to search for it using search_events_by_title before calling get_event_by_id.",
                "Event IDs in the database are not sequential - never assume the 'first event' has ID 1 or 'second event' has ID 2.",
                "If no events are found for a specific city/location, offer to fetch new events using the fetch_events_for_city tool.",
                "Common location formats: 'portugal--lisbon', 'united-states--san-francisco', 'united-kingdom--london', 'spain--barcelona'."
            ],
            tools=[
                self.search_events,
                self.search_events_by_title,
                self.get_event_by_id,
                self.get_all_categories,
                self.get_upcoming_events,
                self.get_events_by_location,
                self.fetch_events_for_city
            ],
            markdown=True,
            # Assign database for conversation persistence
            db=agent_db,
            # Enable conversation history
            add_history_to_context=True,
            num_history_messages=10,  # Include last 10 messages in context
            read_chat_history=True,
            store_history_messages=True
        )
        # Store sessions in memory
        self.sessions: Dict[str, str] = {}
    
    def search_events(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 10
    ) -> str:
        """
        Search for events based on keywords, category, or location.
        
        Args:
            query: Search keywords to match in title or description
            category: Event category to filter by
            location: Location to filter events by (e.g., "Lisbon")
            limit: Maximum number of events to return (default: 10)
            
        Returns:
            Formatted string with event details
        """
        db = next(get_db())
        try:
            # Build query
            events_query = db.query(Event)
            
            # Apply filters
            if query:
                search_filter = or_(
                    Event.title.ilike(f"%{query}%"),
                    Event.description.ilike(f"%{query}%"),
                    Event.address.ilike(f"%{query}%")
                )
                events_query = events_query.filter(search_filter)
            
            if category:
                events_query = events_query.filter(Event.category.ilike(f"%{category}%"))
            
            if location:
                events_query = events_query.filter(Event.location.ilike(f"%{location}%"))
            
            # Execute query
            events = events_query.limit(limit).all()
            
            if not events:
                return "No events found matching your criteria. Try adjusting your search parameters."
            
            # Format results
            result = f"Found {len(events)} event(s):\n\n"
            for i, event in enumerate(events, 1):
                result += self._format_event(event, i)
            
            return result
            
        except Exception as e:
            return f"Error searching events: {str(e)}"
        finally:
            db.close()
    
    def search_events_by_title(self, title: str) -> str:
        """
        Search for events by title to find their ID.
        Use this when a user references a specific event by name.
        
        Args:
            title: Part or full title of the event to search for
            
        Returns:
            Formatted string with matching events including their IDs
        """
        db = next(get_db())
        try:
            events = db.query(Event).filter(
                Event.title.ilike(f"%{title}%")
            ).limit(5).all()
            
            if not events:
                return f"No events found with title containing '{title}'."
            
            result = f"Found {len(events)} event(s) matching '{title}':\n\n"
            for event in events:
                result += f"Event ID {event.id}: {event.title}\n"
                if event.date:
                    result += f"   Date: {event.date}"
                    if event.time:
                        result += f" at {event.time}"
                    result += "\n"
                if event.address:
                    result += f"   Address: {event.address}\n"
                result += "\n"
            
            return result
            
        except Exception as e:
            return f"Error searching events by title: {str(e)}"
        finally:
            db.close()
    
    def get_event_by_id(self, event_id: int) -> str:
        """
        Get detailed information about a specific event by ID.
        
        Args:
            event_id: The ID of the event
            
        Returns:
            Formatted string with event details
        """
        db = next(get_db())
        try:
            event = db.query(Event).filter(Event.id == event_id).first()
            
            if not event:
                return f"Event with ID {event_id} not found."
            
            return self._format_event(event, detailed=True)
            
        except Exception as e:
            return f"Error retrieving event: {str(e)}"
        finally:
            db.close()
    
    def get_all_categories(self) -> str:
        """
        Get a list of all available event categories.
        
        Returns:
            Formatted string with all categories
        """
        db = next(get_db())
        try:
            categories = db.query(Event.category).distinct().filter(
                Event.category.isnot(None)
            ).all()
            
            if not categories:
                return "No categories available."
            
            category_list = [cat[0] for cat in categories if cat[0]]
            result = f"Available categories ({len(category_list)}):\n"
            for cat in sorted(category_list):
                result += f"- {cat}\n"
            
            return result
            
        except Exception as e:
            return f"Error retrieving categories: {str(e)}"
        finally:
            db.close()
    
    def get_upcoming_events(self, limit: int = 10) -> str:
        """
        Get upcoming events sorted by date.
        
        Args:
            limit: Maximum number of events to return (default: 10)
            
        Returns:
            Formatted string with upcoming events
        """
        db = next(get_db())
        try:
            events = db.query(Event).filter(
                Event.date.isnot(None)
            ).order_by(Event.date).limit(limit).all()
            
            if not events:
                return "No upcoming events found."
            
            result = f"Upcoming {len(events)} event(s):\n\n"
            for i, event in enumerate(events, 1):
                result += self._format_event(event, i)
            
            return result
            
        except Exception as e:
            return f"Error retrieving upcoming events: {str(e)}"
        finally:
            db.close()
    
    def get_events_by_location(self, location: str, limit: int = 10) -> str:
        """
        Get events in a specific location.
        
        Args:
            location: Location to search for (e.g., "Lisbon")
            limit: Maximum number of events to return (default: 10)
            
        Returns:
            Formatted string with events in the location
        """
        db = next(get_db())
        try:
            events = db.query(Event).filter(
                Event.location.ilike(f"%{location}%")
            ).limit(limit).all()
            
            if not events:
                return f"No events found in '{location}'."
            
            result = f"Events in {location} ({len(events)}):\n\n"
            for i, event in enumerate(events, 1):
                result += self._format_event(event, i)
            
            return result
            
        except Exception as e:
            return f"Error retrieving events by location: {str(e)}"
        finally:
            db.close()
    
    def fetch_events_for_city(self, location: str, max_results: int = 30) -> str:
        """
        Fetch new events from Eventbrite for a specific city/location.
        Use this when no events are found in the database for a location.
        
        Args:
            location: Location slug in format 'country--city' (e.g., 'portugal--lisbon', 
                     'united-states--san-francisco', 'spain--barcelona')
            max_results: Maximum number of events to fetch (default: 30)
            
        Returns:
            Formatted string with the result of the ETL process
        """
        try:
            # Run ETL synchronously (the agent's tool call is synchronous)
            # We need to create an event loop or run in the existing one
            loop = None
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, we need to schedule the coroutine
                    # This happens when called from an async context
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        count = pool.submit(
                            lambda: asyncio.run(run_etl(location=location, max_results=max_results, fetch_descriptions=False))
                        ).result()
                else:
                    count = loop.run_until_complete(run_etl(location=location, max_results=max_results, fetch_descriptions=False))
            except RuntimeError:
                # No event loop, create one
                count = asyncio.run(run_etl(location=location, max_results=max_results, fetch_descriptions=False))
            
            if count > 0:
                return f"✅ Successfully fetched and stored {count} new events for '{location}'! You can now search for events in this location."
            else:
                return f"⚠️ No new events found for '{location}'. The location might not be available on Eventbrite or there are no upcoming events."
                
        except Exception as e:
            return f"❌ Error fetching events: {str(e)}. Please check that the location format is correct (e.g., 'portugal--lisbon')."
    
    def _format_event(self, event: Event, index: Optional[int] = None, detailed: bool = False) -> str:
        """
        Format an event for display.
        
        Args:
            event: Event object to format
            index: Optional index number for the event
            detailed: Whether to include detailed information
            
        Returns:
            Formatted event string
        """
        prefix = f"{index}. " if index else ""
        
        # Include event ID in a comment for the agent to see
        result = f"{prefix}**{event.title}** (ID: {event.id})\n"
        
        if event.date:
            result += f"   📅 Date: {event.date}"
            if event.time:
                result += f" at {event.time}"
            result += "\n"
        
        if event.address:
            result += f"   📍 Address: {event.address}\n"
        
        if detailed and event.description:
            result += f"   📝 Description: {event.description}\n"
        
        if event.category:
            result += f"   🏷️  Category: {event.category}\n"
        
        if event.url:
            result += f"   🔗 More info: {event.url}\n"
        
        result += "\n"
        return result
    
    async def chat(self, message: str, session_id: Optional[str] = None) -> RunOutput:
        """
        Send a message to the agent and get a response.
        
        Args:
            message: User message
            session_id: Optional session ID to maintain conversation history
            
        Returns:
            Agent response
        """
        if session_id:
            # Use session to maintain conversation history
            return await self.agent.arun(message, session_id=session_id)
        else:
            # No session - single message interaction
            return await self.agent.arun(message)
    
    def print_response(self, response: RunOutput) -> str:
        """
        Extract and return the agent's response text.
        
        Args:
            response: Agent response object
            
        Returns:
            Response text
        """
        if hasattr(response, 'content') and response.content:
            return response.content
        return str(response)


# Singleton instance
_agent_instance = None


def get_agent() -> EventAgent:
    """Get or create the singleton agent instance."""
    global _agent_instance
    if (_agent_instance is None):
        _agent_instance = EventAgent()
    return _agent_instance
