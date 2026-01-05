"""Market data module"""
from .polymarket import PolymarketClient, fetch_active_markets

__all__ = ["PolymarketClient", "fetch_active_markets"]
