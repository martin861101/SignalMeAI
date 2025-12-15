import pandas as pd
import numpy as np
from typing import Dict, Any

class FinancialRiskAnalyzer:
    """
    Analyzes financial risk metrics from OHLCV data.
    """
    
    def __init__(self, ohlcv_df: pd.DataFrame):
        self.ohlcv_df = ohlcv_df
    
    def calculate(self) -> Dict[str, Any]:
        """
        Calculate risk metrics from OHLCV data.
        """
        if self.ohlcv_df.empty:
            return {}
        
        try:
            # Calculate returns
            returns = self.ohlcv_df['Close'].pct_change().dropna()
            
            if len(returns) == 0:
                return {}
            
            # Annualized volatility (assuming daily data)
            volatility = returns.std() * np.sqrt(252)
            
            # Sharpe ratio (assuming 2% risk-free rate)
            risk_free_rate = 0.02
            excess_returns = returns - risk_free_rate / 252
            sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
            
            # Maximum drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Value at Risk (95% confidence)
            var_95 = returns.quantile(0.05)
            
            return {
                'Annualized Volatility': float(volatility),
                'Sharpe Ratio': float(sharpe_ratio),
                'Maximum Drawdown': float(max_drawdown),
                'Value at Risk (95%)': float(var_95)
            }
            
        except Exception as e:
            print(f"Error calculating risk metrics: {e}")
            return {}</content>
<parameter name="filePath">mcp/trading/fetchers/market_data.py