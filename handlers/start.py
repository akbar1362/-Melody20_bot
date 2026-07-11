from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    first_name = user.first_name or "کاربر"

    welcome_text = f"""
🎵 سلام {first_name}!

به ربات دانلود موزیک خوش اومدی!

📌 دستورات اصلی:
┌─────────────────────────────┐
│ 🔍 /search - جستجوی آهنگ  │
│ 🎵 /popular - آهنگ محبوب  │
│ 📋 /help - راهنما          │
│ ⚙️ /settings - تنظیمات    │
│ 📞 /contact - پشتیبانی    │
└─────────────────────────────┘

💡 نکته: کافیه نام آهنگ یا خواننده رو بفرستی!

🚀 شروع کن: /search
"""

    keyboard = [
        [
            InlineKeyboardButton("🔍 جستجوی آهنگ", switch_inline_query_current_chat=""),
        ],
        [
            InlineKeyboardButton("🎵 آهنگ‌های محبوب", callback_data="popular"),
            InlineKeyboardButton("📋 راهنما", callback_data="help"),
        ],
        [
            InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/Akbar_H62"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 راهنمای ربات

┌─────────────────────────────────┐
│ 🔍 جستجوی آهنگ                │
│ /search نام آهنگ یا خواننده    │
│ مثال: /search محسن چاوشی       │
├─────────────────────────────────┤
│ 🎵 آهنگ‌های محبوب             │
│ /popular                        │
├─────────────────────────────────┤
│ 💡 جستجوی سریع                │
│ فقط نام آهنگ رو بفرست          │
│ مثال: آهنگ جدید محسن چاوشی    │
├─────────────────────────────────┤
│ ⚙️ تنظیمات                   │
│ /settings                       │
├─────────────────────────────────┤
│ 📞 پشتیبانی                   │
│ /contact                        │
└─────────────────────────────────┘

🎵 کیفیت دانلود: MP3 320kbps
💰 هزینه: کاملاً رایگان!

─────────────────────
👨‍💻 سازنده: اکبر هنرمند
📞 پشتیبانی: @Akbar_H62
"""

    keyboard = [
        [
            InlineKeyboardButton("🔍 جستجو", switch_inline_query_current_chat=""),
        ],
        [
            InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/Akbar_H62"),
            InlineKeyboardButton("🏠 خانه", callback_data="home"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(help_text, reply_markup=reply_markup)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings_text = """
⚙️ تنظیمات ربات

┌─────────────────────────────────┐
│ 🎵 کیفیت دانلود:              │
│ [✅] MP3 320kbps                │
│ [  ] MP3 128kbps               │
├─────────────────────────────────┤
│ 📁 ذخیره خودکار:              │
│ [✅] روشن                      │
│ [  ] خاموش                      │
├─────────────────────────────────┤
│ 🔔 اعلان‌ها:                   │
│ [✅] روشن                      │
│ [  ] خاموش                      │
└─────────────────────────────────┘
"""

    keyboard = [
        [
            InlineKeyboardButton("🎵 کیفیت MP3 320", callback_data="quality_320"),
            InlineKeyboardButton("🎵 کیفیت MP3 128", callback_data="quality_128"),
        ],
        [
            InlineKeyboardButton("✅ ذخیره خودکار", callback_data="autosave_on"),
            InlineKeyboardButton("❌ خاموش", callback_data="autosave_off"),
        ],
        [
            InlineKeyboardButton("🏠 خانه", callback_data="home"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(settings_text, reply_markup=reply_markup)


async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact_text = """
📞 پشتیبانی ربات

─────────────────────

برای ارتباط با پشتیبانی و سازنده ربات:

👤 اکبر هنرمند
🔗 @Akbar_H62

────────────────────️

💡 برای گزارش مشکل یا پیشنهاد:
پیام مستقیم بفرستید به آیدی بالا

────────────────────️
👨‍💻 سازنده: اکبر هنرمند
"""

    keyboard = [
        [
            InlineKeyboardButton("💬 پیام به پشتیبانی", url="https://t.me/Akbar_H62"),
        ],
        [
            InlineKeyboardButton("🏠 خانه", callback_data="home"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(contact_text, reply_markup=reply_markup)


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    help_text = """
📖 راهنمای ربات

🔍 جستجو: نام آهنگ یا خواننده رو بفرست
🎵 دانلود: روی آهنگ مورد نظر کلیک کن
⭐ علاقه‌مندی‌ها: آهنگ‌های محبوبت رو ذخیره کن
📞 پشتیبانی: @Akbar_H62
"""

    keyboard = [
        [InlineKeyboardButton("🔍 جستجو", switch_inline_query_current_chat="")],
        [
            InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/Akbar_H62"),
            InlineKeyboardButton("🏠 خانه", callback_data="home"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(help_text, reply_markup=reply_markup)


async def home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    user = query.from_user
    first_name = user.first_name or "کاربر"

    welcome_text = f"""
🎵 سلام {first_name}!

به ربات دانلود موزیک خوش اومدی!

🔍 نام آهنگ یا خواننده رو بفرست

────────────────────️
👨‍💻 سازنده: اکبر هنرمند
📞 پشتیبانی: @Akbar_H62
"""

    keyboard = [
        [InlineKeyboardButton("🔍 جستجو", switch_inline_query_current_chat="")],
        [
            InlineKeyboardButton("🎵 محبوب‌ها", callback_data="popular"),
            InlineKeyboardButton("📋 راهنما", callback_data="help"),
        ],
        [
            InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/Akbar_H62"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(welcome_text, reply_markup=reply_markup)
