#!/usr/bin/env python3
"""Direct Polymarket API Check - Query real positions and orders"""
import requests
import json
from datetime import datetime

# Your wallet address
WALLET_ADDRESS = "0x84f809829dA7feB5F947d360ED0c6bB11C308d2b"

# Polymarket CLOB API endpoints
CLOB_API_BASE = "https://clob.polymarket.com"

print("=" * 70)
print(f"POLYMARKET API CHECK")
print(f"Wallet: {WALLET_ADDRESS}")
print(f"Time: {datetime.now().isoformat()}")
print("=" * 70)
print()

# 1. Check orders
print("🔍 Fetching orders from Polymarket CLOB...")
try:
    orders_url = f"{CLOB_API_BASE}/orders"
    params = {"maker": WALLET_ADDRESS}

    response = requests.get(orders_url, params=params, timeout=10)
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        orders = response.json()
        print(f"   Found: {len(orders)} orders")
        print()

        if orders:
            print("📋 ORDERS:")
            print("-" * 70)
            for i, order in enumerate(orders, 1):
                print(f"\n{i}. Order ID: {order.get('id', 'N/A')}")
                print(f"   Market: {order.get('market', 'N/A')}")
                print(f"   Side: {order.get('side', 'N/A')}")
                print(f"   Price: ${float(order.get('price', 0)):.4f}")
                print(f"   Size: {float(order.get('size', 0)):.2f}")
                print(f"   Status: {order.get('status', 'N/A')}")
                print(f"   Created: {order.get('created_at', 'N/A')}")
        else:
            print("   ⚠️  No orders found")
    else:
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("=" * 70)

# 2. Check positions (balances)
print("💼 Fetching positions/balances from Polymarket CLOB...")
try:
    balances_url = f"{CLOB_API_BASE}/balances"
    params = {"address": WALLET_ADDRESS}

    response = requests.get(balances_url, params=params, timeout=10)
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        balances = response.json()
        print(f"   Response type: {type(balances)}")

        # Handle different response formats
        if isinstance(balances, list):
            positions = balances
        elif isinstance(balances, dict):
            positions = balances.get('balances', [])
        else:
            positions = []

        print(f"   Found: {len(positions)} positions")
        print()

        if positions:
            print("📊 POSITIONS:")
            print("-" * 70)
            for i, pos in enumerate(positions, 1):
                balance = float(pos.get('balance', 0))
                if balance > 0:  # Only show non-zero positions
                    print(f"\n{i}. Token: {pos.get('asset_id', 'N/A')}")
                    print(f"   Balance: {balance:.2f} shares")
                    print(f"   Market: {pos.get('market', 'N/A')}")
        else:
            print("   ⚠️  No positions found")
    else:
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("=" * 70)

# 3. Try to get trades history
print("📈 Fetching trade history from Polymarket CLOB...")
try:
    trades_url = f"{CLOB_API_BASE}/trades"
    params = {"maker": WALLET_ADDRESS}

    response = requests.get(trades_url, params=params, timeout=10)
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        trades = response.json()
        print(f"   Found: {len(trades)} trades")
        print()

        if trades:
            print("🔄 RECENT TRADES:")
            print("-" * 70)
            for i, trade in enumerate(trades[:10], 1):  # Show last 10
                print(f"\n{i}. Trade ID: {trade.get('id', 'N/A')[:40]}...")
                print(f"   Market: {trade.get('market', 'N/A')}")
                print(f"   Side: {trade.get('side', 'N/A')}")
                print(f"   Price: ${float(trade.get('price', 0)):.4f}")
                print(f"   Size: {float(trade.get('size', 0)):.2f}")
                print(f"   Time: {trade.get('timestamp', 'N/A')}")
        else:
            print("   ⚠️  No trade history found")
    else:
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("=" * 70)
print("✅ Done!")
