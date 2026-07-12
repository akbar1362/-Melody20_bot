from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import math
import os

from services.music import MusicService
from utils.helpers import sanitize_filename, cleanup_file


music_service = MusicService()

user_search_results = {}


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🎵 نام آهنگ یا خواننده رو بفرست:\n\n"
            "مثال: /search محسن چاوشی",
        )
        return

    query = " ".join(context.args)
    await do_search(update, context, query, chat_id=update.message.chat.id, msg=update.message)


async def text_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.startswith("/") or len(text) < 2:
        return

    await do_search(update, context, text, chat_id=update.message.chat.id, msg=update.message)


async def do_search(update, context, query, chat_id, msg):
    status_msg = await msg.reply_text(f"🔍 در حال جستجوی {query}...")

    results = music_service.search(query, limit=8)

    if not results:
        await status_msg.edit_text("❌ نتیجه‌ای یافت نشد!")
        return

    user_search_results[chat_id] = results

    text = f"🎵 نتایج جستجو: {query}\n\n"

    buttons = []
    for i, track in enumerate(results):
        title = track["title"][:35] + "..." if len(track["title"]) > 35 else track["title"]
        artist = track["artist"][:25] + "..." if len(track["artist"]) > 25 else track["artist"]
        text += f"{i+1}. 🎵 {title}\n   👤 {artist}\n\n"
        buttons.append([InlineKeyboardButton(f"📥 {i+1}. {title[:25]}", callback_data=f"dl{i}")])

    buttons.append([InlineKeyboardButton("🔄 جستجوی جدید", switch_inline_query_current_chat=query)])

    reply_markup = InlineKeyboardMarkup(buttons)
    await status_msg.edit_text(text, reply_markup=reply_markup)


async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("dl"):
        return

    index = int(data.replace("dl", ""))
    chat_id = query.message.chat.id

    print(f"Download requested: chat_id={chat_id}, index={index}")

    if chat_id not in user_search_results:
        await query.edit_message_text("❌ جستجو منقضی شد. دوباره جستجو کن.")
        return

    results = user_search_results[chat_id]
    if index >= len(results):
        await query.edit_message_text("❌ آهنگ یافت نشد.")
        return

    track = results[index]
    url = track.get("url")

    if not url:
        await query.edit_message_text("❌ لینک موجود نیست.")
        return

    try:
        await query.edit_message_text(
            f"📥 در حال دانلود:\n\n"
            f"🎵 {track['title']}\n"
            f"👤 {track['artist']}\n\n"
            f"⏳ لطفاً صبر کن...\n"
            f"💡 اگه طول کشید دوباره امتحان کن"
        )
    except:
        pass

    output_name = f"track_{chat_id}_{index}"

    def progress(p):
        pass

    filepath = music_service.download_with_progress(url, output_name, progress)

    if filepath:
        try:
            file_size = os.path.getsize(filepath)
            max_size = 50 * 1024 * 1024

            if file_size > max_size:
                try:
                    await query.edit_message_text("📦 فایل بزرگه! در حال فشرده‌سازی...")
                except:
                    pass
                filepath = music_service.compress_file(filepath, 45)

            with open(filepath, "rb") as audio:
                caption = f"🎵 {track['title']}\n👤 {track['artist']}\n\n👨‍💻 سازنده: اکبر هنرمند\n📞 @Akbar_H62"

                await context.bot.send_audio(
                    chat_id=chat_id,
                    audio=audio,
                    title=track["title"],
                    performer=track["artist"],
                    caption=caption,
                    read_timeout=600,
                    write_timeout=600,
                    connect_timeout=600,
                )

            await query.edit_message_text(
                f"✅ دانلود شد!\n\n🎵 {track['title']}\n👤 {track['artist']}",
            )

            cleanup_file(filepath)

        except Exception as e:
            print(f"Send error: {e}")
            try:
                await query.edit_message_text(
                    "❌ خطا در ارسال.\n\n"
                    "💡 آهنگ دانلود شد ولی ارسال نشد.\n"
                    "دوباره تلاش کن."
                )
            except:
                pass
    else:
        try:
            await query.edit_message_text(
                "❌ خطا در دانلود.\n\n"
                "💡 دلایل احتمالی:\n"
                "• مشکل اینترنت سرور\n"
                "• یوتیوب محدود کرده\n\n"
                "🔄 چند لحظه صبر کن و دوباره امتحان کن"
            )
        except:
            pass


async def favorite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⭐ ذخیره شد!", show_alert=True)


async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()


async def popular_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("🔍 در حال دریافت...")

    import random
    queries = ["top hits 2024", "popular music", "بهترین آهنگ ایرانی", "موزیک جدید"]
    random_query = random.choice(queries)

    results = music_service.search(random_query, limit=8)

    if not results:
        await query.edit_message_text("❌ خطا.")
        return

    chat_id = query.message.chat.id
    user_search_results[chat_id] = results

    text = f"🎵 آهنگ‌های محبوب:\n\n"

    buttons = []
    for i, track in enumerate(results):
        title = track["title"][:35] + "..." if len(track["title"]) > 35 else track["title"]
        text += f"{i+1}. 🎵 {title}\n   👤 {track['artist']}\n\n"
        buttons.append([InlineKeyboardButton(f"📥 {i+1}. {title[:25]}", callback_data=f"dl{i}")])

    buttons.append([InlineKeyboardButton("🔄 بروزرسانی", callback_data="popular")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(text, reply_markup=reply_markup)
