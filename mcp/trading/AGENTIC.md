# ApexAI Aura Insight - Agentic Orchestration

## Overview

ApexAI Aura Insight is a sophisticated trading signal generation platform that orchestrates multiple specialized AI agents to provide transparent, actionable trading insights. This document details the assembled agentic elements, orchestration architecture, and implementation with real market data and Ollama LLM fallback.

## LLM Manager with Ollama Fallback

### Implementation (`model.py`)
- **LLMManager Class**: Manages LLM selection with automatic fallback hierarchy
- **Fallback Priority**: Gemini → Mistral → Moonshot → Ollama
- **Ollama Integration**: Direct API calls to local Ollama instance (default model: mistral:latest)
- **Error Handling**: Graceful degradation when APIs are unavailable

### Key Features
- Checks Ollama availability on initialization
- Generates responses via HTTP API calls to Ollama
- Supports multiple model configurations
- Thread-safe singleton instance

## Agent Descriptions

### ChartAnalyst (`agents/chartanalyst.py`)
**Role**: Technical analysis expert specializing in pattern recognition
- **Core Functions**:
  - Pivot point detection from OHLCV data
  - AB-CD pattern recognition with Fibonacci ratios
  - Support/resistance level identification
  - Trade level calculations (entry, stop loss, take profit)
- **LLM Integration**: Uses Ollama for comprehensive technical analysis
- **Output**: Signal direction (BUY/SELL/HOLD) with confidence scores

### MacroAgent (`agents/macroagent.py`)
**Role**: Economic analysis specialist monitoring macroeconomic environment
- **Core Functions**:
  - Economic calendar event tracking
  - Central bank policy analysis
  - News sentiment analysis (requires NEWS_API_KEY)
  - Geopolitical risk assessment
- **LLM Integration**: Generates economic outlook and impact analysis
- **Output**: Macroeconomic confidence scores and risk factors

### MarketSentinel (`agents/marketsentinel.py`)
**Role**: Sentiment and flow analyst for market psychology
- **Core Functions**:
  - Social media sentiment monitoring
  - News headline analysis
  - Volume pattern analysis
  - Unusual activity detection
- **LLM Integration**: Processes sentiment data for market direction signals
- **Output**: Sentiment scores and market anomaly alerts

### PlatformPilot (`agents/platformpilot.py`)
**Role**: Master orchestrator and chief strategist
- **Core Functions**:
  - Agent coordination and workflow management
  - Signal synthesis using weighted confidence scoring
  - Risk assessment and position sizing
  - Final signal generation with trade levels
- **Integration**: Uses SignalSynthesizer for advanced signal processing
- **Output**: Comprehensive trading signals with reasoning and recommendations

## Real Market Data Integration

### MarketDataFetcher (`workers/market_data.py`)
**Comprehensive Data Sources**:
- **Yahoo Finance**: Primary OHLCV data and company info
- **Alpha Vantage**: Real-time quotes and technical indicators
- **Polygon**: High-frequency market data
- **Finnhub**: Financial market data and news

### Features
- Asynchronous data fetching for performance
- Fallback handling when APIs are unavailable
- Risk metrics calculation (volatility, Sharpe ratio, drawdown)
- Watchlist support for multiple symbols

### Data Pipeline
1. Raw market data collection
2. Statistical analysis (levels, trends)
3. Risk assessment
4. Formatted state injection for agents

## Orchestration Workflow

### LangGraph Implementation (`orchestration/graph.py`)
**Workflow States**:
```
INITIALIZED → DATA_PREPARATION → AGENT_ANALYSIS → SYNTHESIS → SIGNAL_GENERATION → FEEDBACK → COMPLETED
```

### Node Structure
- **initialize**: Workflow setup and logging
- **prepare_data**: Real market data fetching and preprocessing
- **run_agents**: Sequential execution of ChartAnalyst, MacroAgent, MarketSentinel
- **synthesize_signals**: PlatformPilot signal synthesis
- **generate_signal**: Final signal formatting
- **await_feedback**: User feedback collection
- **complete_workflow**: Results logging and cleanup

### State Management
- **Dict-based State**: Flexible key-value storage for agent outputs
- **Memory Checkpointer**: Persistent state across executions
- **Error Recovery**: Graceful handling of agent failures

## Usage Instructions

### Prerequisites
- Python 3.8+
- Ollama installed and running locally
- Optional: API keys for enhanced data sources

### Installation
```bash
cd /home/projects/platform/mcp/trading
# Ensure dependencies are installed (see TRADING.md)
```

### Running the System
```bash
# Basic usage
python main.py SPY --timeframe 1h

# With different symbols
python main.py GC=F --timeframe 4h

# Help
python main.py --help
```

### Output Format
```json
{
  "asset": "SPY",
  "direction": "BUY",
  "confidence": 0.78,
  "entry_target": 450.50,
  "stop_loss_target": 448.25,
  "take_profit_target": 453.75,
  "signal_strength": "MODERATE",
  "reasoning": "Bullish technical setup with positive macro outlook"
}
```

## Current Status & Limitations

### ✅ Working Components
- Complete orchestration pipeline
- Real market data integration
- Ollama LLM fallback system
- All agents functional with error handling
- CLI interface with progress reporting

### ⚠️ Known Issues & Limitations
- Signal generation may be conservative (HOLD bias) due to data quality
- LLM responses depend on model quality and context
- Some data sources require API keys for full functionality
- Async agent execution could be optimized for parallel processing
- No automated trading (human-in-the-loop by design)

### 🔄 Potential Improvements
- Enhanced pattern recognition algorithms
- Real-time WebSocket data streaming
- Backtesting framework for signal validation
- User feedback learning system
- Cloud deployment options

## Technical Details

### Dependencies
- `langgraph`: Workflow orchestration
- `yfinance`: Primary market data
- `requests`: HTTP API calls (Ollama, news APIs)
- `pandas`: Data manipulation
- `asyncio`: Asynchronous operations

### Environment Variables
```bash
# Optional API Keys
GEMINI_API_KEY=your_key
MISTRAL_API_KEY=your_key
MOONSHOT_API_KEY=your_key
NEWS_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
POLYGON_API_KEY=your_key
FINNHUB_API_KEY=your_key
```

### Architecture Principles
- **Modularity**: Each agent is independently testable
- **Fallback Resilience**: System continues with reduced functionality
- **Transparency**: All signals include reasoning and confidence scores
- **Human-in-the-Loop**: User feedback required for validation
- **Security**: No automated execution, read-only data access

### Performance Considerations
- Sequential agent execution (could be parallelized)
- Caching for repeated data requests
- Timeout handling for API calls
- Memory management for large datasets

---

**ApexAI Aura Insight** - Empowering traders with AI-driven market intelligence through orchestrated agent collaboration.</content>
<parameter name="filePath">AGENTIC.md