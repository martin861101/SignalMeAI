import os
import requests
import json
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Initialize LLM manager
def generate_llm_response(prompt, model_name="mistral:latest"):
    """Generate LLM response with Ollama fallback."""
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


# --- Data Structure for a Pivot Point ---
class Pivot:
    def __init__(self, time, price, is_high):
        self.time = time
        self.price = price
        self.is_high = is_high


# --- AB-CD Pattern Class ---
class ABCD_Pattern:
    def __init__(self, A, B, C, D, pattern_type, used_retr, used_ext):
        self.A = A
        self.B = B
        self.C = C
        self.D = D
        self.pattern_type = pattern_type  # "Bullish" or "Bearish"
        self.used_retr = used_retr
        self.used_ext = used_ext


# --- Pivot Detection Logic ---
def find_pivots(ohlcv_data, pivot_left=3, pivot_right=3):
    """
    Find swing highs and lows in OHLCV data
    """
    pivots = []
    n = len(ohlcv_data)

    for i in range(pivot_left, n - pivot_right):
        curr_high = ohlcv_data[i]["high"]
        curr_low = ohlcv_data[i]["low"]

        # Check for swing high
        is_high = True
        for j in range(1, pivot_left + 1):
            if ohlcv_data[i - j]["high"] > curr_high:
                is_high = False
                break
        if is_high:
            for j in range(1, pivot_right + 1):
                if ohlcv_data[i + j]["high"] > curr_high:
                    is_high = False
                    break

        # Check for swing low
        is_low = True
        for j in range(1, pivot_left + 1):
            if ohlcv_data[i - j]["low"] < curr_low:
                is_low = False
                break
        if is_low:
            for j in range(1, pivot_right + 1):
                if ohlcv_data[i + j]["low"] < curr_low:
                    is_low = False
                    break

        if is_high:
            pivots.append(Pivot(ohlcv_data[i]["time"], curr_high, True))
        if is_low:
            pivots.append(Pivot(ohlcv_data[i]["time"], curr_low, False))

    return pivots


# --- AB-CD Pattern Detection Logic ---
def detect_abcd_pattern(pivots, tolerance=0.10):
    """
    Detect AB-CD patterns from pivot points
    """
    if len(pivots) < 4:
        return None

    # Extract last four pivots
    A, B, C, D = pivots[-4], pivots[-3], pivots[-2], pivots[-1]

    pattern_found = False
    pattern_type = ""
    used_retr = 0.0
    used_ext = 0.0

    fib_retr_ratios = [0.382, 0.5, 0.618, 0.786, 0.886]
    fib_ext_ratios = [2.618, 2.0, 1.618, 1.272, 1.13]

    # Check for Bullish (High-Low-High-Low)
    if A.is_high and not B.is_high and C.is_high and not D.is_high:
        diff_ab = A.price - B.price
        if diff_ab > 0:
            bc_leg = C.price - B.price
            retrace = bc_leg / diff_ab
            cd_leg = C.price - D.price
            extension = cd_leg / bc_leg if bc_leg > 0 else 0

            for retr_ratio in fib_retr_ratios:
                for ext_ratio in fib_ext_ratios:
                    if (
                        abs(retrace - retr_ratio) <= tolerance
                        and abs(extension - ext_ratio) <= tolerance
                        and D.price < B.price
                    ):  # D must be lower than B for bullish
                        pattern_found = True
                        pattern_type = "Bullish"
                        used_retr = retr_ratio
                        used_ext = ext_ratio
                        break
                if pattern_found:
                    break

    # Check for Bearish (Low-High-Low-High)
    if not A.is_high and B.is_high and not C.is_high and D.is_high:
        diff_ab = B.price - A.price
        if diff_ab > 0:
            bc_leg = B.price - C.price
            retrace = bc_leg / diff_ab
            cd_leg = D.price - C.price
            extension = cd_leg / bc_leg if bc_leg > 0 else 0

            for retr_ratio in fib_retr_ratios:
                for ext_ratio in fib_ext_ratios:
                    if (
                        abs(retrace - retr_ratio) <= tolerance
                        and abs(extension - ext_ratio) <= tolerance
                        and D.price > B.price
                    ):  # D must be higher than B for bearish
                        pattern_found = True
                        pattern_type = "Bearish"
                        used_retr = retr_ratio
                        used_ext = ext_ratio
                        break
                if pattern_found:
                    break

    if pattern_found:
        return ABCD_Pattern(A, B, C, D, pattern_type, used_retr, used_ext)
    return None


# --- Helper to get next extension ---
def get_next_ext(used_ext):
    """Get the next Fibonacci extension level"""
    ext_map = {
        1.13: 1.272,
        1.272: 1.618,
        1.618: 2.0,
        2.0: 2.618,
        2.618: 2.618,  # Fallback to itself if max
    }
    return ext_map.get(used_ext, used_ext * 1.618)  # Default fallback


