#!/usr/bin/env python3
"""
Polymarket AI Trading Agent - CLI Entry Point

Usage:
    python main.py              # Run agent in dry-run mode
    python main.py --analyze    # Only fetch and analyze markets
    python main.py --status     # Check configuration status
    python main.py --live       # Run with live trading (caution!)
"""
import argparse
import sys
from datetime import datetime

from src.agent import PolymarketAgent, create_agent
from src.market.polymarket import fetch_active_markets, print_markets
from src.analysis.ai_analyzer import get_analyzer
from src.trading.wallet import get_wallet
from src.utils.kelly import KellyCriterion


def print_banner():
    """Print welcome banner"""
    print()
    print("=" * 70)
    print("  POLYMARKET AI TRADING AGENT")
    print("  Powered by BlockRun - Autonomous AI Payments")
    print("=" * 70)
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()


def cmd_status():
    """Check and display configuration status"""
    print_banner()
    print("CONFIGURATION STATUS\n")

    # Check AI (BlockRun)
    print("[AI Analysis - BlockRun]")
    analyzer = get_analyzer()
    if analyzer:
        print(f"  Status: CONFIGURED")
        print(f"  Wallet: {analyzer.wallet_address}")
    else:
        print(f"  Status: NOT CONFIGURED")
        print(f"  Action: Set BASE_CHAIN_WALLET_KEY in .env")
    print()

    # Check Trading Wallet
    print("[Trading Wallet - Polygon]")
    wallet = get_wallet()
    if wallet:
        print(f"  Status: CONFIGURED")
        print(f"  Address: {wallet.address}")
        balances = wallet.get_balances()
        print(f"  MATIC: {balances['matic']:.4f}")
        print(f"  USDC: {balances['usdc']:.2f}")

        if wallet.check_approval():
            print(f"  Polymarket Approval: OK")
        else:
            print(f"  Polymarket Approval: NEEDED")
            print(f"  Action: python -c \"from src.trading.wallet import *; w=get_wallet(); w.approve_usdc()\"")
    else:
        print(f"  Status: NOT CONFIGURED")
        print(f"  Action: Set POLYGON_WALLET_PRIVATE_KEY in .env")
    print()

    # Check Kelly settings
    print("[Position Sizing - Kelly Criterion]")
    kelly = KellyCriterion()
    print(f"  Bankroll: ${kelly.bankroll}")
    print(f"  Max Bet: {kelly.max_bet_pct*100}%")
    print(f"  Min Edge: {kelly.min_edge_pct*100}%")
    print()


def cmd_analyze():
    """Fetch markets and run AI analysis"""
    print_banner()
    print("MARKET ANALYSIS\n")

    # Fetch markets
    print("Fetching markets...")
    markets = fetch_active_markets(limit=20)

    if not markets:
        print("Failed to fetch markets")
        return

    print(f"Found {len(markets)} active markets\n")

    # Print top markets
    print("Top Markets by End Date:")
    print("-" * 60)
    for i, m in enumerate(markets[:10], 1):
        print(f"{i}. {m['question'][:55]}...")
        vol = float(m.get('volume', 0) or 0)
        print(f"   End: {m['end_date']} | Vol: ${vol:,.0f}")
    print()

    # Run AI analysis
    analyzer = get_analyzer()
    if analyzer:
        print("Running AI analysis...")
        print(f"Using wallet: {analyzer.wallet_address}\n")

        analysis = analyzer.analyze_markets(markets)

        if analysis:
            print("-" * 60)
            print("AI ANALYSIS RESULTS")
            print("-" * 60)
            print(analysis)
        else:
            print("Analysis failed")
    else:
        print("AI analyzer not configured. Set BASE_CHAIN_WALLET_KEY in .env")


def cmd_run(live: bool = False):
    """Run the full agent"""
    print_banner()

    if live:
        print("WARNING: LIVE TRADING MODE")
        print("Real trades will be executed!")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            print("Cancelled")
            return
        print()

    agent = create_agent(
        auto_trade=live,
        dry_run=not live
    )

    # Check status first
    status = agent.check_status()

    if not status.get("ai_analyzer"):
        print("Warning: AI analyzer not configured")
        print("Set BASE_CHAIN_WALLET_KEY in .env for AI analysis\n")

    if live and not status.get("wallet"):
        print("Error: Trading wallet not configured")
        print("Set POLYGON_WALLET_PRIVATE_KEY in .env")
        return

    if live and not status.get("approved"):
        print("Error: USDC not approved for Polymarket")
        print("Run: python -m src.trading.wallet")
        return

    # Run agent
    results = agent.run()

    # Summary
    print("\nSUMMARY:")
    print(f"  Markets analyzed: {len(results.get('markets', []))}")
    print(f"  Recommendations: {len(results.get('recommendations', []))}")
    print(f"  Trades executed: {len(results.get('trades', []))}")


def main():
    parser = argparse.ArgumentParser(
        description="Polymarket AI Trading Agent"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Check configuration status"
    )

    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Fetch markets and run AI analysis"
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help="Run with live trading (use with caution!)"
    )

    args = parser.parse_args()

    if args.status:
        cmd_status()
    elif args.analyze:
        cmd_analyze()
    else:
        cmd_run(live=args.live)


if __name__ == "__main__":
    main()
