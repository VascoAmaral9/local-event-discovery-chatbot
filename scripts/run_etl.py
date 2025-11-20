"""CLI script to run the ETL pipeline."""
import asyncio
import argparse
from src.etl import run_etl


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the ETL pipeline to fetch events from Eventbrite"
    )
    parser.add_argument(
        "--location",
        type=str,
        default="portugal--lisbon",
        help="Location slug (e.g., 'portugal--lisbon', 'united-states--san-francisco')"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of events to fetch (default: 50)"
    )
    parser.add_argument(
        "--no-descriptions",
        action="store_true",
        help="Skip fetching event descriptions (faster but less detailed)"
    )
    
    args = parser.parse_args()
    
    # Invert the flag: --no-descriptions means fetch_descriptions=False
    fetch_descriptions = not args.no_descriptions
    
    print(f"🚀 Starting ETL pipeline for {args.location}...")
    print(f"📊 Max results: {args.max_results}")
    print(f"📝 Fetch descriptions: {'Yes' if fetch_descriptions else 'No (faster)'}")
    
    asyncio.run(run_etl(
        location=args.location,
        max_results=args.max_results,
        fetch_descriptions=fetch_descriptions
    ))
