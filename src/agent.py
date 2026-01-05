"""
Polymarket Trading Agent
Main coordinator that orchestrates market data, AI analysis, and trading
"""
from datetime import datetime
from typing import List, Dict, Any, Optional

from .market.polymarket import PolymarketClient, fetch_active_markets
from .analysis.ai_analyzer import AIAnalyzer, get_analyzer
from .trading.wallet import PolygonWallet, get_wallet
from .trading.executor import TradeExecutor
from .utils.kelly import KellyCriterion


class PolymarketAgent:
    """
    Autonomous Polymarket trading agent

    Workflow:
    1. Fetch market data from Polymarket
    2. Analyze markets using AI (via BlockRun)
    3. Calculate optimal position sizes (Kelly Criterion)
    4. Execute trades on Polygon
    """

    def __init__(
        self,
        auto_trade: bool = False,
        dry_run: bool = True
    ):
        """
        Initialize the agent

        Args:
            auto_trade: Automatically execute trades
            dry_run: If True, simulate trades without executing
        """
        self.auto_trade = auto_trade
        self.dry_run = dry_run

        # Initialize components
        self.market_client = PolymarketClient()
        self.analyzer = get_analyzer()
        self.wallet = get_wallet()
        self.kelly = KellyCriterion()

        if self.wallet and not self.dry_run:
            self.executor = TradeExecutor(self.wallet)
        else:
            self.executor = None

    def run(self) -> Dict[str, Any]:
        """
        Run the full agent workflow

        Returns:
            Dict with results from each step
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "markets": [],
            "analysis": None,
            "recommendations": [],
            "trades": []
        }

        print("=" * 70)
        print(f"POLYMARKET AI AGENT ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        print("Powered by BlockRun - Pay-per-request AI")
        print("=" * 70)

        # Step 1: Fetch markets
        print("\n[1/4] Fetching market data...")
        markets = self.fetch_markets()
        results["markets"] = markets

        if not markets:
            print("No markets found")
            return results

        print(f"Found {len(markets)} active markets")

        # Step 2: AI Analysis
        if self.analyzer:
            print(f"\n[2/4] Analyzing with AI...")
            print(f"Wallet: {self.analyzer.wallet_address}")

            analysis = self.analyze(markets)
            results["analysis"] = analysis

            if analysis:
                print("\n--- AI Analysis ---")
                print(analysis[:1000] + "..." if len(analysis) > 1000 else analysis)
        else:
            print("\n[2/4] AI analysis skipped (not configured)")

        # Step 3: Generate recommendations
        print("\n[3/4] Generating trade recommendations...")
        recommendations = self.generate_recommendations(markets[:5])
        results["recommendations"] = recommendations

        for rec in recommendations:
            print(f"\n{rec['market'][:50]}...")
            print(f"  {rec['recommendation']}")

        # Step 4: Execute trades
        if self.auto_trade and not self.dry_run:
            print("\n[4/4] Executing trades...")
            trades = self.execute_trades(recommendations)
            results["trades"] = trades
        else:
            print(f"\n[4/4] Trade execution: {'DRY RUN' if self.dry_run else 'DISABLED'}")

        print("\n" + "=" * 70)
        print("Agent run complete")
        print("=" * 70)

        return results

    def fetch_markets(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch active markets from Polymarket"""
        raw_markets = self.market_client.fetch_markets(limit=limit)

        if not raw_markets:
            return []

        return [self.market_client.format_market(m) for m in raw_markets]

    def analyze(
        self,
        markets: List[Dict[str, Any]],
        model_tier: str = "deep"
    ) -> Optional[str]:
        """Run AI analysis on markets"""
        if not self.analyzer:
            return None

        return self.analyzer.analyze_markets(markets, model_tier)

    def generate_recommendations(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate trade recommendations for markets

        This is a simplified version - in production you'd use
        the AI analysis to estimate probabilities
        """
        recommendations = []

        for market in markets:
            # Placeholder: Use market volume as a proxy for confidence
            # In production, use AI probability estimates
            volume = market.get("volume", 0)

            if volume > 10000:
                # Assume market odds from outcomes if available
                # This is simplified - real implementation would parse prices
                estimated_prob = 0.55  # Slight edge assumption
                market_prob = 0.50

                result = self.kelly.analyze_opportunity(
                    market["question"],
                    estimated_prob,
                    market_prob
                )
                recommendations.append(result)

        return recommendations

    def execute_trades(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute recommended trades"""
        trades = []

        if not self.executor:
            print("Trade executor not available")
            return trades

        for rec in recommendations:
            if not rec.get("should_bet"):
                continue

            # Would need token_id from market data
            # This is a placeholder
            trade = {
                "market": rec["market"],
                "side": rec["side"],
                "amount": rec["bet_size"],
                "status": "skipped",
                "reason": "Token ID not available in simplified mode"
            }
            trades.append(trade)

        return trades

    def check_status(self) -> Dict[str, Any]:
        """Check agent status and configuration"""
        status = {
            "market_client": True,
            "ai_analyzer": self.analyzer is not None,
            "wallet": self.wallet is not None,
            "executor": self.executor is not None,
            "auto_trade": self.auto_trade,
            "dry_run": self.dry_run
        }

        if self.analyzer:
            status["ai_wallet"] = self.analyzer.wallet_address

        if self.wallet:
            status["trading_wallet"] = self.wallet.address
            status["usdc_balance"] = self.wallet.get_usdc_balance()
            status["approved"] = self.wallet.check_approval()

        return status


def create_agent(
    auto_trade: bool = False,
    dry_run: bool = True
) -> PolymarketAgent:
    """Factory function to create agent"""
    return PolymarketAgent(auto_trade=auto_trade, dry_run=dry_run)


# CLI usage
if __name__ == "__main__":
    print("Creating Polymarket Agent...")

    agent = create_agent(dry_run=True)

    print("\nAgent Status:")
    status = agent.check_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    print("\nRunning agent (dry run)...")
    agent.run()
