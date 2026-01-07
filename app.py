#!/usr/bin/env python3
"""
Polymarket AI Agent - Web Dashboard
Flask application for monitoring and controlling the agent
"""
from flask import Flask, render_template, jsonify, request, Response
from functools import wraps
from datetime import datetime
import os
import logging
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging with in-memory buffer
class LogBuffer(logging.Handler):
    """Store recent logs in memory for dashboard display"""
    def __init__(self, max_lines=100):
        super().__init__()
        self.logs = []
        self.max_lines = max_lines

    def emit(self, record):
        msg = self.format(record)
        self.logs.append(msg)
        if len(self.logs) > self.max_lines:
            self.logs = self.logs[-self.max_lines:]

    def get_logs(self):
        return self.logs.copy()

    def clear(self):
        self.logs = []

log_buffer = LogBuffer()
log_buffer.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.addHandler(log_buffer)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "default-dev-key")

# Basic Auth
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "polymarket2024")


def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS


def authenticate():
    return Response(
        'Login required', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Import modules (after app creation to avoid circular imports)
from src.market.polymarket import fetch_active_markets
from src.analysis.ai_analyzer import get_analyzer
from src.trading.wallet import get_wallet
from src.trading.executor import get_executor

# Initialize BlockRun client and trading
analyzer = get_analyzer()
wallet = get_wallet()
executor = get_executor()

def _truncate(addr):
    return f"{addr[:6]}...{addr[-4:]}" if addr and len(addr) >= 12 else addr

if analyzer:
    logger.info(f"BlockRun client initialized. Wallet: {_truncate(analyzer.wallet_address)}")
else:
    logger.warning("BlockRun not configured. Set BASE_CHAIN_WALLET_KEY in .env")

if wallet:
    logger.info(f"Trading wallet initialized: {_truncate(wallet.address)}")
else:
    logger.warning("Trading wallet not configured. Set POLYGON_WALLET_PRIVATE_KEY in .env")

if executor:
    logger.info("Trade executor initialized")
else:
    logger.warning("Trade executor not available")


# ============ Agent State ============
class AgentState:
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_run = None
        self.cycle_count = 0
        self.decisions = []
        self.trades = []
        self.error = None
        self.auto_trade = False  # Auto-trading disabled by default

state = AgentState()


def run_agent_cycle():
    """Run one cycle of market analysis with multi-model consensus"""
    try:
        state.cycle_count += 1
        state.last_run = datetime.now()
        state.error = None

        markets = fetch_active_markets(limit=20)
        if not markets:
            logger.warning("No markets fetched from Polymarket API")
            return

        if not analyzer:
            state.error = "AI analyzer not configured"
            return

        num_to_analyze = min(10, len(markets))
        logger.info(f"Fetched {len(markets)} markets, analyzing {num_to_analyze} with 3-model consensus...")

        # Analyze markets using multi-model consensus
        for i, market in enumerate(markets[:num_to_analyze]):
            logger.info(f"Analyzing market {i+1}/{num_to_analyze}...")
            try:
                question = market.get("question", "")
                yes_odds = market.get("yes_odds", 0.5)
                # Use condition_id for trade API (more reliable)
                market_id = market.get("condition_id", market.get("id", ""))

                # Get whale/smart money data from real Polymarket API
                whale_data = None
                try:
                    import asyncio
                    from src.signals.trades import get_smart_money_summary
                    whale_data = asyncio.get_event_loop().run_until_complete(
                        get_smart_money_summary(market_id)
                    )
                    if whale_data and whale_data.get("has_smart_money_activity"):
                        logger.info(f"Whale signal: {whale_data.get('consensus')} ({whale_data.get('confidence', 0)*100:.0f}% confidence)")
                except Exception as e:
                    logger.debug(f"Whale data unavailable: {e}")

                # Use 3-model consensus analysis
                analysis = analyzer.consensus_analysis(
                    question=question,
                    current_odds=yes_odds,
                    whale_data=whale_data
                )

                action = analysis.get("recommendation", "SKIP")
                edge = analysis.get("avg_edge", 0)
                consensus = analysis.get("consensus", "MIXED")

                # Build reasoning from model votes
                model_results = analysis.get("model_results", [])
                reasoning_parts = []
                for r in model_results:
                    reasoning_parts.append(f"{r['model']}: {r['probability']*100:.0f}%")
                reasoning = f"[{consensus}] " + " | ".join(reasoning_parts)

                # Add whale info if available
                if whale_data and whale_data.get("has_smart_money_activity"):
                    reasoning += f" | Whales: {whale_data.get('consensus', 'N/A')}"

                # Prepare whale info for decision
                whale_info = None
                if whale_data and whale_data.get("has_smart_money_activity"):
                    whale_info = {
                        "consensus": whale_data.get("consensus"),
                        "confidence": whale_data.get("confidence", 0),
                        "pattern": whale_data.get("pattern"),
                        "direction": whale_data.get("smart_money_direction"),
                        "volume": whale_data.get("total_large_volume", 0),
                        "traders": whale_data.get("large_traders_count", 0),
                    }

                # Get token IDs for trading
                token_ids = market.get("token_ids", [])
                yes_token = token_ids[0] if len(token_ids) > 0 else None
                no_token = token_ids[1] if len(token_ids) > 1 else None
                logger.info(f"Token IDs: {token_ids[:2] if token_ids else 'NONE'}")

                decision = {
                    "timestamp": datetime.now().isoformat(),
                    "market": question[:60],
                    "action": action,
                    "confidence": analysis.get("avg_confidence", 0),
                    "reasoning": reasoning[:200],
                    "edge": edge,
                    "ai_prob": analysis.get("avg_probability", 0),
                    "market_prob": analysis.get("market_probability", 0),
                    "consensus": consensus,
                    "yes_votes": analysis.get("yes_votes", 0),
                    "no_votes": analysis.get("no_votes", 0),
                    "models_used": analysis.get("models_used", 0),
                    "whale_data": whale_info,
                    "trade_result": None,
                }

                # Auto-trade if enabled (only when action is BET YES or BET NO)
                if state.auto_trade and executor and action.startswith("BET"):
                    try:
                        # Determine which token to trade
                        token_id = yes_token if "YES" in action else no_token

                        if token_id:
                            confidence = analysis.get("avg_confidence", 0)
                            bankroll = wallet.get_usdc_balance() if wallet else 100

                            trade_result = executor.execute_signal(
                                token_id=token_id,
                                action=action,
                                edge=edge,
                                confidence=confidence,
                                consensus=consensus,
                                bankroll=bankroll
                            )

                            decision["trade_result"] = trade_result

                            if trade_result.get("status") in ["success", "submitted"]:
                                status_msg = "SUBMITTED" if trade_result.get("status") == "submitted" else "EXECUTED"
                                logger.info(f"TRADE {status_msg}: {action} ${trade_result.get('size', 0):.2f}")
                                logger.info(f"  Order ID: {trade_result.get('order_id', 'Unknown')}")
                                logger.info(f"  ⚠️  Check Polymarket.com to see if order fills")
                                state.trades.append({
                                    "timestamp": datetime.now().isoformat(),
                                    "market": question[:40],
                                    "action": action,
                                    "size": trade_result.get("size", 0),
                                    "order_id": trade_result.get("order_id"),
                                    "status": trade_result.get("status", "submitted"),
                                    "message": trade_result.get("message", "")
                                })
                            else:
                                logger.info(f"Trade skipped: {trade_result.get('reason', 'unknown')}")
                        else:
                            logger.warning("No token ID available for trading")
                    except Exception as e:
                        logger.error(f"Trade execution error: {e}")
                        decision["trade_result"] = {"status": "error", "reason": str(e)}

                state.decisions.append(decision)

                # Keep only last 30
                if len(state.decisions) > 30:
                    state.decisions = state.decisions[-30:]

                logger.info(f"Consensus: {consensus} | {action} for {question[:30]}... (edge: {edge*100:.1f}%)")

            except Exception as e:
                logger.error(f"Analysis error: {e}")

    except Exception as e:
        state.error = str(e)
        logger.error(f"Cycle error: {e}")


def agent_loop():
    """Background agent loop - continuous market analysis"""
    while state.running:
        run_agent_cycle()
        # Wait 6 hours before next cycle (for continuous demo running)
        logger.info("Cycle complete. Next cycle in 6 hours...")
        time.sleep(6 * 60 * 60)  # 6 hours between cycles


def start_agent():
    """Start the agent background thread"""
    if state.running:
        return False
    state.running = True
    state.thread = threading.Thread(target=agent_loop, daemon=True)
    state.thread.start()
    logger.info("Agent started")
    return True


def stop_agent():
    """Stop the agent"""
    state.running = False
    logger.info("Agent stopped")
    return True


def get_dashboard_data():
    """Get data for dashboard display"""
    # Fetch markets
    markets = fetch_active_markets(limit=10)

    # Format for display - keep raw numeric values for template
    formatted_markets = []
    for m in markets[:8]:
        # Handle volume as string or number
        vol = m.get('volume', 0)
        try:
            vol = float(vol) if vol else 0
        except (ValueError, TypeError):
            vol = 0

        # Get odds as floats
        yes_odds = m.get('yes_odds', 0)
        no_odds = m.get('no_odds', 0)
        try:
            yes_odds = float(yes_odds) if yes_odds else 0
        except (ValueError, TypeError):
            yes_odds = 0
        try:
            no_odds = float(no_odds) if no_odds else 0
        except (ValueError, TypeError):
            no_odds = 0

        formatted_markets.append({
            "question": m.get("question", "Unknown"),
            "description": m.get("description", "")[:200],
            "end_date": m.get("end_date", "Unknown"),
            "volume": vol,
            "yes_odds": yes_odds,
            "no_odds": no_odds,
        })

    # Calculate mock totals (in production, use real portfolio data)
    def safe_float(v):
        try:
            return float(v) if v else 0
        except (ValueError, TypeError):
            return 0
    total_bet = sum(safe_float(m.get("volume", 0)) for m in markets[:5]) / 1000
    expected_profit = total_bet * 0.15  # Mock 15% expected return
    roi = 15.0

    return {
        'markets': formatted_markets,
        'tomorrow_display': datetime.now().strftime('%B %d, %Y'),
        'total_bet_amount': total_bet,
        'total_expected_profit': expected_profit,
        'roi_percentage': roi,
        'current_year': datetime.now().year
    }


def truncate_address(address: str) -> str:
    """Truncate wallet address for display (0x1234...5678)"""
    if not address or len(address) < 12:
        return address
    return f"{address[:6]}...{address[-4:]}"


@app.route('/')
def home():
    """Dashboard home page - public for demo"""
    data = get_dashboard_data()
    return render_template('index.html', **data)


@app.route('/api/markets')
def api_markets():
    """API endpoint to get market data"""
    markets = fetch_active_markets(limit=20)
    return jsonify({
        "count": len(markets),
        "markets": markets
    })


@app.route('/api/status')
def api_status():
    """API endpoint to get agent status"""
    status = {
        "ai_configured": analyzer is not None,
        "wallet_configured": wallet is not None,
        "timestamp": datetime.now().isoformat()
    }

    if analyzer:
        status["ai_wallet"] = truncate_address(analyzer.wallet_address)

    if wallet:
        status["trading_wallet"] = truncate_address(wallet.address)
        status["usdc_balance"] = wallet.get_usdc_balance()
        status["approved"] = wallet.check_approval()

    return jsonify(status)


@app.route('/api/analyze')
def api_analyze():
    """API endpoint to run AI analysis"""
    if not analyzer:
        return jsonify({"error": "AI analyzer not configured"}), 503

    markets = fetch_active_markets(limit=10)

    if not markets:
        return jsonify({"error": "No markets available"}), 404

    analysis = analyzer.analyze_markets(markets)

    return jsonify({
        "markets_analyzed": len(markets),
        "analysis": analysis
    })


# ============ Agent Control Endpoints ============

@app.route('/api/agent/start', methods=['POST'])
@requires_auth
def api_start():
    """Start the agent"""
    if start_agent():
        return jsonify({"status": "started"})
    return jsonify({"status": "already_running"})


@app.route('/api/agent/stop', methods=['POST'])
@requires_auth
def api_stop():
    """Stop the agent"""
    stop_agent()
    return jsonify({"status": "stopped"})


@app.route('/api/agent/status')
def api_agent_status():
    """Get detailed agent status"""
    return jsonify({
        "running": state.running,
        "auto_trade": state.auto_trade,
        "last_run": state.last_run.isoformat() if state.last_run else None,
        "cycle_count": state.cycle_count,
        "error": state.error,
        "decisions_count": len(state.decisions),
        "trades_count": len(state.trades),
    })


@app.route('/api/agent/decisions')
def api_decisions():
    """Get recent decisions"""
    return jsonify({"decisions": state.decisions[-20:]})


@app.route('/api/agent/run-once', methods=['POST'])
@requires_auth
def api_run_once():
    """Run one analysis cycle manually"""
    if state.running:
        return jsonify({"error": "Agent is running, stop it first"}), 400
    run_agent_cycle()
    return jsonify({"status": "ok", "cycle": state.cycle_count})


@app.route('/api/agent/auto-trade', methods=['POST'])
@requires_auth
def api_toggle_auto_trade():
    """Toggle auto-trading"""
    data = request.get_json() or {}
    if "enabled" in data:
        state.auto_trade = bool(data["enabled"])
    else:
        state.auto_trade = not state.auto_trade

    logger.info(f"Auto-trade {'ENABLED' if state.auto_trade else 'DISABLED'}")
    return jsonify({"auto_trade": state.auto_trade})


@app.route('/api/agent/trades')
def api_trades():
    """Get recent trades"""
    return jsonify({"trades": state.trades[-20:]})


@app.route('/api/positions')
def api_positions():
    """Get current open positions and orders from Polymarket"""
    if not executor:
        return jsonify({"error": "Executor not configured"}), 503

    try:
        # Get open orders from Polymarket API
        logger.info("📊 Fetching positions from Polymarket...")
        open_orders = executor.get_open_orders()
        logger.info(f"📊 Found {len(open_orders)} open orders from API")

        # Get filled positions
        positions = executor.get_positions()
        logger.info(f"📊 Found {len(positions)} filled positions from API")

        # Also include recently submitted orders from this session
        session_orders = []
        for trade in state.trades:
            if trade.get("status") == "submitted" and trade.get("order_id"):
                session_orders.append({
                    "order_id": trade["order_id"],
                    "market": trade.get("market", "Unknown"),
                    "action": trade.get("action", "Unknown"),
                    "size": trade.get("size", 0),
                    "timestamp": trade.get("timestamp"),
                    "source": "session"  # Mark as from current session
                })

        logger.info(f"📊 Found {len(session_orders)} submitted orders from session")

        return jsonify({
            "open_orders": open_orders,
            "positions": positions,
            "session_orders": session_orders,  # Add session-tracked orders
            "total_orders": len(open_orders),
            "total_positions": len(positions),
            "total_session_orders": len(session_orders)
        })
    except Exception as e:
        logger.error(f"❌ Failed to fetch positions: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e), "open_orders": [], "positions": [], "session_orders": []}), 500


@app.route('/api/logs')
def api_logs():
    """Get recent logs"""
    return jsonify({"logs": log_buffer.get_logs()})


@app.route('/api/logs/clear', methods=['POST'])
@requires_auth
def api_clear_logs():
    """Clear logs"""
    log_buffer.clear()
    return jsonify({"status": "cleared"})


@app.route('/setup')
def setup():
    """Setup page"""
    missing_vars = []
    if not os.getenv("BLOCKRUN_WALLET_KEY"):
        missing_vars.append("BLOCKRUN_WALLET_KEY")
    if not os.getenv("POLYGON_WALLET_PRIVATE_KEY"):
        missing_vars.append("POLYGON_WALLET_PRIVATE_KEY")

    return render_template('setup.html', missing_vars=missing_vars, current_year=datetime.now().year)


# Create templates directory if needed
if not os.path.exists('templates'):
    os.makedirs('templates')
    logger.info("Created templates directory")


if __name__ == '__main__':
    print("=" * 60)
    print("POLYMARKET AI AGENT - WEB DASHBOARD")
    print("=" * 60)

    if not analyzer:
        print("WARNING: BlockRun not configured (AI features disabled)")
    if not wallet:
        print("WARNING: Trading wallet not configured")

    print("\nStarting Flask app...")
    print("Visit http://127.0.0.1:5001 in your browser")

    app.run(debug=True, port=5001)
