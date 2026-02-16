"""
signal_builder.py
--------------------
بناء إشارات التداول بناءً على عقود خيارات واقعية.
يركز فقط على العقود القريبة من المال (Near-the-Money).
"""

from core.fetcher import get_weekly_and_monthly_expirations, fetch_options_for_expiration
from core.scoring import pick_top_2_options, apply_symbol_filters
from core.utils import option_tp_sl


def build_single_option_block(title: str, contract: dict, direction: str) -> str:
    if not contract:
        return f"{title}\nلا يوجد عقد {direction.upper()} مناسب.\n\n"

    tp, sl = option_tp_sl(contract["ask"])

    return f"""
{title}
- السهم: {contract['underlying_symbol']}
- الاتجاه: {direction.upper()}
- Strike: {contract['strike']}
- Expiration: {contract['expiration_date']}
- Bid/Ask: {contract['bid']} / {contract['ask']}
- Volume: {contract['volume']}
- Open Interest: {contract['open_interest']}
- IV: {contract['implied_volatility']:.4f}

- سعر الدخول: {contract['ask']}
- TP: {tp}
- SL: {sl}

"""


def _filter_contracts_by_trend(contracts, trend, stock_price):
    """فلترة ذكية مع توسع تدريجي."""
    if not contracts or not stock_price:
        return []

    # مستويات التوسع: (call_min, call_max, put_min, put_max)
    tolerances = [
        (0.98, 1.05, 0.95, 1.02),  # ضيق
        (0.95, 1.10, 0.90, 1.05),  # متوسط
        (0.90, 1.15, 0.85, 1.10),  # واسع
    ]

    for call_min_mult, call_max_mult, put_min_mult, put_max_mult in tolerances:
        filtered = []
        for c in contracts:
            ask = c.get("ask", 0)
            bid = c.get("bid", 0)
            strike = c.get("strike")
            volume = c.get("volume", 0)
            option_type = c.get("option_type")

            if strike is None or option_type is None:
                continue

            # شروط أساسية
            if ask <= 0.01 or bid <= 0.01 or volume <= 10:
                continue
            if not (0.5 <= ask <= 20):
                continue

            # فلترة حسب الاتجاه
            if trend == "up" and option_type == "call":
                if stock_price * call_min_mult <= strike <= stock_price * call_max_mult:
                    filtered.append(c)
            elif trend == "down" and option_type == "put":
                if stock_price * put_min_mult <= strike <= stock_price * put_max_mult:
                    filtered.append(c)

        if filtered:
            return filtered

    return []


def generate_option_signal_for_symbol(symbol: str, trend: str) -> str:
    """
    يولد إشارة خيارات لسهم معين بناءً على الاتجاه.
    يركز فقط على العقود القابلة للتداول والقريبة من المال.
    """
    trend = trend.lower().strip()

    if trend in ["up", "long", "bull", "bullish"]:
        direction = "up"
    elif trend in ["down", "short", "bear", "bearish"]:
        direction = "down"
    else:
        return f"❌ اتجاه غير معروف للرمز {symbol}. استخدم 'up' أو 'down'."

    try:
        weekly_exp, monthly_exp = get_weekly_and_monthly_expirations(symbol)

        if not weekly_exp and not monthly_exp:
            return f"❌ لا توجد تواريخ انتهاء متاحة للرمز {symbol}."

        # جلب المؤشرات الفنية
        from core.indicators import get_technical_indicators, check_price_alerts
        indicators = get_technical_indicators(symbol)
        current_price = indicators['price']
        price_alerts = check_price_alerts(symbol, current_price)
        
        # جلب العقود
        weekly_contracts = fetch_options_for_expiration(symbol, weekly_exp) if weekly_exp else []
        monthly_contracts = fetch_options_for_expiration(symbol, monthly_exp) if monthly_exp else []

        # تطبيق الفلاتر المخصصة
        weekly_contracts = apply_symbol_filters(weekly_contracts, symbol, direction)
        monthly_contracts = apply_symbol_filters(monthly_contracts, symbol, direction)

        top_weekly = pick_top_2_options(weekly_contracts, direction)
        top_monthly = pick_top_2_options(monthly_contracts, direction)

        alert = f"""
تنبيه أوبشن — {symbol}
------------------------------------
📊 المؤشرات الفنية:
- السعر الحالي: {current_price}
- RSI (14): {indicators['rsi']}
- MA50: {indicators['ma50']}
- MA200: {indicators['ma200']}
"""

        # إضافة تنبيهات السعر
        if price_alerts:
            alert += f"\n🔔 تنبيهات سعرية: السعر قريب من {', '.join(map(str, price_alerts))}\n"

        alert += "\n"

        # عرض Weeklys مع تحديد أنها أسبوعية
        if weekly_exp:
            for c in top_weekly:
                alert += build_single_option_block(f"أسبوعي (ينتهي {weekly_exp})", c, direction)
        else:
            alert += "أسبوعي: لا توجد عقود أسبوعية متاحة.\n\n"

        # عرض Monthlys
        if monthly_exp:
            for c in top_monthly:
                alert += build_single_option_block(f"شهري (ينتهي {monthly_exp})", c, direction)
        else:
            alert += "شهري: لا توجد عقود شهرية متاحة.\n\n"

        if not top_weekly and not top_monthly:
            alert += "❌ لم يتم العثور على عقود مناسبة بعد الفلترة.\n"

        # === تحليل التقلب الضمني (IV Rank) ===
        best_contract = None
        if top_weekly:
            best_contract = top_weekly[0]
        elif top_monthly:
            best_contract = top_monthly[0]

        iv_analysis = {"iv_rank": "N/A", "signal": "غير متوفر"}
        if best_contract and best_contract.get("implied_volatility"):
            try:
                from core.iv_analyzer import get_iv_analysis
                current_iv = best_contract["implied_volatility"]
                iv_analysis = get_iv_analysis(symbol, current_iv)
            except Exception as e:
                print(f"⚠️ خطأ في تحليل IV: {e}")

        alert += f"""
📈 تحليل التقلب الضمني (IV):
- IV Rank: {iv_analysis['iv_rank']}%
- الإشارة: {iv_analysis['signal']}
"""

        # === اكتشاف الاستراتيجيات المتقدمة ===
        all_contracts = weekly_contracts + monthly_contracts
        try:
            from core.strategies import find_straddle, find_strangle, build_strategy_block
            
            straddle = find_straddle(symbol, all_contracts)
            strangle = find_strangle(symbol, all_contracts)
            
            if straddle or strangle:
                alert += "\n🎯 استراتيجيات متقدمة:\n"
                if straddle:
                    alert += build_strategy_block(straddle)
                if strangle:
                    alert += build_strategy_block(strangle)
        except Exception as e:
            print(f"⚠️ خطأ في اكتشاف الاستراتيجيات: {e}")

        alert += "------------------------------------"
        return alert

    except Exception as e:
        return f"❌ خطأ أثناء معالجة {symbol}: {str(e)}"