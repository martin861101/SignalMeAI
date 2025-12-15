import json
import math
from typing import Dict, Any, List, Tuple
from datetime import datetime
from enum import Enum

class SignalDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    HOLD = "HOLD"

class SignalStrength(Enum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class SignalSynthesizer:
    """
    Advanced signal synthesis and confidence scoring system for ApexAI Aura Insight.
    Implements sophisticated algorithms to combine agent analyses and generate final trading signals.
    """
    
    def __init__(self):
        # Agent weights based on market conditions and historical performance
        self.base_agent_weights = {
            "chartanalyst": 0.4,    # Technical analysis
            "macroagent": 0.3,      # Macro analysis
            "marketsentinel": 0.3   # Sentiment analysis
        }
        
        # Confidence thresholds
        self.confidence_thresholds = {
            "strong_signal": 0.75,
            "moderate_signal": 0.65,
            "weak_signal": 0.55,
            "hold_threshold": 0.65
        }
        
        # Risk assessment parameters
        self.risk_parameters = {
            "volatility_threshold": 0.20,
            "volume_threshold": 1.5,  # Volume ratio
            "correlation_threshold": 0.7
        }
    
    def synthesize_signal(self, 
                         symbol: str,
                         chart_analysis: Dict[str, Any],
                         macro_analysis: Dict[str, Any],
                         sentinel_analysis: Dict[str, Any],
                         market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize final trading signal from all agent analyses.
        """
        try:
            # Extract agent signals and confidences
            agent_signals = self._extract_agent_signals(chart_analysis, macro_analysis, sentinel_analysis)
            
            # Calculate weighted confidence
            weighted_confidence = self._calculate_weighted_confidence(
                agent_signals["chartanalyst"]["confidence"],
                agent_signals["macroagent"]["confidence"],
                agent_signals["sentinel"]["confidence"]
            )
            
            # Determine signal direction
            signal_direction = self._determine_signal_direction(agent_signals, weighted_confidence)
            
            # Calculate signal strength
            signal_strength = self._calculate_signal_strength(weighted_confidence, agent_signals)
            
            # Assess risks
            risk_assessment = self._assess_risks(market_data, agent_signals)
            
            # Generate trade levels
            trade_levels = self._calculate_trade_levels(
                symbol, signal_direction, market_data, agent_signals
            )
            
            # Identify confirming and conflicting factors
            confirming_factors, conflicting_factors = self._identify_factors(agent_signals)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                signal_direction, signal_strength, risk_assessment, agent_signals
            )
            
            # Create final signal
            final_signal = {
                "asset": symbol,
                "direction": signal_direction.value,
                "confidence": weighted_confidence,
                "entry_target": trade_levels["entry"],
                "stop_loss_target": trade_levels["stop_loss"],
                "take_profit_target": trade_levels["take_profit"],
                "risk_reward_ratio": trade_levels["risk_reward"],
                "signal_strength": signal_strength.value,
                "agent_consensus": {
                    "chartanalyst": agent_signals["chartanalyst"]["signal"],
                    "macroagent": agent_signals["macroagent"]["signal"],
                    "marketsentinel": agent_signals["sentinel"]["signal"]
                },
                "confirming_factors": confirming_factors,
                "conflicting_factors": conflicting_factors,
                "risk_assessment": risk_assessment,
                "reasoning": self._generate_reasoning(agent_signals, signal_direction, weighted_confidence),
                "recommendations": recommendations,
                "next_review_time": self._calculate_next_review_time(signal_strength),
                "timestamp": datetime.now().isoformat(),
                "workflow_id": f"signal_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            return final_signal
            
        except Exception as e:
            return self._create_error_signal(symbol, str(e))
    
    def _extract_agent_signals(self, chart_analysis: Dict[str, Any], 
                              macro_analysis: Dict[str, Any], 
                              sentinel_analysis: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract signals and confidences from agent analyses."""
        return {
            "chartanalyst": {
                "signal": self._normalize_signal(chart_analysis.get("signal", "HOLD")),
                "confidence": chart_analysis.get("confidence", 0.0) / 100.0 if chart_analysis.get("confidence", 0) > 1 else chart_analysis.get("confidence", 0.0),
                "analysis": chart_analysis.get("analysis", ""),
                "key_factors": chart_analysis.get("key_factors", [])
            },
            "macroagent": {
                "signal": self._convert_macro_signal(macro_analysis.get("economic_outlook", "neutral")),
                "confidence": macro_analysis.get("confidence", 0.0),
                "analysis": macro_analysis.get("reasoning", ""),
                "key_factors": macro_analysis.get("key_drivers", [])
            },
            "sentinel": {
                "signal": self._convert_sentiment_signal(sentinel_analysis.get("sentiment_direction", "neutral")),
                "confidence": sentinel_analysis.get("confidence", 0.0),
                "analysis": sentinel_analysis.get("reasoning", ""),
                "key_factors": sentinel_analysis.get("key_factors", [])
            }
        }
    
    def _normalize_signal(self, signal: str) -> str:
        """Normalize signal to standard format."""
        signal_upper = signal.upper()
        if signal_upper in ["BUY", "LONG", "BULLISH"]:
            return "LONG"
        elif signal_upper in ["SELL", "SHORT", "BEARISH"]:
            return "SHORT"
        else:
            return "HOLD"
    
    def _convert_macro_signal(self, outlook: str) -> str:
        """Convert macro outlook to signal."""
        outlook_lower = outlook.lower()
        if outlook_lower == "bullish":
            return "LONG"
        elif outlook_lower == "bearish":
            return "SHORT"
        else:
            return "HOLD"
    
    def _convert_sentiment_signal(self, sentiment: str) -> str:
        """Convert sentiment to signal."""
        sentiment_lower = sentiment.lower()
        if sentiment_lower == "bullish":
            return "LONG"
        elif sentiment_lower == "bearish":
            return "SHORT"
        else:
            return "HOLD"
    
    def _calculate_weighted_confidence(self, chart_conf: float, macro_conf: float, sentinel_conf: float) -> float:
        """Calculate weighted confidence score."""
        weighted_conf = (
            chart_conf * self.base_agent_weights["chartanalyst"] +
            macro_conf * self.base_agent_weights["macroagent"] +
            sentinel_conf * self.base_agent_weights["marketsentinel"]
        )
        
        # Apply confidence adjustment based on agreement
        agreement_bonus = self._calculate_agreement_bonus(chart_conf, macro_conf, sentinel_conf)
        final_confidence = min(1.0, weighted_conf + agreement_bonus)
        
        return max(0.0, final_confidence)
    
    def _calculate_agreement_bonus(self, chart_conf: float, macro_conf: float, sentinel_conf: float) -> float:
        """Calculate bonus for agent agreement."""
        confidences = [chart_conf, macro_conf, sentinel_conf]
        avg_confidence = sum(confidences) / len(confidences)
        
        # Calculate variance (lower variance = higher agreement)
        variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
        
        # Convert variance to agreement bonus (0.0 to 0.1)
        agreement_bonus = max(0.0, 0.1 - variance * 2)
        
        return agreement_bonus
    
    def _determine_signal_direction(self, agent_signals: Dict[str, Dict[str, Any]], confidence: float) -> SignalDirection:
        """Determine final signal direction based on agent consensus and confidence."""
        signals = [agent_signals["chartanalyst"]["signal"], 
                  agent_signals["macroagent"]["signal"], 
                  agent_signals["sentinel"]["signal"]]
        
        # Count signal types
        long_count = signals.count("LONG")
        short_count = signals.count("SHORT")
        hold_count = signals.count("HOLD")
        
        # Determine direction based on consensus
        if long_count >= 2 and confidence >= self.confidence_thresholds["hold_threshold"]:
            return SignalDirection.LONG
        elif short_count >= 2 and confidence >= self.confidence_thresholds["hold_threshold"]:
            return SignalDirection.SHORT
        else:
            return SignalDirection.HOLD
    
    def _calculate_signal_strength(self, confidence: float, agent_signals: Dict[str, Dict[str, Any]]) -> SignalStrength:
        """Calculate signal strength based on confidence and agent agreement."""
        if confidence >= self.confidence_thresholds["strong_signal"]:
            return SignalStrength.STRONG
        elif confidence >= self.confidence_thresholds["moderate_signal"]:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _assess_risks(self, market_data: Dict[str, Any], agent_signals: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Assess various risk factors."""
        volatility = market_data.get("volatility", 0.0)
        volume = market_data.get("volume", 0)
        avg_volume = market_data.get("yahoo_data", {}).get("avg_volume_30d", volume)
        
        # Market risk based on volatility
        if volatility >= self.risk_parameters["volatility_threshold"]:
            market_risk = RiskLevel.HIGH
        elif volatility >= self.risk_parameters["volatility_threshold"] * 0.7:
            market_risk = RiskLevel.MEDIUM
        else:
            market_risk = RiskLevel.LOW
        
        # Volatility risk
        volatility_risk = market_risk  # Same as market risk for now
        
        # Liquidity risk based on volume
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
        if volume_ratio >= self.risk_parameters["volume_threshold"]:
            liquidity_risk = RiskLevel.LOW
        elif volume_ratio >= 1.0:
            liquidity_risk = RiskLevel.MEDIUM
        else:
            liquidity_risk = RiskLevel.HIGH
        
        return {
            "market_risk": market_risk.value,
            "volatility_risk": volatility_risk.value,
            "liquidity_risk": liquidity_risk.value
        }
    
    def _calculate_trade_levels(self, symbol: str, direction: SignalDirection, 
                               market_data: Dict[str, Any], agent_signals: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Calculate entry, stop loss, and take profit levels."""
        current_price = market_data.get("current_price", 0.0)
        current_ask = market_data.get("current_ask", current_price)
        current_bid = market_data.get("current_bid", current_price)
        volatility = market_data.get("volatility", 0.15)
        
        # Base risk percentage (2% of price)
        risk_percentage = 0.02
        
        if direction == SignalDirection.LONG:
            entry = current_ask
            stop_loss = entry * (1 - risk_percentage)
            take_profit = entry * (1 + risk_percentage * 2)  # 2:1 risk/reward
        elif direction == SignalDirection.SHORT:
            entry = current_bid
            stop_loss = entry * (1 + risk_percentage)
            take_profit = entry * (1 - risk_percentage * 2)  # 2:1 risk/reward
        else:
            entry = current_price
            stop_loss = current_price
            take_profit = current_price
        
        # Calculate risk/reward ratio
        if direction != SignalDirection.HOLD:
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            risk_reward = reward / risk if risk > 0 else 0.0
        else:
            risk_reward = 0.0
        
        return {
            "entry": round(entry, 2),
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "risk_reward": round(risk_reward, 2)
        }
    
    def _identify_factors(self, agent_signals: Dict[str, Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """Identify confirming and conflicting factors."""
        confirming_factors = []
        conflicting_factors = []
        
        # Extract factors from each agent
        chart_factors = agent_signals["chartanalyst"]["key_factors"]
        macro_factors = agent_signals["macroagent"]["key_factors"]
        sentinel_factors = agent_signals["sentinel"]["key_factors"]
        
        # Look for common themes (confirming factors)
        all_factors = chart_factors + macro_factors + sentinel_factors
        factor_counts = {}
        
        for factor in all_factors:
            factor_counts[factor] = factor_counts.get(factor, 0) + 1
        
        # Factors mentioned by multiple agents are confirming
        for factor, count in factor_counts.items():
            if count >= 2:
                confirming_factors.append(factor)
        
        # Check for conflicting signals
        signals = [agent_signals["chartanalyst"]["signal"], 
                  agent_signals["macroagent"]["signal"], 
                  agent_signals["sentinel"]["signal"]]
        
        if len(set(signals)) > 1:  # Multiple different signals
            conflicting_factors.append("Mixed signals from different agents")
        
        return confirming_factors, conflicting_factors
    
    def _generate_recommendations(self, direction: SignalDirection, strength: SignalStrength, 
                                 risk_assessment: Dict[str, str], agent_signals: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate trading recommendations."""
        recommendations = []
        
        if direction == SignalDirection.HOLD:
            recommendations.append("Wait for clearer signals before entering position")
            recommendations.append("Monitor market conditions for better entry points")
        else:
            if strength == SignalStrength.STRONG:
                recommendations.append("Consider taking position with full allocation")
            elif strength == SignalStrength.MODERATE:
                recommendations.append("Consider taking position with reduced allocation")
            else:
                recommendations.append("Consider taking position with minimal allocation")
            
            # Risk-based recommendations
            if risk_assessment["market_risk"] == "HIGH":
                recommendations.append("Use tight stop losses due to high market risk")
            if risk_assessment["liquidity_risk"] == "HIGH":
                recommendations.append("Consider smaller position size due to liquidity concerns")
        
        recommendations.append("Monitor position closely and adjust stop loss as needed")
        recommendations.append("Review signal after next market session")
        
        return recommendations
    
    def _generate_reasoning(self, agent_signals: Dict[str, Dict[str, Any]], 
                           direction: SignalDirection, confidence: float) -> str:
        """Generate comprehensive reasoning for the signal."""
        reasoning_parts = []
        
        # Signal direction reasoning
        signals = [agent_signals["chartanalyst"]["signal"], 
                  agent_signals["macroagent"]["signal"], 
                  agent_signals["sentinel"]["signal"]]
        
        long_count = signals.count("LONG")
        short_count = signals.count("SHORT")
        hold_count = signals.count("HOLD")
        
        if long_count >= 2:
            reasoning_parts.append(f"Bullish consensus with {long_count}/3 agents recommending LONG positions")
        elif short_count >= 2:
            reasoning_parts.append(f"Bearish consensus with {short_count}/3 agents recommending SHORT positions")
        else:
            reasoning_parts.append("Mixed signals from agents, recommending HOLD")
        
        # Confidence reasoning
        reasoning_parts.append(f"Overall confidence score of {confidence:.2f}")
        
        # Agent-specific insights
        if agent_signals["chartanalyst"]["confidence"] > 0.7:
            reasoning_parts.append("Strong technical analysis support")
        if agent_signals["macroagent"]["confidence"] > 0.7:
            reasoning_parts.append("Strong macroeconomic support")
        if agent_signals["sentinel"]["confidence"] > 0.7:
            reasoning_parts.append("Strong sentiment analysis support")
        
        return ". ".join(reasoning_parts) + "."
    
    def _calculate_next_review_time(self, strength: SignalStrength) -> str:
        """Calculate when to review the signal next."""
        if strength == SignalStrength.STRONG:
            return "Next market session"
        elif strength == SignalStrength.MODERATE:
            return "Within 4 hours"
        else:
            return "Within 1 hour"
    
    def _create_error_signal(self, symbol: str, error_msg: str) -> Dict[str, Any]:
        """Create error signal when synthesis fails."""
        return {
            "asset": symbol,
            "direction": SignalDirection.HOLD.value,
            "confidence": 0.0,
            "entry_target": 0.0,
            "stop_loss_target": 0.0,
            "take_profit_target": 0.0,
            "risk_reward_ratio": 0.0,
            "signal_strength": SignalStrength.WEAK.value,
            "agent_consensus": {
                "chartanalyst": "HOLD",
                "macroagent": "HOLD",
                "marketsentinel": "HOLD"
            },
            "confirming_factors": ["Analysis failed"],
            "conflicting_factors": [],
            "risk_assessment": {
                "market_risk": RiskLevel.HIGH.value,
                "volatility_risk": RiskLevel.HIGH.value,
                "liquidity_risk": RiskLevel.HIGH.value
            },
            "reasoning": f"Signal synthesis failed: {error_msg}",
            "recommendations": ["Manual analysis recommended"],
            "next_review_time": "Immediate",
            "timestamp": datetime.now().isoformat(),
            "workflow_id": f"error_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }

# Example usage
if __name__ == "__main__":
    synthesizer = SignalSynthesizer()
    
    # Mock agent analyses
    chart_analysis = {
        "signal": "BUY",
        "confidence": 80,
        "analysis": "Strong bullish pattern detected",
        "key_factors": ["Bullish engulfing", "RSI oversold recovery"]
    }
    
    macro_analysis = {
        "economic_outlook": "bullish",
        "confidence": 0.7,
        "reasoning": "Positive economic indicators",
        "key_drivers": ["Strong GDP growth", "Low unemployment"]
    }
    
    sentinel_analysis = {
        "sentiment_direction": "bullish",
        "confidence": 0.75,
        "reasoning": "Positive market sentiment",
        "key_factors": ["High social media mentions", "Positive news flow"]
    }
    
    market_data = {
        "current_price": 450.0,
        "current_ask": 450.05,
        "current_bid": 449.95,
        "volume": 1000000,
        "volatility": 0.15
    }
    
    result = synthesizer.synthesize_signal(
        symbol="SPY",
        chart_analysis=chart_analysis,
        macro_analysis=macro_analysis,
        sentinel_analysis=sentinel_analysis,
        market_data=market_data
    )
    
    print(json.dumps(result, indent=2))