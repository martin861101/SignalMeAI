# AI Learning Summarizer

A comprehensive learning research assistant that scrapes web content, generates AI-powered summaries, and delivers them via email.

## Features

- **Topic Research**: Search for topics using Tavily API to find the best sources
- **URL Scraping**: Directly scrape content from provided URLs using Selenium
- **AI Summarization**: Generate structured learning summaries using Google Gemini
- **Email Delivery**: Optionally send summaries to specified email addresses
- **Web Interface**: Vue.js frontend for easy interaction
- **MCP Integration**: Model Context Protocol server for tool integration

## Project Structure

- `frontend/`: Vue.js application with Vite and Tailwind CSS
- `mcp/`: Model Context Protocol server implementation

## Installation

### Backend (MCP Server)

1. Navigate to the `mcp/` directory:
   ```bash
   cd mcp
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in a `.env` file:
   ```
   EMAIL_USER=your_email@example.com
   EMAIL_PASS=your_email_password
   EMAIL_HOST=smtp.example.com
   EMAIL_PORT=465
   TAVILY_API_KEY=your_tavily_api_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

### Frontend

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Usage

### Running the Backend

From the `mcp/` directory:
```bash
python server.py
```

The server will run on `http://localhost:8000` (or your network IP).

### Running the Frontend

From the `frontend/` directory:
```bash
npm run dev
```

### API Endpoints

- `GET /`: Health check
- `POST /learning_summary`: Generate learning summary
  - Body: `{ "mode": "topic"|"url", "topic": "string", "url": "string", "email": "string" }`

### MCP Tool

The MCP server provides a `learning_summary` tool for integration with MCP-compatible clients.