"""
Google Cloud Storage for persistent data storage (OPTIONAL)
Stores: orders, AI decisions, market data

This module is OPTIONAL. Enable via USE_GCS_STORAGE=true in .env
When disabled, the application uses local /tmp storage (data lost on redeployment)
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# GCS Configuration - read from environment variables
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "polymarket-agent-data")
ORDERS_FILE = "orders.json"
DECISIONS_FILE = "decisions.json"
MARKETS_FILE = "markets.json"


class GCSStorage:
    """Google Cloud Storage handler for persistent data"""

    def __init__(self):
        self.bucket = None
        self.client = None
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """Initialize GCS client and bucket"""
        if self._initialized:
            return True

        try:
            from google.cloud import storage

            self.client = storage.Client()
            self.bucket = self.client.bucket(BUCKET_NAME)

            # Verify bucket exists
            if not self.bucket.exists():
                logger.error(f"GCS bucket {BUCKET_NAME} does not exist")
                return False

            self._initialized = True
            logger.info(f"✅ GCS storage initialized (bucket: {BUCKET_NAME})")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize GCS: {e}")
            return False

    def _read_json(self, filename: str) -> Dict[str, Any]:
        """Read JSON data from GCS"""
        if not self._ensure_initialized():
            return {}

        try:
            blob = self.bucket.blob(filename)

            # Check if file exists
            if not blob.exists():
                logger.info(f"📂 {filename} does not exist yet, returning empty data")
                return {}

            # Download and parse
            data_str = blob.download_as_text()
            data = json.loads(data_str)
            logger.info(f"📥 Loaded {filename} from GCS")
            return data

        except Exception as e:
            logger.error(f"Failed to read {filename} from GCS: {e}")
            return {}

    def _write_json(self, filename: str, data: Dict[str, Any]) -> bool:
        """Write JSON data to GCS"""
        if not self._ensure_initialized():
            return False

        try:
            blob = self.bucket.blob(filename)
            blob.upload_from_string(
                json.dumps(data, indent=2),
                content_type='application/json'
            )
            logger.info(f"📤 Saved {filename} to GCS")
            return True

        except Exception as e:
            logger.error(f"Failed to write {filename} to GCS: {e}")
            return False

    # ========== Orders Management ==========

    def load_orders(self) -> List[Dict[str, Any]]:
        """Load order history from GCS"""
        data = self._read_json(ORDERS_FILE)
        orders = data.get('orders', [])
        logger.info(f"📦 Loaded {len(orders)} orders from GCS")
        return orders

    def save_orders(self, orders: List[Dict[str, Any]]) -> bool:
        """Save order history to GCS"""
        data = {
            'orders': orders,
            'updated_at': datetime.now().isoformat(),
            'total_orders': len(orders)
        }
        success = self._write_json(ORDERS_FILE, data)
        if success:
            logger.info(f"💾 Saved {len(orders)} orders to GCS")
        return success

    def add_order(self, order: Dict[str, Any]) -> bool:
        """Add a single order to storage"""
        orders = self.load_orders()
        orders.append(order)
        return self.save_orders(orders)

    # ========== Decisions Management ==========

    def load_decisions(self) -> List[Dict[str, Any]]:
        """Load AI decisions from GCS"""
        data = self._read_json(DECISIONS_FILE)
        decisions = data.get('decisions', [])
        logger.info(f"🧠 Loaded {len(decisions)} AI decisions from GCS")
        return decisions

    def save_decisions(self, decisions: List[Dict[str, Any]]) -> bool:
        """Save AI decisions to GCS"""
        data = {
            'decisions': decisions,
            'updated_at': datetime.now().isoformat(),
            'total_decisions': len(decisions)
        }
        success = self._write_json(DECISIONS_FILE, data)
        if success:
            logger.info(f"💾 Saved {len(decisions)} decisions to GCS")
        return success

    def add_decision(self, decision: Dict[str, Any]) -> bool:
        """Add a single AI decision to storage"""
        decisions = self.load_decisions()
        decisions.append(decision)
        return self.save_decisions(decisions)

    # ========== Markets Management ==========

    def load_markets(self) -> List[Dict[str, Any]]:
        """Load analyzed markets from GCS"""
        data = self._read_json(MARKETS_FILE)
        markets = data.get('markets', [])
        logger.info(f"📊 Loaded {len(markets)} markets from GCS")
        return markets

    def save_markets(self, markets: List[Dict[str, Any]]) -> bool:
        """Save analyzed markets to GCS"""
        data = {
            'markets': markets,
            'updated_at': datetime.now().isoformat(),
            'total_markets': len(markets)
        }
        success = self._write_json(MARKETS_FILE, data)
        if success:
            logger.info(f"💾 Saved {len(markets)} markets to GCS")
        return success

    def add_market_analysis(self, market: Dict[str, Any]) -> bool:
        """Add a single market analysis to storage"""
        markets = self.load_markets()

        # Keep only last 100 markets to avoid unbounded growth
        if len(markets) >= 100:
            markets = markets[-99:]  # Keep last 99, add 1 new = 100

        markets.append(market)
        return self.save_markets(markets)


# Global instance
_storage = None


def get_storage() -> Optional[GCSStorage]:
    """
    Get global GCS storage instance (OPTIONAL)

    Returns:
        GCSStorage instance if USE_GCS_STORAGE=true, otherwise None

    When None is returned, the application should use local /tmp storage
    """
    global _storage

    # Check if GCS is enabled via environment variable
    use_gcs = os.getenv("USE_GCS_STORAGE", "false").lower() == "true"

    if not use_gcs:
        logger.info("📂 GCS storage disabled (USE_GCS_STORAGE=false), using local /tmp storage")
        return None

    # Initialize GCS if enabled
    if _storage is None:
        _storage = GCSStorage()
    return _storage
