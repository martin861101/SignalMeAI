import os
import requests
import json
import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv
# LLM imports - using Ollama with fallback

# Load environment variables
load_dotenv()


class MacroAgent:
    """
    MacroAgent: The economist agent.
    Monitors macroeconomic news, economic calendar events (CPI, FOMC meetings),
    geopolitical developments, and central bank statements to assess broad market impact.
    """

    def __init__(self):
        self.llm = self._initialize_llm()
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.economic_indicators = {
            "CPI": {"impact": "high", "frequency": "monthly"},
            "FOMC": {"impact": "high", "frequency": "quarterly"},
            "GDP": {"impact": "high", "frequency": "quarterly"},
            "Unemployment": {"impact": "medium", "frequency": "monthly"},
            "Interest_Rates": {"impact": "high", "frequency": "variable"},
        }

    def _initialize_llm(self):
        """Initialize LLM with Ollama fallback."""
        return self._ollama_llm

    def _ollama_llm(self, prompt: str) -> str:
        """Generate response using Ollama."""
        import requests

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "mistral:latest", "prompt": prompt, "stream": False},
                timeout=60,
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                return f"Ollama API error: {response.status_code}"
        except Exception as e:
            return f"LLM generation failed: {e}"

    async def analyze_macro_environment(
        self, symbol: str, timeframe: str = "1h"
    ) -> Dict[str, Any]:
        """
        Analyze macroeconomic environment and its impact on the given symbol.
        """
        try:
            # Get economic calendar events
            economic_events = await self._get_economic_calendar()

            # Get central bank news
            central_bank_news = await self._get_central_bank_news()

            # Get geopolitical developments
            geopolitical_news = await self._get_geopolitical_news()

            # Get market data context
            market_context = await self._get_market_context(symbol)

            # Combine all data for LLM analysis
            analysis_prompt = f"""
            You are a MacroAgent specializing in macroeconomic analysis and forecasting.
            
            Analyze the macroeconomic environment and its impact on {symbol}:
            
            Economic Calendar Events (upcoming):
            {json.dumps(economic_events, indent=2)}
            
            Central Bank News:
            {json.dumps(central_bank_news, indent=2)}
            
            Geopolitical Developments:
            {json.dumps(geopolitical_news, indent=2)}
            
            Market Context:
            {json.dumps(market_context, indent=2)}
            
            Provide your analysis in the following JSON format:
            {{
                "economic_outlook": "<bullish/bearish/neutral>",
                "key_drivers": [
                    "<driver1>",
                    "<driver2>",
                    "<driver3>"
                ],
                "forecast_impact": "<positive/negative/neutral>",
                "confidence": <float between 0.0 and 1.0>,
                "risk_factors": [
                    "<risk1>",
                    "<risk2>"
                ],
                "opportunities": [
                    "<opportunity1>",
                    "<opportunity2>"
                ],
                "economic_indicators_status": {{
                    "inflation": "<trending_up/trending_down/stable>",
                    "interest_rates": "<rising/falling/stable>",
                    "employment": "<improving/deteriorating/stable>",
                    "growth": "<accelerating/slowing/stable>"
                }},
                "recommendations": [
                    "<recommendation1>",
                    "<recommendation2>"
                ],
                "reasoning": "<brief explanation of macroeconomic analysis>"
            }}
            """

            response_text = self._ollama_llm(analysis_prompt)
            try:
                result = json.loads(response_text)
                result["agent"] = "macroagent"
                result["symbol"] = symbol
                result["timestamp"] = datetime.datetime.now().isoformat()
                return result
            except json.JSONDecodeError:
                return self._create_fallback_response(symbol, "JSON parsing error")

        except Exception as e:
            return self._create_fallback_response(symbol, f"Analysis error: {str(e)}")

    async def _get_economic_calendar(self) -> List[Dict[str, Any]]:
        """Get upcoming economic calendar events."""
        # In a real implementation, this would connect to economic calendar APIs
        # For now, we'll simulate economic events
        return [
            {
                "event": "CPI Release",
                "date": (
                    datetime.datetime.now() + datetime.timedelta(days=2)
                ).isoformat(),
                "impact": "high",
                "forecast": "3.2%",
                "previous": "3.1%",
            },
            {
                "event": "FOMC Meeting",
                "date": (
                    datetime.datetime.now() + datetime.timedelta(days=7)
                ).isoformat(),
                "impact": "high",
                "forecast": "Rate hold at 5.25%",
                "previous": "Rate hold at 5.25%",
            },
            {
                "event": "Unemployment Claims",
                "date": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat(),
                "impact": "medium",
                "forecast": "210K",
                "previous": "215K",
            },
        ]

    async def _get_central_bank_news(self) -> List[Dict[str, Any]]:
        """Get recent central bank news and statements."""
        if not self.news_api_key:
            return self._get_mock_central_bank_news()

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": "Federal Reserve OR ECB OR Bank of England",
                "apiKey": self.news_api_key,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 5,
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("articles", [])[:3]
            else:
                return self._get_mock_central_bank_news()
        except Exception:
            return self._get_mock_central_bank_news()

    def _get_mock_central_bank_news(self) -> List[Dict[str, Any]]:
        """Return mock central bank news."""
        return [
            {
                "title": "Fed maintains dovish stance amid inflation concerns",
                "source": "Federal Reserve",
                "published_at": datetime.datetime.now().isoformat(),
                "sentiment": "dovish",
            },
            {
                "title": "ECB signals potential rate cuts in Q2",
                "source": "European Central Bank",
                "published_at": datetime.datetime.now().isoformat(),
                "sentiment": "dovish",
            },
        ]

    async def _get_geopolitical_news(self) -> List[Dict[str, Any]]:
        """Get geopolitical developments that could affect markets."""
        if not self.news_api_key:
            return self._get_mock_geopolitical_news()

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": "geopolitical OR trade war OR sanctions",
                "apiKey": self.news_api_key,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 3,
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("articles", [])[:2]
            else:
                return self._get_mock_geopolitical_news()
        except Exception:
            return self._get_mock_geopolitical_news()

    def _get_mock_geopolitical_news(self) -> List[Dict[str, Any]]:
        """Return mock geopolitical news."""
        return [
            {
                "title": "Trade tensions ease between major economies",
                "source": "Reuters",
                "published_at": datetime.datetime.now().isoformat(),
                "impact": "positive",
            },
            {
                "title": "Energy sector faces supply chain challenges",
                "source": "Bloomberg",
                "published_at": datetime.datetime.now().isoformat(),
                "impact": "negative",
            },
        ]

    async def _get_market_context(self, symbol: str) -> Dict[str, Any]:
        """Get broader market context for the symbol."""
        # In a real implementation, this would fetch actual market data
        return {
            "market_sector": "Technology"
            if "AAPL" in symbol or "MSFT" in symbol
            else "General",
            "market_cap": "Large Cap",
            "volatility_index": "VIX",
            "current_vix": 18.5,
            "market_trend": "Bullish",
            "sector_performance": "+2.3%",
            "correlation_spy": 0.85,
        }

    def _create_fallback_response(self, symbol: str, error_msg: str) -> Dict[str, Any]:
        """Create a fallback response when analysis fails."""
        return {
            "agent": "macroagent",
            "symbol": symbol,
            "economic_outlook": "neutral",
            "key_drivers": ["Limited data available"],
            "forecast_impact": "neutral",
            "confidence": 0.1,
            "risk_factors": ["Data availability issues"],
            "opportunities": ["Manual analysis recommended"],
            "economic_indicators_status": {
                "inflation": "stable",
                "interest_rates": "stable",
                "employment": "stable",
                "growth": "stable",
            },
            "recommendations": ["Monitor economic indicators"],
            "reasoning": f"Analysis failed: {error_msg}",
            "timestamp": datetime.datetime.now().isoformat(),
        }


# Node function for LangGraph integration
def macroagent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    MacroAgent node for LangGraph workflow.
    """
    symbol = state.get("symbol", "SPY")
    timeframe = state.get("timeframe", "1h")

    macro_agent = MacroAgent()
    # Run the async function in sync context
    import asyncio

    analysis = asyncio.run(macro_agent.analyze_macro_environment(symbol, timeframe))

    # Update state with MacroAgent analysis
    state["macro_analysis"] = analysis
    return state


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_macroagent():
        macro_agent = MacroAgent()
        result = await macro_agent.analyze_macro_environment("SPY")
        print(json.dumps(result, indent=2))

    asyncio.run(test_macroagent())
