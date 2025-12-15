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

# --- Fetcher Imports ---
try:
    from ..workers.market_data import MarketDataFetcher, FinancialRiskAnalyzer
    from ..fetchers.levels import LevelsAnalyzer
    from ..fetchers.news import NewsProcessor
except ImportError:
    # Fallback if fetchers not available
    MarketDataFetcher = None
    LevelsAnalyzer = None
    NewsProcessor = None
    FinancialRiskAnalyzer = None

# --- Agent Node Imports ---
try:
    from ..agents.chartanalyst import chartanalyst_node
    from ..agents.macroagent import macroagent_node
    from ..agents.marketsentinel import marketsentinel_node
    from ..agents.platformpilot import platformpilot_node
except ImportError:
    # Fallback functions
    def chartanalyst_node(state):
        return state

    def macroagent_node(state):
        return state

    def marketsentinel_node(state):
        return state

    def platformpilot_node(state):
        return state


# Load environment variables (for NEWS_API_KEY)
load_dotenv()


class TradingGraph:
    """
    LangGraph orchestration for trading signal generation using dict-based state.
    """

    def __init__(self, memory: MemorySaver):
        self.memory = memory
        self.workflow = self._build_workflow()
        self.news_api_key = os.getenv("NEWS_API_KEY")

    def _build_workflow(self):
        """Build the LangGraph workflow."""
        workflow = StateGraph(Dict[str, Any])

        # Add nodes
        workflow.add_node("initialize", self._initialize_workflow)
        workflow.add_node("prepare_data", self._prepare_analysis_data)
        workflow.add_node("run_agents", self._run_all_agents)
        workflow.add_node("synthesize_signals", platformpilot_node)
        workflow.add_node("generate_signal", self._generate_final_signal)
        workflow.add_node("await_feedback", self._await_user_feedback)
        workflow.add_node("complete_workflow", self._complete_workflow)

        # Set entry point and edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "prepare_data")
        workflow.add_edge("prepare_data", "run_agents")
        workflow.add_conditional_edges(
            "run_agents",
            self._should_synthesize,
            {"synthesize": "synthesize_signals", "idle": "complete_workflow"},
        )
        workflow.add_conditional_edges(
            "synthesize_signals",
            self._should_generate_signal_decision,
            {"generate": "generate_signal", "hold": "complete_workflow"},
        )
        workflow.add_edge("generate_signal", "await_feedback")
        workflow.add_edge("await_feedback", "complete_workflow")

        return workflow.compile(checkpointer=self.memory)

    def _initialize_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        symbol = state.get("symbol", "UNKNOWN")
        print(f"🚀 Initializing workflow for {symbol}")
        state["messages"] = state.get("messages", [])
        state["messages"].append(
            f"Workflow initialized for {symbol} at {datetime.now()}"
        )
        state["current_state"] = "initialized"
        return state

    def _prepare_analysis_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetches and analyzes data for the symbol using real market data fetcher.
        """
        symbol = state.get("symbol", "UNKNOWN")
        timeframe = state.get("timeframe", "1h")
        print(f"🛠️ Preparing all analysis data for {symbol} ({timeframe})")

        try:
            # Use comprehensive market data fetcher if available
            if MarketDataFetcher:
                # Run async fetcher in sync context
                import asyncio

                async def fetch_data():
                    async with MarketDataFetcher() as fetcher:
                        return await fetcher.fetch_comprehensive_data(symbol, timeframe)

                market_data = asyncio.run(fetch_data())

                # Extract data for state
                state["price"] = market_data.get("current_price", 0.0)
                state["current_ask"] = market_data.get("current_ask", state["price"])
                state["current_bid"] = market_data.get("current_bid", state["price"])
                state["volume"] = market_data.get("volume", 0)
                state["volatility"] = market_data.get("volatility", 0.0)
                state["ohlcv_data"] = market_data.get("ohlcv_data", [])
                state["market_data"] = market_data  # Store full market data

                print(
                    f"   - Fetched market data: Price ${state['price']:.2f}, Volume {state['volume']}"
                )
            else:
                # Fallback to basic yfinance
                lookback_period = 100
                ohlcv_df = yf.download(
                    symbol, period=f"{lookback_period}d", interval=timeframe
                )
                if ohlcv_df.empty:
                    raise ValueError(f"No OHLCV data returned for {symbol}")

                if isinstance(ohlcv_df.columns, pd.MultiIndex):
                    ohlcv_df.columns = ohlcv_df.columns.droplevel(1)

                latest_data = ohlcv_df.iloc[-1]
                state["price"] = float(latest_data["Close"])
                state["current_ask"] = float(
                    latest_data.get("Ask", latest_data["Close"])
                )
                state["current_bid"] = float(
                    latest_data.get("Bid", latest_data["Close"])
                )
                state["volume"] = int(latest_data["Volume"])
                state["ohlcv_data"] = ohlcv_df.reset_index().to_dict(orient="records")

            # Run additional analyses if available
            stat_levels = {}
            news_summary = []
            risk_metrics = {}

            # Convert OHLCV data back to DataFrame for analysis
            if state["ohlcv_data"]:
                ohlcv_df = pd.DataFrame(state["ohlcv_data"])
                if "Date" in ohlcv_df.columns:
                    ohlcv_df["Date"] = pd.to_datetime(ohlcv_df["Date"])
                    ohlcv_df.set_index("Date", inplace=True)

                lookback_period = len(ohlcv_df)

                if LevelsAnalyzer:
                    try:
                        levels_analyzer = LevelsAnalyzer(ohlcv_df, lookback_period)
                        stat_levels = levels_analyzer.calculate()
                        print(
                            f"   - Calculated Statistical Levels: Median at {stat_levels.get('median', 0):.2f}"
                        )
                    except Exception as e:
                        print(f"   - Levels analysis failed: {e}")

                if NewsProcessor and self.news_api_key:
                    try:
                        news_processor = NewsProcessor(self.news_api_key)
                        news_summary = news_processor.fetch_and_process(
                            symbol, ohlcv_df
                        )
                        print(f"   - Collated {len(news_summary)} news summaries.")
                    except Exception as e:
                        print(f"   - News processing failed: {e}")

                if FinancialRiskAnalyzer:
                    try:
                        risk_analyzer = FinancialRiskAnalyzer(ohlcv_df)
                        risk_metrics = risk_analyzer.calculate()
                        state["volatility"] = float(
                            risk_metrics.get("Annualized Volatility", 0.0)
                        )
                        print(
                            f"   - Calculated Risk Metrics: Volatility at {state['volatility']:.2%}"
                        )
                    except Exception as e:
                        print(f"   - Risk analysis failed: {e}")

            state["stat_levels"] = stat_levels
            state["news_summary"] = news_summary
            state["risk_metrics"] = risk_metrics

            state["messages"].append(
                f"Comprehensive data analysis complete for {symbol}."
            )
            state["current_state"] = "analyzing"
            return state

        except Exception as e:
            print(f"Error during data preparation: {e}. Using fallback data.")
            state["messages"].append(f"Data preparation failed: {e}. Using fallback.")
            state["price"] = 0.0
            state["current_ask"] = 0.0
            state["current_bid"] = 0.0
            state["volume"] = 0
            state["volatility"] = 0.0
            state["ohlcv_data"] = []
            state["stat_levels"] = {}
            state["news_summary"] = []
            state["risk_metrics"] = {}
            state["current_state"] = "analyzing"
            return state

        except Exception as e:
            print(f"Error during data preparation: {e}. Using fallback data.")
            state["messages"].append(f"Data preparation failed: {e}. Using fallback.")
            state["price"] = 0.0
            state["current_ask"] = 0.0
            state["current_bid"] = 0.0
            state["volume"] = 0
            state["volatility"] = 0.0
            state["ohlcv_data"] = []
            state["stat_levels"] = {}
            state["news_summary"] = []
            state["risk_metrics"] = {}
            state["current_state"] = "analyzing"
            return state

    def _run_all_agents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run all agents in sequence."""
        print("🤖 Running all agents...")

        # Run ChartAnalyst
        try:
            print("  📈 Running ChartAnalyst...")
            state = chartanalyst_node(state)
            print(
                f"  ✅ ChartAnalyst completed - signal: {state.get('chart_signal', {}).get('signal', 'NONE')}"
            )
        except Exception as e:
            print(f"  ❌ ChartAnalyst failed: {e}")

        # Run MacroAgent
        try:
            print("  🌍 Running MacroAgent...")
            state = macroagent_node(state)
            print(
                f"  ✅ MacroAgent completed - signal: {state.get('macro_analysis', {}).get('signal', 'NONE')}"
            )
        except Exception as e:
            print(f"  ❌ MacroAgent failed: {e}")

        # Run MarketSentinel
        try:
            print("  📊 Running MarketSentinel...")
            state = marketsentinel_node(state)
            print(
                f"  ✅ MarketSentinel completed - signal: {state.get('sentinel_analysis', {}).get('signal', 'NONE')}"
            )
        except Exception as e:
            print(f"  ❌ MarketSentinel failed: {e}")

        print(
            f"  📊 Signals check - chart: {bool(state.get('chart_signal'))}, macro: {bool(state.get('macro_analysis'))}, sentiment: {bool(state.get('sentinel_analysis'))}"
        )
        if state.get("chart_signal"):
            print(
                f"    Chart signal details: {state['chart_signal'].get('signal', 'NO_SIGNAL_KEY')}"
            )
        if state.get("macro_analysis"):
            print(
                f"    Macro signal details: {state['macro_analysis'].get('signal', 'NO_SIGNAL_KEY')}"
            )
        if state.get("sentinel_analysis"):
            print(
                f"    Sentinel signal details: {state['sentinel_analysis'].get('signal', 'NO_SIGNAL_KEY')}"
            )

        state["current_state"] = "analyzing"
        return state

    def _should_synthesize(self, state: Dict[str, Any]) -> str:
        """Determine if we should proceed to synthesis."""
        # Check if we have agent signals
        has_signals = any(
            [
                state.get("chart_signal"),
                state.get("macro_signal"),
                state.get("sentiment_signal"),
            ]
        )
        return "synthesize" if has_signals else "idle"

    def _should_generate_signal_decision(self, state: Dict[str, Any]) -> str:
        """Determine if we should generate a signal or hold based on confidence."""
        final_signal = state.get("final_signal", {})
        return (
            "generate"
            if final_signal and final_signal.get("confidence", 0) >= 0.65
            else "hold"
        )

    async def _generate_final_signal(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the final trading signal."""
        symbol = state.get("symbol", "UNKNOWN")
        print(f"🎯 Generating final signal for {symbol}")
        final_signal = state.get("final_signal")
        if final_signal:
            state["current_state"] = "deciding"
            return state
        else:
            state["current_state"] = "idle"
            state["messages"].append("No signal generated - insufficient confidence")
            return state

    async def _await_user_feedback(self, state: Dict[str, Any]) -> Dict[str, Any]:
        symbol = state.get("symbol", "UNKNOWN")
        print(f"👤 Awaiting user feedback for {symbol}")
        state["current_state"] = "awaiting_feedback"
        state["messages"].append("Signal generated and awaiting user feedback")
        return state

    async def _complete_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        symbol = state.get("symbol", "UNKNOWN")
        print(f"✅ Completing workflow for {symbol}")
        state["current_state"] = "completed"
        state["execution_time"] = time.time()

        summary = self._get_workflow_summary(state)
        state["messages"].append(f"Workflow completed: {summary}")
        print(f"Workflow summary: {summary}")
        return summary

    def _get_workflow_summary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the workflow execution."""
        summary = {
            "symbol": state.get("symbol"),
            "timeframe": state.get("timeframe", "1h"),
            "current_state": state.get("current_state"),
            "execution_time": state.get("execution_time"),
            "messages": state.get("messages", []),
            "success": state.get("current_state") == "completed",
        }

        final_signal = state.get("final_signal")
        if final_signal:
            summary["signal"] = final_signal

        if state.get("price"):
            summary["market_data"] = {
                "current_price": state.get("price"),
                "volume": state.get("volume", 0),
                "volatility": state.get("volatility", 0),
            }

        return summary

    async def run_signal_generation(
        self, symbol: str, timeframe: str = "1h", trigger_type: str = "user_initiated"
    ) -> Dict[str, Any]:
        """Run the complete signal generation workflow."""
        initial_state = {
            "symbol": symbol,
            "timeframe": timeframe,
            "trigger_type": trigger_type,
            "trigger_time": datetime.now(),
            "messages": [],
        }

        try:
            result_state = await self.workflow.ainvoke(
                initial_state,
                config={
                    "configurable": {"thread_id": f"signal_{symbol}_{time.time()}"}
                },
            )
            summary = self._get_workflow_summary(result_state)
            summary["success"] = True
            return summary
        except Exception as e:
            return {"success": False, "error": str(e), "symbol": symbol}
