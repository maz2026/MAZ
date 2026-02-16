"""
indicators.py
-------------
حساب المؤشرات الفنية الأساسية باستخدام yfinance.
"""

import yfinance as yf
import pandas as pd


def calculate_rsi(data: pd.Series, window: int = 14) -> float:
    """حساب مؤشر RSI"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else 50.0


def calculate_ma(data: pd.Series, window: int) -> float:
    """حساب المتوسط المتحرك"""
    ma = data.rolling(window=window).mean()
    return ma.iloc[-1] if not ma.empty else 0.0


def get_technical_indicators(symbol: str) -> dict:
    """
    جلب المؤشرات الفنية للسهم.
    Returns:
        dict: {'rsi': float, 'ma50': float, 'ma200': float, 'price': float}
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="6mo")  # نحتاج 6 أشهر لحساب MA200
        
        if hist.empty or len(hist) < 50:
            return {"rsi": 50.0, "ma50": 0.0, "ma200": 0.0, "price": 0.0}
        
        close_prices = hist['Close']
        current_price = close_prices.iloc[-1]
        
        rsi = calculate_rsi(close_prices)
        ma50 = calculate_ma(close_prices, 50)
        ma200 = calculate_ma(close_prices, 200)
        
        return {
            "rsi": round(rsi, 2),
            "ma50": round(ma50, 2),
            "ma200": round(ma200, 2),
            "price": round(current_price, 2)
        }
    except Exception as e:
        print(f"❌ خطأ في جلب المؤشرات لـ {symbol}: {e}")
        return {"rsi": 50.0, "ma50": 0.0, "ma200": 0.0, "price": 0.0}


def check_price_alerts(symbol: str, current_price: float) -> list:
    """
    التحقق من مستويات التنبيه السعري.
    Returns:
        list: المستويات القريبة (ضمن ±1%)
    """
    try:
        from data.price_levels import price_levels
        levels = price_levels.get(symbol, [])
        alerts = []
        
        for level in levels:
            # التحقق إذا كان السعر الحالي قريب من المستوى (ضمن ±1%)
            if abs(current_price - level) / level <= 0.01:
                alerts.append(level)
                
        return alerts
    except Exception as e:
        print(f"❌ خطأ في التحقق من التنبيهات لـ {symbol}: {e}")
        return []