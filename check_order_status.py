#!/usr/bin/env python3
"""
Check Order Status - Debug Script
Shows the actual status of recent orders to understand failures
"""
import sys
sys.path.insert(0, '.')

from src.trading.executor import get_executor
from src.trading.wallet import get_wallet
import json

def main():
    print("=" * 70)
    print("POLYMARKET ORDER STATUS CHECKER")
    print("=" * 70)

    wallet = get_wallet()
    if not wallet:
        print("❌ Wallet not configured")
        return

    print(f"\n💼 Wallet: {wallet.address}")
    print(f"💵 USDC Balance: ${wallet.get_usdc_balance():.2f}")

    executor = get_executor()
    if not executor:
        print("❌ Executor not initialized")
        return

    print(f"\n📊 Fetching orders from Polymarket...\n")

    # Get all orders
    try:
        orders = executor.get_open_orders()

        if not orders:
            print("ℹ️  No open orders found")
        else:
            print(f"Found {len(orders)} open orders:\n")
            for i, order in enumerate(orders, 1):
                print(f"{i}. Order ID: {order.get('order_id', 'Unknown')[:30]}...")
                print(f"   Status: {order.get('status', 'Unknown')}")
                print(f"   Market: {order.get('market', 'Unknown')}")
                print(f"   Side: {order.get('side', 'Unknown')}")
                print(f"   Price: {order.get('price', 0):.3f}")
                print(f"   Size: {order.get('size', 0):.2f} shares")
                print(f"   Value: ${order.get('value', 0):.2f}")
                print()

        # Get positions (filled orders)
        print("\n📈 Fetching positions (filled orders)...\n")
        positions = executor.get_positions()

        if not positions:
            print("ℹ️  No filled positions found")
        else:
            print(f"Found {len(positions)} filled positions:\n")
            for i, pos in enumerate(positions, 1):
                print(f"{i}. Asset: {pos.get('asset_id', 'Unknown')[:30]}...")
                print(f"   Size: {pos.get('size', 0):.2f} shares")
                print(f"   Avg Price: {pos.get('avg_price', 0):.3f}")
                print(f"   Cost Basis: ${pos.get('value', 0):.2f}")
                print()

        # Try to get all orders including filled/cancelled
        print("\n🔍 Checking all recent orders (including filled/cancelled)...\n")
        if hasattr(executor.client, 'get_orders'):
            all_orders = executor.client.get_orders()

            # Group by status
            status_counts = {}
            for order in all_orders:
                if isinstance(order, dict):
                    status = order.get('status', 'Unknown')
                else:
                    status = getattr(order, 'status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1

            print("Order Status Summary:")
            for status, count in status_counts.items():
                print(f"  {status}: {count} orders")

            # Show cancelled/rejected orders
            print("\n❌ Failed/Cancelled Orders:")
            failed_count = 0
            for order in all_orders:
                if isinstance(order, dict):
                    status = order.get('status', 'Unknown')
                    order_id = order.get('id') or order.get('orderID', 'Unknown')
                else:
                    status = getattr(order, 'status', 'Unknown')
                    order_id = getattr(order, 'id', None) or getattr(order, 'orderID', 'Unknown')

                if status in ['CANCELLED', 'REJECTED', 'EXPIRED', 'FAILED']:
                    failed_count += 1
                    print(f"\n  {failed_count}. {status}")
                    print(f"     Order ID: {str(order_id)[:30]}...")
                    if isinstance(order, dict):
                        print(f"     Market: {order.get('market', 'Unknown')}")
                    else:
                        print(f"     Market: {getattr(order, 'market', 'Unknown')}")

            if failed_count == 0:
                print("  ✓ No failed orders found")

    except Exception as e:
        print(f"❌ Error fetching orders: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
