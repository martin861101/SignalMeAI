#!/usr/bin/env python3
"""
Main entry point for ApexAI Aura Insight Trading Platform.
Runs the orchestrated workflow with real market data and Ollama fallback.
"""

import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestration.graph import TradingGraph
from langgraph.checkpoint.memory import MemorySaver


def main():
    parser = argparse.ArgumentParser(
        description="ApexAI Aura Insight - Trading Signal Generation"
    )
    parser.add_argument("symbol", help="Trading symbol (e.g., SPY, GC=F, ZAR=X)")
    parser.add_argument(
        "--timeframe", default="1h", help="Timeframe for analysis (default: 1h)"
    )
    parser.add_argument(
        "--ollama-only", action="store_true", help="Use only Ollama (skip API checks)"
    )

    args = parser.parse_args()

    # Check if Ollama is available
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        ollama_available = response.status_code == 200
    except:
        ollama_available = False

    if not ollama_available:
        print("⚠️  Ollama is not running. Please start Ollama locally:")
        print("   ollama serve")
        print("   ollama pull llama3.2")
        return

    print("🚀 ApexAI Aura Insight - Starting Orchestrated Analysis")
    print(f"📊 Symbol: {args.symbol}")
    print(f"⏰ Timeframe: {args.timeframe}")
    print(
        f"🤖 LLM: Ollama (llama3.2)"
        + (" + API fallback" if not args.ollama_only else "")
    )
    print("-" * 50)

    # Initialize memory for state management
    memory = MemorySaver()

    # Create trading graph
    try:
        trading_graph = TradingGraph(memory)
    except Exception as e:
        print(f"❌ Failed to initialize trading graph: {e}")
        return

    # Run signal generation
    try:
        result = asyncio.run(
            trading_graph.run_signal_generation(
                symbol=args.symbol, timeframe=args.timeframe
            )
        )

        if result.get("success"):
            signal_data = result.get("signal", {})
            print("✅ Analysis Complete!")
            print(f"🎯 Signal: {signal_data.get('direction', 'HOLD')}")
            print(".2%")
            print(f"📈 Entry: ${signal_data.get('entry_target', 0):.2f}")
            print(f"🎛️  Stop Loss: ${signal_data.get('stop_loss_target', 0):.2f}")
            print(f"🎯 Take Profit: ${signal_data.get('take_profit_target', 0):.2f}")
            print(f"⚖️  Risk/Reward: {signal_data.get('risk_reward_ratio', 0):.1f}")

            reasoning = signal_data.get("reasoning", "")
            if reasoning:
                print(
                    f"💭 Reasoning: {reasoning[:100]}..."
                    if len(reasoning) > 100
                    else f"💭 Reasoning: {reasoning}"
                )

        else:
            print("❌ Analysis failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Runtime error: {e}")


if __name__ == "__main__":
    main()
