from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import math
import os

from services.music import MusicService
from utils.helpers import sanitize_filename, cleanup_file


music_service = MusicService()

user_search_results = {}


def save_search_results(chat_id: int, data: dict):
    user_search_results[chat_id] = data


def get_search_results(chat_id: int) -> dict | None:
    return user_search_results.get(chat_id)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        keyboard = [
            [InlineKeyboardButton("🔍 جستجو در یوتیوب", switch_inline_query_current_chat="")],
            [InlineKeyboardButton("💡 مثال: محسن چاوشی", switch_inline_query_current_chat="محسن چاوشی")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🎵 نام آهنگ یا خواننده رو بفرست:\n\n"
            "💡 می‌تونی به فارسی یا انگلیسی جستجو کنی",
            reply_markup=reply_markup,
        )
        return

    query = " ".join(context.args)
    await perform_search(update, context, query, is_callback=False)


async def text_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.startswith("/") or len(text) < 2:
        return

    await perform_search(update, context, text, is_callback=False)


async def perform_search(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str, is_callback: bool = False):
    if is_callback:
        msg = await update.callback_query.edit_message_text(f"🔍 در حال جستجوی {query}...")
        chat_id = update.callback_query.message.chat.id
    else:
        msg = await update.message.reply_text(f"🔍 در حال جستجوی {query}...")
        chat_id = update.message.chat.id

    results = music_service.search(query, limit=10)

    if not results:
        keyboard = [
            [InlineKeyboardButton("🔄 جستجوی مجدد", switch_inline_query_current_chat=query)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await msg.edit_text(
            "❌ نتیجه‌ای یافت نشد!\n\n"
            "💡 پیشنهادات:\n"
            "• نام رو بررسی کن\n"
            "• از نام انگلیسی استفاده کن\n"
            "• کلمات کلیدی کمتری بفرست",
            reply_markup=reply_markup,
        )
        return

    save_search_results(chat_id, {
        "query": query,
        "results": results,
        "page": 1,
        "total_pages": math.ceil(len(results) / 5),
    })

    await show_search_results(msg, chat_id, page=1)


async def show_search_results(msg, chat_id: int, page: int = 1):
    data = get_search_results(chat_id)
    if not data:
        await msg.edit_text("❌ خطا: اطلاعات جستجو یافت نشد. دوباره جستجو کن.")
        return

    results = data["results"]
    query = data["query"]
    items_per_page = 5
    total_pages = math.ceil(len(results) / items_per_page)
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_results = results[start_idx:end_idx]

    text = f"🎵 نتایج جستجو: {query}\n"
    text += f"📄 صفحه {page} از {total_pages}\n"
    text += "─────────────────────\n\n"

    buttons = []
    for i, track in enumerate(page_results):
        idx = start_idx + i
        duration = format_duration(track["duration"]) if track.get("duration") else "??:??"
        title = track["title"][:40] + "..." if len(track["title"]) > 40 else track["title"]
        artist = track["artist"][:30] + "..." if len(track["artist"]) > 30 else track["artist"]

        text += f"{idx + 1}. 🎵 {title}\n"
        text += f"   👤 {artist}\n"
        text += f"   ⏱ {duration}\n\n"

        buttons.append([
            InlineKeyboardButton(
                f"📥 {title[:30]}",
                callback_data=f"dl_{chat_id}_{idx}"
            )
        ])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"page_{chat_id}_{page - 1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"page_{chat_id}_{page + 1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([
        InlineKeyboardButton("🔄 جستجوی جدید", switch_inline_query_current_chat=query),
        InlineKeyboardButton("🏠 خانه", callback_data="home"),
    ])

    reply_markup = InlineKeyboardMarkup(buttons)

    try:
        await msg.edit_text(text, reply_markup=reply_markup)
    except Exception:
        await msg.edit_text(text[:4000], reply_markup=reply_markup)


async def page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("page_"):
        return

    parts = data.split("_")
    chat_id = int(parts[1])
    page = int(parts[2])

    saved_data = get_search_results(chat_id)
    if saved_data:
        saved_data["page"] = page
        await show_search_results(query.message, chat_id, page)


async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    data = query.data
    if not data.startswith("dl_"):
        return

    parts = data.split("_")
    chat_id = int(parts[1])
    index = int(parts[2])

    saved_data = get_search_results(chat_id)
    if not saved_data:
        try:
            await query.edit_message_text("❌ زمان جستجو تمام شد. دوباره جستجو کن.")
        except Exception:
            pass
        return

    results = saved_data["results"]
    if index >= len(results):
        try:
            await query.edit_message_text("❌ آهنگ یافت نشد.")
        except Exception:
            pass
        return

    track = results[index]
    url = track.get("url")

    if not url:
        try:
            await query.edit_message_text("❌ لینک آهنگ موجود نیست.")
        except Exception:
            pass
        return

    output_name = sanitize_filename(f"{track['title']}_{chat_id}")

    progress_text = create_progress_text(0, track)
    keyboard = [
        [InlineKeyboardButton("⏳ 0% - در حال شروع...", callback_data="downloading")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(progress_text, reply_markup=reply_markup)
    except Exception:
        pass

    last_percent = [0]

    def progress_callback(percent):
        last_percent[0] = percent

    filepath = music_service.download_with_progress(url, output_name, progress_callback)

    if filepath:
        try:
            progress_text = create_progress_text(100, track)
            keyboard = [[InlineKeyboardButton("✅ تکمیل شد!", callback_data="noop")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(progress_text, reply_markup=reply_markup)
        except Exception:
            pass

        try:
            file_size = os.path.getsize(filepath)
            max_telegram_size = 50 * 1024 * 1024

            if file_size > max_telegram_size:
                try:
                    compress_text = "📦 فایل بزرگه! در حال فشرده‌سازی..."
                    await query.edit_message_text(compress_text)
                except Exception:
                    pass

                filepath = music_service.compress_file(filepath, max_size_mb=45)

            with open(filepath, "rb") as audio:
                caption = f"🎵 {track['title']}\n👤 {track['artist']}"

                keyboard = [
                    [
                        InlineKeyboardButton("⭐ ذخیره", callback_data=f"fav_{index}"),
                        InlineKeyboardButton("🔄 دوباره", callback_data=f"dl_{chat_id}_{index}"),
                    ],
                    [
                        InlineKeyboardButton("🔍 جستجوی جدید", switch_inline_query_current_chat=""),
                    ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await context.bot.send_audio(
                    chat_id=chat_id,
                    audio=audio,
                    title=track["title"],
                    performer=track["artist"],
                    caption=caption,
                    reply_markup=reply_markup,
                    read_timeout=600,
                    write_timeout=600,
                    connect_timeout=600,
                )
        except Exception as e:
            print(f"Send audio error: {e}")
            try:
                keyboard = [
                    [
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"dl_{chat_id}_{index}"),
                        InlineKeyboardButton("🔍 جستجو", switch_inline_query_current_chat=""),
                    ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ خطا در ارسال فایل!\n\n"
                    "💡 آهنگ دانلود شد ولی در ارسال مشکل پیش اومد.\n"
                    "دوباره تلاش کن.",
                    reply_markup=reply_markup,
                )
            except Exception:
                pass
            return

        file_size = get_file_size(filepath)

        keyboard = [
            [
                InlineKeyboardButton("🔍 جستجوی جدید", switch_inline_query_current_chat=""),
                InlineKeyboardButton("🏠 خانه", callback_data="home"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(
                f"✅ دانلود با موفقیت انجام شد!\n\n"
                f"🎵 {track['title']}\n"
                f"👤 {track['artist']}\n\n"
                f"📊 حجم: {file_size}",
                reply_markup=reply_markup,
            )
        except Exception:
            pass

        cleanup_file(filepath)
    else:
        keyboard = [
            [
                InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"dl_{chat_id}_{index}"),
                InlineKeyboardButton("🔍 جستجو", switch_inline_query_current_chat=""),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(
                "❌ خطا در دانلود!\n\n"
                "💡 دلایل احتمالی:\n"
                "• مشکل اینترنت\n"
                "• محدودیت منطقه‌ای\n"
                "• آهنگ موجود نیست",
                reply_markup=reply_markup,
            )
        except Exception:
            pass


def create_progress_text(percent: float, track: dict) -> str:
    filled = int(percent // 5)
    empty = 20 - filled
    bar = "█" * filled + "░" * empty

    if percent >= 100:
        status = "✅ تکمیل شد"
    elif percent >= 50:
        status = "📥 در حال دانلود..."
    elif percent >= 25:
        status = "🔄 در حال دریافت..."
    else:
        status = "⏳ شروع دانلود..."

    text = f"📥 در حال دانلود:\n\n"
    text += f"🎵 {track['title']}\n"
    text += f"👤 {track['artist']}\n\n"
    text += f"┌────────────────────────┐\n"
    text += f"│ {bar} │\n"
    text += f"└────────────────────────┘\n"
    text += f"📊 {percent:.1f}% - {status}"

    return text


def get_file_size(filepath: str) -> str:
    try:
        size = os.path.getsize(filepath)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    except:
        return "نامشخص"


async def favorite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer("⭐ به علاقه‌مندی‌ها اضافه شد!", show_alert=True)
    except Exception:
        pass


async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass


async def popular_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    try:
        await query.edit_message_text("🔍 در حال دریافت آهنگ‌های محبوب...")
    except Exception:
        pass

    import random
    popular_queries = [
        "بهترین آهنگ‌های ایرانی 2024",
        "پرطرفدارترین آهنگ‌های فارسی",
        "top hits 2024",
        "popular music",
    ]

    random_query = random.choice(popular_queries)
    results = music_service.search(random_query, limit=10)

    if not results:
        try:
            await query.edit_message_text("❌ خطا در دریافت آهنگ‌ها.")
        except Exception:
            pass
        return

    chat_id = query.message.chat.id
    save_search_results(chat_id, {
        "query": "محبوب‌ها",
        "results": results,
        "page": 1,
        "total_pages": math.ceil(len(results) / 5),
    })

    await show_search_results(query.message, chat_id, page=1)


def format_duration(seconds) -> str:
    try:
        seconds = int(float(seconds))
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    except:
        return "??:??"
