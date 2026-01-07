"""
Trade Executor Module
Handles order placement on Polymarket using py-clob-client
"""
import os
import json
import logging
from typing import Optional, Dict, Any, Tuple, Union
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

        # Get wallet address from private key (EOA that signs)
        from eth_account import Account
        self.signer_address = Account.from_key(self.private_key).address

        # Polymarket proxy wallet (where funds are held and trades execute)
        # This is the funder address on Polymarket
        self.wallet_address = os.getenv("POLYMARKET_PROXY_WALLET", self.signer_address)

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

            # Check for stored API credentials (REQUIRED for trading)
            api_key = os.getenv("POLYMARKET_API_KEY")
            api_secret = os.getenv("POLYMARKET_API_SECRET")
            passphrase = os.getenv("POLYMARKET_PASSPHRASE")

            if api_key and api_secret and passphrase:
                # Use existing credentials
                logger.info("Using stored Polymarket API credentials")
                self._api_creds = ApiCreds(
                    api_key=api_key,
                    api_secret=api_secret,
                    api_passphrase=passphrase
                )
                # Determine signature type based on wallet setup
                # 0 = EOA (signer = funder), 2 = Gnosis Safe proxy (most common)
                sig_type = 2 if self.wallet_address != self.signer_address else 0
                logger.info(f"Using signature_type={sig_type} (proxy={self.wallet_address != self.signer_address})")
                self.client = ClobClient(
                    host=CLOB_HOST,
                    chain_id=CHAIN_ID,
                    key=self.private_key,
                    creds=self._api_creds,
                    signature_type=sig_type,
                    funder=self.wallet_address
                )
                self._initialized = True
                logger.info(f"CLOB client initialized for wallet {self.wallet_address[:10]}...")
                return True
            else:
                # Try to create/derive credentials programmatically
                logger.info("No stored credentials, attempting to create/derive API key...")
                # Determine signature type based on wallet setup
                # 0 = EOA (signer = funder), 2 = Gnosis Safe proxy (most common)
                sig_type = 2 if self.wallet_address != self.signer_address else 0
                logger.info(f"Using signature_type={sig_type} (proxy={self.wallet_address != self.signer_address})")
                self.client = ClobClient(
                    host=CLOB_HOST,
                    chain_id=CHAIN_ID,
                    key=self.private_key,
                    signature_type=sig_type,
                    funder=self.wallet_address
                )
                try:
                    # Use the recommended create_or_derive_api_creds method
                    self._api_creds = self.client.create_or_derive_api_creds()
                    logger.info("Obtained API credentials via create_or_derive_api_creds()")

                    # Log credentials for user to save
                    api_key = self._api_creds.get("apiKey") or getattr(self._api_creds, "api_key", None)
                    api_secret = self._api_creds.get("secret") or getattr(self._api_creds, "api_secret", None)
                    passphrase = self._api_creds.get("passphrase") or getattr(self._api_creds, "api_passphrase", None)

                    logger.info(f"Successfully obtained API credentials!")
                    logger.info(f"Add these to .env to avoid re-deriving:")
                    logger.info(f"POLYMARKET_API_KEY={api_key}")
                    logger.info(f"POLYMARKET_API_SECRET={api_secret}")
                    logger.info(f"POLYMARKET_PASSPHRASE={passphrase}")

                    # Set credentials on the client
                    self.client.set_api_creds(self._api_creds)
                    self._initialized = True
                    logger.info(f"CLOB client initialized for wallet {self.wallet_address[:10]}...")
                    return True
                except Exception as auth_err:
                    logger.error(f"Could not create/derive API key: {auth_err}")
                    logger.error("SOLUTION: Your wallet must be registered with Polymarket first!")
                    logger.error("1. Go to https://polymarket.com")
                    logger.error("2. Connect with the same wallet used for POLYGON_WALLET_PRIVATE_KEY")
                    logger.error("3. Sign in and accept terms of service")
                    logger.error("4. Then trading will work, OR add API credentials to .env")
                    return False

        except Exception as e:
            logger.error(f"Failed to initialize CLOB client: {e}")
            return False

    def get_orderbook(self, token_id: str) -> Optional[Any]:
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
                asks = getattr(orderbook, 'asks', []) or []
                if asks:
                    # Handle both dict and object formats
                    first_ask = asks[0]
                    price = getattr(first_ask, 'price', None) or first_ask.get('price', 0) if isinstance(first_ask, dict) else first_ask.price
                    return float(price)
            else:
                # Best bid price (highest buy)
                bids = getattr(orderbook, 'bids', []) or []
                if bids:
                    first_bid = bids[0]
                    price = getattr(first_bid, 'price', None) or first_bid.get('price', 0) if isinstance(first_bid, dict) else first_bid.price
                    return float(price)
        except Exception as e:
            logger.error(f"Error parsing orderbook: {e}")

        return None

    def get_open_orders(self) -> list[Dict[str, Any]]:
        """
        Get all open orders for this wallet

        Returns:
            List of open orders with their details
        """
        if not self._ensure_initialized():
            logger.error("Cannot fetch orders - client not initialized")
            return []

        try:
            # Fetch open orders from Polymarket CLOB
            orders = self.client.get_orders()

            if not orders:
                return []

            # Format orders for display
            formatted_orders = []
            for order in orders:
                try:
                    # Handle both dict and object formats
                    if isinstance(order, dict):
                        order_id = order.get('id') or order.get('orderID')
                        market = order.get('market', 'Unknown')
                        asset_id = order.get('asset_id') or order.get('tokenID')
                        price = float(order.get('price', 0))
                        size = float(order.get('size', 0))
                        side = order.get('side', 'BUY')
                        status = order.get('status', 'OPEN')
                    else:
                        order_id = getattr(order, 'id', None) or getattr(order, 'orderID', None)
                        market = getattr(order, 'market', 'Unknown')
                        asset_id = getattr(order, 'asset_id', None) or getattr(order, 'tokenID', None)
                        price = float(getattr(order, 'price', 0))
                        size = float(getattr(order, 'size', 0))
                        side = getattr(order, 'side', 'BUY')
                        status = getattr(order, 'status', 'OPEN')

                    formatted_orders.append({
                        'order_id': order_id,
                        'market': market,
                        'asset_id': asset_id,
                        'price': price,
                        'size': size,
                        'side': side,
                        'value': price * size,
                        'status': status
                    })
                except Exception as e:
                    logger.error(f"Error formatting order: {e}")
                    continue

            return formatted_orders

        except Exception as e:
            logger.error(f"Failed to fetch open orders: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def get_positions(self) -> list[Dict[str, Any]]:
        """
        Get current positions (filled orders / holdings)

        Returns:
            List of positions with market info
        """
        if not self._ensure_initialized():
            logger.error("Cannot fetch positions - client not initialized")
            return []

        try:
            # Try to get positions from balance endpoint
            # This requires the client to support balance queries
            balances = []
            try:
                # Some versions of py-clob-client have get_balances
                if hasattr(self.client, 'get_balances'):
                    balances = self.client.get_balances()
            except:
                pass

            if not balances:
                # Fallback: get filled orders
                logger.info("Fetching filled orders as positions...")
                try:
                    # Get all orders and filter for filled/matched
                    all_orders = self.client.get_orders()
                    filled_orders = [
                        o for o in all_orders
                        if (getattr(o, 'status', None) or o.get('status') if isinstance(o, dict) else None)
                        in ['MATCHED', 'FILLED']
                    ]

                    # Group by token to create positions
                    positions_map = {}
                    for order in filled_orders:
                        try:
                            if isinstance(order, dict):
                                asset_id = order.get('asset_id') or order.get('tokenID')
                                size = float(order.get('size', 0))
                                price = float(order.get('price', 0))
                                side = order.get('side', 'BUY')
                            else:
                                asset_id = getattr(order, 'asset_id', None) or getattr(order, 'tokenID', None)
                                size = float(getattr(order, 'size', 0))
                                price = float(getattr(order, 'price', 0))
                                side = getattr(order, 'side', 'BUY')

                            if asset_id not in positions_map:
                                positions_map[asset_id] = {
                                    'asset_id': asset_id,
                                    'total_size': 0,
                                    'avg_price': 0,
                                    'total_cost': 0
                                }

                            # Add to position (buy adds, sell subtracts)
                            if side == 'BUY':
                                positions_map[asset_id]['total_size'] += size
                                positions_map[asset_id]['total_cost'] += size * price
                            else:
                                positions_map[asset_id]['total_size'] -= size
                                positions_map[asset_id]['total_cost'] -= size * price
                        except:
                            continue

                    # Calculate avg prices and format
                    balances = []
                    for asset_id, pos in positions_map.items():
                        if pos['total_size'] > 0.001:  # Only include non-zero positions
                            balances.append({
                                'asset_id': asset_id,
                                'balance': pos['total_size'],
                                'avg_price': pos['total_cost'] / pos['total_size'] if pos['total_size'] > 0 else 0
                            })

                except Exception as e:
                    logger.error(f"Error getting filled orders: {e}")

            # Format positions for display
            formatted_positions = []
            for bal in balances:
                try:
                    if isinstance(bal, dict):
                        asset_id = bal.get('asset_id') or bal.get('tokenID')
                        balance = float(bal.get('balance', 0))
                        avg_price = float(bal.get('avg_price', 0))
                    else:
                        asset_id = getattr(bal, 'asset_id', None) or getattr(bal, 'tokenID', None)
                        balance = float(getattr(bal, 'balance', 0))
                        avg_price = float(getattr(bal, 'avg_price', 0))

                    if balance > 0.001:  # Only show non-zero positions
                        formatted_positions.append({
                            'asset_id': asset_id,
                            'size': balance,
                            'avg_price': avg_price,
                            'value': balance * avg_price,
                            'market': 'Unknown'  # Would need market lookup
                        })
                except Exception as e:
                    logger.error(f"Error formatting position: {e}")
                    continue

            return formatted_positions

        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

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
        logger.info(f"📝 Attempting order: token={token_id[:20]}..., side={side}, amount=${amount_usdc}")

        # Validation checks
        if not token_id or len(token_id) < 10:
            logger.error(f"❌ Invalid token_id: {token_id}")
            logger.error("   Token ID must be a valid Polymarket outcome token")
            return None

        if amount_usdc <= 0:
            logger.error(f"❌ Invalid amount: ${amount_usdc}")
            logger.error("   Amount must be greater than 0")
            return None

        logger.info(f"🔄 Checking CLOB client initialization...")
        init_result = self._ensure_initialized()
        logger.info(f"🔄 CLOB client init result: {init_result}")

        if not init_result:
            logger.error("❌ Failed to initialize CLOB client")
            logger.error("   Check your wallet configuration and API credentials")
            logger.error("   POLYGON_WALLET_PRIVATE_KEY must be set in .env")
            logger.error(f"   Initialized flag: {self._initialized}")
            logger.error(f"   Client exists: {self.client is not None}")
            return None

        try:
            from py_clob_client.order_builder.constants import BUY, SELL
            from py_clob_client.clob_types import OrderArgs

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

            # Create and sign order using OrderArgs (required by py-clob-client)
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=order_side,
            )

            logger.info(f"Submitting order to CLOB...")
            # Submit order with tick_size for proper price rounding
            # Most Polymarket markets use 0.01 tick_size and are not neg_risk
            signed_order = self.client.create_and_post_order(order_args)
            logger.info(f"CLOB response: {signed_order}")

            if signed_order:
                order_id = signed_order.get("orderID") or signed_order.get("order_id") or signed_order.get("id")
                status = signed_order.get("status", "UNKNOWN")

                logger.info(f"✓ Order submitted to CLOB: {order_id}")
                logger.info(f"  Initial status: {status}")
                logger.info(f"  Token: {token_id[:30]}...")
                logger.info(f"  Price: {price:.3f} | Size: {size:.2f} shares | Value: ${amount_usdc:.2f}")
                logger.info(f"  ⚠️  Note: Order is now in orderbook waiting to fill")
                logger.info(f"  Check https://polymarket.com for order status")

                return order_id

            logger.error("CLOB returned empty response")
            return None

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Order execution failed: {type(e).__name__}: {error_msg}")
            import traceback
            logger.error(traceback.format_exc())

            # Provide helpful error messages
            if "unauthorized" in error_msg.lower() or "401" in error_msg:
                logger.error("❌ AUTHENTICATION ERROR:")
                logger.error("   Your API credentials are invalid or expired.")
                logger.error("   SOLUTION:")
                logger.error("   1. Go to https://polymarket.com and sign in with your wallet")
                logger.error("   2. Re-run the agent to regenerate API credentials")
                logger.error(f"   3. Or manually set POLYMARKET_API_KEY in .env")
            elif "insufficient" in error_msg.lower() or "balance" in error_msg.lower():
                logger.error("❌ INSUFFICIENT BALANCE:")
                logger.error(f"   Your wallet needs more USDC to place this order")
                logger.error(f"   SOLUTION: Add USDC to {self.wallet_address[:10]}...")
            elif "token" in error_msg.lower() and "not found" in error_msg.lower():
                logger.error("❌ INVALID TOKEN:")
                logger.error(f"   Token ID may be incorrect or market is closed")
                logger.error(f"   Token: {token_id[:30]}...")
            elif "price" in error_msg.lower():
                logger.error("❌ PRICE ERROR:")
                logger.error(f"   The order price may be out of bounds")
                logger.error(f"   Attempted price: {price if price else 'N/A'}")
            elif "signature" in error_msg.lower():
                logger.error("❌ SIGNATURE ERROR:")
                logger.error(f"   Signature type mismatch (proxy wallet issue)")
                logger.error(f"   Current setup: signature_type={2 if self.wallet_address != self.signer_address else 0}")
                logger.error(f"   Signer: {self.signer_address[:10]}...")
                logger.error(f"   Funder: {self.wallet_address[:10]}...")
            else:
                logger.error("❌ ORDER FAILED:")
                logger.error(f"   Error: {error_msg[:200]}")
                logger.error("   Check logs above for details")

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
        logger.info(f"🎯 execute_signal called: action={action}, conf={confidence}, consensus={consensus}, bankroll=${bankroll:.2f}")

        # Validate signal
        should_trade, reason = self.validate_trade_signal(action, edge, confidence, consensus)
        logger.info(f"🎯 Validation result: should_trade={should_trade}, reason={reason}")

        if not should_trade:
            logger.info(f"Skipping trade: {reason}")
            return {"status": "skipped", "reason": reason}

        # Calculate position size
        size = self.calculate_position_size(edge, confidence, bankroll)
        logger.info(f"🎯 Calculated position size: ${size:.2f}")

        # Determine side
        side = "BUY"  # We always buy (YES or NO tokens)

        logger.info(f"🎯 Executing: {action} ${size:.2f} (edge: {edge*100:.1f}%, conf: {confidence}/10)")

        # Place order
        order_id = self.place_market_order(token_id, side, size)

        if order_id:
            return {
                "status": "submitted",  # Changed from "success" to be more accurate
                "order_id": order_id,
                "action": action,
                "size": size,
                "edge": edge,
                "confidence": confidence,
                "message": "Order submitted to orderbook (waiting to fill)"
            }
        else:
            return {
                "status": "failed",
                "reason": "Order placement failed - check logs for details"
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
