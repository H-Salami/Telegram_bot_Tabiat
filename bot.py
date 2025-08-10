import telebot
import os
import sqlite3

# --- تنظیمات ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# --- مسیر دیتابیس ---
DB_NAME = "registrations.db"

# --- توابع دیتابیس ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  name TEXT,
                  count INTEGER,
                  username TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

def save_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def save_registration(user_id, name, count, username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    c.execute("INSERT OR REPLACE INTO users (user_id, name, count, username, timestamp) VALUES (?, ?, ?, ?, ?)",
              (user_id, name, count, username, ''))
    conn.commit()
    conn.close()

def get_all_registrations():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, count, username FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

def get_total_count():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT SUM(count) FROM users")
    total = c.fetchone()[0]
    conn.close()
    return total or 0

# --- دکمه‌های اصلی ---
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👥 لیست شرکت‌کنندگان")
    return markup

# --- دستور /start ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == 'private':
        bot.reply_to(message, """
        🌿 خوش آمدید به ربات برنامه طبیعت‌گردی!

        🌌 برنامه: شهاب‌باران و شب مانی در تاریک دره  
        📅 جمعه ۱۴ اردیبهشت ۱۴۰۴  
        🕢 ساعت 21:00  
        📍 تاریک دره، دماوند  

        برای ثبت‌نام، دستور /join را بزنید.
        """, reply_markup=main_menu())
    else:
        # در گروه فقط دکمه نمایش داده می‌شود
        send_group_message(message.chat.id)

def send_group_message(chat_id):
    total = get_total_count()
    registrations = get_all_registrations()
    
    if not registrations:
        list_text = "📭 هنوز کسی ثبت‌نام نکرده است."
    else:
        list_text = f"📋 لیست شرکت‌کنندگان (جمع: {total} نفر):\n\n"
        for i, (name, count, username) in enumerate(registrations, 1):
            uname = f"@{username}" if username else "ناشناس"
            list_text += f"{i}. {name} → {count} نفر ({uname})\n"

    # دکمه هدایت به پیوی
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("✅ ثبت‌نام در پیوی", url=f"https://t.me/{bot.get_me().username}")
    markup.add(btn)

    bot.send_message(
        chat_id,
        f"🌿 برنامه: شهاب‌باران و شب مانی در تاریک دره\n"
        f"👥 مجموع شرکت‌کنندگان: {total} نفر\n\n"
        f"{list_text}\n"
        f"برای ثبت‌نام، روی دکمه زیر کلیک کنید:",
        reply_markup=markup
    )

# --- تنظیم گروه ---
@bot.message_handler(commands=['setgroup'])
def set_group(message):
    if str(message.chat.type) not in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل اجراست.")
        return
    group_id = message.chat.id
    save_setting("GROUP_ID", group_id)
    bot.reply_to(message, f"✅ این گروه به عنوان گروه مجاز تنظیم شد.\n🔢 شناسه گروه: `{group_id}`", parse_mode="Markdown")

# --- تنظیم ادمین ---
@bot.message_handler(commands=['setadmin'])
def set_admin(message):
    user_id = message.from_user.id
    save_setting("ADMIN_ID", user_id)
    bot.reply_to(message, f"✅ شما به عنوان ادمین تنظیم شدید.\n🔢 شناسه شما: {user_id}")

# --- بررسی عضویت ---
def is_member(user_id):
    group_id = get_setting("GROUP_ID")
    if not group_id:
        return False
    try:
        group_id = int(group_id)
        member = bot.get_chat_member(group_id, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- ثبت‌نام در پیوی ---
@bot.message_handler(func=lambda message: message.text == "✅ ثبت‌نام در برنامه" or message.text == "/join")
def join_step1(message):
    if message.chat.type != 'private':
        return

    if not is_member(message.from_user.id):
        bot.reply_to(message, """
        ❌ برای ثبت‌نام، باید عضو گروه مجاز باشید.
        لطفاً به گروه بروید و دوباره تلاش کنید.
        """)
        return

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

# --- نمایش لیست در پیوی ---
@bot.message_handler(func=lambda message: message.text == "👥 لیست شرکت‌کنندگان")
def show_list(message):
    if message.chat.type != 'private':
        return
        
    registrations = get_all_registrations()
    total = get_total_count()
    if not registrations:
        response = "📭 هنوز کسی ثبت‌نام نکرده است."
    else:
        response = f"📋 لیست شرکت‌کنندگان (جمع کل: {total} نفر):\n\n"
        for name, count, username in registrations:
            uname = f"@{username}" if username else "ناشناس"
            response += f"• {name} → {count} نفر ({uname})\n"
    bot.reply_to(message, response)

# --- پنل مدیریت ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.type != 'private':
        return
        
    admin_id = get_setting("ADMIN_ID")
    if not admin_id or int(admin_id) != message.from_user.id:
        bot.reply_to(message, "❌ دسترسی محدود به ادمین.")
        return

    registrations = get_all_registrations()
    if not registrations:
        bot.reply_to(message, "هیچ شرکت‌کننده‌ای وجود ندارد.")
        return

    response = "🔐 پنل مدیریت:\n\n"
    for name, count, username in registrations:
        uname = f"@{username}" if username else "ناشناس"
        response += f"• {name} ({uname}) → {count} نفر\n"
    response += "\nبرای حذف، دستور زیر را بزنید:\n/delete [نام]"

    bot.reply_to(message, response)

# --- حذف کاربر ---
@bot.message_handler(commands=['delete'])
def delete_user(message):
    if message.chat.type != 'private':
        return

    admin_id = get_setting("ADMIN_ID")
    if not admin_id or int(admin_id) != message.from_user.id:
        return

    try:
        name_to_delete = message.text.split(maxsplit=1)[1]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE name = ?", (name_to_delete,))
        if c.rowcount > 0:
            conn.commit()
            total = get_total_count()
            bot.reply_to(message, f"✅ شخص با نام '{name_to_delete}' حذف شد.\n👥 مجموع جدید: {total} نفر")
        else:
            bot.reply_to(message, "❌ شخصی با این نام یافت نشد.")
        conn.close()
    except IndexError:
        bot.reply_to(message, "❌ لطفاً دستور را به صورت `/delete علی` وارد کنید.")

# --- اجرا ---
print("ربات در حال اجراست...")
init_db()
bot.polling()
