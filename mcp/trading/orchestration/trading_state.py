from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class WorkflowState(str, Enum):
    INITIALIZED = "initialized"
    ANALYZING = "analyzing"
    SYNTHESIZING = "synthesizing"
    DECIDING = "deciding"
    AWAITING_FEEDBACK = "awaiting_feedback"
    COMPLETED = "completed"
    IDLE = "idle"

class MarketData(BaseModel):
    symbol: str
    current_price: float
    current_ask: float
    current_bid: float
    volume: int
    volatility: float
    timestamp: datetime
    ohlcv_data: List[Dict[str, Any]] = Field(default_factory=list)
    stat_levels: Dict[str, Any] = Field(default_factory=dict)
    news_summary: List[Dict[str, Any]] = Field(default_factory=list)
    risk_metrics: Dict[str, Any] = Field(default_factory=dict)

class TradingState(BaseModel):
    symbol: str
    timeframe: str = "1h"
    trigger_type: str = "user_initiated"
    trigger_time: datetime = Field(default_factory=datetime.now)
    current_state: WorkflowState = WorkflowState.INITIALIZED
    market_data: Optional[MarketData] = None
    chart_signal: Optional[Dict[str, Any]] = None
    macro_signal: Optional[Dict[str, Any]] = None
    sentiment_signal: Optional[Dict[str, Any]] = None
    final_signal: Optional[Dict[str, Any]] = None
    messages: List[str] = Field(default_factory=list)
    execution_time: Optional[float] = None

def create_initial_state(symbol: str, timeframe: str = "1h", trigger_type: str = "user_initiated") -> TradingState:
    """Create initial trading state."""
    return TradingState(
        symbol=symbol,
        timeframe=timeframe,
        trigger_type=trigger_type,
        current_state=WorkflowState.INITIALIZED,
        messages=[f"Initialized workflow for {symbol} at {datetime.now()}"]
    )

def update_state_market_data(state: TradingState, market_data: MarketData) -> TradingState:
    """Update state with market data."""
    state.market_data = market_data
    state.messages.append(f"Market data updated for {state.symbol}")
    return state

def update_state_final_signal(state: TradingState, final_signal: Dict[str, Any]) -> TradingState:
    """Update state with final signal."""
    state.final_signal = final_signal
    state.current_state = WorkflowState.DECIDING
    state.messages.append(f"Final signal generated: {final_signal.get('direction', 'UNKNOWN')}")
    return state

def should_generate_signal(state: TradingState) -> bool:
    """Determine if we should generate a signal based on current state."""
    # Check if we have market data and at least one agent signal
    has_market_data = state.market_data is not None
    has_agent_signals = any([
        state.chart_signal is not None,
        state.macro_signal is not None,
        state.sentiment_signal is not None
    ])
    return has_market_data and has_agent_signals

def get_workflow_summary(state: TradingState) -> Dict[str, Any]:
    """Get a summary of the workflow execution."""
    summary = {
        "symbol": state.symbol,
        "timeframe": state.timeframe,
        "trigger_type": state.trigger_type,
        "current_state": state.current_state.value,
        "execution_time": state.execution_time,
        "messages": state.messages,
        "success": state.current_state == WorkflowState.COMPLETED
    }

    if state.final_signal:
        summary["signal"] = state.final_signal

    if state.market_data:
        summary["market_data"] = {
            "current_price": state.market_data.current_price,
            "volume": state.market_data.volume,
            "volatility": state.market_data.volatility
        }

    return summary</content>
<parameter name="filePath">mcp/trading/orchestration/trading_state.py