# --- Calculate Trade Levels ---
def calculate_trade_levels(
    abcd_pattern, current_ask, current_bid, min_point_size=0.0001
):
    """Calculate entry, stop loss, and take profit levels"""
    entry_price = 0
    stop_loss = 0
    take_profit = 0

    # Calculate pattern range (CD length)
    pattern_range = abs(abcd_pattern.C.price - abcd_pattern.D.price)

    # Determine next_ext for stop loss
    next_ext = get_next_ext(abcd_pattern.used_ext)

    if abcd_pattern.pattern_type == "Bullish":
        entry_price = current_ask
        bc_leg = abcd_pattern.C.price - abcd_pattern.B.price
        stop_loss = abcd_pattern.C.price - next_ext * bc_leg
        if stop_loss > abcd_pattern.D.price:
            stop_loss = abcd_pattern.D.price - 10 * min_point_size
        take_profit = abcd_pattern.D.price + 0.618 * pattern_range

    elif abcd_pattern.pattern_type == "Bearish":
        entry_price = current_bid
        bc_leg = abcd_pattern.B.price - abcd_pattern.C.price
        stop_loss = abcd_pattern.C.price + next_ext * bc_leg
        if stop_loss < abcd_pattern.D.price:
            stop_loss = abcd_pattern.D.price + 10 * min_point_size
        take_profit = abcd_pattern.D.price - 0.618 * pattern_range

    return entry_price, stop_loss, take_profit


# --- Enhanced Chart Analyst Function ---
def chartanalyst_node(state):
    """
    Enhanced chart analyst with pivot detection and AB-CD pattern recognition
    """
    symbol = state.get("symbol", "XAUUSD")
    price = state.get("price", 2000)
    timeframe = state.get("timeframe", "1h")
    news = state.get("news", "")
    ohlcv_data = state.get("ohlcv_data", [])  # Expected OHLCV data
    current_ask = state.get("current_ask", price)
    current_bid = state.get("current_bid", price - 0.0001)

    # Initialize analysis results
    analysis_results = {
        "agent": "chartanalyst",
        "symbol": symbol,
        "timeframe": timeframe,
        "pivot_analysis": {},
        "abcd_pattern": None,
        "trade_levels": {},
        "signal": "HOLD",
        "confidence": 50,
        "analysis": "",
        "timestamp": datetime.datetime.now().isoformat(),
    }

    try:
        # Perform pivot analysis if OHLCV data is available
        if ohlcv_data and len(ohlcv_data) >= 7:  # Minimum required for pivot detection
            pivots = find_pivots(ohlcv_data)

            analysis_results["pivot_analysis"] = {
                "total_pivots": len(pivots),
                "recent_pivots": [
                    {
                        "time": p.time.isoformat()
                        if hasattr(p.time, "isoformat")
                        else str(p.time),
                        "price": round(p.price, 5),
                        "type": "High" if p.is_high else "Low",
                    }
                    for p in pivots[-10:]  # Last 10 pivots
                ],
            }

            # Detect AB-CD pattern
            abcd_pattern = detect_abcd_pattern(pivots)
            if abcd_pattern:
                analysis_results["abcd_pattern"] = {
                    "type": abcd_pattern.pattern_type,
                    "points": {
                        "A": {
                            "price": round(abcd_pattern.A.price, 5),
                            "type": "High" if abcd_pattern.A.is_high else "Low",
                        },
                        "B": {
                            "price": round(abcd_pattern.B.price, 5),
                            "type": "High" if abcd_pattern.B.is_high else "Low",
                        },
                        "C": {
                            "price": round(abcd_pattern.C.price, 5),
                            "type": "High" if abcd_pattern.C.is_high else "Low",
                        },
                        "D": {
                            "price": round(abcd_pattern.D.price, 5),
                            "type": "High" if abcd_pattern.D.is_high else "Low",
                        },
                    },
                    "fibonacci_ratios": {
                        "retracement": round(abcd_pattern.used_retr, 3),
                        "extension": round(abcd_pattern.used_ext, 3),
                    },
                }

                # Calculate trade levels
                entry, sl, tp = calculate_trade_levels(
                    abcd_pattern, current_ask, current_bid
                )
                analysis_results["trade_levels"] = {
                    "entry": round(entry, 5),
                    "stop_loss": round(sl, 5),
                    "take_profit": round(tp, 5),
                    "risk_reward": round(abs(tp - entry) / abs(entry - sl), 2)
                    if abs(entry - sl) > 0
                    else 0,
                }

                # Set signal based on pattern
                if abcd_pattern.pattern_type == "Bullish":
                    analysis_results["signal"] = "BUY"
                    analysis_results["confidence"] = 80
                elif abcd_pattern.pattern_type == "Bearish":
                    analysis_results["signal"] = "SELL"
                    analysis_results["confidence"] = 80

        # Create enhanced prompt for LLM analysis
        enhanced_prompt = f"""
You are an advanced Chart Analyst specializing in technical analysis and pattern recognition.

Market Data for {symbol}:
- Current price: {price}
- Timeframe: {timeframe}
- Current Ask/Bid: {current_ask}/{current_bid}
- Recent news: {news}

Technical Analysis Results:
- Pivots detected: {analysis_results["pivot_analysis"].get("total_pivots", 0)}
- AB-CD Pattern: {"Detected " + analysis_results["abcd_pattern"]["type"] if analysis_results["abcd_pattern"] else "None detected"}

Provide comprehensive technical analysis including:
1. Overall market structure and trend
2. Key support/resistance levels
3. Pattern confirmation and reliability
4. Risk assessment
5. Trading recommendation with reasoning

Format your response clearly and concisely.
        """

        # Get LLM analysis
        llm_analysis = generate_llm_response(enhanced_prompt)
        analysis_results["analysis"] = llm_analysis

        # Override signal if LLM suggests different direction (with lower confidence)
        if llm_analysis and analysis_results["signal"] == "HOLD":
            if "BUY" in llm_analysis.upper() or "BULLISH" in llm_analysis.upper():
                analysis_results["signal"] = "BUY"
                analysis_results["confidence"] = 60
            elif "SELL" in llm_analysis.upper() or "BEARISH" in llm_analysis.upper():
                analysis_results["signal"] = "SELL"
                analysis_results["confidence"] = 60

        # Update state
        state["chart_signal"] = analysis_results
        return state

    except Exception as e:
        print(f"Error in enhanced chartanalyst: {e}")
        analysis_results["error"] = str(e)
        state["chart_signal"] = analysis_results
        return state


