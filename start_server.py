#!/usr/bin/env python3
"""
MCP Server Launcher
Starts the MCP server with trading capabilities.
"""

import os
import sys
import subprocess


def main():
    print("🚀 Starting ApexAI Aura Insight MCP Server")
    print("=" * 50)

    # Change to mcp directory
    mcp_dir = os.path.join(os.path.dirname(__file__), "mcp")
    os.chdir(mcp_dir)

    # Check if Ollama is running
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            print("✅ Ollama is running")
        else:
            print("⚠️  Ollama may not be running (unexpected response)")
    except:
        print("⚠️  Ollama is not running. Start with: ollama serve")
        print("   Then pull models: ollama pull mistral:latest")

    print("📡 Starting MCP server on http://localhost:8000")
    print("🔄 Trading signals available at /trading/signal")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    # Start the server
    try:
        subprocess.run([sys.executable, "server.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")


if __name__ == "__main__":
    main()
