#!/usr/bin/env python3
"""Add existing order to persistent storage"""
import requests
import json

# The existing order that needs to be tracked
order_data = {
    "order_id": "0xccf754f812e413a3228da2b3d03ddca1615f3a45f4a557ba28ce15516846842b",
    "market": "Will Jesus Christ return before GTA VI?",
    "action": "BET NO",
    "size": 2.25,
    "timestamp": "2026-01-07T20:09:55.093Z",
    "status": "submitted",
    "message": "Order submitted to orderbook (waiting to fill)"
}

# POST to the API endpoint
url = "https://polyagent.blockrun.ai/api/add_order"
headers = {"Content-Type": "application/json"}

print(f"📤 Adding order to persistent storage...")
print(f"   Order ID: {order_data['order_id'][:40]}...")
print(f"   Market: {order_data['market']}")
print(f"   Action: {order_data['action']}")
print(f"   Size: ${order_data['size']}")

response = requests.post(url, json=order_data, headers=headers)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Success! Order added to persistent storage")
    print(f"   Status: {result.get('status')}")
    print(f"\n🌐 View at: https://polyagent.blockrun.ai/")
    print(f"   The order should now appear in 'Recently Submitted Orders' section")
else:
    print(f"❌ Failed: HTTP {response.status_code}")
    print(f"   Response: {response.text}")