# --- Example Usage ---
if __name__ == "__main__":
    # Example state with OHLCV data
    example_ohlcv = [
        {
            "time": datetime.datetime(2025, 9, 1, 0, 0),
            "open": 1.1000,
            "high": 1.1050,
            "low": 1.0950,
            "close": 1.1000,
        },
        {
            "time": datetime.datetime(2025, 9, 1, 1, 0),
            "open": 1.1000,
            "high": 1.1100,
            "low": 1.0980,
            "close": 1.1050,
        },
        {
            "time": datetime.datetime(2025, 9, 1, 2, 0),
            "open": 1.1050,
            "high": 1.1150,
            "low": 1.1000,
            "close": 1.1100,
        },
        {
            "time": datetime.datetime(2025, 9, 1, 3, 0),
            "open": 1.1100,
            "high": 1.1200,
            "low": 1.1050,
            "close": 1.1150,
        },
        {
            "time": datetime.datetime(2025, 9, 1, 4, 0),
            "open": 1.1150,
            "high": 1.1180,
            "low": 1.1100,
            "close": 1.1120,
        },
        {
            "time": datetime.datetime(2025, 9, 1, 5, 0),
            "open": 1.1120,
            "high": 1.1150,
            "low": 1.1050,
            "close": 1.1080,
        },
        {
            "time": datetime.datetime(2025, 9, 1, 6, 0),
            "open": 1.1080,
            "high": 1.1100,
            "low": 1.1000,
            "close": 1.1020,
        },
        {
            "time": datetime.datetime(2025, 9, 1, 7, 0),
            "open": 1.1020,
            "high": 1.1080,
            "low": 1.1010,
            "close": 1.1060,
        },
        {
            "time": datetime.datetime(2025, 9, 1, 8, 0),
            "open": 1.1060,
            "high": 1.1120,
            "low": 1.1050,
            "close": 1.1100,
        },
        {
            "time": datetime.datetime(2025, 9, 1, 9, 0),
            "open": 1.1100,
            "high": 1.1160,
            "low": 1.1080,
            "close": 1.1140,
        },
        {
            "time": datetime.datetime(2025, 9, 1, 10, 0),
            "open": 1.1140,
            "high": 1.1150,
            "low": 1.1050,
            "close": 1.1070,
        },
        {
            "time": datetime.datetime(2025, 9, 1, 11, 0),
            "open": 1.1070,
            "high": 1.1080,
            "low": 1.0980,
            "close": 1.1000,
        },
        {
            "time": datetime.datetime(2025, 9, 1, 12, 0),
            "open": 1.1000,
            "high": 1.1020,
            "low": 1.0920,
            "close": 1.0950,
        },
        {
            "time": datetime.datetime(2025, 9, 1, 13, 0),
            "open": 1.0950,
            "high": 1.0970,
            "low": 1.0930,
            "close": 1.0960,
        },
    ]

    test_state = {
        "symbol": "EURUSD",
        "price": 1.0960,
        "timeframe": "1h",
        "news": "ECB dovish stance continues",
        "ohlcv_data": example_ohlcv,
        "current_ask": 1.0965,
        "current_bid": 1.0960,
    }

    # Run the enhanced chart analyst
    result_state = chartanalyst_node(test_state)
    print(json.dumps(result_state["chart_signal"], indent=2))
