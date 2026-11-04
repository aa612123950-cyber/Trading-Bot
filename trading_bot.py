import os
import telebot
from google import genai
from google.genai import types

# جلب المفاتيح مباشرة من إعدادات السرفر (Environment Variables)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# تحقق من وجود المفاتيح لتفادي الأخطاء
if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("المرجو التأكد من إضافة TELEGRAM_TOKEN و GEMINI_API_KEY في إعدادات البيئة (Environment variables).")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# توجيهات التحليل الفني والاستراتيجيات
TRADING_SYSTEM_INSTRUCTION = """
أنت محلل فني خبير ومحترف في أسواق المال والتداول (Trading Expert).
عندما يطلب منك المستخدم زوج معين وفريم زمني، قم بتحليل السوق بناءً على الاستراتيجيات التالية بتوازن تام:
1. هيكل السوق والاتجاه العام (Market Structure & Trend).
2. مستويات الدعم والمقاومة، ومناطق العرض والطلب (Supply/Demand & S/R).
3. مؤشرات الزخم (RSI / MACD) لرصد التشبعات أو الدايفرجنس.
4. إدارة المخاطر: تحديد وقف خسارة دقيق وأهداف ربحية (TP1, TP2) بنسبة عائد للمخاطرة ممتازة.

قدم النتيجة بالصيغة التالية بدقة واحترافية:
- **الزوج / الأداة**: [اسم الزوج والفريم]
- **نوع الصفقة**: [BUY / SELL]
- **سعر الدخول (Entry)**: [السعر المقترح]
- **وقف الخسارة (Stop Loss)**: [المستوى بدقة]
- **الهدف الأول (TP1)**: [...]
- **الهدف الثاني (TP2)**: [...]
- **التحليل والأسباب**: [شرح مبسط وواضح للاستراتيجيات التي بنيت عليها الصفقة]
"""

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "مرحباً بك، أنا بوت التحليل الفني الذكي 📊\n\n"
        "أعمل على مدار الساعة طوال أيام الأسبوع.\n"
        "أرسل لي الآن اسم الزوج والفريم الزمني (مثال: `EURUSD 1H` أو `BTCUSDT 4H`) وسأقوم بالتحليل فوراً."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def analyze_trade(message):
    user_query = message.text.strip()
    
    bot.reply_to(message, "⏳ جاري فحص الشارت وتطبيق الاستراتيجيات، لحظات...")

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"قم بتحليل وتوفير صفقة تداول بناءً على الطلب التالي: {user_query}",
            config=types.GenerateContentConfig(
                system_instruction=TRADING_SYSTEM_INSTRUCTION,
                temperature=0.2
            )
        )
        
        bot.send_message(message.chat.id, response.text, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء التحليل: {str(e)}")

if __name__ == "__main__":
    print("البوت يعمل الآن وجاهز للاستجابة...")
    bot.infinity_polling()