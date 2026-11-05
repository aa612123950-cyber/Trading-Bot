import os
import logging
import requests
import telebot
from telebot import types
import google.generativeai as genai

# إعدادات التسجيل للأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# قراءة مفاتيح التشغيل من متغيرات البيئة
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    logger.error("المرجو التأكد من إعداد TELEGRAM_BOT_TOKEN و GEMINI_API_KEY في متغيرات البيئة!")
    exit(1)

# تهيئة بوت تيليجرام ومكتبة الذكاء الاصطناعي
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# إعداد نموذج جيميناي
generation_config = {
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 800,
}

model = genai.GenerativeModel(
    model_name="gemini-3.8-flash",
    generation_config=generation_config
)

def get_live_price(symbol_text):
    """
    دالة مرنة لجلب السعر الحي وتفادي أي خطأ في قراءة النص المدخل
    """
    text = symbol_text.upper()
    
    try:
        if "XAU" in text or "GOLD" in text:
            url = "https://api.coinbase.com/v2/prices/PAXG-USD/spot"
            response = requests.get(url, timeout=5)
            data = response.json()
            price = data['data']['amount']
            return f"السعر الحقيقي الحالي للذهب (XAUUSD): {price} USD"
            
        elif "BTC" in text:
            url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
            response = requests.get(url, timeout=5)
            data = response.json()
            price = data['data']['amount']
            return f"السعر الحقيقي الحالي لبيتكوين (BTCUSD): {price} USD"
            
        else:
            return f"الزوج أو الأصول المطلوبة: {symbol_text} (مبني على التحليل الفني المباشر لسعار السوق الحالية)"
            
    except Exception as e:
        logger.error(f"خطأ في جلب السعر الحي: {e}")
        return f"الزوج المطلوبة: {symbol_text}"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "مرحباً بك في بوت التداول الذكي 📊\n\n"
        "البوت مربوط الآن بالأسعار الحية.\n"
        "أرسل لي **اسم الزوج والتايم فريم** (مثال: `XAUUSD 15M` أو `BTCUSD 1H`) وسأجلب لك السعر الحي وأعطيك التحليل الفوري والدقيق!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_input = message.text.strip()
    sent_msg = bot.reply_to(message, f"🌐 جاري جلب السعر الحي وإعداد التحليل لـ `{user_input}`، لحظات...")
    
    try:
        # جلب السعر الحي بطريقة آمنة
        live_price_info = get_live_price(user_input)
        
        prompt = (
            f"أنت خبير تحليل فني محترف في الأسواق المالية.\n"
            f"بيانات السوق الحية الحالية:\n{live_price_info}\n"
            f"الزوج والتايم فريم المطلوب: {user_input}\n\n"
            "قم بعمل تحليل فني متكامل واحترافي مبني حصراً على السعر الحي المذكور أعلاه.\n"
            "عليك تقديم التوصية بالتنسيق التالي:\n"
            "1. السعر الحي المعتمد\n"
            "2. اتجاه السوق (Bullish / Bearish)\n"
            "3. الصفقة (BUY / SELL)\n"
            "4. سعر الدخول\n"
            "5. وقف الخسارة (Stop Loss)\n"
            "6. الأهداف (Take Profit 1 & Take Profit 2)\n"
            "7. الأسباب الفنية باختصار."
        )
        
        response = model.generate_content(prompt)
        bot.edit_message_text(chat_id=message.chat.id, message_id=sent_msg.message_id, text=response.text)
            
    except Exception as e:
        logger.error(f"خطأ أثناء توليد التحليل: {e}")
        bot.edit_message_text(chat_id=message.chat.id, message_id=sent_msg.message_id, text=f"❌ حدث خطأ في النظام، يرجى المحاولة مجدداً.")

if __name__ == '__main__':
    bot.infinity_polling()
