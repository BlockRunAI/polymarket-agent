#!/usr/bin/env python3
"""Check real Polymarket positions using authenticated CLOB client"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print(f"POLYMARKET REAL POSITION CHECK")
print(f"Time: {datetime.now().isoformat()}")
print("=" * 70)
print()

# Import after path setup
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get credentials
wallet_address = os.getenv("POLYGON_WALLET_ADDRESS", "0x84f809829dA7feB5F947d360ED0c6bB11C308d2b")
api_key = os.getenv("POLYMARKET_API_KEY")
api_secret = os.getenv("POLYMARKET_API_SECRET")
api_passphrase = os.getenv("POLYMARKET_API_PASSPHRASE")

print(f"🔐 Wallet: {wallet_address}")
print(f"🔑 API Key: {'✅ Set' if api_key else '❌ Not set'}")
print(f"🔑 API Secret: {'✅ Set' if api_secret else '❌ Not set'}")
print(f"🔑 API Passphrase: {'✅ Set' if api_passphrase else '❌ Not set'}")
print()

if not all([api_key, api_secret, api_passphrase]):
    print("❌ Missing API credentials!")
    print("   Please set in .env file:")
    print("   - POLYMARKET_API_KEY")
    print("   - POLYMARKET_API_SECRET")
    print("   - POLYMARKET_API_PASSPHRASE")
    sys.exit(1)

# Create authenticated client
print("🔄 Connecting to Polymarket CLOB...")
try:
    creds = ApiCreds(
        api_key=api_key,
        api_secret=api_secret,
        api_passphrase=api_passphrase
    )

    client = ClobClient(
        host="https://clob.polymarket.com",
        chain_id=137,  # Polygon
        key=os.getenv("POLYGON_WALLET_PRIVATE_KEY", ""),
        creds=creds
    )
    print("✅ Connected!")
    print()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# 1. Get orders
print("=" * 70)
print("📋 FETCHING ORDERS...")
print("=" * 70)
try:
    orders = client.get_orders()
    print(f"Found: {len(orders)} orders")
    print()

    if orders:
        for i, order in enumerate(orders, 1):
            print(f"{i}. Order ID: {order.get('id', 'N/A')[:60]}...")
            print(f"   Market: {order.get('market', 'N/A')}")
            print(f"   Asset ID: {order.get('asset_id', 'N/A')[:40]}...")
            print(f"   Side: {order.get('side', 'N/A')}")
            print(f"   Price: ${float(order.get('price', 0)):.4f}")
            print(f"   Original Size: {float(order.get('original_size', 0)):.2f}")
            print(f"   Size Matched: {float(order.get('size_matched', 0)):.2f}")
            print(f"   Status: {order.get('status', 'N/A')}")
            print(f"   Created: {order.get('created_at', 'N/A')}")
            print()
    else:
        print("⚠️  No open orders found")
        print("   This could mean:")
        print("   1. All orders have been filled")
        print("   2. All orders have been cancelled")
        print("   3. No orders have been placed yet")
    print()
except Exception as e:
    print(f"❌ Error fetching orders: {e}")
    print()

# 2. Get balances (positions)
print("=" * 70)
print("💼 FETCHING BALANCES/POSITIONS...")
print("=" * 70)
try:
    # Try get_balances if available
    try:
        balances = client.get_balances()
        print(f"Found: {len(balances)} balance entries")
        print()

        non_zero = [b for b in balances if float(b.get('balance', 0)) > 0]
        if non_zero:
            for i, bal in enumerate(non_zero, 1):
                print(f"{i}. Asset ID: {bal.get('asset_id', 'N/A')[:40]}...")
                print(f"   Balance: {float(bal.get('balance', 0)):.4f} shares")
                print(f"   Market: {bal.get('market', 'N/A')}")
                print()
        else:
            print("⚠️  No non-zero balances found")
            print("   This means you have no active positions")
    except AttributeError:
        print("⚠️  get_balances() not available in this client version")
        print("   Trying alternative method...")

        # Alternative: check if there are any filled orders
        print("   Checking order history for fills...")

except Exception as e:
    print(f"❌ Error fetching balances: {e}")
    print()

# 3. Get order book for specific market (if we know the ID)
print("=" * 70)
print("🔍 CHECKING SPECIFIC ORDER...")
print("=" * 70)
order_id = "0xccf754f812e413a3228da2b3d03ddca1615f3a45f4a557ba28ce15516846842b"
print(f"Order ID: {order_id}")
print()

try:
    # Try to get specific order
    order = client.get_order(order_id)
    if order:
        print("✅ Order found!")
        print(f"   Market: {order.get('market', 'N/A')}")
        print(f"   Side: {order.get('side', 'N/A')}")
        print(f"   Price: ${float(order.get('price', 0)):.4f}")
        print(f"   Original Size: {float(order.get('original_size', 0)):.2f}")
        print(f"   Size Matched: {float(order.get('size_matched', 0)):.2f}")
        print(f"   Status: {order.get('status', 'N/A')}")
        print(f"   Created: {order.get('created_at', 'N/A')}")
        print()

        if order.get('status') == 'MATCHED':
            print("   🎉 This order has been FILLED!")
        elif order.get('status') == 'LIVE':
            print("   ⏳ This order is still OPEN (waiting to fill)")
        elif order.get('status') == 'CANCELLED':
            print("   ❌ This order was CANCELLED")
    else:
        print("⚠️  Order not found")
        print("   This could mean:")
        print("   1. Order was already filled and removed from orderbook")
        print("   2. Order was cancelled")
        print("   3. Order ID is incorrect")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 70)
print("✅ COMPLETE!")
print("=" * 70)
