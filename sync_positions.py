#!/usr/bin/env python3
"""
Sync positions and orders from Polymarket to the dashboard
Usage: python3 sync_positions.py
"""
import requests
import json
from datetime import datetime

DASHBOARD_URL = "https://polyagent.blockrun.ai"
WALLET_ADDRESS = "0x84f809829dA7feB5F947d360ED0c6bB11C308d2b"

print("=" * 70)
print("POLYMARKET POSITION SYNC TOOL")
print("=" * 70)
print(f"Wallet: {WALLET_ADDRESS}")
print(f"Dashboard: {DASHBOARD_URL}")
print()

# Manual entry mode
print("📝 Please provide your positions/orders from Polymarket.com:")
print()

orders = []

while True:
    print("-" * 70)
    print("Enter order details (or press Enter to finish):")
    market = input("Market question: ").strip()

    if not market:
        break

    action = input("Action (BET YES/BET NO): ").strip() or "BET NO"
    size = input("Size ($): ").strip()
    order_id = input("Order ID (optional, from Polymarket): ").strip()
    status = input("Status (submitted/filled/open): ").strip() or "submitted"

    try:
        size_float = float(size)
    except:
        print("⚠️  Invalid size, skipping...")
        continue

    order = {
        "market": market,
        "action": action,
        "size": size_float,
        "order_id": order_id or f"manual_{datetime.now().timestamp()}",
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "message": "Manually synced from Polymarket"
    }

    orders.append(order)
    print(f"✅ Added: {market} - {action} ${size_float}")
    print()

if not orders:
    print("No orders to sync.")
    exit(0)

print()
print("=" * 70)
print(f"📤 Syncing {len(orders)} orders to dashboard...")
print("=" * 70)

for i, order in enumerate(orders, 1):
    print(f"\n{i}. Syncing: {order['market'][:50]}...")

    try:
        response = requests.post(
            f"{DASHBOARD_URL}/api/add_order",
            json=order,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            print(f"   ✅ Success!")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print()
print("=" * 70)
print("✅ Sync complete!")
print(f"🌐 View at: {DASHBOARD_URL}")
print("=" * 70)
