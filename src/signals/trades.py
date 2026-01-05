"""
市场交易流数据 - 使用真实 Polymarket API
获取某个市场的所有交易记录
只关注大仓位交易者 - 小仓位没有意义
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional
import statistics

# Polymarket API Endpoints (from informedge)
DATA_API = "https://data-api.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"

# 最小仓位阈值 - 低于此金额的交易不考虑
MIN_POSITION_AMOUNT = 500  # $500 USDC


async def get_recent_trades(
    market_id: str,
    hours: int = 24,
    min_amount: float = MIN_POSITION_AMOUNT
) -> list[dict]:
    """
    获取市场的最近大额交易记录 (真实 API)

    只返回仓位 >= min_amount 的交易
    小仓位的交易没有太多参考价值

    返回:
    [
        {
            "trader": "0x1234...",
            "side": "BUY",           # BUY or SELL
            "position": "YES",       # YES or NO (based on asset)
            "amount": 1000.0,        # USDC value
            "size": 2000,            # number of shares
            "price": 0.55,
            "timestamp": "2025-01-03T12:00:00Z",
        },
        ...
    ]
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Call Polymarket Data API
            response = await client.get(
                f"{DATA_API}/trades",
                params={
                    "market": market_id,
                    "limit": 200
                },
                headers={
                    "User-Agent": "PolymarketAgent/1.0",
                    "Accept": "application/json"
                }
            )
            response.raise_for_status()
            raw_trades = response.json()

            if not raw_trades:
                return []

            # Transform to our format
            trades = []
            for t in raw_trades:
                try:
                    size = float(t.get("size", 0))
                    price = float(t.get("price", 0))
                    amount = size * price  # USDC value

                    if amount < min_amount:
                        continue

                    # Determine position based on asset name (YES/NO token)
                    asset = t.get("asset", "").upper()
                    if "YES" in asset or t.get("outcome") == "Yes":
                        position = "YES"
                    elif "NO" in asset or t.get("outcome") == "No":
                        position = "NO"
                    else:
                        position = "YES"  # Default

                    trades.append({
                        "trader": t.get("maker", t.get("taker", "Unknown")),
                        "side": t.get("side", "BUY").upper(),
                        "position": position,
                        "amount": amount,
                        "size": size,
                        "price": price,
                        "timestamp": t.get("timestamp", t.get("createdAt", "")),
                    })
                except (ValueError, TypeError):
                    continue

            return trades

    except Exception as e:
        print(f"Error fetching trades for {market_id}: {e}")
        return []


async def get_large_trades(market_id: str, min_amount: float = 1000) -> list[dict]:
    """
    获取大额交易 (鲸鱼动向)
    这些是最重要的信号
    """
    all_trades = await get_recent_trades(market_id, min_amount=min_amount)
    # 按金额排序，最大的在前
    return sorted(all_trades, key=lambda t: t["amount"], reverse=True)


async def get_trade_summary(market_id: str, min_amount: float = MIN_POSITION_AMOUNT) -> dict:
    """
    汇总大额交易数据
    只统计大仓位交易，小仓位不计入
    """
    trades = await get_recent_trades(market_id, min_amount=min_amount)

    if not trades:
        return {
            "total_large_trades": 0,
            "buy_yes_volume": 0,
            "sell_yes_volume": 0,
            "buy_no_volume": 0,
            "sell_no_volume": 0,
            "net_yes_flow": 0,
            "net_no_flow": 0,
            "unique_large_buyers": 0,
            "unique_large_sellers": 0,
            "largest_trade": None,
            "top_trades": [],
        }

    # 统计大仓位交易
    buy_yes_volume = sum(t["amount"] for t in trades if t["side"] == "BUY" and t["position"] == "YES")
    sell_yes_volume = sum(t["amount"] for t in trades if t["side"] == "SELL" and t["position"] == "YES")
    buy_no_volume = sum(t["amount"] for t in trades if t["side"] == "BUY" and t["position"] == "NO")
    sell_no_volume = sum(t["amount"] for t in trades if t["side"] == "SELL" and t["position"] == "NO")

    unique_buyers = set(t["trader"] for t in trades if t["side"] == "BUY")
    unique_sellers = set(t["trader"] for t in trades if t["side"] == "SELL")

    # 最大单笔
    largest_trade = max(trades, key=lambda t: t["amount"])

    # Top trades 按金额排序
    top_trades = sorted(trades, key=lambda t: t["amount"], reverse=True)[:10]

    return {
        "total_large_trades": len(trades),
        "min_position_threshold": min_amount,
        "buy_yes_volume": buy_yes_volume,
        "sell_yes_volume": sell_yes_volume,
        "buy_no_volume": buy_no_volume,
        "sell_no_volume": sell_no_volume,
        "net_yes_flow": buy_yes_volume - sell_yes_volume,  # 正=买入压力
        "net_no_flow": buy_no_volume - sell_no_volume,
        "unique_large_buyers": len(unique_buyers),
        "unique_large_sellers": len(unique_sellers),
        "largest_trade": largest_trade,
        "top_trades": top_trades,  # 按金额排序的大额交易
    }


