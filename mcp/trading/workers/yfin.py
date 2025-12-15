
import os
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
import warnings

# Suppress ignorable warnings
warnings.filterwarnings('ignore')

# --- 1. Data Fetching Class ---
class MarketDataFetcher:
    """
    Responsible for fetching and preparing financial market data from Yahoo Finance.
    """
    def __init__(self, symbols: dict, period: str = "1y", interval: str = "1d"):
        self.symbols = symbols
        self.period = period
        self.interval = interval
        self.data = {}

    def fetch_all_data(self) -> dict:
        """Fetches OHLC data for all symbols and stores it."""
        print(f"\nFetching market data for {len(self.symbols)} instruments...")
        successful_fetches = 0
        for name, ticker in self.symbols.items():
            df = self._fetch_single_symbol(name, ticker)
            if not df.empty:
                self.data[name] = df
                successful_fetches += 1
                print(f"✓ Fetched {name} ({len(df)} observations)")
            else:
                print(f"✗ Failed to fetch {name}")
        
        print(f"\nSuccessfully fetched data for {successful_fetches}/{len(self.symbols)} symbols.")
        return self.data

    def _fetch_single_symbol(self, name: str, ticker: str) -> pd.DataFrame:
        """
        Fetches OHLC data for a single ticker with error handling and original cleaning logic.
        """
        try:
            df = yf.download(ticker, period=self.period, interval=self.interval, auto_adjust=False, progress=False)
            if df.empty:
                raise ValueError(f"No data returned for {ticker}")
            
            # <<< RESTORED ORIGINAL COLUMN CLEANING LOGIC >>>
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ["_".join([str(x).lower() for x in col if x]) for col in df.columns]
            else:
                df.columns = [str(c).lower() for c in df.columns]

            symbol_variants = [
                ticker.lower(),
                ticker.lower().replace("^", ""),
                ticker.lower().replace("=", ""),
                ticker.lower().replace("-", ""),
                ticker.lower().replace("^", "").replace("=", "").replace("-", "")
            ]
            cleaned_cols = {}
            for c in df.columns:
                matched = False
                for variant in symbol_variants:
                    if c.endswith("_" + variant):
                        base = c[: -(len(variant) + 1)]
                        cleaned_cols[c] = base
                        matched = True
                        break
                if not matched:
                    cleaned_cols[c] = c
            df.rename(columns=cleaned_cols, inplace=True)
            # <<< END OF RESTORED LOGIC >>>

            if "close" not in df.columns:
                if "adj_close" in df.columns:
                    df["close"] = df["adj_close"]
                else:
                    raise ValueError(f"{ticker}: no usable 'close' column. Available: {df.columns.tolist()}")
            
            return df.dropna(how="any")
        except Exception as e:
            # Silently handle errors
            return pd.DataFrame()

# --- 2. Financial Analysis Class ---
class FinancialAnalyzer:
    """
    Performs various financial analyses like correlation, risk metrics, and regression.
    """
    def __init__(self, data: dict):
        self.data = data

    def compute_correlation_matrix(self) -> pd.DataFrame:
        """Computes the static correlation matrix of asset returns."""
        valid_closes = {k: v["close"] for k, v in self.data.items() if "close" in v.columns and not v.empty}
        if len(valid_closes) < 2:
            print("Warning: Less than 2 valid symbols for correlation analysis.")
            return pd.DataFrame()
        price_df = pd.concat(valid_closes, axis=1).dropna()
        returns_df = price_df.pct_change().dropna()
        return returns_df.corr()

    def compute_rolling_correlations(self, window: int = 30) -> dict:
        """Computes rolling correlations between all pairs of assets."""
        valid_closes = {k: v["close"] for k, v in self.data.items() if "close" in v.columns and not v.empty}
        if len(valid_closes) < 2:
            return {}
        price_df = pd.concat(valid_closes, axis=1).dropna()
        returns_df = price_df.pct_change().dropna()
        rolling_corrs = {}
        symbols = list(returns_df.columns)
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                corr_name = f"{sym1}_vs_{sym2}"
                rolling_corrs[corr_name] = returns_df[sym1].rolling(window=window).corr(returns_df[sym2])
        return rolling_corrs

    def calculate_risk_metrics(self, returns_series: pd.Series) -> dict:
        """Calculates key risk metrics for a given return series."""
        returns_clean = returns_series.dropna()
        if len(returns_clean) == 0:
            return {}
        
        annualized_return = returns_clean.mean() * 252
        annualized_vol = returns_clean.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / annualized_vol if annualized_vol != 0 else 0
        
        cumulative = (1 + returns_clean).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max

        return {
            'Annualized Return': annualized_return,
            'Annualized Volatility': annualized_vol,
            'Sharpe Ratio': sharpe_ratio,
            'VaR (95%)': np.percentile(returns_clean, 5),
            'Max Drawdown': drawdown.min(),
            'Skewness': stats.skew(returns_clean),
            'Kurtosis': stats.kurtosis(returns_clean)
        }
        
    def perform_regression_analysis(self, dependent_returns: pd.Series, independent_returns: pd.DataFrame) -> dict:
        """Performs multiple regression or falls back to correlation."""
        # <<< RESTORED ORIGINAL FALLBACK LOGIC >>>
        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import r2_score

            combined = pd.concat([dependent_returns, independent_returns], axis=1).dropna()
            if len(combined) < 10:
                return {}

            y = combined.iloc[:, 0]
            X = combined.iloc[:, 1:]

            model = LinearRegression()
            model.fit(X, y)
            
            return {
                'R-squared': model.score(X, y),
                'Coefficients': dict(zip(X.columns, model.coef_)),
                'Intercept': model.intercept_
            }
        except ImportError:
            # Fallback if scikit-learn is not installed
            print("Warning: scikit-learn not found. Falling back to simple correlations.")
            correlations = {}
            for col in independent_returns.columns:
                aligned = pd.concat([dependent_returns, independent_returns[col]], axis=1).dropna()
                if len(aligned) > 1:
                    correlations[col] = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
            return {'Correlations': correlations}
        # <<< END OF RESTORED LOGIC >>>

