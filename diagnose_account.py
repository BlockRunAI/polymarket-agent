#!/usr/bin/env python3
"""
Comprehensive Polymarket Account Diagnostic Tool
Checks orders, positions, trades, and balances
"""
import requests
import json
from datetime import datetime

WALLET_ADDRESS = "0x84f809829dA7feB5F947d360ED0c6bB11C308d2b"
CLOB_API = "https://clob.polymarket.com"

print("=" * 80)
print("POLYMARKET ACCOUNT DIAGNOSTIC")
print("=" * 80)
print(f"Wallet: {WALLET_ADDRESS}")
print(f"Time: {datetime.now().isoformat()}")
print("=" * 80)
print()

# Test 1: Check open orders
print("📋 TEST 1: Checking Open Orders...")
print("-" * 80)
try:
    response = requests.get(
        f"{CLOB_API}/orders",
        params={"maker": WALLET_ADDRESS},
        timeout=10
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        orders = response.json()
        print(f"Found: {len(orders)} orders")

        if orders:
            for i, order in enumerate(orders[:5], 1):
                print(f"\n  Order {i}:")
                print(f"    ID: {order.get('id', 'N/A')[:40]}...")
                print(f"    Market: {order.get('market', 'N/A')}")
                print(f"    Side: {order.get('side', 'N/A')}")
                print(f"    Price: {order.get('price', 'N/A')}")
                print(f"    Size: {order.get('size', 'N/A')}")
                print(f"    Status: {order.get('status', 'N/A')}")
        else:
            print("  ⚠️  No open orders found")
    else:
        print(f"  ❌ Error: {response.text}")
except Exception as e:
    print(f"  ❌ Exception: {e}")

print()
print("=" * 80)

# Test 2: Check trades history
print("📈 TEST 2: Checking Trade History...")
print("-" * 80)
try:
    response = requests.get(
        f"{CLOB_API}/trades",
        params={"maker": WALLET_ADDRESS},
        timeout=10
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        trades = response.json()
        print(f"Found: {len(trades)} trades")

        if trades:
            for i, trade in enumerate(trades[:5], 1):
                print(f"\n  Trade {i}:")
                print(f"    ID: {trade.get('id', 'N/A')[:40]}...")
                print(f"    Market: {trade.get('market', 'N/A')}")
                print(f"    Side: {trade.get('side', 'N/A')}")
                print(f"    Price: {trade.get('price', 'N/A')}")
                print(f"    Size: {trade.get('size', 'N/A')}")
                print(f"    Time: {trade.get('timestamp', 'N/A')}")
        else:
            print("  ⚠️  No trade history found")
    else:
        print(f"  Error: {response.text}")
except Exception as e:
    print(f"  ❌ Exception: {e}")

print()
print("=" * 80)

# Test 3: Check via Gamma API (market data)
print("🌐 TEST 3: Checking via Gamma API...")
print("-" * 80)
try:
    # This won't show user-specific data but helps verify connectivity
    response = requests.get(
        "https://gamma-api.polymarket.com/markets",
        params={"limit": 3, "active": True},
        timeout=10
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        markets = response.json()
        print(f"✅ Gamma API accessible ({len(markets)} markets fetched)")
    else:
        print(f"⚠️  Gamma API issue: {response.status_code}")
except Exception as e:
    print(f"❌ Exception: {e}")

print()
print("=" * 80)
print("RECOMMENDATIONS:")
print("=" * 80)

print("""
1. 访问 https://polymarket.com 并连接钱包 0x84f8...8d2b
2. 检查以下内容：
   - Activity → Open Orders (未成交订单)
   - Portfolio → Positions (持仓)
   - Activity → History (历史记录)

3. 如果您在 Polymarket.com 上看到订单/持仓但这里显示为 0：

   可能原因：
   a) API 凭证关联到不同的账户
   b) 订单已经被成交或取消
   c) 代理钱包地址不匹配

4. 下一步：
   - 请告诉我您在 Polymarket.com 上实际看到的内容
   - 我会帮您手动导入这些持仓到 Dashboard
""")

print("=" * 80)