def analyze_trade_patterns(trades: list[dict]) -> dict:
    """
    分析交易模式 (来自 informedge)
    检测: HFT算法, Market Making, 鲸鱼活动, 散户FOMO
    """
    if not trades:
        return {
            "pattern_detected": False,
            "pattern_name": None,
            "net_flow": None,
            "smart_money_direction": None,
            "execution_speed": None,
            "insights": []
        }

    # Calculate net flow
    buy_volume = sum(t["amount"] for t in trades if t["side"] == "BUY")
    sell_volume = sum(t["amount"] for t in trades if t["side"] == "SELL")
    total_volume = buy_volume + sell_volume
    net_flow = buy_volume - sell_volume

    # Determine smart money direction
    smart_money_direction = None
    if total_volume > 0:
        buy_ratio = buy_volume / total_volume
        if buy_ratio >= 0.65:
            smart_money_direction = "Strong BUY"
        elif buy_ratio >= 0.55:
            smart_money_direction = "BUY"
        elif buy_ratio <= 0.35:
            smart_money_direction = "Strong SELL"
        elif buy_ratio <= 0.45:
            smart_money_direction = "SELL"
        else:
            smart_money_direction = "Neutral"

    # Calculate execution speed (trades per minute)
    execution_speed = None
    try:
        timestamps = [t.get("timestamp") for t in trades[:30] if t.get("timestamp")]
        if len(timestamps) >= 2:
            times = []
            for ts in timestamps:
                try:
                    clean_ts = ts.replace("Z", "+00:00") if isinstance(ts, str) else str(ts)
                    times.append(datetime.fromisoformat(clean_ts))
                except:
                    pass
            if len(times) >= 2:
                duration = abs((times[0] - times[-1]).total_seconds()) / 60
                if duration > 0:
                    execution_speed = len(times) / duration
    except:
        pass

    # Detect patterns
    pattern_detected = False
    pattern_name = None
    insights = []

    # Pattern 1: HFT/Algorithm trading
    if execution_speed and execution_speed > 5:
        pattern_detected = True
        pattern_name = "HFT Algorithm"
        insights.append(f"{execution_speed:.1f} trades/min = Algorithm trading")
        insights.append(f"Net flow: ${net_flow/1000:.1f}K towards {smart_money_direction}")

    # Pattern 2: Whale accumulation
    large_trades = [t for t in trades[:20] if t["amount"] > 5000]
    if len(large_trades) >= 2:
        pattern_detected = True
        pattern_name = "Whale Activity"
        largest_val = max(t["amount"] for t in large_trades)
        insights.append(f"{len(large_trades)} whale trades detected (max ${largest_val/1000:.1f}K)")
        insights.append(f"Smart money is {smart_money_direction}")

    # Pattern 3: Retail activity (small average size)
    if not pattern_detected and len(trades) >= 10:
        avg_size = statistics.mean([t.get("size", 0) for t in trades[:20]])
        if avg_size < 100:
            pattern_detected = True
            pattern_name = "Retail Activity"
            insights.append(f"Small avg size ({avg_size:.0f} shares) = Retail traders")
            insights.append(f"Flow is {smart_money_direction}, but low conviction")

    return {
        "pattern_detected": pattern_detected,
        "pattern_name": pattern_name,
        "net_flow": net_flow,
        "net_flow_formatted": f"${abs(net_flow)/1000:.1f}K {smart_money_direction}" if total_volume > 0 else "No activity",
        "smart_money_direction": smart_money_direction,
        "execution_speed": execution_speed,
        "execution_speed_formatted": f"{execution_speed:.1f} trades/min" if execution_speed else "Normal",
        "insights": insights,
        "buy_volume": buy_volume,
        "sell_volume": sell_volume,
        "total_volume": total_volume
    }


async def get_smart_money_summary(market_id: str) -> dict:
    """
    获取 smart money (大仓位交易者) 的汇总
    给 AI 一个清晰的信号

    使用真实 Polymarket API 数据
    """
    trades = await get_recent_trades(market_id, min_amount=1000)  # Only $1000+ trades

    if not trades:
        return {
            "has_smart_money_activity": False,
            "message": "No large trades found in this market",
        }

    # Analyze patterns
    pattern_analysis = analyze_trade_patterns(trades)

    # Calculate YES vs NO volume from large traders
    yes_amount = sum(
        t["amount"] for t in trades
        if t["side"] == "BUY" and t["position"] == "YES"
    )
    no_amount = sum(
        t["amount"] for t in trades
        if t["side"] == "BUY" and t["position"] == "NO"
    )

    # Also consider sells (selling YES = bearish, selling NO = bullish)
    sell_yes = sum(
        t["amount"] for t in trades
        if t["side"] == "SELL" and t["position"] == "YES"
    )
    sell_no = sum(
        t["amount"] for t in trades
        if t["side"] == "SELL" and t["position"] == "NO"
    )

    # Net bullish/bearish calculation
    bullish_flow = yes_amount + sell_no  # Buying YES or selling NO = bullish
    bearish_flow = no_amount + sell_yes  # Buying NO or selling YES = bearish

    total = bullish_flow + bearish_flow
    if total == 0:
        consensus = "neutral"
        confidence = 0
    elif bullish_flow > bearish_flow:
        consensus = "YES"
        confidence = bullish_flow / total
    else:
        consensus = "NO"
        confidence = bearish_flow / total

    return {
        "has_smart_money_activity": True,
        "large_traders_count": len(set(t["trader"] for t in trades)),
        "total_large_volume": sum(t["amount"] for t in trades),
        "yes_volume": yes_amount,
        "no_volume": no_amount,
        "bullish_flow": bullish_flow,
        "bearish_flow": bearish_flow,
        "consensus": consensus,
        "confidence": round(confidence, 2),
        "pattern": pattern_analysis.get("pattern_name"),
        "smart_money_direction": pattern_analysis.get("smart_money_direction"),
        "insights": pattern_analysis.get("insights", []),
        "top_trades": trades[:5],  # 最重要的 5 笔
    }
