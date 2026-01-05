"""
Kelly Criterion Position Sizing
Optimal bet sizing for prediction markets
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class KellyCriterion:
    """Kelly Criterion position sizing calculator"""

    def __init__(
        self,
        bankroll: Optional[float] = None,
        max_bet_pct: Optional[float] = None,
        min_edge_pct: Optional[float] = None,
        kelly_fraction: float = 0.25
    ):
        """
        Initialize Kelly calculator

        Args:
            bankroll: Total bankroll in USD
            max_bet_pct: Maximum bet as fraction of bankroll
            min_edge_pct: Minimum edge required to bet
            kelly_fraction: Fraction of Kelly (0.25 = quarter Kelly)
        """
        self.bankroll = bankroll or float(os.getenv("INITIAL_BANKROLL", 100))
        self.max_bet_pct = max_bet_pct or float(os.getenv("MAX_BET_PERCENTAGE", 0.05))
        self.min_edge_pct = min_edge_pct or float(os.getenv("MIN_EDGE_PERCENTAGE", 0.15))
        self.kelly_fraction = kelly_fraction

    def calculate_edge(
        self,
        estimated_prob: float,
        market_prob: float
    ) -> float:
        """
        Calculate betting edge

        Args:
            estimated_prob: Your probability estimate (0-1)
            market_prob: Current market probability (0-1)

        Returns:
            Edge as decimal (positive = favorable)
        """
        return estimated_prob - market_prob

    def kelly_bet_size(
        self,
        estimated_prob: float,
        market_prob: float
    ) -> Dict[str, Any]:
        """
        Calculate optimal bet size using Kelly Criterion

        Args:
            estimated_prob: Your probability estimate (0-1)
            market_prob: Current market probability (0-1)

        Returns:
            Dict with bet_size, edge, side, should_bet
        """
        # Determine which side to bet
        edge = self.calculate_edge(estimated_prob, market_prob)

        if abs(edge) < self.min_edge_pct:
            return {
                "should_bet": False,
                "reason": f"Edge {edge*100:.1f}% below minimum {self.min_edge_pct*100:.1f}%",
                "edge": edge,
                "bet_size": 0,
                "side": None
            }

        # Determine side (YES if we think probability is higher than market)
        if edge > 0:
            side = "YES"
            p = estimated_prob
            odds = 1 / market_prob  # Decimal odds for YES
        else:
            side = "NO"
            p = 1 - estimated_prob
            odds = 1 / (1 - market_prob)  # Decimal odds for NO
            edge = abs(edge)

        # Kelly formula: f* = (bp - q) / b
        # where b = odds - 1, p = prob of winning, q = 1 - p
        b = odds - 1
        q = 1 - p

        kelly_fraction_raw = (b * p - q) / b if b > 0 else 0

        # Apply fractional Kelly and cap
        kelly_adjusted = kelly_fraction_raw * self.kelly_fraction
        kelly_capped = min(kelly_adjusted, self.max_bet_pct)
        kelly_capped = max(kelly_capped, 0)  # No negative bets

        bet_size = self.bankroll * kelly_capped

        return {
            "should_bet": bet_size > 0,
            "side": side,
            "edge": edge,
            "kelly_raw": kelly_fraction_raw,
            "kelly_adjusted": kelly_adjusted,
            "bet_size": round(bet_size, 2),
            "bet_percentage": kelly_capped * 100,
            "expected_value": bet_size * edge
        }

    def analyze_opportunity(
        self,
        market_question: str,
        estimated_prob: float,
        market_prob: float
    ) -> Dict[str, Any]:
        """
        Full analysis of betting opportunity

        Args:
            market_question: Market question
            estimated_prob: Your probability estimate
            market_prob: Current market probability

        Returns:
            Complete analysis with recommendation
        """
        result = self.kelly_bet_size(estimated_prob, market_prob)

        result.update({
            "market": market_question,
            "your_estimate": f"{estimated_prob*100:.1f}%",
            "market_odds": f"{market_prob*100:.1f}%",
        })

        if result["should_bet"]:
            result["recommendation"] = (
                f"BET ${result['bet_size']:.2f} on {result['side']} "
                f"(Edge: {result['edge']*100:.1f}%)"
            )
        else:
            result["recommendation"] = f"NO BET - {result.get('reason', 'Insufficient edge')}"

        return result


def calculate_bet(
    estimated_prob: float,
    market_prob: float,
    bankroll: float = 100
) -> Dict[str, Any]:
    """
    Convenience function for bet calculation

    Args:
        estimated_prob: Your probability (0-1)
        market_prob: Market probability (0-1)
        bankroll: Your bankroll

    Returns:
        Kelly calculation result
    """
    kelly = KellyCriterion(bankroll=bankroll)
    return kelly.kelly_bet_size(estimated_prob, market_prob)


# CLI usage
if __name__ == "__main__":
    print("=" * 60)
    print("KELLY CRITERION CALCULATOR")
    print("=" * 60)

    kelly = KellyCriterion()

    print(f"\nSettings:")
    print(f"  Bankroll: ${kelly.bankroll}")
    print(f"  Max bet: {kelly.max_bet_pct*100}%")
    print(f"  Min edge: {kelly.min_edge_pct*100}%")
    print(f"  Kelly fraction: {kelly.kelly_fraction}")

    # Example calculation
    print("\nExample: You estimate 70% YES, market shows 50%")
    result = kelly.analyze_opportunity(
        "Will Bitcoin reach $100K?",
        estimated_prob=0.70,
        market_prob=0.50
    )

    print(f"\nResult:")
    print(f"  Edge: {result['edge']*100:.1f}%")
    print(f"  Recommendation: {result['recommendation']}")