# --- 3. Portfolio Backtesting Class ---
class PortfolioBacktester:
    """
    Runs simple portfolio backtests based on defined strategies and weights.
    """
    def __init__(self, data: dict, analyzer: FinancialAnalyzer, initial_capital: float = 10000):
        self.data = data
        self.analyzer = analyzer
        self.initial_capital = initial_capital

    def run_backtest(self, strategy_name: str, weights: dict) -> pd.Series:
        """Runs a backtest for a single portfolio strategy."""
        returns = pd.DataFrame()
        valid_weights = {}

        for name, df in self.data.items():
            if not df.empty and "close" in df.columns and name in weights:
                returns[name] = df["close"].pct_change()
                valid_weights[name] = weights[name]
        
        if not valid_weights:
            print(f"No valid symbols with data for '{strategy_name}' strategy.")
            return pd.Series()

        total_weight = sum(valid_weights.values())
        if total_weight == 0:
            return pd.Series()
        
        normalized_weights = {k: v / total_weight for k, v in valid_weights.items()}

        portfolio_ret = sum(returns[name] * normalized_weights[name] for name in valid_weights.keys())
        portfolio_ret = portfolio_ret.dropna()
        
        if portfolio_ret.empty:
            return pd.Series()
        
        print(f"\n--- {strategy_name} Strategy ---")
        risk_metrics = self.analyzer.calculate_risk_metrics(portfolio_ret)
        for metric, value in risk_metrics.items():
            print(f"{metric}: {value:.4f}")
            
        cumulative_value = (1 + portfolio_ret).cumprod() * self.initial_capital
        
        print(f"Final value: ${cumulative_value.iloc[-1]:,.2f}")
        print(f"Total return: {(cumulative_value.iloc[-1] / self.initial_capital - 1) * 100:.2f}%")
        
        return cumulative_value

