"""
scoring.py
----------
تقييم العقود بناءً على السيولة، السبريد، والتقلب الضمني.
"""

from typing import List, Dict, Any


def _score_option(c):
    bid = c.get("bid", 0)
    ask = c.get("ask", 0)
    volume = c.get("volume", 0)
    oi = c.get("open_interest", 0)
    iv = c.get("implied_volatility", 0)
    expiration = c.get("expiration_date", "")

    spread = ((ask - bid) / bid * 100) if bid > 0.01 else 999

    # حساب الأيام حتى الانتهاء
    try:
        from datetime import datetime
        exp_date = datetime.strptime(expiration, "%Y-%m-%d").date()
        today = datetime.today().date()
        days_to_exp = (exp_date - today).days
    except:
        days_to_exp = 30

    # تعديل سيولة بناءً على القرب من الانتهاء
    liquidity_bonus = 20 if days_to_exp <= 7 else 0

    liquidity_score = (
        (50 if volume >= 300 else 30 if volume >= 100 else 10) +
        (50 if oi >= 1000 else 30 if oi >= 500 else 10) +
        liquidity_bonus  # مكافأة للعقود الأسبوعية
    )

    spread_score = max(0, 100 - spread)
    iv_score = max(0, 100 - abs(iv - 0.40) * 100)

    total = liquidity_score * 0.5 + spread_score * 0.3 + iv_score * 0.2
    return total


def pick_top_2_options(contracts: List[Dict[str, Any]], direction: str) -> List[Dict[str, Any]]:
    """
    يختار أفضل عقدين بناءً على التقييم.
    """
    if not contracts:
        return []

    scored = []
    for c in contracts:
        underlying_price = c.get("underlying_price", 0)
        strike = c.get("strike", 0)

        if direction == "up":
            if strike < underlying_price * 0.95 or strike > underlying_price * 1.15:
                continue
        else:  # down
            if strike < underlying_price * 0.85 or strike > underlying_price * 1.05:
                continue

        score = _score_option(c)
        c["score"] = score
        scored.append(c)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:2]


def get_symbol_filter(symbol: str) -> dict:
    """الحصول على إعدادات الفلترة الخاصة بالسهم"""
    try:
        from data.user_preferences import user_settings
        symbol_filters = user_settings.get("symbol_filters", {})
        return symbol_filters.get(symbol, symbol_filters.get("default", {}))
    except Exception as e:
        print(f"⚠️ خطأ في تحميل إعدادات {symbol}: {e}")
        return {
            "rsi_buy_threshold": 30,
            "rsi_sell_threshold": 70,
            "min_volume": 300,
            "min_oi": 1000
        }


def apply_symbol_filters(contracts: list, symbol: str, trend: str) -> list:
    """
    تطبيق الفلاتر المخصصة على العقود.
    """
    try:
        filters = get_symbol_filter(symbol)
        min_volume = filters.get("min_volume", 300)
        min_oi = filters.get("min_oi", 1000)
        
        filtered = []
        for c in contracts:
            if c.get("volume", 0) >= min_volume and c.get("open_interest", 0) >= min_oi:
                filtered.append(c)
                
        return filtered
    except Exception as e:
        print(f"⚠️ خطأ في تطبيق الفلاتر: {e}")
        return contracts