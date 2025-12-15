import os
import asyncio
import time
from datetime import datetime
from typing import Dict, Any

import yfinance as yf
import pandas as pd
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# --- Updated Imports for the new State Management System ---
from .trading_state import (
    TradingState,
    WorkflowState,
    MarketData,
    create_initial_state,
    update_state_market_data,
    update_state_final_signal,
    get_workflow_summary,
    should_generate_signal  # Assuming this is also in trading_state
)

# --- Fetcher Imports ---
from fetchers.levels import LevelsAnalyzer
from fetchers.news import NewsProcessor
from fetchers.market_data import FinancialRiskAnalyzer
# --- Assumed Agent Node Imports ---
from agents.chartanalyst import chartanalyst_node
from agents.macroagent import macroagent_node
from agents.marketsentinel import marketsentinel_node
from agents.platformpilot import platformpilot_node

# Load environment variables (for NEWS_API_KEY)
load_dotenv()


class TradingGraph:
    """
    Enhanced LangGraph orchestration using a Pydantic model for robust state management
    and integrating comprehensive data analysis at the preparation stage.
    """
    def __init__(self, memory: MemorySaver):
        self.memory = memory
        self.workflow = self._build_workflow()
        self.news_api_key = os.getenv("NEWS_API_KEY")

    def _build_workflow(self):
        """Build the LangGraph workflow."""
        workflow = StateGraph(TradingState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_workflow)
        workflow.add_node("prepare_data", self._prepare_analysis_data)
        workflow.add_node("chart_analysis", chartanalyst_node)
        workflow.add_node("macro_analysis", macroagent_node)
        workflow.add_node("sentinel_analysis", marketsentinel_node)
        workflow.add_node("synthesize_signals", platformpilot_node)
        workflow.add_node("generate_signal", self._generate_final_signal)
        workflow.add_node("await_feedback", self._await_user_feedback)
        workflow.add_node("complete_workflow", self._complete_workflow)
        
        # Set entry point and edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "prepare_data")
        workflow.add_edge("prepare_data", "chart_analysis")
        workflow.add_edge("chart_analysis", "macro_analysis")
        workflow.add_edge("macro_analysis", "sentinel_analysis")
        workflow.add_conditional_edges(
            "sentinel_analysis", self._should_synthesize,
            {"synthesize": "synthesize_signals", "idle": "complete_workflow"}
        )
        workflow.add_conditional_edges(
            "synthesize_signals", self._should_generate_signal_decision,
            {"generate": "generate_signal", "hold": "complete_workflow"}
        )
        workflow.add_edge("generate_signal", "await_feedback")
        workflow.add_edge("await_feedback", "complete_workflow")
        
        return workflow.compile(checkpointer=self.memory)

    def _initialize_workflow(self, state: TradingState) -> TradingState:
        print(f"🚀 Initializing workflow for {state.symbol}")
        # The create_initial_state function already sets the state to INITIALIZED
        state.messages.append(f"Workflow initialized for {state.symbol} at {state.trigger_time}")
        return state

    def _prepare_analysis_data(self, state: TradingState) -> TradingState:
        """
        Fetches and analyzes data, then updates the state using the defined helper function.
        """
        symbol = state.symbol
        timeframe = state.timeframe
        print(f"🛠️ Preparing all analysis data for {symbol} ({timeframe})")
        
        try:
            # 1. Fetch Raw Market Data
            lookback_period = 100
            ohlcv_df = yf.download(symbol, period=f"{lookback_period}d", interval=timeframe)
            if ohlcv_df.empty:
                raise ValueError(f"No OHLCV data returned for {symbol}")
            if isinstance(ohlcv_df.columns, pd.MultiIndex):
                ohlcv_df.columns = ohlcv_df.columns.droplevel(1)
            
            # 2. Run All Analyses
            levels_analyzer = LevelsAnalyzer(ohlcv_df, lookback_period)
            stat_levels = levels_analyzer.calculate()
            print(f"   - Calculated Statistical Levels: Median at {stat_levels.get('median', 0):.2f}")

            news_processor = NewsProcessor(self.news_api_key)
            news_summary = news_processor.fetch_and_process(symbol, ohlcv_df)
            print(f"   - Collated {len(news_summary)} news summaries.")

            risk_analyzer = FinancialRiskAnalyzer(ohlcv_df)
            risk_metrics = risk_analyzer.calculate()
            print(f"   - Calculated Risk Metrics: Volatility at {risk_metrics.get('Annualized Volatility', 0):.2%}")
            
            # 3. Assemble the structured MarketData object
            latest_data = ohlcv_df.iloc[-1]
            market_data = MarketData(
                symbol=symbol,
                current_price=float(latest_data['Close']),
                current_ask=float(latest_data.get("Ask", latest_data['Close'])),
                current_bid=float(latest_data.get("Bid", latest_data['Close'])),
                volume=int(latest_data['Volume']),
                volatility=float(risk_metrics.get('Annualized Volatility', 0.0)),
                timestamp=ohlcv_df.index[-1].to_pydatetime(),
                ohlcv_data=ohlcv_df.reset_index().to_dict(orient='records'),
                # Add enriched analytical data to the market_data dictionary
                stat_levels=stat_levels,
                news_summary=news_summary,
                risk_metrics=risk_metrics
            )
            
            # 4. Update state using the helper function
            state.messages.append(f"Comprehensive data analysis complete for {symbol}.")
            state.current_state = WorkflowState.ANALYZING
            return update_state_market_data(state, market_data)

        except Exception as e:
            print(f"Error during data preparation: {e}. Using fallback data.")
            state.messages.append(f"Data preparation failed: {e}. Using fallback.")
            # Use fallback data and update state with the helper function
            fallback_data = MarketData(
                symbol=symbol, current_price=0.0, current_ask=0.0, current_bid=0.0,
                volume=0, volatility=0.0, timestamp=datetime.now(), ohlcv_data=[],
                stat_levels={}, news_summary=[], risk_metrics={}
            )
            state.current_state = WorkflowState.ANALYZING
            return update_state_market_data(state, fallback_data)

    def _should_synthesize(self, state: TradingState) -> str:
        """Determine if we should proceed to synthesis."""
        return "synthesize" if should_generate_signal(state) else "idle"
    
    def _should_generate_signal_decision(self, state: TradingState) -> str:
        """Determine if we should generate a signal or hold based on confidence."""
        final_signal = state.final_signal
        return "generate" if final_signal and final_signal.get("confidence", 0) >= 0.65 else "hold"

    async def _generate_final_signal(self, state: TradingState) -> TradingState:
        """Generate the final trading signal."""
        print(f"🎯 Generating final signal for {state.symbol}")
        final_signal = state.final_signal
        if final_signal:
            # Use the dedicated state update function
            return update_state_final_signal(state, final_signal)
        else:
            state.current_state = WorkflowState.IDLE
            state.messages.append("No signal generated - insufficient confidence")
            return state

    async def _await_user_feedback(self, state: TradingState) -> TradingState:
        print(f"👤 Awaiting user feedback for {state.symbol}")
        state.current_state = WorkflowState.AWAITING_FEEDBACK
        state.messages.append("Signal generated and awaiting user feedback")
        return state

    async def _complete_workflow(self, state: TradingState) -> TradingState:
        print(f"✅ Completing workflow for {state.symbol}")
        state.current_state = WorkflowState.COMPLETED
        state.execution_time = time.time() - state.trigger_time.timestamp()
        
        # Use the dedicated summary function
        summary = get_workflow_summary(state)
        state.messages.append(f"Workflow completed: {summary}")
        print(f"Workflow summary: {summary}")
        return state

    async def run_signal_generation(self, symbol: str, timeframe: str = "1h", trigger_type: str = "time_based") -> Dict[str, Any]:
        """Run the complete signal generation workflow."""
        # Use the state creation function
        initial_state = create_initial_state(symbol, timeframe, trigger_type)
        
        try:
            # The result will be a TradingState object
            result_state = await self.workflow.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": f"signal_{symbol}_{time.time()}"}}
            )
            summary = get_workflow_summary(result_state)
            summary["success"] = True
            return summary
        except Exception as e:
            return { "success": False, "error": str(e), "symbol": symbol }


