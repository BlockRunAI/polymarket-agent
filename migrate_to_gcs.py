#!/usr/bin/env python3
"""Migrate existing order data to Google Cloud Storage"""
import json
from datetime import datetime
from google.cloud import storage

BUCKET_NAME = "polymarket-agent-data"

# Current orders
orders = [
    {
        "action": "BET NO",
        "market": "Will Jesus Christ return before GTA VI?",
        "message": "12.6 shares at 52¢ (avg cost), current value $6.47",
        "order_id": "filled_jesus_gtavi_1767837280",
        "size": 6.47,
        "status": "filled",
        "timestamp": "2026-01-08T01:54:40Z"
    },
    {
        "action": "BET NO",
        "market": "Will bitcoin hit $1m before GTA VI?",
        "message": "1.1 shares at 52¢ (avg cost), current value $0.59",
        "order_id": "filled_btc_gtavi_1767837280",
        "size": 0.59,
        "status": "filled",
        "timestamp": "2026-01-08T01:54:40Z"
    }
]

print("=" * 70)
print("MIGRATING DATA TO GOOGLE CLOUD STORAGE")
print("=" * 70)
print(f"Bucket: {BUCKET_NAME}")
print(f"Orders to migrate: {len(orders)}")
print()

# Initialize GCS client
client = storage.Client()
bucket = client.bucket(BUCKET_NAME)

# Upload orders
print("📤 Uploading orders.json...")
orders_data = {
    'orders': orders,
    'updated_at': datetime.now().isoformat(),
    'total_orders': len(orders)
}

blob = bucket.blob('orders.json')
blob.upload_from_string(
    json.dumps(orders_data, indent=2),
    content_type='application/json'
)
print(f"✅ Uploaded {len(orders)} orders to GCS")

# Initialize empty decisions file
print("📤 Initializing decisions.json...")
decisions_data = {
    'decisions': [],
    'updated_at': datetime.now().isoformat(),
    'total_decisions': 0
}

blob = bucket.blob('decisions.json')
blob.upload_from_string(
    json.dumps(decisions_data, indent=2),
    content_type='application/json'
)
print("✅ Initialized decisions.json")

# Initialize empty markets file
print("📤 Initializing markets.json...")
markets_data = {
    'markets': [],
    'updated_at': datetime.now().isoformat(),
    'total_markets': 0
}

blob = bucket.blob('markets.json')
blob.upload_from_string(
    json.dumps(markets_data, indent=2),
    content_type='application/json'
)
print("✅ Initialized markets.json")

print()
print("=" * 70)
print("✅ MIGRATION COMPLETE!")
print("=" * 70)
print()
print("Verify migration:")
print(f"  gsutil ls gs://{BUCKET_NAME}/")
print(f"  gsutil cat gs://{BUCKET_NAME}/orders.json")
