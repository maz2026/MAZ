"""
strategies.py
-------------
بناء استراتيجيات خيارات متقدمة تلقائيًا.
"""

from typing import List, Dict, Optional


def find_straddle(symbol: str, contracts: List[Dict]) -> Optional[Dict]:
    """
    البحث عن Straddle مثالي (Call + Put بنفس Strike و Expiration).
    """
    calls = [c for c in contracts if c.get("option_type") == "call"]
    puts = [c for c in contracts if c.get("option_type") == "put"]
    
    # تجميع العقود حسب (Strike, Expiration)
    call_dict = {}
    for c in calls:
        key = (c["strike"], c["expiration_date"])
        call_dict[key] = c
    
    for p in puts:
        key = (p["strike"], p["expiration_date"])
        if key in call_dict:
            call = call_dict[key]
            total_cost = call["ask"] + p["ask"]
            # فلترة حسب التكلفة والسيولة
            if total_cost <= 20 and call["volume"] >= 100 and p["volume"] >= 100:
                return {
                    "strategy": "Straddle",
                    "symbol": symbol,
                    "strike": p["strike"],
                    "expiration": p["expiration_date"],
                    "call": call,
                    "put": p,
                    "total_cost": round(total_cost, 2),
                    "max_loss": round(total_cost, 2),
                    "break_even_up": round(p["strike"] + total_cost, 2),
                    "break_even_down": round(p["strike"] - total_cost, 2)
                }
    return None


def find_strangle(symbol: str, contracts: List[Dict]) -> Optional[Dict]:
    """
    البحث عن Strangle (Call أعلى Strike + Put أقل Strike).
    """
    calls = sorted([c for c in contracts if c.get("option_type") == "call"], key=lambda x: x["strike"])
    puts = sorted([c for c in contracts if c.get("option_type") == "put"], key=lambda x: x["strike"], reverse=True)
    
    if not calls or not puts:
        return None
        
    # نأخذ السعر من أول عقد (أو نحسب متوسط)
    current_price = contracts[0].get("underlying_price", 0.0)
    if current_price == 0.0:
        # fallback: نستخدم متوسط strikes كتقريب
        all_strikes = [c["strike"] for c in contracts if c["strike"] > 0]
        current_price = sum(all_strikes) / len(all_strikes) if all_strikes else 0.0
    
    call = next((c for c in calls if c["strike"] > current_price), None)
    put = next((p for p in puts if p["strike"] < current_price), None)
    
    if call and put and call["expiration_date"] == put["expiration_date"]:
        total_cost = call["ask"] + put["ask"]
        if total_cost <= 15 and call["volume"] >= 80 and put["volume"] >= 80:
            return {
                "strategy": "Strangle",
                "symbol": symbol,
                "call_strike": call["strike"],
                "put_strike": put["strike"],
                "expiration": call["expiration_date"],
                "call": call,
                "put": put,
                "total_cost": round(total_cost, 2),
                "max_loss": round(total_cost, 2),
                "break_even_up": round(call["strike"] + total_cost, 2),
                "break_even_down": round(put["strike"] - total_cost, 2)
            }
    return None


def build_strategy_block(strategy: Dict) -> str:
    """بناء رسالة نصية للاستراتيجية."""
    if strategy["strategy"] == "Straddle":
        return f"""
🎯 استراتيجية: {strategy['strategy']}
- السهم: {strategy['symbol']}
- Strike: {strategy['strike']}
- الانتهاء: {strategy['expiration']}
- التكلفة الكلية: ${strategy['total_cost']}
- نقطة التعادل العليا: ${strategy['break_even_up']}
- نقطة التعادل السفلى: ${strategy['break_even_down']}
- الحد الأقصى للخسارة: ${strategy['max_loss']} (إذا بقي السعر عند Strike)

"""
    elif strategy["strategy"] == "Strangle":
        return f"""
🎯 استراتيجية: {strategy['strategy']}
- السهم: {strategy['symbol']}
- Call Strike: {strategy['call_strike']}
- Put Strike: {strategy['put_strike']}
- الانتهاء: {strategy['expiration']}
- التكلفة الكلية: ${strategy['total_cost']}
- نقطة التعادل العليا: ${strategy['break_even_up']}
- نقطة التعادل السفلى: ${strategy['break_even_down']}
- الحد الأقصى للخسارة: ${strategy['max_loss']}

"""
    return ""