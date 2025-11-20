# 🎉 Local Event Discovery Chatbot

A conversational AI-powered chatbot API that recommends local events. Built with FastAPI, Agno AgentOS, and powered by web scraping from Eventbrite.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Using the Chatbot](#using-the-chatbot)
- [API Documentation](#api-documentation)
- [Scripts](#scripts)
- [Project Structure](#project-structure)

## ✨ Features

- **Conversational AI Agent**: Chat naturally to discover local events
- **Event Database**: SQLite database with events scraped from Eventbrite
- **Smart Search**: Search by keywords, location, category, or date
- **RESTful API**: FastAPI-based API with automatic documentation
- **ETL Pipeline**: Web scraper to fetch and store events
- **Interactive CLI**: Command-line interface for chatting with the agent

## 🛠 Tech Stack

- **Python 3.10+**
- **FastAPI** - Modern web framework for building APIs
- **Agno AgentOS** - AI agent framework for conversational interfaces
- **SQLAlchemy** - SQL toolkit and ORM
- **BeautifulSoup4** - Web scraping library
- **OpenAI** - LLM for the conversational agent
- **UV** - Fast Python package manager

## 📦 Prerequisites

- Python 3.10 or higher
- UV package manager
- OpenAI API key

## 🚀 Installation

### 1. Update UV Package Manager

First, ensure you have the latest version of UV:

```bash
uv self update
```

If you don't have UV installed, install it first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone the Repository

```bash
cd /path/to/your/projects
# If cloning from git:
# git clone <repository-url>
# cd Event_Recommender
```

### 3. Sync Dependencies

Install all project dependencies using UV:

```bash
uv sync
```

This will:
- Create a virtual environment in `.venv`
- Install all dependencies from `pyproject.toml`
- Generate/update `uv.lock`

## ⚙️ Configuration

### Create `.env` File

Create a `.env` file in the project root with your API keys:

```bash
# Required: OpenAI API key for the conversational agent
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**⚠️ Important:** Never commit your `.env` file to version control!

### Get an OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Create a new API key
4. Copy and paste it into your `.env` file

## 🏃 Running the Application

### Start the FastAPI Server

Run the main application server:

```bash
uv run uvicorn src.main:app --reload
```

The server will start on **http://localhost:8000**

Options:
- `--reload` - Auto-reload on code changes (development mode)
- `--host 0.0.0.0` - Make server accessible from other machines
- `--port 8080` - Use a different port

### Verify Server is Running

Open your browser and visit:
- **http://localhost:8000** - Root endpoint with API info
- **http://localhost:8000/health** - Health check
- **http://localhost:8000/docs** - Interactive API documentation

## 💬 Using the Chatbot

### Option 1: Interactive CLI (Recommended for Testing)

Start an interactive chat session in your terminal:

```bash
uv run python scripts/chat_cli.py
```

**Features:**
- Natural language conversation
- Colorful, formatted responses
- Type `exit`, `quit`, or press `Ctrl+C` to quit

**Example conversation:**
```
You: What events are happening this weekend?
🤖 Agent: Here are some exciting events...

You: Show me music events
🤖 Agent: I found these music events...

You: exit
👋 Goodbye! Have fun at the events!
```

### Option 2: API Endpoint

Send POST requests to the chat endpoint:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What events are happening in Lisbon?"}'
```

**Request Format:**
```json
{
  "message": "Your question here",
  "session_id": "optional-session-id"
}
```

**Response Format:**
```json
{
  "response": "Agent's response here...",
  "session_id": null
}
```

### Option 3: Interactive API Documentation

Visit **http://localhost:8000/docs** for a full interactive API interface where you can:
- Test all endpoints
- See request/response schemas
- Execute API calls directly from the browser

## 📚 API Documentation

### Available Endpoints

#### Chat with Agent
```http
POST /api/chat
```
Chat with the AI agent about events.

#### Get Events
```http
GET /api/events?skip=0&limit=20&category=Music&location=Lisbon
```
Retrieve events from the database with optional filters.

#### Get Event by ID
```http
GET /api/events/{event_id}
```
Get detailed information about a specific event.

#### Get Statistics
```http
GET /api/events/stats/summary
```
Get summary statistics about events in the database.

#### Trigger ETL
```http
POST /api/etl/run
```
Manually trigger the ETL pipeline to scrape new events.

**Request body:**
```json
{
  "location": "portugal--lisbon",
  "max_results": 50
}
```

### Try All Endpoints

Visit **http://localhost:8000/docs** for the interactive Swagger UI where you can:
1. Expand any endpoint
2. Click "Try it out"
3. Fill in parameters
4. Click "Execute"
5. See the response

## 📜 Scripts

All scripts are located in the `scripts/` directory.

### 1. Run ETL Pipeline

Fetch and store events from Eventbrite:

```bash
uv run python scripts/run_etl.py
```

**Options:**
```bash
# Specify location and max results
uv run python scripts/run_etl.py --location "portugal--lisbon" --max-results 50

# Specify no descriptions for faster run
uv run python scripts/run_etl.py --location "Bristol" --no-descriptions
```

**What it does:**
- Scrapes events from Eventbrite website
- Extracts event details (title, date, location, URL)
- Stores events in SQLite database
- Skips duplicates automatically
- Goes to every event webpage to exctract descriptions, if disabled events are not stored with descriptions but runs faster

**Location format:** Supports both the slug format from Eventbrite URLs or just a city
- `portugal--lisbon` for Lisbon, Portugal
- `Bristol` for Bristol, UK

### 2. Interactive Chat CLI

Start a chat session with the agent:

```bash
uv run python scripts/chat_cli.py
```

**What you can ask:**
- "What events are happening this week?"
- "Show me music events"
- "What's happening in Lisbon?"
- "Tell me about upcoming events"
- "Are there any tech conferences?"

### 3. Clean Duplicate Events

Remove duplicate events from the database:

```bash
uv run python scripts/clean_duplicates.py
```

**What it does:**
- Finds duplicate events (same URL)
- Keeps the first occurrence
- Deletes the rest
- Shows how many duplicates were removed

### 4. Drop Database

Delete the entire database (use with caution):

```bash
# Interactive mode (asks for confirmation)
uv run python scripts/drop_db.py

# Force mode (no confirmation)
uv run python scripts/drop_db.py --force
```

**When to use:**
- Starting fresh with new data
- Testing the ETL pipeline
- Database corruption issues

**After dropping:** Run the ETL script to repopulate the database.

## 📁 Project Structure

```
Event_Recommender/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── database/
│   │   ├── models.py        # SQLAlchemy Event model
│   │   └── connection.py    # Database configuration
│   ├── etl/
│   │   └── event_scraper.py # Eventbrite web scraper
│   ├── agents/
│   │   └── event_agent.py   # Agno AI agent with tools
│   └── api/
│       └── routes.py        # API endpoints
├── scripts/
│   ├── run_etl.py          # ETL pipeline script
│   ├── chat_cli.py         # Interactive chat CLI
│   ├── clean_duplicates.py # Duplicate removal utility
│   └── drop_db.py          # Database reset utility
├── data/
│   └── events.db           # SQLite database (auto-created)
├── pyproject.toml          # Project dependencies
├── uv.lock                 # Locked dependencies
├── .env                    # Environment variables (create this)
├── .gitignore             # Git ignore file
└── README.md              # This file
```

## 🎯 Typical Workflow

### First Time Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Create `.env` file:**
   ```bash
   echo "OPENAI_API_KEY=your-key-here" > .env
   ```

3. **Run ETL to populate database:**
   ```bash
   uv run python scripts/run_etl.py
   ```

4. **Start the server:**
   ```bash
   uv run uvicorn src.main:app --reload
   ```

5. **Test the chatbot:**
   ```bash
   uv run python scripts/chat_cli.py
   ```

### Regular Usage

1. **Update events (weekly/daily):**
   ```bash
   uv run python scripts/run_etl.py
   ```

2. **Start server:**
   ```bash
   uv run uvicorn src.main:app --reload
   ```

3. **Chat with the agent:**
   - Use CLI: `uv run python scripts/chat_cli.py`
   - Or use API: `curl http://localhost:8000/api/chat`
   - Or visit: `http://localhost:8000/docs`

### Maintenance

- **Clean duplicates:** `uv run python scripts/clean_duplicates.py`
- **Reset database:** `uv run python scripts/drop_db.py`
- **Update dependencies:** `uv sync`

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:
```bash
uv run uvicorn src.main:app --reload --port 8080
```

### Database Locked Error

If you get "database is locked" errors:
1. Stop all running instances of the application
2. Delete `data/events.db`
3. Run the ETL script again

### OpenAI API Errors

If you get OpenAI API errors:
- Check that your API key is valid in `.env`
- Ensure you have credits in your OpenAI account
- Verify the key has the correct permissions

### Import Errors

If you get import errors:
```bash
uv sync
```
