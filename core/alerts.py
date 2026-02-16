"""
alerts.py
---------
وظيفة هذا الملف: إرسال التنبيهات إلى التليقرام.
"""

import os
import requests
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# الحصول على إعدادات التليقرام
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(message: str):
    """
    إرسال رسالة إلى التليقرام مع تقسيم الرسائل الطويلة تلقائيًا.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        error_msg = "❌ خطأ: لم يتم تعيين TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID في ملف .env"
        print(error_msg)
        return {"error": error_msg}

    try:
        # تقسيم الرسائل الطويلة (حد التليقرام 4096 حرف)
        max_length = 4000  # نستخدم 4000 لترك هامش أمان
        messages = [message[i:i + max_length] for i in range(0, len(message), max_length)]
        
        results = []
        for i, msg_part in enumerate(messages):
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg_part,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, data=payload, timeout=10)
            result = response.json()
            results.append(result)
            
            if not result.get("ok"):
                print(f"❌ فشل إرسال الجزء {i+1}: {result.get('description')}")
                return result
        
        print(f"✅ تم إرسال {len(messages)} جزء إلى التليقرام بنجاح!")
        return {"ok": True, "parts": len(messages)}
        
    except Exception as e:
        error_msg = f"💥 خطأ في إرسال التليقرام: {str(e)}"
        print(error_msg)
        return {"error": error_msg}


def create_compact_message(contracts: list) -> str:
    """
    إنشاء رسالة مختصرة للإرسال السريع.
    التنسيق: الرمز | النوع | Strike | السعر
    """
    if not contracts:
        return "⚠️ لا توجد عقود للعرض"
    
    lines = ["<b>📊 العقود المختارة:</b>"]
    for c in contracts[:10]:  # أول 10 عقود كحد أقصى
        symbol = c.get('underlying_symbol', 'N/A')
        direction = 'CALLTYPE' if c.get('direction') == 'up' else 'PUT'
        strike = c.get('strike', 'N/A')
        price = c.get('ask', 'N/A')
        lines.append(f"{symbol} | {direction} | {strike} | {price}")
    
    return "\n".join(lines)


def send_signal_to_telegram_compact(symbol: str, trend: str, contract: dict):
    """
    إرسال إشارة فردية مختصرة للتليقرام.
    """
    try:
        direction = 'CALLTYPE' if trend == 'up' else 'PUT'
        strike = contract.get('strike', 'N/A')
        ask = contract.get('ask', 'N/A')
        
        message = f"<b>🔔 إشارة تداول</b>\n{symbol} | {direction} | {strike} | {ask}"
        return send_telegram_message(message)
    except Exception as e:
        return {"error": str(e)}


def send_top10_compact(contracts: list):
    """
    إرسال قائمة مختصرة لأفضل 10 عقود.
    """
    try:
        message = create_compact_message(contracts)
        return send_telegram_message(message)
    except Exception as e:
        return {"error": str(e)}


def send_top10_alert(alert_text: str):
    """
    إرسال تنبيه أفضل 10 عقود (النسخة الكاملة).
    """
    header = "🔥 <b>أفضل 10 عقود ذات سيولة عالية</b> 🔥\n\n"
    full_message = header + alert_text
    return send_telegram_message(full_message)