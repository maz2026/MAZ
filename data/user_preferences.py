"""
user_preferences.py
------------------
تفضيلات المستخدم الشخصية.
يمكن تعديلها يدويًا أو لاحقًا عبر واجهة.
"""

user_settings = {
    "favorite_symbols": ["QQQ", "SPY", "AAPL", "NVDA"],
    "symbol_filters": {
        "QQQ": {
            "rsi_buy_threshold": 40,      # شراء عندما RSI < 40
            "rsi_sell_threshold": 60,     # بيع عندما RSI > 60
            "min_volume": 500,
            "min_oi": 2000
        },
        "SPY": {
            "rsi_buy_threshold": 35,
            "rsi_sell_threshold": 65,
            "min_volume": 1000,
            "min_oi": 5000
        },
        "default": {
            "rsi_buy_threshold": 30,
            "rsi_sell_threshold": 70,
            "min_volume": 300,
            "min_oi": 1000
        }
    }
}