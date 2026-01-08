#!/bin/bash
# Add existing Polymarket positions to Dashboard

DASHBOARD_URL="https://polyagent.blockrun.ai"

echo "=========================================="
echo "Adding Polymarket Positions to Dashboard"
echo "=========================================="
echo ""

# Position 1: Jesus Christ/GTA VI
echo "1. Adding: Will Jesus Christ return before GTA VI?"
curl -X POST "${DASHBOARD_URL}/api/add_order" \
  -H "Content-Type: application/json" \
  -d '{
    "market": "Will Jesus Christ return before GTA VI?",
    "action": "BET NO",
    "size": 6.47,
    "order_id": "filled_jesus_gtavi_'$(date +%s)'",
    "status": "filled",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "message": "12.6 shares at 52¢ (avg cost), current value $6.47"
  }'
echo ""
echo ""

# Position 2: Bitcoin $1M/GTA VI
echo "2. Adding: Will bitcoin hit $1m before GTA VI?"
curl -X POST "${DASHBOARD_URL}/api/add_order" \
  -H "Content-Type: application/json" \
  -d '{
    "market": "Will bitcoin hit $1m before GTA VI?",
    "action": "BET NO",
    "size": 0.59,
    "order_id": "filled_btc_gtavi_'$(date +%s)'",
    "status": "filled",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "message": "1.1 shares at 52¢ (avg cost), current value $0.59"
  }'
echo ""
echo ""

echo "=========================================="
echo "✅ Positions added!"
echo "🌐 View at: ${DASHBOARD_URL}"
echo "=========================================="
