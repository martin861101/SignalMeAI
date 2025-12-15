import os
import requests
import json
import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv
# LLM imports - using Ollama with fallback

# Load environment variables
load_dotenv()


class MarketSentinel:
    """
    MarketSentinel: The sentiment and flow analyst agent.
    Monitors social media, news headlines, and options flow data to gauge market sentiment
    and identify unusual activity or herd behavior related to specific assets.
    """

    def __init__(self):
        self.llm = self._initialize_llm()
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.sentiment_thresholds = {"bullish": 0.6, "bearish": -0.6, "neutral": 0.2}

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

    async def analyze_sentiment(
        self, symbol: str, timeframe: str = "1h"
    ) -> Dict[str, Any]:
        """
        Analyze market sentiment for a given symbol.
        """
        try:
            # Get news data
            news_data = await self._fetch_news(symbol)

            # Get social sentiment (simulated for now)
            social_sentiment = await self._analyze_social_sentiment(symbol)

            # Get volume analysis
            volume_analysis = await self._analyze_volume_patterns(symbol)

            # Combine all data for LLM analysis
            analysis_prompt = f"""
            You are a MarketSentinel agent specializing in sentiment and flow analysis.
            
            Analyze the following market sentiment data for {symbol}:
            
            News Headlines (last 24h):
            {json.dumps(news_data, indent=2)}
            
            Social Media Sentiment:
            {json.dumps(social_sentiment, indent=2)}
            
            Volume Analysis:
            {json.dumps(volume_analysis, indent=2)}
            
            Provide your analysis in the following JSON format:
            {{
                "sentiment_score": <float between -1.0 and 1.0>,
                "sentiment_direction": "<bullish/bearish/neutral>",
                "confidence": <float between 0.0 and 1.0>,
                "key_factors": [
                    "<factor1>",
                    "<factor2>",
                    "<factor3>"
                ],
                "anomalies_detected": [
                    "<anomaly1>",
                    "<anomaly2>"
                ],
                "alert_level": "<NONE/LOW/MEDIUM/HIGH>",
                "recommendations": [
                    "<recommendation1>",
                    "<recommendation2>"
                ],
                "reasoning": "<brief explanation of analysis>"
            }}
            """

            response_text = self._ollama_llm(analysis_prompt)
            try:
                result = json.loads(response_text)
                result["agent"] = "marketsentinel"
                result["symbol"] = symbol
                result["timestamp"] = datetime.datetime.now().isoformat()
                return result
            except json.JSONDecodeError:
                return self._create_fallback_response(symbol, "JSON parsing error")

        except Exception as e:
            return self._create_fallback_response(symbol, f"Analysis error: {str(e)}")

    async def _fetch_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch recent news for the symbol."""
        if not self.news_api_key:
            # Return mock data if no API key
            return [
                {
                    "title": f"Market Update: {symbol} shows mixed signals",
                    "source": "Financial News",
                    "published_at": datetime.datetime.now().isoformat(),
                    "sentiment": "neutral",
                },
                {
                    "title": f"Analysts bullish on {symbol} prospects",
                    "source": "Market Watch",
                    "published_at": datetime.datetime.now().isoformat(),
                    "sentiment": "bullish",
                },
            ]

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": symbol,
                "apiKey": self.news_api_key,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 10,
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("articles", [])[:5]  # Limit to 5 articles
            else:
                return self._get_mock_news(symbol)
        except Exception:
            return self._get_mock_news(symbol)

    def _get_mock_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Return mock news data."""
        return [
            {
                "title": f"{symbol} shows strong momentum in recent trading",
                "source": "Financial Times",
                "published_at": datetime.datetime.now().isoformat(),
                "sentiment": "bullish",
            },
            {
                "title": f"Market volatility affects {symbol} performance",
                "source": "Reuters",
                "published_at": datetime.datetime.now().isoformat(),
                "sentiment": "neutral",
            },
        ]

    async def _analyze_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze social media sentiment (simulated)."""
        # In a real implementation, this would connect to social media APIs
        # For now, we'll simulate sentiment analysis
        return {
            "twitter_sentiment": {
                "mentions": 1250,
                "sentiment_score": 0.3,
                "trending": True,
            },
            "reddit_sentiment": {
                "mentions": 45,
                "sentiment_score": 0.1,
                "subreddits": ["investing", "stocks"],
            },
            "overall_social_sentiment": 0.2,
        }

    async def _analyze_volume_patterns(self, symbol: str) -> Dict[str, Any]:
        """Analyze volume patterns for unusual activity."""
        # In a real implementation, this would analyze actual volume data
        return {
            "current_volume": 1500000,
            "avg_volume_30d": 1200000,
            "volume_ratio": 1.25,
            "unusual_activity": True,
            "volume_trend": "increasing",
        }

    def _create_fallback_response(self, symbol: str, error_msg: str) -> Dict[str, Any]:
        """Create a fallback response when analysis fails."""
        return {
            "agent": "marketsentinel",
            "symbol": symbol,
            "sentiment_score": 0.0,
            "sentiment_direction": "neutral",
            "confidence": 0.1,
            "key_factors": ["Limited data available"],
            "anomalies_detected": [],
            "alert_level": "NONE",
            "recommendations": ["Manual analysis recommended"],
            "reasoning": f"Analysis failed: {error_msg}",
            "timestamp": datetime.datetime.now().isoformat(),
        }


# Node function for LangGraph integration
def marketsentinel_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    MarketSentinel node for LangGraph workflow.
    """
    symbol = state.get("symbol", "SPY")
    timeframe = state.get("timeframe", "1h")

    sentinel = MarketSentinel()
    # Run the async function in sync context
    import asyncio

    analysis = asyncio.run(sentinel.analyze_sentiment(symbol, timeframe))

    # Update state with MarketSentinel analysis
    state["sentinel_analysis"] = analysis
    return state


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_marketsentinel():
        sentinel = MarketSentinel()
        result = await sentinel.analyze_sentiment("SPY")
        print(json.dumps(result, indent=2))

    asyncio.run(test_marketsentinel())
