"""
main.py
-------
النقطة الرئيسية لتشغيل المشروع.
يستخدم الدوال من مجلد core/ لضمان الفصل النظيف للمنطق.
"""

import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# استيراد الرموز
from data.symbols_filtered import filtered_symbols as symbols

# استيراد الدوال من core (بدون calculate_iv_rank)
from core.fetcher import get_weekly_and_monthly_expirations, fetch_options_for_expiration
from core.scoring import pick_top_2_options  # ← تم إزالة calculate_iv_rank
from core.alerts import (
    send_telegram_message, 
    send_top10_alert, 
    send_signal_to_telegram_compact, 
    send_top10_compact
)
from core.top10 import get_top_10_across_symbols, build_top10_alert
from core.signal_builder import generate_option_signal_for_symbol
from core.utils import option_tp_sl



# ✅ جسر لواجهة Streamlit (لأنها تتوقع هذه الدالة هنا)
def generate_option_signal(symbol: str, trend: str) -> str:
    """
    دالة متوافقة مع frontend.py.
    تقوم فقط بتمرير المكالمة إلى الدالة الصحيحة في core.
    """
    return generate_option_signal_for_symbol(symbol, trend)


if __name__ == "__main__":
    print("🚀 تشغيل فحص السوق الحقيقي...")

    # ✅ استخدام اتجاه صحيح: "up" أو "down"
    top10 = get_top_10_across_symbols("up")  # أو "down"

    if not top10:
        print("❌ لم يتم العثور على أي عقود مناسبة.")
    else:
        # بناء التنبيه
        alert_text = build_top10_alert(top10)

        # طباعة النتيجة
        print(alert_text)

        # إرسال للتليقرام (اختياري — فعّله بإزالة التعليق)
        # send_top10_alert(alert_text)

    print("✅ اكتمل الفحص.")