from data.symbols_filtered import filtered_symbols as symbols
from core.fetcher import (
    get_weekly_and_monthly_expirations,
    fetch_options_for_expiration
    # ← تم إزالة get_underlying_price
)
from core.scoring import pick_top_2_options
from core.utils import option_tp_sl


def process_symbol(symbol: str, trend: str):
    """
    يعالج سهم واحد ويعيد أفضل عقدين بناءً على الاتجاه.
    يركز فقط على العقود القريبة من المال (Near-the-Money).
    """
    try:
        print(f"\n🔍 Processing {symbol} ...")

        # 1) جلب Weekly + Monthly expirations
        weekly_exp, monthly_exp = get_weekly_and_monthly_expirations(symbol)

        # 2) جلب العقود
        weekly_contracts = fetch_options_for_expiration(symbol, weekly_exp) if weekly_exp else []
        monthly_contracts = fetch_options_for_expiration(symbol, monthly_exp) if monthly_exp else []

        print(f"Weekly contracts: {len(weekly_contracts)}")
        print(f"Monthly contracts: {len(monthly_contracts)}")

        all_contracts = weekly_contracts + monthly_contracts
        print(f"Total before filtering: {len(all_contracts)}")

        if not all_contracts:
            print("❌ No contracts found")
            return []

        # 3) ✅ استخراج السعر الحالي من أول عقد (تمت إضافته في fetch_options_for_expiration)
        stock_price = all_contracts[0].get("underlying_price", 0.0)
        if stock_price <= 0:
            print("❌ Failed to fetch underlying price from contracts")
            return []

        # 4) ✅ فلترة ذكية للصفقات الحقيقية (مع توسيع تدريجي)
        filtered = []
        tolerances = [
            (0.98, 1.05, 0.95, 1.02),  # ±2% للـ Call، ±5% للـ Put (ضيق)
            (0.95, 1.10, 0.90, 1.05),  # ±5% للـ Call، ±10% للـ Put (متوسط)
            (0.90, 1.15, 0.85, 1.10),  # ±10% للـ Call، ±15% للـ Put (واسع)
        ]

        for call_min_mult, call_max_mult, put_min_mult, put_max_mult in tolerances:
            temp_filtered = []
            for c in all_contracts:
                ask = c.get("ask", 0)
                bid = c.get("bid", 0)
                strike = c.get("strike")
                iv = c.get("implied_volatility")
                volume = c.get("volume", 0)
                option_type = c.get("option_type")

                if strike is None or iv is None or option_type is None:
                    continue

                # ✅ استبعد العقود غير القابلة للتداول
                if ask <= 0.01 or bid <= 0.01 or volume <= 10:
                    continue

                # ✅ نطاق سعري واقعي للتداول اليومي
                if not (0.5 <= ask <= 20):
                    continue

                # ✅ شرط المنطق الحقيقي للصفقات (مع التوسع التدريجي)
                if trend == "up":
                    if option_type != "call":
                        continue
                    if not (stock_price * call_min_mult <= strike <= stock_price * call_max_mult):
                        continue
                elif trend == "down":
                    if option_type != "put":
                        continue
                    if not (stock_price * put_min_mult <= strike <= stock_price * put_max_mult):
                        continue

                temp_filtered.append(c)

            if temp_filtered:
                filtered = temp_filtered
                break  # نستخدم أول مجموعة ناجحة

        print(f"After filtering: {len(filtered)}")

        if not filtered:
            print("❌ No contracts after filtering")
            return []

        # 5) حساب IV Rank
        for c in filtered:
            c["iv_rank"] = calculate_iv_rank(filtered)

        # 6) اختيار أفضل عقدين
        top2 = pick_top_2_options(filtered, trend)
        print(f"Top2 selected: {len(top2)}")

        # 7) إضافة TP/SL
        for c in top2:
            ask = c.get("ask", 0)
            tp, sl = option_tp_sl(ask)
            c["tp"] = tp
            c["sl"] = sl
            c["direction"] = trend

        return top2

    except Exception as e:
        print(f"⚠️ Error in {symbol}: {e}")
        return []


def get_top_10_across_symbols(trend: str):
    """
    يجمع أفضل 10 عقود من جميع الأسهم.
    """
    all_results = []

    for symbol in symbols:
        top2 = process_symbol(symbol, trend)
        if top2:
            all_results.extend(top2)

    print(f"\n📊 Total collected contracts: {len(all_results)}")

    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)

    return all_results[:10]


def build_top10_alert(contracts):
    """
    يبني نص تنبيه Top 10 لإرساله إلى التليقرام.
    """
    if not contracts:
        return "⚠️ لا توجد عقود مناسبة حالياً."

    lines = ["🔥 أفضل 10 عقود حسب الفلترة:\n"]

    for c in contracts:
        line = (
            f"📌 {c.get('underlying_symbol')} | {c.get('direction').upper()}\n"
            f"Strike: {c.get('strike')} | Exp: {c.get('expiration_date')}\n"
            f"Bid: {c.get('bid')} | Ask: {c.get('ask')}\n"
            f"IV: {round(c.get('implied_volatility', 0), 4)} | Score: {round(c.get('score', 0), 2)}\n"
            f"TP: {c.get('tp')} | SL: {c.get('sl')}\n"
            "-----------------------------\n"
        )
        lines.append(line)

    return "".join(lines)