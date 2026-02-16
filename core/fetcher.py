"""
fetcher.py
----------
جلب تواريخ انتهاء الخيارات وبيانات العقود من yfinance.
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Optional, Tuple


def get_expirations(symbol: str) -> List[str]:
    """
    يُرجع قائمة بتواريخ انتهاء الخيارات المتاحة للسهم.
    """
    try:
        ticker = yf.Ticker(symbol)
        expirations = ticker.options  # tuple of strings in 'YYYY-MM-DD'
        return list(expirations) if expirations else []
    except Exception as e:
        print(f"❌ خطأ في جلب تواريخ الانتهاء لـ {symbol}: {e}")
        return []


def get_weekly_and_monthly_expirations(symbol: str) -> Tuple[Optional[str], Optional[str]]:
    """
    يُرجع تاريخين:
    - weekly: أقرب انتهاء (خلال 7 أيام)
    - monthly: انتهاء يوم الجمعة الثالث (أو الرابع) من الشهر
    """
    expirations = get_expirations(symbol)
    if not expirations:
        return None, None

    try:
        today = datetime.today().date()
        dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in expirations]
        dates.sort()
        
        # البحث عن Weekly (ضمن 7 أيام)
        weekly = None
        for d in dates:
            days_diff = (d - today).days
            if 0 <= days_diff <= 7:
                weekly = d.strftime("%Y-%m-%d")
                break
        
        # البحث عن Monthly (الجمعة الثالثة أو الرابعة)
        monthly = None
        for d in dates:
            if d.weekday() == 4:  # الجمعة
                # التحقق إذا كانت الجمعة الثالثة أو الرابعة من الشهر
                first_day = d.replace(day=1)
                # حساب رقم الأسبوع في الشهر
                week_number = (d.day - 1) // 7 + 1
                if week_number in [3, 4]:
                    monthly = d.strftime("%Y-%m-%d")
                    break
        
        return weekly, monthly
    except Exception as e:
        print(f"❌ خطأ في تصنيف التواريخ لـ {symbol}: {e}")
        return None, None


def fetch_options_for_expiration(symbol: str, expiration: str) -> list:
    """
    جلب جميع عقود Call و Put لتاريخ انتهاء معين.
    يُضمن أن كل عقد يحتوي على السعر الحالي للسهم (underlying_price).
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # جلب السعر الحالي بدقة (آخر سعر تداول)
        hist = ticker.history(period="1d")
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
        else:
            # إذا فشل، نحاول period="5d"
            hist = ticker.history(period="5d")
            current_price = hist['Close'].iloc[-1] if not hist.empty else 0.0

        opt_chain = ticker.option_chain(expiration)
        calls = opt_chain.calls
        puts = opt_chain.puts

        contracts = []
        
        # معالجة عقود Call
        for _, row in calls.iterrows():
            strike = row.get('strike', 0)
            bid = row.get('bid', 0)
            ask = row.get('ask', 0)
            volume = row.get('volume', 0)
            oi = row.get('openInterest', 0)
            iv = row.get('impliedVolatility', 0.0)

            contracts.append({
                "underlying_symbol": symbol,
                "option_type": "call",
                "strike": strike,
                "expiration_date": expiration,
                "bid": bid,
                "ask": ask,
                "volume": volume,
                "open_interest": oi,
                "implied_volatility": iv,
                "underlying_price": current_price  # ← السعر الحقيقي الآن!
            })
        
        # معالجة عقود Put
        for _, row in puts.iterrows():
            strike = row.get('strike', 0)
            bid = row.get('bid', 0)
            ask = row.get('ask', 0)
            volume = row.get('volume', 0)
            oi = row.get('openInterest', 0)
            iv = row.get('impliedVolatility', 0.0)

            contracts.append({
                "underlying_symbol": symbol,
                "option_type": "put",
                "strike": strike,
                "expiration_date": expiration,
                "bid": bid,
                "ask": ask,
                "volume": volume,
                "open_interest": oi,
                "implied_volatility": iv,
                "underlying_price": current_price  # ← السعر الحقيقي الآن!
            })
            
        return contracts
    except Exception as e:
        print(f"❌ خطأ في جلب خيارات {symbol} بتاريخ {expiration}: {e}")
        return []