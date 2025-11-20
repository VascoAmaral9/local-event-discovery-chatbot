"""Script to remove duplicate events from the database."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_db, Event
from sqlalchemy import func


def clean_duplicates():
    """Remove duplicate events, keeping the first occurrence."""
    db = next(get_db())
    
    try:
        # Find duplicates by URL
        print("🔍 Finding duplicates by URL...")
        url_duplicates = db.query(Event.url, func.count(Event.id).label('count')).filter(
            Event.url.isnot(None)
        ).group_by(Event.url).having(func.count(Event.id) > 1).all()
        
        deleted_count = 0
        
        for url, count in url_duplicates:
            # Get all events with this URL
            events = db.query(Event).filter(Event.url == url).order_by(Event.id).all()
            # Keep the first, delete the rest
            for event in events[1:]:
                print(f"🗑️  Deleting duplicate: {event.title}")
                db.delete(event)
                deleted_count += 1
        
        db.commit()
        print(f"\n✅ Removed {deleted_count} duplicate events!")
        
        # Show final stats
        total = db.query(Event).count()
        print(f"📊 Total events remaining: {total}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error cleaning duplicates: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    clean_duplicates()
