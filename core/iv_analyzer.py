"""
iv_analyzer.py
--------------
تحليل التقلب الضمني (Implied Volatility) وتاريخه.
"""

import yfinance as yf
import numpy as np
from datetime import datetime, timedelta


def get_historical_iv(symbol: str, days: int = 365) -> list:
    """
    جلب تاريخ التقلب الضمني للسهم.
    ملاحظة: yfinance لا يوفر IV مباشرة، لذا نستخدم تقريبًا عبر خيارات الماضي.
    """
    try:
        ticker = yf.Ticker(symbol)
        # نحاول جلب خيارات لأقرب تاريخ متاح
        expirations = ticker.options
        if not expirations:
            return []
        
        iv_history = []
        today = datetime.today().date()
        cutoff_date = today - timedelta(days=days)
        
        # نأخذ أول 3 تواريخ انتهاء كعينة
        for exp in expirations[:3]:
            try:
                opt = ticker.option_chain(exp)
                calls = opt.calls
                puts = opt.puts
                
                # جمع IV من العقود ذات السيولة
                for df in [calls, puts]:
                    if 'impliedVolatility' in df.columns and 'volume' in df.columns:
                        liquid = df[df['volume'] > 100]
                        if not liquid.empty:
                            avg_iv = liquid['impliedVolatility'].mean()
                            if not np.isnan(avg_iv):
                                iv_history.append(float(avg_iv))
            except:
                continue
        
        return iv_history
    except Exception as e:
        print(f"⚠️ خطأ في جلب IV التاريخي لـ {symbol}: {e}")
        return []


def calculate_iv_rank(current_iv: float, iv_history: list) -> float:
    """
    حساب IV Rank.
    IV Rank = (عدد القيم في التاريخ < IV الحالي) / إجمالي عدد القيم
    """
    if not iv_history or current_iv is None or np.isnan(current_iv):
        return 0.5
    
    count_lower = sum(1 for iv in iv_history if iv < current_iv)
    rank = count_lower / len(iv_history)
    return round(rank * 100, 1)  # بنسبة مئوية


def get_iv_analysis(symbol: str, current_iv: float) -> dict:
    """تحليل IV مع التنبيهات"""
    iv_history = get_historical_iv(symbol)
    iv_rank = calculate_iv_rank(current_iv, iv_history)
    
    # تحديد نوع الفرصة
    if iv_rank >= 70:
        signal = "🔴 IV مرتفع — فرصة لبيع الخيارات"
    elif iv_rank <= 30:
        signal = "🟢 IV منخفض — فرصة لشراء الخيارات"
    else:
        signal = "⚪ IV طبيعي — لا إشارة واضحة"
    
    return {
        "iv_rank": iv_rank,
        "signal": signal,
        "history_count": len(iv_history)
    }