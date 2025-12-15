# ApexAI Aura Insight - Integrated System

## Overview

This integrated system combines:
- **Frontend Vue.js App**: Modern web interface with trading dashboard
- **MCP Backend Server**: FastAPI server providing API endpoints
- **Trading Orchestration**: Multi-agent trading signal generation with real market data
- **LLM Integration**: Ollama-based AI agents with fallback capabilities

## Quick Start

### 1. Start Ollama (Required for AI Agents)
```bash
# Start Ollama service
ollama serve

# Pull required models (in another terminal)
ollama pull mistral:latest
```

### 2. Start MCP Server
```bash
# From project root
python start_server.py
# Server will be available at http://localhost:8000
```

### 3. Start Frontend
```bash
# From project root
cd frontend
npm install
npm run dev
# Frontend will be available at http://localhost:5173
```

### 4. Use the Trading Dashboard
1. Open http://localhost:5173 in your browser
2. Navigate to the "Trader" tab
3. Enter a symbol (e.g., SPY, GC=F, EURUSD)
4. Click "Generate Signal"
5. View the multi-agent analysis results

## Architecture

### Frontend (`frontend/`)
- **Vue.js 3** with Composition API
- **Trading.vue**: Integrated trading dashboard
- Real-time signal generation and display
- Agent consensus visualization
- Risk assessment and recommendations

### Backend (`mcp/`)
- **FastAPI** server with CORS support
- **Trading Integration**: Calls real orchestration system
- **Error Handling**: Graceful fallbacks and mock responses
- **WebSocket Ready**: For future real-time updates

### Trading Engine (`mcp/trading/`)
- **Multi-Agent System**: ChartAnalyst, MacroAgent, MarketSentinel, PlatformPilot
- **Real Market Data**: Yahoo Finance, Alpha Vantage, Polygon, Finnhub
- **LLM Fallback**: Ollama with API key support
- **LangGraph Orchestration**: Stateful workflow management

## API Endpoints

### Trading Signals
```http
POST /trading/signal
Content-Type: application/json

{
  "symbol": "SPY"
}
```

**Response:**
```json
{
  "asset": "SPY",
  "direction": "LONG",
  "confidence": 0.78,
  "entry_target": 451.00,
  "stop_loss_target": 450.25,
  "take_profit_target": 452.50,
  "agent_consensus": {
    "chartanalyst": "BUY",
    "macroagent": "BUY",
    "marketsentinel": "HOLD"
  },
  "reasoning": "Bullish consensus with technical and macro alignment",
  "recommendations": ["Monitor closely", "Use stop loss"]
}
```

## System Requirements

- **Python 3.8+**
- **Node.js 16+**
- **Ollama** (with mistral:latest model)
- **Optional API Keys**: For enhanced data sources

## Environment Variables

Create `.env` file in project root:
```bash
# Trading API Keys (Optional)
GEMINI_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
POLYGON_API_KEY=your_key
FINNHUB_API_KEY=your_key
NEWS_API_KEY=your_key

# Email (for research summaries)
EMAIL_USER=your_email
EMAIL_PASS=your_password
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
```

## Troubleshooting

### Common Issues

1. **"Failed to connect to backend"**
   - Ensure MCP server is running: `python start_server.py`
   - Check backend URL in frontend (default: http://localhost:8000)

2. **"LLM generation failed"**
   - Start Ollama: `ollama serve`
   - Pull model: `ollama pull mistral:latest`

3. **No signals generated**
   - Check console for agent errors
   - Verify market data availability
   - Ensure Ollama is responding

### Debug Commands

```bash
# Test Ollama
curl http://localhost:11434/api/tags

# Test MCP server
curl http://localhost:8000/

# Test trading endpoint
curl -X POST http://localhost:8000/trading/signal \
  -H "Content-Type: application/json" \
  -d '{"symbol": "SPY"}'
```

## Development

### Frontend Development
```bash
cd frontend
npm run dev      # Development server
npm run build    # Production build
npm run preview  # Preview build
```

### Backend Development
```bash
cd mcp
python server.py  # Auto-reload enabled
```

### Trading Engine Development
```bash
cd mcp/trading
python main.py SPY  # Test trading system
```

## Security & Risk Management

- **No Automated Trading**: Signals are for analysis only
- **Human-in-the-Loop**: User validation required
- **Risk Assessment**: Built-in position sizing and stop loss
- **Data Privacy**: Local processing, no user data stored
- **API Security**: Optional API keys for enhanced features

## Performance

- **Sequential Agent Execution**: ~30-60 seconds per signal
- **Caching**: Market data cached to reduce API calls
- **Async Operations**: Non-blocking I/O for better responsiveness
- **Fallback Resilience**: System continues with reduced functionality

---

**Built with ❤️ using Vue.js, FastAPI, LangGraph, and Ollama**</content>
<parameter name="filePath">INTEGRATION_README.md