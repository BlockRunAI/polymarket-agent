"""
AI Market Analyzer - Powered by BlockRun
Uses BlockRun SDK for pay-per-request AI analysis without API keys.
"""
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Import BlockRun SDK
try:
    from blockrun_llm import LLMClient
    BLOCKRUN_AVAILABLE = True
except ImportError:
    BLOCKRUN_AVAILABLE = False
    print("Warning: blockrun-llm not installed. AI analysis unavailable.")


class AIAnalyzer:
    """AI-powered market analyzer using BlockRun"""

    # Model options for different use cases
    MODELS = {
        "fast": "openai/gpt-4o-mini",      # Quick, cheap screening
        "standard": "openai/gpt-4o",        # Standard analysis
        "deep": "anthropic/claude-sonnet-4", # Deep reasoning
        "premium": "anthropic/claude-opus-4", # Complex analysis
    }

    # 3-model consensus: GPT + Gemini + Claude
    CONSENSUS_MODELS = [
        "openai/gpt-4o-mini",           # GPT - fast, cheap
        "google/gemini-2.5-flash",      # Gemini - fast
        "anthropic/claude-haiku-4.5",   # Claude - reasoning
    ]

    def __init__(self):
        if not BLOCKRUN_AVAILABLE:
            raise RuntimeError("BlockRun SDK not available")

        self.client = LLMClient()
        self._wallet_address = None

    @property
    def wallet_address(self) -> str:
        """Get the BlockRun wallet address"""
        if not self._wallet_address:
            self._wallet_address = self.client.get_wallet_address()
        return self._wallet_address

    def analyze_markets(
        self,
        markets: List[Dict[str, Any]],
        model_tier: str = "deep"
    ) -> Optional[str]:
        """
        Analyze markets using AI

        Args:
            markets: List of market data dictionaries
            model_tier: "fast", "standard", "deep", or "premium"

        Returns:
            Analysis text or None if failed
        """
        if not markets:
            return None

        model = self.MODELS.get(model_tier, self.MODELS["deep"])

        # Format markets for analysis
        market_text = self._format_markets_for_prompt(markets[:10])

        prompt = f"""You are an expert prediction market analyst. Analyze these active Polymarket markets:

{market_text}

Provide:
1. Top 3 markets with best opportunity (mispriced odds)
2. For each: recommended position (YES/NO), confidence level (1-10), reasoning
3. Risk assessment for each recommendation

Focus on:
- Market inefficiencies and information advantages
- Current news/events that could affect outcomes
- Risk/reward profile"""

        system = "You are a professional prediction market analyst specializing in identifying profitable opportunities."

        try:
            result = self.client.chat(
                model=model,
                prompt=prompt,
                system=system,
                max_tokens=2048,
                temperature=0.7
            )
            return result
        except Exception as e:
            print(f"Analysis failed: {e}")
            return None

    def quick_check(self, question: str) -> Optional[str]:
        """
        Quick probability check for a single market

        Args:
            question: Market question

        Returns:
            Quick analysis or None
        """
        prompt = f"Briefly analyze this prediction market question and estimate probability: {question}"

        try:
            result = self.client.chat(
                model=self.MODELS["fast"],
                prompt=prompt,
                max_tokens=512,
                temperature=0.5
            )
            return result
        except Exception as e:
            print(f"Quick check failed: {e}")
            return None

    def compare_market(
        self,
        question: str,
        current_odds: float,
        model_tier: str = "standard"
    ) -> Dict[str, Any]:
        """
        Compare AI probability estimate with market odds

        Args:
            question: Market question
            current_odds: Current market probability (0-1)
            model_tier: Model to use

        Returns:
            Dict with ai_probability, edge, recommendation
        """
        model = self.MODELS.get(model_tier, self.MODELS["standard"])

        prompt = f"""Analyze this prediction market:

Question: {question}
Current market odds: {current_odds*100:.1f}% YES

Respond in this exact format:
PROBABILITY: [your estimated probability as a number 0-100]
CONFIDENCE: [your confidence in this estimate 1-10]
REASONING: [1-2 sentence explanation]"""

        try:
            result = self.client.chat(
                model=model,
                prompt=prompt,
                max_tokens=256,
                temperature=0.3
            )

            # Parse response
            lines = result.strip().split("\n")
            ai_prob = current_odds  # Default to market odds
            confidence = 5

            for line in lines:
                if line.startswith("PROBABILITY:"):
                    try:
                        ai_prob = float(line.split(":")[1].strip().replace("%", "")) / 100
                    except:
                        pass
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = int(line.split(":")[1].strip())
                    except:
                        pass

            edge = ai_prob - current_odds

            return {
                "ai_probability": ai_prob,
                "market_probability": current_odds,
                "edge": edge,
                "confidence": confidence,
                "recommendation": "BUY YES" if edge > 0.05 else ("BUY NO" if edge < -0.05 else "SKIP"),
                "raw_analysis": result
            }

        except Exception as e:
            return {
                "error": str(e),
                "ai_probability": current_odds,
                "edge": 0,
                "recommendation": "ERROR"
            }

    def _format_markets_for_prompt(self, markets: List[Dict[str, Any]]) -> str:
        """Format market list for AI prompt"""
        lines = []
        for i, m in enumerate(markets, 1):
            question = m.get("question", "Unknown")
            end_date = m.get("end_date", "Unknown")
            volume = m.get("volume", 0)
            lines.append(f"{i}. {question}")
            lines.append(f"   End: {end_date} | Volume: ${volume:,.0f}")
        return "\n".join(lines)

    def consensus_analysis(
        self,
        question: str,
        current_odds: float,
        whale_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Multi-model consensus analysis using 3 cheap models
        Returns aggregated decision from all models

        Args:
            question: Market question
            current_odds: Current YES probability (0-1)
            whale_data: Optional whale/smart money signals

        Returns:
            Dict with consensus decision, individual model results, confidence
        """
        # Build prompt with whale data if available
        whale_context = ""
        if whale_data and whale_data.get("has_smart_money_activity"):
            whale_context = f"""
SMART MONEY SIGNALS:
- Top traders consensus: {whale_data.get('consensus', 'N/A')}
- Smart money confidence: {whale_data.get('confidence', 0)*100:.0f}%
- YES volume from whales: ${whale_data.get('yes_volume', 0):,.0f}
- NO volume from whales: ${whale_data.get('no_volume', 0):,.0f}
- Number of top traders active: {whale_data.get('top_traders_count', 0)}
"""

        prompt = f"""Analyze this prediction market:

Question: {question}
Current market odds: {current_odds*100:.1f}% YES
{whale_context}
Respond in this exact format:
PROBABILITY: [your estimated probability 0-100]
CONFIDENCE: [your confidence 1-10]
REASONING: [1 sentence]"""

        results = []
        errors = []

        # Query each model
        for model in self.CONSENSUS_MODELS:
            try:
                response = self.client.chat(
                    model=model,
                    prompt=prompt,
                    max_tokens=150,
                    temperature=0.3
                )

                # Parse response
                ai_prob = current_odds
                confidence = 5
                reasoning = ""

                for line in response.strip().split("\n"):
                    if line.startswith("PROBABILITY:"):
                        try:
                            ai_prob = float(line.split(":")[1].strip().replace("%", "")) / 100
                        except:
                            pass
                    elif line.startswith("CONFIDENCE:"):
                        try:
                            confidence = int(line.split(":")[1].strip())
                        except:
                            pass
                    elif line.startswith("REASONING:"):
                        reasoning = line.split(":", 1)[1].strip() if ":" in line else ""

                results.append({
                    "model": model.split("/")[-1],
                    "probability": ai_prob,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "edge": ai_prob - current_odds
                })

            except Exception as e:
                errors.append({"model": model, "error": str(e)})

        if not results:
            return {
                "consensus": "ERROR",
                "recommendation": "SKIP",
                "error": "All models failed",
                "errors": errors
            }

        # Calculate consensus
        avg_prob = sum(r["probability"] for r in results) / len(results)
        avg_confidence = sum(r["confidence"] for r in results) / len(results)
        avg_edge = avg_prob - current_odds

        # Count votes
        yes_votes = sum(1 for r in results if r["edge"] > 0.05)
        no_votes = sum(1 for r in results if r["edge"] < -0.05)
        hold_votes = len(results) - yes_votes - no_votes

        # Determine recommendation based on majority
        # Need 2+ models agreeing on direction to trade
        if yes_votes >= 2:
            recommendation = "BET YES"
            consensus = "BULLISH"
        elif no_votes >= 2:
            recommendation = "BET NO"
            consensus = "BEARISH"
        else:
            recommendation = "SKIP"
            consensus = "MIXED"

        return {
            "consensus": consensus,
            "recommendation": recommendation,
            "avg_probability": avg_prob,
            "avg_confidence": avg_confidence,
            "avg_edge": avg_edge,
            "market_probability": current_odds,
            "yes_votes": yes_votes,
            "no_votes": no_votes,
            "hold_votes": hold_votes,
            "models_used": len(results),
            "model_results": results,
            "errors": errors if errors else None,
            "whale_data": whale_data
        }


def get_analyzer() -> Optional[AIAnalyzer]:
    """Get an AIAnalyzer instance if BlockRun is configured"""
    try:
        return AIAnalyzer()
    except Exception as e:
        print(f"Failed to initialize AI analyzer: {e}")
        return None


# CLI usage
if __name__ == "__main__":
    print("=" * 70)
    print("BLOCKRUN AI ANALYZER")
    print("=" * 70)

    analyzer = get_analyzer()

    if analyzer:
        print(f"Wallet: {analyzer.wallet_address}")
        print("\nTesting quick analysis...")

        result = analyzer.quick_check("Will Bitcoin reach $150K by end of 2025?")
        if result:
            print("\nAnalysis:")
            print(result)
    else:
        print("AI analyzer not available. Check BASE_CHAIN_WALLET_KEY in .env")
