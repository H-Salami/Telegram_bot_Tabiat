# bot.py
import telebot
import os

# دریافت توکن از متغیر محیطی
TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, """
    🌿 خوش آمدید به ربات برنامه طبیعت‌گردی!
    
    🌌 برنامه: شهاب‌باران و شب مانی در تاریک دره
    📅 پنجشنبه 23 مرداد ۱۴۰۴
    🕢 ساعت 16:30
    📍 تاریک دره، چنگه بز
    
    برای ثبت‌نام، دستور /join را بزنید.
    """)

@bot.message_handler(commands=['join'])
def join(message):
    msg = bot.reply_to(message, "چند نفر (شامل خودتان) می‌خواهید شرکت کنید؟ لطفاً یک عدد وارد کنید.")
    bot.register_next_step_handler(msg, process_count)

def process_count(message):
    try:
        count = int(message.text)
        user_name = message.from_user.first_name
        bot.reply_to(message, f"✅ {user_name} عزیز، با {count} نفر ثبت‌نام کردید. ممنون از شما!")
    except ValueError:
        bot.reply_to(message, "❌ لطفاً یک عدد معتبر وارد کنید.")

print("ربات در حال اجراست...")
bot.polling()