"""Script to clear all records from the database."""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db, init_db
from src.database.models import Event


def clear_database():
    """Clear all records from the database."""
    # Get database path
    db_path = project_root / "data" / "events.db"
    
    if not db_path.exists():
        print("❌ Database file not found at:", db_path)
        print("💡 Run the ETL script to create a new database.")
        return
    
    # Get record count
    db = next(get_db())
    try:
        record_count = db.query(Event).count()
        
        if record_count == 0:
            print("✅ Database is already empty.")
            return
        
        # Check database size
        db_size = db_path.stat().st_size
        db_size_kb = db_size / 1024
        
        # Confirm deletion
        print("⚠️  WARNING: This will permanently delete all records from the database!")
        print(f"📂 Database location: {db_path}")
        print(f"📊 Database size: {db_size_kb:.2f} KB")
        print(f"📝 Number of records: {record_count}")
        
        response = input("\n❓ Are you sure you want to clear all records? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            try:
                db.query(Event).delete()
                db.commit()
                print("\n✅ All records cleared successfully!")
                print(f"🗑️  Deleted {record_count} record(s)")
                print("💡 Run the ETL script to populate the database with fresh data.")
            except Exception as e:
                db.rollback()
                print(f"\n❌ Error clearing records: {e}")
        else:
            print("\n❌ Operation cancelled.")
    finally:
        db.close()


def force_clear_database():
    """Force clear all records without confirmation (for automated scripts)."""
    db_path = project_root / "data" / "events.db"
    
    if not db_path.exists():
        print("❌ Database file not found.")
        return False
    
    db = next(get_db())
    try:
        record_count = db.query(Event).count()
        db.query(Event).delete()
        db.commit()
        print(f"✅ Cleared {record_count} record(s) successfully!")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing records: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    # Check for --force flag
    if "--force" in sys.argv:
        force_clear_database()
    else:
        clear_database()
