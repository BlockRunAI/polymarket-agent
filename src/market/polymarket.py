"""
Polymarket Market Data Module
Fetches market data from Polymarket Gamma API
"""
import requests
import time
from datetime import datetime
from typing import List, Dict, Any, Optional


# API Configuration
GAMMA_API_URL = "https://gamma-api.polymarket.com/markets"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
    "Cache-Control": "no-cache"
}


class PolymarketClient:
    """Client for fetching Polymarket data"""

    def __init__(self):
        self.api_url = GAMMA_API_URL
        self.headers = DEFAULT_HEADERS

    def fetch_markets(
        self,
        limit: int = 50,
        active: bool = True,
        closed: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch markets from Polymarket Gamma API

        Args:
            limit: Maximum number of markets to fetch
            active: Only fetch active markets
            closed: Include closed markets

        Returns:
            List of market dictionaries or None if failed
        """
        timestamp = int(time.time() * 1000)

        params = {
            "limit": limit,
            "active": active,
            "closed": closed,
            "_t": timestamp  # Cache buster
        }

        try:
            response = requests.get(
                self.api_url,
                params=params,
                headers=self.headers,
                timeout=10
            )

            if response.status_code != 200:
                print(f"Failed to fetch markets: {response.status_code}")
                return None

            markets = response.json()

            if isinstance(markets, dict):
                print(f"Unexpected response format: {markets}")
                return None

            # Sort by end date (soonest first)
            markets.sort(key=lambda x: x.get("endDate", "9999"))

            return markets

        except Exception as e:
            print(f"Error fetching markets: {e}")
            return None

    def get_market_by_id(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific market by ID"""
        try:
            url = f"{self.api_url}/{market_id}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching market {market_id}: {e}")
            return None

    def format_market(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """Format market data for display"""
        end_date = market.get("endDate", "")
        formatted_date = "Unknown"

        if end_date:
            try:
                date_obj = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
            except:
                pass

        # Parse outcome prices (YES/NO odds)
        yes_odds, no_odds = 0.0, 0.0
        outcome_prices = market.get("outcomePrices", "[]")
        try:
            import json
            if isinstance(outcome_prices, str):
                prices = json.loads(outcome_prices)
            else:
                prices = outcome_prices
            if len(prices) >= 2:
                yes_odds = float(prices[0]) if prices[0] else 0.0
                no_odds = float(prices[1]) if prices[1] else 0.0
        except:
            pass

        return {
            "id": market.get("id"),
            "condition_id": market.get("conditionId", market.get("id")),  # For trade API
            "question": market.get("question", "Unknown"),
            "description": market.get("description", ""),
            "end_date": formatted_date,
            "volume": market.get("volume", 0),
            "liquidity": market.get("liquidity", 0),
            "outcomes": market.get("outcomes", []),
            "token_ids": self._parse_token_ids(market),
            "yes_odds": yes_odds,
            "no_odds": no_odds,
        }

    def _parse_token_ids(self, market: Dict[str, Any]) -> List[str]:
        """Extract token IDs from market data"""
        tokens = market.get("tokens", [])
        if tokens:
            return [t.get("token_id", "") for t in tokens]

        # Fallback: try clob_token_ids
        clob_ids = market.get("clobTokenIds", "")
        if clob_ids:
            return clob_ids.split(",")

        return []


def fetch_active_markets(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Convenience function to fetch active markets

    Args:
        limit: Maximum number of markets

    Returns:
        List of formatted market data
    """
    import logging
    logger = logging.getLogger(__name__)

    client = PolymarketClient()
    # Fetch more to filter out expired ones
    markets = client.fetch_markets(limit=limit * 5)

    if not markets:
        logger.warning("Polymarket API returned no markets")
        return []

    logger.info(f"Polymarket API returned {len(markets)} raw markets")

    # Filter for markets that haven't ended yet (use UTC for consistency)
    from datetime import timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # UTC without tzinfo for comparison
    future_markets = []

    for m in markets:
        end_date_str = m.get("endDate", "")
        if end_date_str:
            try:
                # Parse ISO date - handle timezone properly
                clean_date = end_date_str.replace("Z", "")
                if "+" in clean_date:
                    clean_date = clean_date.split("+")[0]
                end_date = datetime.fromisoformat(clean_date)
                if end_date > now:
                    future_markets.append(m)
            except Exception as e:
                # Include if we can't parse the date
                future_markets.append(m)
        else:
            future_markets.append(m)

    logger.info(f"After date filter: {len(future_markets)} future markets")

    # Sort by volume (highest first) for more interesting markets
    future_markets.sort(key=lambda x: float(x.get('volume', 0) or 0), reverse=True)

    # Return only the requested limit
    return [client.format_market(m) for m in future_markets[:limit]]


def print_markets(markets: List[Dict[str, Any]]) -> None:
    """Print markets in a readable format"""
    print(f"\nFound {len(markets)} active markets:\n")

    for i, market in enumerate(markets, 1):
        print(f"{i}. {market['question']}")
        print(f"   End Date: {market['end_date']}")
        print(f"   Volume: ${market['volume']:,.0f}")
        print()


# CLI usage
if __name__ == "__main__":
    print("=" * 70)
    print("POLYMARKET MARKET FETCHER")
    print("=" * 70)

    markets = fetch_active_markets(limit=20)
    print_markets(markets)
