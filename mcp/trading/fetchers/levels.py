import pandas as pd
import numpy as np
from typing import Dict, Any

class LevelsAnalyzer:
    """
    Analyzes statistical levels from OHLCV data.
    """
    
    def __init__(self, ohlcv_df: pd.DataFrame, lookback_period: int = 100):
        self.ohlcv_df = ohlcv_df
        self.lookback_period = lookback_period
    
    def calculate(self) -> Dict[str, Any]:
        """
        Calculate statistical levels from OHLCV data.
        """
        if self.ohlcv_df.empty:
            return {}
        
        try:
            # Use recent data for analysis
            recent_data = self.ohlcv_df.tail(self.lookback_period)
            
            # Calculate statistical levels
            high = recent_data['High'].max()
            low = recent_data['Low'].min()
            close = recent_data['Close'].iloc[-1]
            
            # Simple moving averages
            sma_20 = recent_data['Close'].rolling(window=20).mean().iloc[-1] if len(recent_data) >= 20 else close
            sma_50 = recent_data['Close'].rolling(window=50).mean().iloc[-1] if len(recent_data) >= 50 else close
            
            # Support and resistance levels
            pivot = (high + low + close) / 3
            r1 = 2 * pivot - low
            s1 = 2 * pivot - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
            
            # Median and percentiles
            median = recent_data['Close'].median()
            q25 = recent_data['Close'].quantile(0.25)
            q75 = recent_data['Close'].quantile(0.75)
            
            return {
                'pivot': float(pivot),
                'r1': float(r1),
                'r2': float(r2),
                's1': float(s1),
                's2': float(s2),
                'median': float(median),
                'q25': float(q25),
                'q75': float(q75),
                'sma_20': float(sma_20),
                'sma_50': float(sma_50),
                'high': float(high),
                'low': float(low)
            }
            
        except Exception as e:
            print(f"Error calculating levels: {e}")
            return {}</content>
<parameter name="filePath">mcp/trading/fetchers/levels.py