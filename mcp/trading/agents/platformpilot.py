import os
import json
import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
# LLM imports - using Ollama with fallback

# Load environment variables
load_dotenv()


class PlatformPilot:
    """
    PlatformPilot: The orchestrator and chief strategist.
    Initiates workflows, queries the other agents, synthesizes their conflicting or confirming findings,
    assigns a final confidence score to potential trades, and communicates the final, reasoned signal to the user.
    """

    def __init__(self):
        self.llm = self._initialize_llm()
        self.confidence_threshold = 0.65  # Minimum confidence for signal generation
        self.agent_weights = {
            "chartanalyst": 0.4,  # Technical analysis weight
            "macroagent": 0.3,  # Macro analysis weight
            "marketsentinel": 0.3,  # Sentiment analysis weight
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

    async def synthesize_signals(
        self,
        symbol: str,
        chart_analysis: Dict[str, Any],
        macro_analysis: Dict[str, Any],
        sentinel_analysis: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Synthesize signals from all agents and generate final trading signal.
        """
        try:
            # Use the advanced signal synthesis module
            from agents.synthizer import SignalSynthesizer

            synthesizer = SignalSynthesizer()
            result = synthesizer.synthesize_signal(
                symbol=symbol,
                chart_analysis=chart_analysis,
                macro_analysis=macro_analysis,
                sentinel_analysis=sentinel_analysis,
                market_data=market_data,
            )

            # Add platform pilot metadata
            result["agent"] = "platformpilot"
            result["timestamp"] = datetime.datetime.now().isoformat()
            result["workflow_id"] = (
                f"signal_{symbol}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # Validate and enhance the result
            result = self._validate_and_enhance_signal(result, symbol)

            return result

        except Exception as e:
            return self._create_fallback_response(symbol, f"Synthesis error: {str(e)}")

    def _validate_and_enhance_signal(
        self, signal: Dict[str, Any], symbol: str
    ) -> Dict[str, Any]:
        """Validate and enhance the generated signal."""
        # Ensure confidence is within bounds
        confidence = signal.get("confidence", 0.0)
        if confidence < 0.0:
            confidence = 0.0
        elif confidence > 1.0:
            confidence = 1.0

        # If confidence is below threshold, change to HOLD
        if confidence < self.confidence_threshold:
            signal["direction"] = "HOLD"
            signal["signal_strength"] = "WEAK"

        # Add metadata
        signal["validation_status"] = "validated"
        signal["threshold_used"] = self.confidence_threshold
        signal["agent_weights"] = self.agent_weights

        return signal

    def calculate_weighted_confidence(
        self,
        chart_confidence: float,
        macro_confidence: float,
        sentinel_confidence: float,
    ) -> float:
        """Calculate weighted confidence score based on agent weights."""
        weighted_confidence = (
            chart_confidence * self.agent_weights["chartanalyst"]
            + macro_confidence * self.agent_weights["macroagent"]
            + sentinel_confidence * self.agent_weights["marketsentinel"]
        )
        return min(1.0, max(0.0, weighted_confidence))

    def determine_agent_consensus(
        self, chart_signal: str, macro_signal: str, sentinel_signal: str
    ) -> Dict[str, str]:
        """Determine consensus among agents."""
        return {
            "chartanalyst": chart_signal,
            "macroagent": macro_signal,
            "marketsentinel": sentinel_signal,
        }

    def assess_signal_quality(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality and reliability of the generated signal."""
        quality_metrics = {
            "data_completeness": 0.0,
            "agent_agreement": 0.0,
            "confidence_alignment": 0.0,
            "risk_assessment_completeness": 0.0,
        }

        # Check data completeness
        required_fields = ["direction", "confidence", "reasoning"]
        completeness = sum(1 for field in required_fields if field in signal) / len(
            required_fields
        )
        quality_metrics["data_completeness"] = completeness

        # Check agent agreement
        consensus = signal.get("agent_consensus", {})
        if consensus:
            signals = list(consensus.values())
            agreement = len(set(signals)) == 1  # All signals are the same
            quality_metrics["agent_agreement"] = 1.0 if agreement else 0.5

        # Check confidence alignment
        confidence = signal.get("confidence", 0.0)
        direction = signal.get("direction", "HOLD")
        if direction == "HOLD" and confidence < self.confidence_threshold:
            quality_metrics["confidence_alignment"] = 1.0
        elif direction != "HOLD" and confidence >= self.confidence_threshold:
            quality_metrics["confidence_alignment"] = 1.0
        else:
            quality_metrics["confidence_alignment"] = 0.5

        # Check risk assessment
        risk_assessment = signal.get("risk_assessment", {})
        risk_fields = ["market_risk", "volatility_risk", "liquidity_risk"]
        risk_completeness = sum(
            1 for field in risk_fields if field in risk_assessment
        ) / len(risk_fields)
        quality_metrics["risk_assessment_completeness"] = risk_completeness

        # Calculate overall quality score
        overall_quality = sum(quality_metrics.values()) / len(quality_metrics)
        quality_metrics["overall_quality"] = overall_quality

        return quality_metrics

    def _create_fallback_response(self, symbol: str, error_msg: str) -> Dict[str, Any]:
        """Create a fallback response when synthesis fails."""
        return {
            "agent": "platformpilot",
            "asset": symbol,
            "direction": "HOLD",
            "confidence": 0.0,
            "entry_target": 0.0,
            "stop_loss_target": 0.0,
            "take_profit_target": 0.0,
            "risk_reward_ratio": 0.0,
            "signal_strength": "WEAK",
            "agent_consensus": {
                "chartanalyst": "HOLD",
                "macroagent": "HOLD",
                "marketsentinel": "HOLD",
            },
            "confirming_factors": ["Analysis failed"],
            "conflicting_factors": [],
            "risk_assessment": {
                "market_risk": "HIGH",
                "volatility_risk": "HIGH",
                "liquidity_risk": "HIGH",
            },
            "reasoning": f"Synthesis failed: {error_msg}",
            "recommendations": ["Manual analysis recommended"],
            "next_review_time": "Immediate",
            "timestamp": datetime.datetime.now().isoformat(),
            "workflow_id": f"fallback_{symbol}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        }


# Node function for LangGraph integration
def platformpilot_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    PlatformPilot node for LangGraph workflow.
    """
    symbol = state.get("symbol", "SPY")

    # Extract agent analyses from state
    chart_analysis = state.get("chart_signal", {})
    macro_analysis = state.get("macro_analysis", {})
    sentinel_analysis = state.get("sentinel_analysis", {})
    market_data = state.get("market_data", {})

    pilot = PlatformPilot()
    # Run the async function in sync context
    import asyncio

    final_signal = asyncio.run(
        pilot.synthesize_signals(
            symbol=symbol,
            chart_analysis=chart_analysis,
            macro_analysis=macro_analysis,
            sentinel_analysis=sentinel_analysis,
            market_data=market_data,
        )
    )

    # Assess signal quality
    quality_metrics = pilot.assess_signal_quality(final_signal)
    final_signal["quality_metrics"] = quality_metrics

    # Update state with final signal
    state["final_signal"] = final_signal
    state["workflow_status"] = "completed"

    return state


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_platformpilot():
        pilot = PlatformPilot()

        # Mock agent analyses
        chart_analysis = {
            "signal": "BUY",
            "confidence": 0.8,
            "analysis": "Strong bullish pattern detected",
        }

        macro_analysis = {
            "economic_outlook": "bullish",
            "confidence": 0.7,
            "forecast_impact": "positive",
        }

        sentinel_analysis = {
            "sentiment_score": 0.6,
            "sentiment_direction": "bullish",
            "confidence": 0.75,
        }

        market_data = {"current_price": 450.0, "volume": 1000000, "volatility": 0.15}

        result = await pilot.synthesize_signals(
            symbol="SPY",
            chart_analysis=chart_analysis,
            macro_analysis=macro_analysis,
            sentinel_analysis=sentinel_analysis,
            market_data=market_data,
        )

        print(json.dumps(result, indent=2))

    asyncio.run(test_platformpilot())
