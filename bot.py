import telebot
import os
import sqlite3
from datetime import datetime

# --- تنظیمات ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# --- ایجاد دیتابیس ---
def init_db():
    conn = sqlite3.connect('registrations.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  name TEXT,
                  count INTEGER,
                  username TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

# --- توابع کمکی ---
def save_registration(user_id, name, count, username):
    conn = sqlite3.connect('registrations.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))  # حذف قبلی
    c.execute("INSERT OR REPLACE INTO users (user_id, name, count, username, timestamp) VALUES (?, ?, ?, ?, ?)",
              (user_id, name, count, username, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_registrations():
    conn = sqlite3.connect('registrations.db')
    c = conn.cursor()
    c.execute("SELECT name, count, username FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

def get_total_count():
    conn = sqlite3.connect('registrations.db')
    c = conn.cursor()
    c.execute("SELECT SUM(count) FROM users")
    total = c.fetchone()[0]
    conn.close()
    return total or 0

def delete_registration(user_id):
    conn = sqlite3.connect('registrations.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# --- دکمه‌های اصلی ---
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✅ ثبت‌نام در برنامه")
    markup.add("👥 لیست شرکت‌کنندگان")
    return markup

# --- دستور /start ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, """
    🌿 خوش آمدید به ربات برنامه طبیعت‌گردی!

    🌌 برنامه: شهاب‌باران و شب مانی در تاریک دره  
    📅 جمعه ۱۴ اردیبهشت ۱۴۰۴  
    🕢 ساعت 21:00  
    📍 تاریک دره، دماوند  

    برای ثبت‌نام یا مشاهده لیست، از دکمه‌های زیر استفاده کنید.
    """, reply_markup=main_menu())

# --- دکمه ثبت‌نام ---
@bot.message_handler(func=lambda message: message.text == "✅ ثبت‌نام در برنامه")
def join_step1(message):
    msg = bot.reply_to(message, "لطفاً نام خود را وارد کنید:")
    bot.register_next_step_handler(msg, join_step2)

def join_step2(message):
    user_name = message.text.strip()
    if not user_name:
        bot.reply_to(message, "لطفاً یک نام معتبر وارد کنید.")
        return
    msg = bot.reply_to(message, "چند نفر (شامل خودتان) می‌خواهید شرکت کنید؟ لطفاً یک عدد وارد کنید.")
    bot.register_next_step_handler(msg, lambda m: join_step3(m, user_name))

def join_step3(message, user_name):
    try:
        count = int(message.text)
        if count < 1:
            raise ValueError
        username = message.from_user.username or "ناشناس"
        save_registration(message.from_user.id, user_name, count, username)
        total = get_total_count()
        bot.reply_to(message, f"""
        ✅ {user_name} عزیز، با {count} نفر ثبت‌نام کردید. ممنون از شما!

        👥 مجموع شرکت‌کنندگان: {total} نفر
        """, reply_markup=main_menu())
    except ValueError:
        bot.reply_to(message, "❌ لطفاً یک عدد مثبت وارد کنید.")

# --- دکمه لیست شرکت‌کنندگان ---
@bot.message_handler(func=lambda message: message.text == "👥 لیست شرکت‌کنندگان")
def show_list(message):
    registrations = get_all_registrations()
    total = get_total_count()
    if not registrations:
        response = "📭 هنوز کسی ثبت‌نام نکرده است."
    else:
        response = f"📋 لیست شرکت‌کنندگان (جمع کل: {total} نفر):\n\n"
        for i, (name, count, username) in enumerate(registrations, 1):
            uname = f"@{username}" if username else "ناشناس"
            response += f"{i}. {name} → {count} نفر ({uname})\n"
    bot.reply_to(message, response)

# --- اجرای ربات ---
print("ربات در حال اجراست...")
init_db()
bot.polling()
