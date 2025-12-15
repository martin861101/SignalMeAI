import os
import requests
import yfinance as yf
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MarketDataFetcher:
    """
    Enhanced market data fetcher for ApexAI Aura Insight.
    Integrates multiple data sources for comprehensive market analysis.
    """
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.polygon_key = os.getenv("POLYGON_API_KEY")
        self.finnhub_key = os.getenv("FINNHUB_API_KEY")
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_comprehensive_data(self, symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
        """
        Fetch comprehensive market data for a symbol.
        """
        try:
            # Fetch data from multiple sources in parallel
            tasks = [
                self._fetch_yahoo_data(symbol, timeframe),
                self._fetch_real_time_data(symbol),
                self._fetch_volume_data(symbol),
                self._fetch_volatility_data(symbol)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Combine results
            yahoo_data = results[0] if isinstance(results[0], dict) else {}
            real_time_data = results[1] if isinstance(results[1], dict) else {}
            volume_data = results[2] if isinstance(results[2], dict) else {}
            volatility_data = results[3] if isinstance(results[3], dict) else {}
            
            # Create comprehensive data structure
            comprehensive_data = {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.now().isoformat(),
                "yahoo_data": yahoo_data,
                "real_time_data": real_time_data,
                "volume_data": volume_data,
                "volatility_data": volatility_data,
                "current_price": real_time_data.get("current_price", yahoo_data.get("current_price", 0)),
                "current_ask": real_time_data.get("ask", 0),
                "current_bid": real_time_data.get("bid", 0),
                "volume": volume_data.get("current_volume", 0),
                "volatility": volatility_data.get("current_volatility", 0),
                "ohlcv_data": yahoo_data.get("ohlcv_data", [])
            }
            
            return comprehensive_data
            
        except Exception as e:
            print(f"Error fetching comprehensive data for {symbol}: {e}")
            return self._create_fallback_data(symbol)
    
    async def _fetch_yahoo_data(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Fetch data from Yahoo Finance."""
        try:
            # Map timeframe to yfinance interval
            interval_map = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "1h": "1h",
                "4h": "4h",
                "1d": "1d"
            }
            
            interval = interval_map.get(timeframe, "1h")
            period = "5d" if interval in ["1m", "5m", "15m"] else "1mo"
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                return {}
            
            # Convert to list of dictionaries
            ohlcv_data = []
            for idx, row in hist.iterrows():
                ohlcv_data.append({
                    "time": str(idx),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"])
                })
            
            # Get current info
            info = ticker.info
            
            return {
                "current_price": float(hist["Close"].iloc[-1]),
                "ohlcv_data": ohlcv_data,
                "market_cap": info.get("marketCap", 0),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "pe_ratio": info.get("trailingPE", 0),
                "beta": info.get("beta", 0)
            }
            
        except Exception as e:
            print(f"Error fetching Yahoo data for {symbol}: {e}")
            return {}
    
    async def _fetch_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time data from available APIs."""
        try:
            if self.alpha_vantage_key:
                return await self._fetch_alpha_vantage_data(symbol)
            elif self.polygon_key:
                return await self._fetch_polygon_data(symbol)
            elif self.finnhub_key:
                return await self._fetch_finnhub_data(symbol)
            else:
                return {"error": "No API keys available for real-time data"}

        except Exception as e:
            print(f"Error fetching real-time data for {symbol}: {e}")
            return {"error": f"Failed to fetch real-time data: {e}"}
    
    async def _fetch_alpha_vantage_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from Alpha Vantage API."""
        if not self.session or not self.alpha_vantage_key:
            return {}

        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    quote = data.get("Global Quote", {})
                    
                    return {
                        "current_price": float(quote.get("05. price", 0)),
                        "ask": float(quote.get("09. ask", 0)),
                        "bid": float(quote.get("08. bid", 0)),
                        "change": float(quote.get("09. change", 0)),
                        "change_percent": quote.get("10. change percent", "0%")
                    }
        except Exception as e:
            print(f"Alpha Vantage API error: {e}")
        
        return {}
    
    async def _fetch_polygon_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from Polygon API."""
        if not self.session or not self.polygon_key:
            return {}

        try:
            url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
            params = {"apikey": self.polygon_key}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    ticker_data = data.get("ticker", {})
                    
                    return {
                        "current_price": ticker_data.get("last", {}).get("price", 0),
                        "ask": ticker_data.get("lastQuote", {}).get("ask", 0),
                        "bid": ticker_data.get("lastQuote", {}).get("bid", 0),
                        "volume": ticker_data.get("day", {}).get("volume", 0)
                    }
        except Exception as e:
            print(f"Polygon API error: {e}")
        
        return {}
    
    async def _fetch_finnhub_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from Finnhub API."""
        if not self.session or not self.finnhub_key:
            return {}

        try:
            url = "https://finnhub.io/api/v1/quote"
            params = {
                "symbol": symbol,
                "token": self.finnhub_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        "current_price": data.get("c", 0),
                        "change": data.get("d", 0),
                        "change_percent": data.get("dp", 0),
                        "high": data.get("h", 0),
                        "low": data.get("l", 0),
                        "open": data.get("o", 0),
                        "previous_close": data.get("pc", 0)
                    }
        except Exception as e:
            print(f"Finnhub API error: {e}")
        
        return {}
    
    async def _fetch_volume_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch volume analysis data."""
        try:
            # Volume data requires real implementation
            return {"error": "Volume data not available"}
        except Exception as e:
            print(f"Error fetching volume data: {e}")
            return {"error": f"Failed to fetch volume data: {e}"}
    
    async def _fetch_volatility_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch volatility analysis data."""
        try:
            # Volatility data requires real implementation
            return {"error": "Volatility data not available"}
        except Exception as e:
            print(f"Error fetching volatility data: {e}")
            return {"error": f"Failed to fetch volatility data: {e}"}
    

    
    def _create_fallback_data(self, symbol: str) -> Dict[str, Any]:
        """Create fallback data when all sources fail."""
        return {
            "symbol": symbol,
            "error": "Data extraction failed"
        }
    
    async def fetch_watchlist_data(self, watchlist: List[str], timeframe: str = "1h") -> Dict[str, Dict[str, Any]]:
        """Fetch data for multiple symbols in parallel."""
        tasks = [self.fetch_comprehensive_data(symbol, timeframe) for symbol in watchlist]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        watchlist_data = {}
        for i, symbol in enumerate(watchlist):
            if isinstance(results[i], Exception):
                watchlist_data[symbol] = self._create_fallback_data(symbol)
            else:
                watchlist_data[symbol] = results[i]
        
        return watchlist_data

# Integration function for trading graph
async def fetch_market_data_for_symbol(symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
    """
    Standalone function to fetch market data for integration with trading graph.
    """
    async with MarketDataFetcher() as fetcher:
        return await fetcher.fetch_comprehensive_data(symbol, timeframe)

# --- FINANCIAL RISK ANALYZER CLASS ---
class FinancialRiskAnalyzer:
    def __init__(self, ohlcv_df: pd.DataFrame):
        self.ohlcv_df = ohlcv_df

    def calculate(self) -> Dict[str, Any]:
        """Calculate risk metrics from OHLCV data."""
        if self.ohlcv_df.empty:
            return {}
        try:
            # Calculate returns
            self.ohlcv_df['Returns'] = self.ohlcv_df['Close'].pct_change()
            returns = self.ohlcv_df['Returns'].dropna()

            # Annualized volatility (assuming daily data)
            volatility = returns.std() * (252 ** 0.5)  # 252 trading days

            # Sharpe ratio (assuming risk-free rate of 0.02)
            risk_free_rate = 0.02
            excess_returns = returns - risk_free_rate / 252
            sharpe_ratio = excess_returns.mean() / returns.std() * (252 ** 0.5) if returns.std() > 0 else 0

            # Maximum drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()

            # Value at Risk (95% confidence)
            var_95 = returns.quantile(0.05)

            return {
                'Annualized Volatility': volatility,
                'Sharpe Ratio': sharpe_ratio,
                'Maximum Drawdown': max_drawdown,
                'Value at Risk (95%)': var_95
            }
        except Exception as e:
            print(f"Risk calculation error: {e}")
            return {}

# Live data extraction for gold, silver, and USD/ZAR
if __name__ == "__main__":
    async def live_data_extraction():
        async with MarketDataFetcher() as fetcher:
            # Fetch data for gold, silver, and USD/ZAR
            symbols = ["GC=F", "SI=F", "ZAR=X"]
            watchlist_data = await fetcher.fetch_watchlist_data(symbols)
            print("Live Market Data:")
            for symbol, data in watchlist_data.items():
                if 'error' in data:
                    print(f"{symbol}: {data['error']}")
                else:
                    current_price = data.get('current_price', 'N/A')
                    volume = data.get('volume', 'N/A')
                    volatility = data.get('volatility', 'N/A')
                    print(f"{symbol}: ${current_price} (Vol: {volume}, Volat: {volatility})")

    asyncio.run(live_data_extraction())