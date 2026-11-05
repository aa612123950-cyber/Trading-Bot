import os
import logging
import telebot
from telebot import types
from PIL import Image
import google.generativeai as genai

# إعدادات التسجيل لمتابعة الأخطاء
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

# إعداد نموذج جيميناي مع تقليل التوكنز لتسريع الاستجابة
generation_config = {
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 800,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config
)

user_states = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "مرحباً بك، أنا بوت التحليل الفني الذكي 📊\n\n"
        "أعمل على تحليل الشارتات بدقة.\n"
        "أرسل لي اسم الزوج والتايم فريم (مثال: `XAUUSD 15M`) مع صورة الشارت لنبدأ التحليل!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    user_states[user_id] = message.text.strip()
    bot.reply_to(message, f"📌 تم استقبال الرمز: `{message.text}`\nالآن أرسل لي **صورة الشارت** لنقوم بالتحليل الفوري!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    text_info = user_states.get(user_id, "XAUUSD 15M")
    
    sent_msg = bot.reply_to(message, "⏳ جاري فحص الشارت وقراءة الأسعار الحالية بسرعة، لحظات...")
    
    image_path = "temp_chart.jpg"
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(image_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # ضغط وتقليل حجم الصورة لتجنب مشاكل Timeout (504)
        img = Image.open(image_path)
        img.thumbnail((1024, 1024))
        
        prompt = (
            "أنت خبير تحليل فني محترف في الأسواق المالية.\n"
            "قواعد صارمة:\n"
            "1. اقرأ السعر الحالي الحقيقي للسوق الظاهر في أقصى يمين الشارت بدقة.\n"
            "2. ابنِ مناطق الدخول، وقف الخسارة، والأهداف حصراً على السعر الحالي.\n"
            f"قم بتحليل شارت التداول للزوج والتايم فريم: {text_info}، واعطني التوصية بالترتيب (BUY/SELL، سعر الدخول، وقف الخسارة، والأهداف مع الأسباب الفنية)."
        )
        
        # استدعاء النموذج مع مهلة أمان
        response = model.generate_content([img, prompt])
        bot.edit_message_text(chat_id=message.chat.id, message_id=sent_msg.message_id, text=response.text)
            
    except Exception as e:
        logger.error(f"خطأ أثناء المعالجة: {e}")
        bot.edit_message_text(chat_id=message.chat.id, message_id=sent_msg.message_id, text=f"❌ حدث خطأ في الاتصال (TimeOut): تأكد من وضوح الشارت وحاول مجدداً.")
    
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

if __name__ == '__main__':
    bot.infinity_polling()
