import os
import logging
import telebot
from telebot import types
import google.generativeai as genai

# إعدادات التسجيل لمتابعة الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# قراءة مفاتيح التشغيل من متغيرات البيئة في Railway
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    logger.error("المرجو التأكد من إعداد TELEGRAM_BOT_TOKEN و GEMINI_API_KEY في متغيرات البيئة!")
    exit(1)

# تهيئة بوت تيليجرام ومكتبة الذكاء الاصطناعي
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# إعداد نموذج جيميناي بطريقة مستقرة ومتوافقة
generation_config = {
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1024,
}

model = genai.GenerativeModel(
    model_name="gemini-3.8-flash",
    generation_config=generation_config
)

# تخزين مؤقت لحالة المستخدمين (لانتظار الشارت)
user_states = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "مرحباً بك، أنا بوت التحليل الفني الذكي 📊\n\n"
        "أعمل على مدار الساعة لتحليل الشارتات بدقة.\n"
        "للبدء، أرسل لي **اسم الزوج والتايم زمني** (مثال: `XAUUSD 15M` أو `EURUSD 1H`) مع **صورة الشارت** في نفس الوقت، وسأقوم بالتحليل الفوري بالأسعار الحقيقية!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['analyze'])
def request_analysis(message):
    bot.reply_to(message, "من فضلك، أرسل لي لقطة الشاشة (Screenshot) للشارت مع كتابة اسم الزوج والتايم فريم في تعليق مع الصورة (Caption) لكي أباشر التحليل الفوري.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    user_states[user_id] = message.text.strip()
    bot.reply_to(message, f"📌 تم استقبال الرمز والتايم فريم: `{message.text}`\nالآن أرسل لي **صورة الشارت (Screenshot)** لنقرا السعر الحقيقي ونبدأ التحليل!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    text_info = user_states.get(user_id, "XAUUSD 15M")
    
    sent_msg = bot.reply_to(message, "⏳ جاري فحص الشارت وقراءة الأسعار الحقيقية الحالية، لحظات...")
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_path = "temp_chart.jpg"
        with open(image_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        sample_file = genai.upload_file(path=image_path, display_name="Chart Screenshot")
        
        prompt = (
            "أنت خبير تحليل فني محترف في الأسواق المالية (خصوصاً الذهب XAUUSD والعملات). مهمتك هي تحليل لقطة الشاشة (Screenshot) المرفقة للشارت بدقة تامة.\n"
            "قواعد صارمة جداً:\n"
            "1. اقرأ السعر الحالي الحقيقي للسوق الظاهر في أقصى يمين الشارت (سعر السوق الراهن بدقة).\n"
            "2. يجب أن تكون مناطق الدخول، وقف الخسارة، والأهداف مبنية حصراً وبشكل واقعي تماماً على السعر الحالي الظاهر في الصورة، وممنوع نهائياً استخدام أي أسعار افتراضية أو قديمة أو ثابتة.\n"
            f"قم بتحليل شارت التداول للزوج والتايم فريم: {text_info}، واعطني التوصية الكاملة بالترتيب (الزوج والفريم، نوع الصفقة BUY/SELL، سعر الدخول، وقف الخسارة، والأهداف الأول والثاني مع الأسباب الفنية)."
        )
        
        response = model.generate_content([sample_file, prompt])
        
        bot.edit_message_text(chat_id=message.chat.id, message_id=sent_msg.message_id, text=response.text)
        
        if os.path.exists(image_path):
            os.remove(image_path)
            
    except Exception as e:
        logger.error(f"خطأ أثناء المعالجة: {e}")
        bot.edit_message_text(chat_id=message.chat.id, message_id=sent_msg.message_id, text=f"❌ حدث خطأ أثناء التحليل: {str(e)}")

# تشغيل البوت باستمرار
if __name__ == '__main__':
    logger.info("البوت بدأ يعمل بنجاح...")
    bot.infinity_polling()
