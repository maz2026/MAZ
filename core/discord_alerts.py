"""
discord_alerts.py
-----------------
إرسال التنبيهات إلى قنوات Discord عبر Webhooks.
"""

import os
import requests
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# الحصول على Webhook URL من .env
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def send_discord_message_simple(message: str) -> dict:
    """
    إرسال رسالة بسيطة (بدون Embed) إلى Discord.
    """
    if not DISCORD_WEBHOOK_URL:
        error_msg = "❌ خطأ: لم يتم تعيين DISCORD_WEBHOOK_URL في ملف .env"
        print(error_msg)
        return {"error": error_msg}

    try:
        payload = {"content": message[:2000]}  # حد Discord للـ content
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        
        if response.status_code in [200, 204]:
            print("✅ تم إرسال الرسالة إلى Discord بنجاح!")
            return {"ok": True}
        else:
            error_desc = response.text
            print(f"❌ فشل إرسال Discord: {error_desc}")
            return {"error": error_desc}
            
    except Exception as e:
        error_msg = f"💥 خطأ في إرسال Discord: {str(e)}"
        print(error_msg)
        return {"error": error_msg}


def send_discord_message(message: str, title: str = "Option Scanner Alert") -> dict:
    """
    إرسال رسالة إلى Discord عبر Webhook (بنمط Embed).
    """
    if not DISCORD_WEBHOOK_URL:
        error_msg = "❌ خطأ: لم يتم تعيين DISCORD_WEBHOOK_URL في ملف .env"
        print(error_msg)
        return {"error": error_msg}

    try:
        # تنسيق الرسالة كـ Embed
        embed = {
            "title": title,
            "description": message[:4000],  # حد Discord للـ Embed
            "color": 0x4CAF50,  # أخضر
            "footer": {"text": "Option Scanner Pro"}
        }
        
        payload = {"embeds": [embed]}
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        result = response.json() if response.status_code != 204 else {"ok": True}
        
        if response.status_code in [200, 204]:
            print("✅ تم إرسال الرسالة إلى Discord بنجاح!")
            return {"ok": True}
        else:
            error_desc = result.get("message", "Unknown error")
            print(f"❌ فشل إرسال Discord: {error_desc}")
            return {"error": error_desc}
            
    except Exception as e:
        error_msg = f"💥 خطأ في إرسال Discord: {str(e)}"
        print(error_msg)
        return {"error": error_msg}


def send_discord_compact(symbol: str, direction: str, strike: float, ask: float):
    """إرسال رسالة مختصرة إلى Discord."""
    message = f"**{symbol}** | {direction.upper()} | {strike} | {ask}"
    return send_discord_message_simple(message)


def send_discord_top10(alert_text: str):
    """إرسال أفضل 10 عقود إلى Discord."""
    return send_discord_message(alert_text[:4000], "🔥 أفضل 10 عقود ذات سيولة عالية")