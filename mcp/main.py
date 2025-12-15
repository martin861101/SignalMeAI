import time
import requests
import uvicorn
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- SELENIUM IMPORTS ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# --- CONFIGURATION ---
# GET YOUR KEY HERE: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY = "YOUR_API_KEY_HERE"
FOREX_FACTORY_URL = "https://www.forexfactory.com/calendar"

app = FastAPI(title="AI Trading Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 1. SELENIUM SCRAPER INTEGRATION ---
def setup_driver():
    """Setup Chromium/Chrome driver with headless options"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    try:
        service = Service(
            ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
        )
        driver = webdriver.Chrome(service=service, options=options)
    except Exception:
        # Fallback to standard Chrome
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    return driver


def format_day(date):
    """Convert date to ForexFactory format: monDD.YYYY"""
    return date.strftime("%b").lower() + date.strftime("%d.%Y")


def fetch_economic_events(days=3) -> List[Dict]:
    """Scrapes ForexFactory for High Impact events for the next N days"""
    print(f"--- Starting ForexFactory Scraper for next {days} days ---")
    driver = setup_driver()
    all_events = []

    try:
        today = datetime.utcnow()
        # Create list of dates to check
        dates_to_check = [today + timedelta(days=i) for i in range(days)]

        for date in dates_to_check:
            day_str = format_day(date)
            url = f"{FOREX_FACTORY_URL}?day={day_str}"

            try:
                driver.get(url)
                # Wait for table
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "calendar__table"))
                )

                rows = driver.find_elements(By.CSS_SELECTOR, "tr.calendar__row")

                for row in rows:
                    try:
                        # 1. Check Impact First (Optimization)
                        impact_el = row.find_elements(
                            By.CSS_SELECTOR,
                            "td.calendar__impact span.icon--ff-impact-red",
                        )
                        if not impact_el:
                            continue  # Skip non-red impact

                        # 2. Check Currency
                        currency_el = row.find_elements(
                            By.CSS_SELECTOR, "td.calendar__currency"
                        )
                        if not currency_el:
                            continue
                        currency = currency_el[0].text.strip()

                        # Filter: USD is primary, but keep Gold/Silver relevant ones if needed
                        if currency not in ["USD"]:
                            continue

                        # 3. Extract Details
                        event_name = row.find_element(
                            By.CSS_SELECTOR,
                            "td.calendar__event span.calendar__event-title",
                        ).text.strip()
                        event_time = row.find_element(
                            By.CSS_SELECTOR, "td.calendar__time"
                        ).text.strip()
                        forecast = row.find_elements(
                            By.CSS_SELECTOR, "td.calendar__forecast"
                        )[0].text.strip()

                        all_events.append(
                            {
                                "date": date.strftime("%Y-%m-%d"),
                                "time": event_time,
                                "currency": currency,
                                "event": event_name,
                                "forecast": forecast,
                                "impact": "HIGH",
                            }
                        )
                    except Exception:
                        continue  # Skip malformed rows
            except Exception as e:
                print(f"  Error scraping {day_str}: {e}")
                continue

    finally:
        driver.quit()
        print(f"--- Scraper finished. Found {len(all_events)} high impact events ---")

    return all_events


# --- 2. ALPHA VANTAGE AGENTS ---
def get_av_data(symbol: str, function: str, key: str = "Global Quote"):
    """Generic helper for Alpha Vantage API"""
    url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    try:
        r = requests.get(url)
        data = r.json()
        return data.get(key, {})
    except Exception as e:
        print(f"AV API Error: {e}")
        return {}


def get_sentiment(symbol: str):
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&limit=10&apikey={ALPHA_VANTAGE_API_KEY}"
    try:
        r = requests.get(url)
        data = r.json()
        items = data.get("feed", [])
        if not items:
            return 0, "NEUTRAL"

        # Calculate average sentiment score
        avg_score = sum(
            float(i.get("overall_sentiment_score", 0)) for i in items
        ) / len(items)
        label = "NEUTRAL"
        if avg_score > 0.15:
            label = "BULLISH"
        if avg_score < -0.15:
            label = "BEARISH"
        return avg_score, label
    except:
        return 0, "NEUTRAL"


# --- 3. API ENDPOINTS ---
class TradingSignalRequest(BaseModel):
    symbol: str


# Import trading agents
chart_agent_available = False
chartanalyst_node = None
MarketDataFetcher = None

try:
    from trading.agents.chartanalyst import chartanalyst_node
    from trading.workers.market_data import MarketDataFetcher

    chart_agent_available = True
except ImportError as e:
    print(f"Warning: Could not import trading agents: {e}")


@app.post("/trading/signal")
async def generate_signal(req: TradingSignalRequest):
    symbol = req.symbol.upper()
    print(f"Analyzing {symbol}...")

    # Try to use advanced trading agents if available
    if chart_agent_available and chartanalyst_node and MarketDataFetcher:
        try:
            # Fetch market data
            async with MarketDataFetcher() as fetcher:
                market_data = await fetcher.fetch_comprehensive_data(symbol, "1h")

            # Prepare state for chart agent
            state = {
                "symbol": symbol,
                "price": market_data.get("current_price", 0),
                "timeframe": "1h",
                "news": "",  # Could be populated from news fetcher
                "ohlcv_data": market_data.get("ohlcv_data", []),
                "current_ask": market_data.get(
                    "current_ask", market_data.get("current_price", 0)
                ),
                "current_bid": market_data.get(
                    "current_bid", market_data.get("current_price", 0)
                ),
            }

            # Run chart analysis (with timeout protection)
            try:
                import time

                start_time = time.time()
                chart_result = chartanalyst_node(state)
                elapsed = time.time() - start_time
                if elapsed > 10:  # If it took more than 10 seconds
                    print("Chart analysis took too long, using fallback")
                    chart_signal = {}
                else:
                    chart_signal = chart_result.get("chart_signal", {})
            except Exception as e:
                print(f"Chart analysis failed: {e}, using fallback")
                chart_signal = {}

            # Use chart signal if available and confident
            if chart_signal.get("confidence", 0) > 60:
                direction = (
                    "LONG"
                    if chart_signal.get("signal") == "BUY"
                    else "SHORT"
                    if chart_signal.get("signal") == "SELL"
                    else "NEUTRAL"
                )
                confidence = chart_signal.get("confidence", 50) / 100.0

                # Get trade levels
                trade_levels = chart_signal.get("trade_levels", {})
                entry = trade_levels.get("entry", market_data.get("current_price", 0))
                stop_loss = trade_levels.get("stop_loss", entry * 0.98)
                take_profit = trade_levels.get("take_profit", entry * 1.04)

                return {
                    "asset": symbol,
                    "direction": direction,
                    "confidence": confidence,
                    "entry_target": entry,
                    "stop_loss_target": stop_loss,
                    "take_profit_target": take_profit,
                    "risk_reward_ratio": 2.0,
                    "agent_consensus": {
                        "chartanalyst": chart_signal.get("signal", "HOLD"),
                        "macroagent": "HOLD",  # Placeholder
                        "marketsentinel": "HOLD",  # Placeholder
                    },
                    "confirming_factors": [
                        chart_signal.get("analysis", "")[:100] + "..."
                    ]
                    if chart_signal.get("analysis")
                    else [],
                    "conflicting_factors": [],
                    "macro_events": [],  # Will be populated if available
                    "reasoning": f"Chart analysis: {chart_signal.get('analysis', '')}",
                    "recommendations": ["Monitor technical levels closely"],
                    "risk_assessment": {
                        "market_risk": "MEDIUM",
                        "volatility_risk": "MEDIUM",
                        "liquidity_risk": "LOW",
                    },
                }
        except Exception as e:
            print(f"Error using advanced agents: {e}. Falling back to simple logic.")

    # Fallback to original simple logic
    # A. Fetch Market Data (Alpha Vantage)
    quote = get_av_data(symbol, "GLOBAL_QUOTE")
    current_price = float(quote.get("05. price", 0))

    # RSI (Technical Agent)
    rsi_data = get_av_data(
        symbol, "RSI", "Technical Analysis: RSI"
    )  # This returns dict of dates
    # Get latest RSI
    latest_rsi = 50.0
    if rsi_data:
        last_date = sorted(rsi_data.keys())[-1]
        latest_rsi = float(rsi_data[last_date]["RSI"])

    # Sentiment (News Agent)
    sent_score, sent_label = get_sentiment(symbol)

    # B. Fetch Macro Data (Selenium Agent)
    # We scrape 3 days ahead for context
    macro_events = fetch_economic_events(days=3)

    # C. Agent Consensus Logic
    # 1. Chart Analyst
    chart_vote = "HOLD"
    if latest_rsi > 70:
        chart_vote = "SELL"
    elif latest_rsi < 30:
        chart_vote = "BUY"

    # 2. Market Sentinel
    sent_vote = "HOLD"
    if sent_label == "BULLISH":
        sent_vote = "BUY"
    elif sent_label == "BEARISH":
        sent_vote = "SELL"

    # 3. Macro Agent
    # If high impact USD news is coming, be cautious
    macro_vote = "BUY"  # Default bullish on economic stability
    risk_factor = False
    for e in macro_events:
        if e["currency"] == "USD":
            risk_factor = True
            macro_vote = "HOLD"  # Caution
            break

    # D. Final Decision
    votes = [chart_vote, sent_vote, macro_vote]
    buy_count = votes.count("BUY")
    sell_count = votes.count("SELL")

    direction = "NEUTRAL"
    confidence = 0.50

    if buy_count >= 2:
        direction = "LONG"
        confidence = 0.70 + (0.1 * buy_count)
    elif sell_count >= 2:
        direction = "SHORT"
        confidence = 0.70 + (0.1 * sell_count)

    # E. Targets
    stop_loss = current_price * 0.98 if direction == "LONG" else current_price * 1.02
    take_profit = current_price * 1.04 if direction == "LONG" else current_price * 0.96

    return {
        "asset": symbol,
        "direction": direction,
        "confidence": min(confidence, 0.99),
        "entry_target": current_price,
        "stop_loss_target": stop_loss,
        "take_profit_target": take_profit,
        "risk_reward_ratio": 2.0,
        "agent_consensus": {
            "chartanalyst": chart_vote,
            "macroagent": macro_vote,
            "marketsentinel": sent_vote,
        },
        "confirming_factors": [
            f"RSI is {latest_rsi:.1f} ({chart_vote})",
            f"News Sentiment is {sent_label} ({sent_score:.2f})",
        ],
        "conflicting_factors": [
            f"{len(macro_events)} High Impact events ahead"
            if risk_factor
            else "No immediate macro threats"
        ],
        # PASSING SCRAPED EVENTS TO FRONTEND HERE
        "macro_events": macro_events,
        "reasoning": f"Technicals are {chart_vote}, Sentiment is {sent_vote}. Macro agent detected {len(macro_events)} high impact events.",
        "recommendations": [
            "Verify spread before entry" if risk_factor else "Standard entry size",
            "Monitor news release times",
        ],
        "risk_assessment": {
            "market_risk": "HIGH" if risk_factor else "LOW",
            "volatility_risk": "MEDIUM",
            "liquidity_risk": "LOW",
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
