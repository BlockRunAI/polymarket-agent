"""
Trade Executor Module
Handles order placement on Polymarket using py-clob-client
"""
import os
import json
import logging
from typing import Optional, Dict, Any, Tuple
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Polymarket CLOB endpoints
CLOB_HOST = "https://clob.polymarket.com"
CHAIN_ID = 137  # Polygon

# Trading limits
MAX_BET_SIZE = 10.0  # Max $10 per trade for safety
MIN_CONFIDENCE = 5  # Minimum confidence score (out of 10) - AI must be at least 50% confident


class TradeExecutor:
    """Executes trades on Polymarket using py-clob-client"""

    def __init__(self, private_key: Optional[str] = None):
        """
        Initialize executor

        Args:
            private_key: Polygon wallet private key (or from env)
        """
        self.private_key = private_key or os.getenv("POLYGON_WALLET_PRIVATE_KEY", "")
        if not self.private_key.startswith("0x"):
            self.private_key = "0x" + self.private_key

        self.client = None
        self._api_creds = None
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """Initialize the CLOB client with API credentials"""
        if self._initialized:
            return True

        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import ApiCreds

            # Check for stored API credentials
            api_key = os.getenv("POLYMARKET_API_KEY")
            api_secret = os.getenv("POLYMARKET_API_SECRET")
            passphrase = os.getenv("POLYMARKET_PASSPHRASE")

            if api_key and api_secret and passphrase:
                # Use existing credentials
                self._api_creds = ApiCreds(
                    api_key=api_key,
                    api_secret=api_secret,
                    api_passphrase=passphrase
                )
                self.client = ClobClient(
                    host=CLOB_HOST,
                    chain_id=CHAIN_ID,
                    key=self.private_key,
                    creds=self._api_creds
                )
            else:
                # Create new client and derive credentials
                self.client = ClobClient(
                    host=CLOB_HOST,
                    chain_id=CHAIN_ID,
                    key=self.private_key
                )
                # Derive API credentials from wallet signature
                self._api_creds = self.client.derive_api_key()
                logger.info(f"Derived API credentials. Save these to .env:")
                logger.info(f"POLYMARKET_API_KEY={self._api_creds.api_key}")
                logger.info(f"POLYMARKET_API_SECRET={self._api_creds.api_secret}")
                logger.info(f"POLYMARKET_PASSPHRASE={self._api_creds.api_passphrase}")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize CLOB client: {e}")
            return False

    def get_orderbook(self, token_id: str) -> Optional[Dict]:
        """Get order book for a token"""
        if not self._ensure_initialized():
            return None

        try:
            return self.client.get_order_book(token_id)
        except Exception as e:
            logger.error(f"Failed to get orderbook: {e}")
            return None

    def get_best_price(self, token_id: str, side: str) -> Optional[float]:
        """Get best available price for a trade"""
        orderbook = self.get_orderbook(token_id)
        if not orderbook:
            return None

        try:
            if side.upper() == "BUY":
                # Best ask price (lowest sell)
                asks = orderbook.get("asks", [])
                if asks:
                    return float(asks[0].get("price", 0))
            else:
                # Best bid price (highest buy)
                bids = orderbook.get("bids", [])
                if bids:
                    return float(bids[0].get("price", 0))
        except Exception as e:
            logger.error(f"Error parsing orderbook: {e}")

        return None

    def place_market_order(
        self,
        token_id: str,
        side: str,
        amount_usdc: float,
        price: Optional[float] = None
    ) -> Optional[str]:
        """
        Place a market order

        Args:
            token_id: Outcome token ID
            side: "BUY" or "SELL"
            amount_usdc: Amount in USDC
            price: Optional limit price (uses market price if not specified)

        Returns:
            Order ID or None if failed
        """
        logger.info(f"Attempting order: token={token_id[:20]}..., side={side}, amount=${amount_usdc}")

        if not token_id or len(token_id) < 10:
            logger.error(f"Invalid token_id: {token_id}")
            return None

        if not self._ensure_initialized():
            logger.error("Failed to initialize CLOB client")
            return None

        try:
            from py_clob_client.order_builder.constants import BUY, SELL

            # Enforce safety limits
            if amount_usdc > MAX_BET_SIZE:
                logger.warning(f"Reducing bet from ${amount_usdc} to ${MAX_BET_SIZE}")
                amount_usdc = MAX_BET_SIZE

            # Get current price if not specified
            if price is None:
                price = self.get_best_price(token_id, side)
                if price is None:
                    logger.error(f"Could not determine price for token {token_id[:20]}...")
                    return None
                logger.info(f"Best price: {price}")

            # Calculate size in shares
            size = amount_usdc / price
            logger.info(f"Order details: price={price}, size={size:.4f} shares")

            order_side = BUY if side.upper() == "BUY" else SELL

            # Create and sign order
            order_args = {
                "token_id": token_id,
                "price": price,
                "size": size,
                "side": order_side,
            }

            logger.info(f"Submitting order to CLOB...")
            signed_order = self.client.create_and_post_order(order_args)
            logger.info(f"CLOB response: {signed_order}")

            if signed_order:
                order_id = signed_order.get("orderID") or signed_order.get("order_id") or signed_order.get("id")
                logger.info(f"Order placed successfully: {order_id}")
                return order_id

            logger.error("CLOB returned empty response")
            return None

        except Exception as e:
            logger.error(f"Order execution failed: {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def validate_trade_signal(
        self,
        action: str,
        edge: float,
        confidence: float,
        consensus: str
    ) -> Tuple[bool, str]:
        """
        Validate if a trade signal meets our criteria

        Returns:
            (should_trade, reason)
        """
        if action not in ("BET YES", "BET NO"):
            return False, f"Action is {action} - no trade"

        if confidence < MIN_CONFIDENCE:
            return False, f"Confidence {confidence:.1f}/10 below minimum {MIN_CONFIDENCE}"

        if consensus == "MIXED":
            return False, "No clear model consensus (need 2+ models agreeing)"

        # AI decides to trade - consensus reached with sufficient confidence
        return True, f"AI consensus: {consensus} with {confidence:.1f}/10 confidence"

    def calculate_position_size(
        self,
        edge: float,
        confidence: float,
        bankroll: float
    ) -> float:
        """
        Calculate position size using Kelly Criterion

        Args:
            edge: Expected edge (e.g., 0.10 for 10%)
            confidence: Confidence level (1-10)
            bankroll: Available capital

        Returns:
            Recommended bet size in USDC
        """
        # Kelly fraction: f = (bp - q) / b
        # where b = net odds, p = win probability, q = 1-p

        # For prediction markets with 50% implied odds:
        # Simplified Kelly: bet_fraction = edge * (confidence / 10)

        kelly_fraction = abs(edge) * (confidence / 10) * 0.5  # Half-Kelly for safety

        # Position size
        size = bankroll * kelly_fraction

        # Apply limits
        size = min(size, MAX_BET_SIZE)
        size = max(size, 1.0)  # Minimum $1

        return round(size, 2)

    def execute_signal(
        self,
        token_id: str,
        action: str,
        edge: float,
        confidence: float,
        consensus: str,
        bankroll: float = 100.0
    ) -> Optional[Dict]:
        """
        Execute a trade based on AI signal

        Args:
            token_id: Polymarket outcome token ID
            action: "BUY YES", "BUY NO", or "HOLD"
            edge: Expected edge
            confidence: AI confidence (1-10)
            consensus: Model consensus ("BULLISH", "BEARISH", "MIXED")
            bankroll: Available capital

        Returns:
            Trade result or None
        """
        # Validate signal
        should_trade, reason = self.validate_trade_signal(action, edge, confidence, consensus)

        if not should_trade:
            logger.info(f"Skipping trade: {reason}")
            return {"status": "skipped", "reason": reason}

        # Calculate position size
        size = self.calculate_position_size(edge, confidence, bankroll)

        # Determine side
        side = "BUY"  # We always buy (YES or NO tokens)

        logger.info(f"Executing: {action} ${size:.2f} (edge: {edge*100:.1f}%, conf: {confidence}/10)")

        # Place order
        order_id = self.place_market_order(token_id, side, size)

        if order_id:
            return {
                "status": "success",
                "order_id": order_id,
                "action": action,
                "size": size,
                "edge": edge,
                "confidence": confidence
            }
        else:
            return {
                "status": "failed",
                "reason": "Order placement failed"
            }


def get_executor() -> Optional[TradeExecutor]:
    """Get executor instance if configured"""
    try:
        return TradeExecutor()
    except Exception as e:
        logger.error(f"Failed to initialize executor: {e}")
        return None


# CLI usage
if __name__ == "__main__":
    print("=" * 60)
    print("POLYMARKET TRADE EXECUTOR")
    print("=" * 60)

    from .wallet import get_wallet
    wallet = get_wallet()

    if wallet:
        print(f"Wallet: {wallet.address}")
        print(f"USDC: ${wallet.get_usdc_balance():.2f}")
        print(f"Approved: {wallet.check_approval()}")

        executor = get_executor()
        if executor:
            print("\nExecutor initialized")
            print(f"Max bet size: ${MAX_BET_SIZE}")
            print(f"Min edge required: {MIN_EDGE_REQUIRED*100:.0f}%")
        else:
            print("\nExecutor failed to initialize")
    else:
        print("Wallet not configured")
