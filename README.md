# 🎵 Music Downloader Bot

ربات دانلود موزیک تلگرام - ساخته شده توسط **اکبر هنرمند**

## ✨ امکانات

- 🔍 جستجوی آهنگ به فارسی و انگلیسی
- 📥 دانلود MP3 320kbps
- 📊 نوار پیشرفت واقعی
- 🎵 آهنگ‌های محبوب
- 📞 پشتیبانی مستقیم

## 🚀 استقرار روی Railway

### قدم ۱: آماده‌سازی

1. یک اکانت Railway بسازید: https://railway.app
2. یک پروژه جدید بسازید
3. گزینه "Deploy from GitHub" رو انتخاب کنید

### قدم ۲: آپلود کد

فایل‌های پروژه رو آپلود کنید:
```
bot_download_music/
├── bot.py
├── config.py
├── requirements.txt
├── Dockerfile
├── railway.json
├── .gitignore
├── handlers/
│   ├── __init__.py
│   ├── start.py
│   └── search.py
├── services/
│   ├── __init__.py
│   └── music.py
└── utils/
    ├── __init__.py
    └── helpers.py
```

### قدم ۳: تنظیم Environment Variables

در پنل Railway، به تب "Variables" برید و اضافه کنید:

```
TELEGRAM_BOT_TOKEN=توکن_ربات_تلگرام_شما
DOWNLOAD_PATH=./downloads
MAX_FILE_SIZE=50
```

### قدم ۴: استقرار

روی دکمه "Deploy" کلیک کنید و منتظر باشید.

## 📱 استفاده

| دستور | توضیح |
|-------|-------|
| `/start` | شروع ربات |
| `/search نام آهنگ` | جستجو |
| `/popular` | آهنگ‌های محبوب |
| `/help` | راهنما |
| `/contact` | پشتیبانی |

## 👨‍💻 سازنده

**اکبر هنرمند**
- تلگرام: [@Akbar_H62](https://t.me/Akbar_H62)

## 📜 مجوز

این ربات برای استفاده شخصی و آموزشی طراحی شده است.
