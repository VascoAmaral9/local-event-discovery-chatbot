"""ETL pipeline for scraping events from Eventbrite website."""
import httpx
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from src.database.models import Event
from src.database.connection import get_db


class EventbriteScraper:
    """Scraper for fetching events from Eventbrite website."""
    
    def __init__(self):
        """Initialize the scraper."""
        self.base_url = "https://www.eventbrite.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    
    async def search_events(
        self,
        location: str = "portugal--lisbon",
        max_results: int = 50
    ) -> List[dict]:
        """
        Scrape events from Eventbrite website.
        
        Args:
            location: Location slug (e.g., "portugal--lisbon", "united-states--san-francisco")
            max_results: Maximum number of events to fetch
            
        Returns:
            List of event dictionaries
        """
        events = []
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            url = f"{self.base_url}/d/{location}/events/"
            
            try:
                print(f"📄 Fetching events from {location}...")
                print(f"🔗 URL: {url}")
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find event cards by class
                event_cards = soup.find_all('div', class_='event-card')
                
                if not event_cards:
                    print(f"⚠️  No event cards found")
                    return []
                
                print(f"✅ Found {len(event_cards)} event cards")
                
                for card in event_cards[:max_results]:
                    event_data = self._parse_event_card(card)
                    if event_data:
                        events.append(event_data)
                
            except httpx.HTTPError as e:
                print(f"❌ Error fetching events: {e}")
        
        return events
    
    def _parse_event_card(self, card) -> Optional[dict]:
        """
        Parse event data from HTML card.
        
        Args:
            card: BeautifulSoup element containing event data
            
        Returns:
            Parsed event dictionary or None
        """
        try:
            # Extract title from the link
            title_link = card.find('a', class_='event-card-link')
            if not title_link:
                return None
            
            # Get URL
            url = title_link.get('href', '')
            if url and not url.startswith('http'):
                url = f"{self.base_url}{url}" if url.startswith('/') else url
            
            # Extract category from data-event-category attribute on the link
            category = title_link.get('data-event-category', None)
            if category:
                # Capitalize first letter of each word for consistency
                category = category.title()
            
            # Extract title - it's usually in a h3 within the card
            title_elem = card.find(['h2', 'h3', 'h4'])
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:
                return None
            
            # Extract date/time and venue from p tags
            # The structure is consistent:
            # 1st p tag with bold styling and bullet (•) = date/time
            # 2nd p tag with clamp-line class = venue
            # 3rd p tag = price info
            
            date_str = None
            time_str = None
            venue = None
            
            p_tags = card.find_all('p', class_=lambda x: x and 'Typography_root' in str(x))
            
            for p in p_tags:
                text = p.get_text(strip=True)
                classes = p.get('class', [])
                
                # Check if this is the date/time element (has • and AM/PM)
                if '•' in text and ('AM' in text or 'PM' in text):
                    # Parse date and time from format like "Fri, Nov 28 •  11:00 PM"
                    parts = text.split('•')
                    if len(parts) == 2:
                        date_str = parts[0].strip()
                        time_str = parts[1].strip()
                
                # Check if this is the venue element (has clamp-line class)
                elif any('clamp-line' in str(c) for c in classes):
                    venue = text
                    break  # Found venue, we can stop
            
            return {
                "title": title,
                "description": None,
                "location": None,  # Will be set by the calling method
                "address": venue,
                "date": date_str,
                "time": time_str,
                "url": url,
                "source": "Eventbrite",
                "category": category
            }
        
        except Exception as e:
            print(f"⚠️  Error parsing event card: {e}")
            return None
    
    async def _fetch_event_description(self, event_url: str, client: httpx.AsyncClient) -> Optional[str]:
        """
        Fetch event description from individual event page.
        
        Args:
            event_url: URL of the event page
            client: HTTP client to use for the request
            
        Returns:
            Event description text or None
        """
        try:
            response = await client.get(
                event_url,
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find description by id first
            desc_elem = soup.find(id='event-description')
            
            # If not found by id, try by class
            if not desc_elem:
                desc_elem = soup.find('div', class_='event-description')
            
            # Try summary class as fallback
            if not desc_elem:
                desc_elem = soup.find('div', class_='summary')
            
            if desc_elem:
                # Get text and clean it up
                description = desc_elem.get_text(strip=True)
                # Limit description length to avoid storing too much data
                if len(description) > 1000:
                    description = description[:1000] + "..."
                return description
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error fetching description: {e}")
            return None
    
    async def scrape_and_store(
        self,
        location: str = "portugal--lisbon",
        max_results: int = 50,
        fetch_descriptions: bool = True
    ) -> int:
        """
        Scrape events from Eventbrite and store them in the database.
        
        Args:
            location: Location slug (e.g., "portugal--lisbon")
            max_results: Maximum number of events to fetch
            fetch_descriptions: Whether to fetch event descriptions from individual pages
            
        Returns:
            Number of events stored
        """
        print(f"🔍 Searching for events in {location}...")
        
        # Fetch events from Eventbrite
        events = await self.search_events(location, max_results)
        
        if not events:
            print("❌ No events found")
            return 0
        
        print(f"✅ Found {len(events)} events")
        
        # Parse and store events
        db = next(get_db())
        stored_count = 0
        seen_urls = set()  # Track URLs in this batch to prevent duplicates
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                for event_data in events:
                    # Skip events without title
                    if not event_data.get("title"):
                        continue
                    
                    # Set the location slug
                    event_data["location"] = location
                    
                    # Skip if we've already seen this URL in this batch
                    event_url = event_data.get("url")
                    if event_url:
                        if event_url in seen_urls:
                            print(f"⏭️  Skipping duplicate in batch: {event_data['title']}")
                            continue
                        seen_urls.add(event_url)
                    
                    # Check if event already exists in database (by URL or title)
                    if event_url:
                        existing_event = db.query(Event).filter(
                            Event.url == event_url
                        ).first()
                    else:
                        # Fallback to title check if no URL
                        existing_event = db.query(Event).filter(
                            Event.title == event_data["title"],
                            Event.source == "Eventbrite"
                        ).first()
                    
                    if existing_event:
                        print(f"⏭️  Skipping duplicate in DB: {event_data['title']}")
                        continue
                    
                    # Fetch description if enabled
                    if fetch_descriptions and event_url:
                        event_data["description"] = await self._fetch_event_description(event_url, client)
                    
                    # Create new event
                    new_event = Event(**event_data)
                    db.add(new_event)
                    stored_count += 1
                    print(f"✅ Stored: {event_data['title']}")
                
                db.commit()
                print(f"\n🎉 Successfully stored {stored_count} new events!")
                
            except Exception as e:
                db.rollback()
                print(f"❌ Error storing events: {e}")
                raise
            finally:
                db.close()
        
        return stored_count


async def run_etl(location: str = "portugal--lisbon", max_results: int = 50, fetch_descriptions: bool = True) -> int:
    """
    Run the ETL pipeline to fetch and store events.
    
    Args:
        location: Location slug to search for events
        max_results: Maximum number of events to fetch
        fetch_descriptions: Whether to fetch event descriptions (slower but more complete)
        
    Returns:
        Number of events stored
    """
    try:
        scraper = EventbriteScraper()
        count = await scraper.scrape_and_store(
            location=location, 
            max_results=max_results,
            fetch_descriptions=fetch_descriptions
        )
        return count
    except Exception as e:
        print(f"❌ Error running ETL: {e}")
        import traceback
        traceback.print_exc()
        return 0


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_etl())