# --- 4. Visualization Class ---
class Visualizer:
    """
    Creates all visualizations for the market analysis.
    """
    def __init__(self, data: dict, corr_matrix: pd.DataFrame, rolling_corrs: dict, portfolio_results: dict):
        self.data = data
        self.corr_matrix = corr_matrix
        self.rolling_corrs = rolling_corrs
        self.portfolio_results = portfolio_results

    def plot_analysis_dashboard(self):
        """Creates a 2x2 dashboard with key market analysis charts."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Cross-Market Analysis Dashboard', fontsize=16, fontweight='bold')

        # 1. Normalized Price Series
        ax1 = axes[0, 0]
        for name, df in self.data.items():
            if not df.empty and "close" in df.columns:
                normalized = df["close"] / df["close"].iloc[0]
                ax1.plot(normalized.index, normalized, label=name, linewidth=2)
        ax1.set_title("Normalized Price Series")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Correlation Heatmap
        ax2 = axes[0, 1]
        if not self.corr_matrix.empty:
            sns.heatmap(self.corr_matrix, annot=True, cmap='RdYlBu_r', center=0, square=True, ax=ax2, cbar_kws={'shrink': 0.8})
        ax2.set_title("Correlation Matrix")

        # 3. Rolling Correlations
        ax3 = axes[1, 0]
        for name, series in self.rolling_corrs.items():
            if not series.empty:
                ax3.plot(series.index, series, label=name, alpha=0.7)
        ax3.set_title("30-Day Rolling Correlations")
        ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)

        # 4. Return Distributions
        ax4 = axes[1, 1]
        # <<< RESTORED ORIGINAL HISTOGRAM PLOT >>>
        for name, df in self.data.items():
            if not df.empty and "close" in df.columns:
                returns = df["close"].pct_change().dropna()
                if len(returns) > 0:
                    ax4.hist(returns, bins=30, alpha=0.6, label=name, density=True)
        # <<< END OF RESTORED PLOT >>>
        ax4.set_title("Return Distributions")
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.show()

    def plot_portfolio_comparison(self):
        """Plots the performance of different portfolio strategies over time."""
        if not self.portfolio_results:
            return
            
        plt.figure(figsize=(12, 8))
        for name, portfolio_values in self.portfolio_results.items():
            plt.plot(portfolio_values.index, portfolio_values, label=name, linewidth=2)
        
        plt.title("Portfolio Strategy Comparison", fontsize=14, fontweight='bold')
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value ($)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

# --- 5. Main Orchestrator Class ---
class AnalysisOrchestrator:
    """
    Main class to orchestrate the entire analysis workflow.
    """
    def __init__(self, symbols: dict, strategies: dict):
        self.symbols = symbols
        self.strategies = strategies

    def run_analysis(self):
        """Executes the complete analysis pipeline."""
        print("=" * 60)
        print("ENHANCED CROSS-MARKET CORRELATION & HEDGING ANALYSIS")
        print("=" * 60)

        fetcher = MarketDataFetcher(self.symbols, period="1y")
        market_data = fetcher.fetch_all_data()

        if len(market_data) < 2:
            print("Insufficient data for meaningful analysis. Exiting.")
            return

        analyzer = FinancialAnalyzer(market_data)
        
        print("\n" + "="*50)
        print("CORRELATION ANALYSIS")
        print("="*50)
        corr_matrix = analyzer.compute_correlation_matrix()
        if not corr_matrix.empty:
            print("\nStatic Correlation Matrix:\n", corr_matrix.round(3))
        
        rolling_corrs = analyzer.compute_rolling_correlations(window=30)

        print("\n" + "="*50)
        print("MACRO/COMMODITY IMPACT ANALYSIS")
        print("="*50)
        macro_factors = ["Gold", "Silver", "Oil", "USD/ZAR", "USD/EUR", "VIX", "10Y_Treasury"]
        small_caps = ["SmallCap1", "SmallCap2", "SmallCap3"]
        for stock in small_caps:
            if stock in market_data:
                print(f"\n--- {stock} Factor Analysis ---")
                stock_returns = market_data[stock]["close"].pct_change().dropna()
                
                factor_returns = pd.DataFrame()
                for factor in macro_factors:
                    if factor in market_data:
                        factor_returns[factor] = market_data[factor]["close"].pct_change()

                if not factor_returns.empty:
                    regression_results = analyzer.perform_regression_analysis(stock_returns, factor_returns)
                    
                    # <<< RESTORED LOGIC TO HANDLE DIFFERENT REGRESSION OUTPUTS >>>
                    if 'Correlations' in regression_results:
                        print("Factor Correlations:")
                        for factor, corr in regression_results['Correlations'].items():
                            print(f"  {factor}: {corr:.3f}")
                    elif 'R-squared' in regression_results:
                        print(f"R-squared: {regression_results['R-squared']:.3f}")
                        print("Factor Exposures (Coefficients):")
                        for factor, coef in regression_results['Coefficients'].items():
                            print(f"  {factor}: {coef:.4f}")
                    # <<< END OF RESTORED LOGIC >>>

        print("\n" + "="*50)
        print("MULTI-ASSET PORTFOLIO BACKTESTING")
        print("="*50)
        backtester = PortfolioBacktester(market_data, analyzer)
        portfolio_results = {
            name: backtester.run_backtest(name, weights) 
            for name, weights in self.strategies.items()
        }
        # Filter out empty results
        portfolio_results = {k: v for k, v in portfolio_results.items() if not v.empty}

        print("\n" + "="*50)
        print("GENERATING VISUALIZATIONS")
        print("="*50)
        visualizer = Visualizer(market_data, corr_matrix, rolling_corrs, portfolio_results)
        visualizer.plot_analysis_dashboard()
        visualizer.plot_portfolio_comparison()
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)

if __name__ == "__main__":
    symbol_universe = {
        "SmallCap1": "AGMI",
        "SmallCap2": "IAUX",
        "SmallCap3": "KREF",
        "Gold": "GC=F",
        "Silver": "SI=F",
        "Oil": "CL=F",
        "USD/ZAR": "ZAR=X",
        "USD/EUR": "EURUSD=X",
        "S&P500": "^GSPC",
        "VIX": "^VIX",
        "10Y_Treasury": "^TNX"
    }

    portfolio_strategies = {
        "Equal Weight": {name: 1 for name in symbol_universe.keys()},
        "Small-Cap Focus": {"SmallCap1": 0.4, "SmallCap2": 0.3, "SmallCap3": 0.3},
        "Diversified": {"SmallCap1": 0.25, "SmallCap2": 0.25, "Gold": 0.15, "Silver": 0.10, "S&P500": 0.25},
        "Defensive": {"Gold": 0.3, "10Y_Treasury": 0.3, "S&P500": 0.4}
    }
    
    orchestrator = AnalysisOrchestrator(symbol_universe, portfolio_strategies)
    orchestrator.run_analysis()

