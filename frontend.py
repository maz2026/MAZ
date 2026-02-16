import streamlit as st
from main import generate_option_signal
import re

# === دعم PWA (Progressive Web App) ===
st.markdown("""
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#4CAF50">
""", unsafe_allow_html=True)

# === تحسين عرض الجوال ===
st.markdown("""
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
""", unsafe_allow_html=True)

# === الإعدادات الأساسية ===
st.set_page_config(
    page_title="Option Scanner Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# === أنماط CSS مخصصة ===
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .result-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #f44336;
    }
    .success-box {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        font-size: 1.1rem;
        border-radius: 8px;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .top10-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 2rem 0;
    }
    
    /* تحسينات الجوال */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        .stButton>button {
            padding: 0.75rem 1rem;
            font-size: 1rem;
        }
        .stColumns {
            flex-direction: column !important;
        }
    }
</style>
""", unsafe_allow_html=True)


def extract_contract_from_result(result_text: str, symbol: str, trend: str):
    """استخراج معلومات العقد من نص النتيجة (مُحسّن للتنسيق الحالي)"""
    try:
        contract_info = {
            'underlying_symbol': symbol,
            'direction': 'up' if trend == 'up' else 'down',
            'strike': 0,
            'ask': 0
        }
        
        # استخراج Strike
        strike_match = re.search(r'Strike\s*:\s*([0-9.]+)', result_text)
        if strike_match:
            contract_info['strike'] = float(strike_match.group(1))
        
        # استخراج Ask من Bid/Ask أو سعر الدخول
        ask_match = re.search(r'Bid/Ask\s*:\s*[0-9.]+\s*/\s*([0-9.]+)', result_text)
        if not ask_match:
            ask_match = re.search(r'سعر الدخول\s*:\s*([0-9.]+)', result_text)
            
        if ask_match:
            contract_info['ask'] = float(ask_match.group(1))
        
        return contract_info
    except Exception as e:
        print(f"❌ خطأ في استخراج العقد: {e}")
        return None


# === العنوان الرئيسي ===
st.markdown('<div class="main-header">📊 Option Scanner Pro</div>', unsafe_allow_html=True)

# === شرح موجز ===
st.info("🔍 أدخل رمز السهم (مثل AAPL أو QQQ) واختر الاتجاه للحصول على أفضل عقود الخيارات")

# === إدخال البيانات ===
col1, col2 = st.columns([2, 1])

with col1:
    symbol = st.text_input("رمز السهم", value="AAPL", max_chars=10, help="مثال: AAPL, TSLA, QQQ")

with col2:
    trend = st.selectbox(
        "الاتجاه",
        ["up (صاعد - Call)", "down (هابط - Put)"],
        index=0
    )

# === زر التوليد ===
if st.button("🚀 توليد الإشارة", key="generate_btn"):
    if not symbol.strip():
        st.error("❌ يرجى إدخال رمز السهم")
    else:
        with st.spinner("⏳ جاري جلب البيانات وتحليلها..."):
            try:
                # استخراج القيمة الصحيحة
                trend_value = "up" if "up" in trend else "down"
                symbol_clean = symbol.strip().upper()
                
                # توليد الإشارة
                result = generate_option_signal(symbol_clean, trend_value)
                
                # === عرض النتيجة ===
                if "لا توجد عقود مناسبة" in result or "❌" in result:
                    st.markdown('<div class="error-box">' + result + '</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="success-box"><b>✅ تم العثور على عقود!</b></div>', unsafe_allow_html=True)
                    st.markdown('<div class="result-box">' + result + '</div>', unsafe_allow_html=True)
                    
                    # أزرار الحفظ والإرسال
                    col_save, col_telegram_full, col_telegram_compact, col_discord_full, col_discord_compact = st.columns(5)
                    
                    with col_save:
                        st.download_button(
                            label="💾 حفظ كـ TXT",
                            data=result,
                            file_name=f"option_signal_{symbol_clean}_{trend_value}.txt",
                            mime="text/plain"
                        )
                    
                    with col_telegram_full:
                        if st.button("📲 إرسال كامل", key="telegram_full_btn"):
                            try:
                                from core.alerts import send_telegram_message
                                full_msg = f"🔔 <b>إشارة تداول لـ {symbol_clean}</b>\n\n{result}"
                                result_send = send_telegram_message(full_msg)
                                if result_send.get("ok"):
                                    st.success("✅ تم الإرسال الكامل!")
                                else:
                                    st.error(f"❌ فشل الإرسال: {result_send.get('error', 'خطأ غير معروف')}")
                            except Exception as e:
                                st.error(f"❌ خطأ في الإرسال: {str(e)}")
                    
                    with col_telegram_compact:
                        if st.button("📱 إرسال مختصر", key="telegram_compact_btn"):
                            try:
                                contract_data = extract_contract_from_result(result, symbol_clean, trend_value)
                                print(f"📊 بيانات العقد المستخرجة: {contract_data}")  # ← للتحقق
                                if contract_data and contract_data['strike'] > 0 and contract_data['ask'] > 0:
                                    from core.alerts import send_signal_to_telegram_compact
                                    result_send = send_signal_to_telegram_compact(
                                        symbol_clean, 
                                        trend_value, 
                                        contract_data
                                    )
                                    if result_send.get("ok"):
                                        st.success("✅ تم الإرسال المختصر!")
                                    else:
                                        st.error(f"❌ فشل الإرسال: {result_send.get('error', 'خطأ غير معروف')}")
                                else:
                                    st.error("❌ لا يمكن استخراج بيانات العقد للإرسال")
                            except Exception as e:
                                st.error(f"❌ خطأ في الإرسال: {str(e)}")
                    
                    with col_discord_full:
                        if st.button("💬 Discord كامل", key="discord_full_btn"):
                            try:
                                from core.discord_alerts import send_discord_message
                                full_msg = f"🔔 **إشارة تداول لـ {symbol_clean}**\n\n{result}"
                                result_send = send_discord_message(full_msg)
                                if result_send.get("ok"):
                                    st.success("✅ تم الإرسال إلى Discord!")
                                else:
                                    st.error(f"❌ فشل الإرسال: {result_send.get('error', 'خطأ غير معروف')}")
                            except Exception as e:
                                st.error(f"❌ خطأ في الإرسال: {str(e)}")
                    
                    with col_discord_compact:
                        if st.button("📱 Discord مختصر", key="discord_compact_btn"):
                            try:
                                contract_data = extract_contract_from_result(result, symbol_clean, trend_value)
                                if contract_data and contract_data['strike'] > 0 and contract_data['ask'] > 0:
                                    from core.discord_alerts import send_discord_compact
                                    direction = "CALLTYPE" if trend_value == "up" else "PUT"
                                    result_send = send_discord_compact(
                                        symbol_clean,
                                        direction,
                                        contract_data['strike'],
                                        contract_data['ask']
                                    )
                                    if result_send.get("ok"):
                                        st.success("✅ تم الإرسال المختصر إلى Discord!")
                                    else:
                                        st.error(f"❌ فشل الإرسال: {result_send.get('error', 'خطأ غير معروف')}")
                                else:
                                    st.error("❌ لا يمكن استخراج بيانات العقد")
                            except Exception as e:
                                st.error(f"❌ خطأ في الإرسال: {str(e)}")
                    
            except Exception as e:
                error_msg = f"❌ حدث خطأ أثناء المعالجة: {str(e)}"
                st.markdown(f'<div class="error-box">{error_msg}</div>', unsafe_allow_html=True)

# === قسم أفضل 10 عقود ===
st.markdown("---")
st.markdown('<div class="top10-section"><h3>🔥 أفضل 10 عقود ذات سيولة عالية</h3><p>تحديث فوري لأفضل الفرص التداولية اليوم</p></div>', unsafe_allow_html=True)

if st.button("🔄 تحديث قائمة أفضل 10 عقود", key="top10_btn"):
    with st.spinner("⏳ جاري جلب أفضل العقود ذات السيولة العالية..."):
        try:
            from main import get_top_10_across_symbols, build_top10_alert
            
            # جلب أفضل 10 عقود (للصعود والهبوط)
            top_calls = get_top_10_across_symbols("up")
            top_puts = get_top_10_across_symbols("down")
            
            all_top = top_calls + top_puts
            all_top.sort(key=lambda x: x.get("score", 0), reverse=True)
            top10_final = all_top[:10]
            
            if top10_final:
                # عرض كجدول احترافي
                st.subheader("🏆 أفضل 10 عقود اليوم")
                df_data = []
                for c in top10_final:
                    df_data.append({
                        "السهم": c.get("underlying_symbol"),
                        "النوع": "CALLTYPE" if c.get("direction") == "up" else "PUT",
                        "Strike": c.get("strike"),
                        "الانتهاء": c.get("expiration_date"),
                        "السعر": c.get("ask"),
                        "الحجم": c.get("volume"),
                        "OI": c.get("open_interest"),
                        "النتيجة": round(c.get("score", 0), 2)
                    })
                
                import pandas as pd
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, height=400)
                
                # أزرار الحفظ والإرسال
                alert_text = build_top10_alert(top10_final)
                col_save, col_telegram_full, col_telegram_compact, col_discord_full, col_discord_compact = st.columns(5)
                
                with col_save:
                    st.download_button(
                        "💾 حفظ القائمة كـ TXT",
                        alert_text,
                        "top10_contracts.txt",
                        "text/plain"
                    )
                
                with col_telegram_full:
                    if st.button("📲 إرسال كامل", key="telegram_top10_full_btn"):
                        try:
                            from core.alerts import send_telegram_message
                            full_message = "🔥 <b>أفضل 10 عقود ذات سيولة عالية</b> 🔥\n\n" + alert_text
                            result = send_telegram_message(full_message)
                            if result.get("ok"):
                                st.success("✅ تم الإرسال الكامل!")
                            else:
                                st.error(f"❌ فشل الإرسال: {result.get('error', 'خطأ غير معروف')}")
                        except Exception as e:
                            st.error(f"❌ خطأ في الإرسال: {str(e)}")
                
                with col_telegram_compact:
                    if st.button("📱 إرسال مختصر", key="telegram_top10_compact_btn"):
                        try:
                            from core.alerts import send_top10_compact
                            result = send_top10_compact(top10_final)
                            if result.get("ok"):
                                st.success("✅ تم الإرسال المختصر!")
                            else:
                                st.error(f"❌ فشل الإرسال: {result.get('error', 'خطأ غير معروف')}")
                        except Exception as e:
                            st.error(f"❌ خطأ في الإرسال: {str(e)}")
                
                with col_discord_full:
                    if st.button("💬 Discord كامل", key="discord_top10_full_btn"):
                        try:
                            from core.discord_alerts import send_discord_top10
                            result = send_discord_top10(alert_text)
                            if result.get("ok"):
                                st.success("✅ تم الإرسال إلى Discord!")
                            else:
                                st.error(f"❌ فشل الإرسال: {result.get('error', 'خطأ غير معروف')}")
                        except Exception as e:
                            st.error(f"❌ خطأ في الإرسال: {str(e)}")
                
                with col_discord_compact:
                    if st.button("📱 Discord مختصر", key="discord_top10_compact_btn"):
                        try:
                            from core.discord_alerts import send_discord_compact
                            # لإرسال مختصر لأفضل عقد فقط
                            if top10_final:
                                best = top10_final[0]
                                direction = "CALLTYPE" if best.get("direction") == "up" else "PUT"
                                result = send_discord_compact(
                                    best.get("underlying_symbol"),
                                    direction,
                                    best.get("strike"),
                                    best.get("ask")
                                )
                                if result.get("ok"):
                                    st.success("✅ تم الإرسال المختصر إلى Discord!")
                                else:
                                    st.error(f"❌ فشل الإرسال: {result.get('error', 'خطأ غير معروف')}")
                            else:
                                st.error("❌ لا توجد عقود للإرسال")
                        except Exception as e:
                            st.error(f"❌ خطأ في الإرسال: {str(e)}")
            else:
                st.warning("⚠️ لم يتم العثور على عقود سائلة كافية")
                
        except Exception as e:
            st.error(f"❌ خطأ في جلب أفضل 10 عقود: {str(e)}")

# === زر اختبار اتصال التليقرام ===
st.markdown("---")
st.subheader("🧪 تشخيص مشكلة التليقرام")

if st.button("🔍 اختبار اتصال التليقرام من Streamlit", key="test_telegram_btn"):
    try:
        import requests
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        st.write(f"🔍 التوكن: {token[:10]}..." if token else "❌ التوكن غير موجود")
        st.write(f"🔍 Chat ID: {chat_id}" if chat_id else "❌ Chat ID غير موجود")
        
        if not token or not chat_id:
            st.error("❌ التوكن أو Chat ID غير موجود في ملف .env")
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"  # ← إصلاح المسافة الزائدة
            response = requests.post(
                url, 
                data={"chat_id": chat_id, "text": "✅ اختبار اتصال من Streamlit!"}
            )
            response_json = response.json()
            st.write("📡 استجابة API:", response_json)
            
            if response_json.get("ok"):
                st.success("✅ الاتصال يعمل من Streamlit!")
            else:
                st.error(f"❌ فشل الاتصال: {response_json.get('description', 'خطأ غير معروف')}")
                
    except Exception as e:
        st.error(f"💥 خطأ في الاتصال: {str(e)}")
        st.code(str(e))

# === قسم المساعدة ===
with st.expander("ℹ️ كيفية الاستخدام"):
    st.markdown("""
    ### 📝 التعليمات:
    1. **أدخل رمز السهم** (مثل AAPL, NVDA, QQQ)
    2. **اختر الاتجاه**:
       - **up**: للبحث عن عقود Call (صعود)
       - **down**: للبحث عن عقود Put (هبوط)
    3. **اضغط "توليد الإشارة"**
    
    ### 📊 المؤشرات الفنية:
    - **RSI < 30**: ذروة بيع (فرصة شراء)
    - **RSI > 70**: ذروة شراء (فرصة بيع)
    - **السعر فوق MA50 وMA200**: اتجاه صاعد
    - **السعر تحت MA50 وMA200**: اتجاه هابط
    
    ### 🔔 التنبيهات السعرية:
    - النظام يتحقق من مستويات السعر المحددة مسبقًا
    - يُظهر تنبيه عندما يكون السعر قريبًا (±1%) من أي مستوى
    
    ### ⚠️ ملاحظات مهمة:
    - يعمل أفضل خلال ساعات التداول (9:30 صباحًا - 4:00 مساءً بتوقيت نيويورك)
    - قد لا تظهر نتائج خارج ساعات التداول
    - العقود المعروضة تكون قريبة من سعر السهم الحالي
    
    ### 🔥 ميزات الإرسال:
    - **التليقرام**: 📲 كامل / 📱 مختصر
    - **Discord**: 💬 كامل / 📱 مختصر
    - **الإرسال المختصر**: (الرمز | النوع | Strike | السعر) - مثالي للهواتف!
    
    ### 🧪 تشخيص المشاكل:
    - استخدم زر "اختبار اتصال التليقرام" لرؤية السبب الحقيقي للمشكلة
    """)