"""Multi-language support (EN / UZ / RU)."""
from __future__ import annotations

from typing import Dict

# ─────────────────────────────────────────────────────────────────────────────
# Translation dictionaries
# ─────────────────────────────────────────────────────────────────────────────

_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # ── Start / Help ─────────────────────────────────────────────────────
        "start": (
            "👋 Hello <b>{name}</b>!\n\n"
            "I can download videos & audio from Instagram, TikTok, YouTube, "
            "Twitter/X, Facebook, Vimeo, SoundCloud, Pinterest, Reddit and "
            "<b>1500+ other sites</b>.\n\n"
            "📎 Just send me a link and I'll handle the rest.\n\n"
            "📋 <b>Commands:</b>\n"
            "/help – Show help\n"
            "/language – Change language\n"
            "/cookies – Set cookies for private content\n"
            "/myfiles – Your uploaded files\n"
            "/stats – Bot statistics (admin)"
        ),
        "help": (
            "🛟 <b>How to use:</b>\n\n"
            "1️⃣ Send any supported link\n"
            "2️⃣ Choose quality: Best / 1080p / 720p / 480p / Audio / Low size\n"
            "3️⃣ Wait while I download & send the file\n\n"
            "📌 <b>For private Instagram/TikTok:</b> use /cookies\n"
            "📁 <b>Upload your own files:</b> just send them to me\n"
            "📂 <b>View your files:</b> /myfiles\n\n"
            "⚠️ Files >50 MB will be compressed or sent as a link."
        ),
        "choose_quality":   "🎬 <b>{title}</b>\n\nChoose quality:",
        "downloading":      "⏳ Downloading… <code>{percent}%</code> {bar}\n{speed} • ETA {eta}",
        "download_done":    "✅ Done! Sending file…",
        "download_failed":  "❌ Download failed: {error}",
        "retrying":         "⚠️ Network issue… retrying in {secs}s (attempt {n}/{max})",
        "cancelled":        "❌ Cancelled.",
        "file_too_large":   "⚠️ File is {size}. Compressing to fit Telegram limit…",
        "compressing":      "🔧 Compressing video…",
        "compress_failed":  "⚠️ Compression failed. Uploading to external host…",
        "external_link":    "📎 File too large for Telegram.\n\n🔗 <a href='{url}'>Download here</a>\n\n⏰ Link expires in 3 days.",
        "unsupported_url":  "❓ I couldn't recognise that URL. Make sure it's a supported site.",
        "too_many_downloads": "⏳ You already have {n} active download(s). Please wait.",
        "server_busy":      "⏳ The server is busy. Please try again in a minute.",
        "caption":          "{title}\n🔗 {url}\n\n📥 Downloaded via @{bot}",

        # ── Cookies ──────────────────────────────────────────────────────────
        "cookies_prompt":   (
            "🍪 <b>Set Cookies</b>\n\n"
            "Export your browser cookies as a <b>Netscape format .txt</b> file "
            "(use <i>Get cookies.txt LOCALLY</i> extension), then send the file here.\n\n"
            "Cookies are stored encrypted and expire after 30 days."
        ),
        "cookies_saved":    "✅ Cookies saved! They will be used for private content.",
        "cookies_invalid":  "❌ Invalid cookie file. Make sure it's Netscape format.",
        "cookies_cancel":   "❌ Cookie setup cancelled.",
        "cookies_deleted":  "🗑️ Cookies deleted.",
        "cookies_cancel_btn": "❌ Cancel",

        # ── Language ─────────────────────────────────────────────────────────
        "language_prompt":  "🌐 Choose your language:",
        "language_set":     "✅ Language set to English.",

        # ── My Files ─────────────────────────────────────────────────────────
        "myfiles_empty":    "📂 You have no stored files.",
        "myfiles_header":   "📂 <b>Your files</b> (auto-deleted after 24h):",
        "myfiles_item":     "{n}. <b>{name}</b> – {size} – {date}",
        "file_resent":      "📤 File re-sent!",
        "file_deleted":     "🗑️ File deleted.",
        "file_not_found":   "❌ File not found or expired.",

        # ── Upload ───────────────────────────────────────────────────────────
        "upload_saved":     "✅ File <b>{name}</b> saved! Use /myfiles to manage it.",
        "upload_too_large": "❌ File is too large (max {max} MB).",

        # ── Stats (admin) ────────────────────────────────────────────────────
        "stats": (
            "📊 <b>Bot Statistics</b>\n\n"
            "📥 Total downloads: <b>{downloads}</b>\n"
            "❌ Total errors: <b>{errors}</b>\n"
            "👥 Unique users: <b>{users}</b>\n"
            "⏳ Queue size: <b>{queue}</b>\n"
            "🔄 Active downloads: <b>{active}</b>"
        ),
        "not_admin":        "⛔ You don't have permission to use this command.",
    },

    "uz": {
        "start": (
            "👋 Salom <b>{name}</b>!\n\n"
            "Men Instagram, TikTok, YouTube, Twitter/X, Facebook, Vimeo, "
            "SoundCloud, Pinterest, Reddit va <b>1500+ boshqa saytlardan</b> "
            "video va audio yuklab olishim mumkin.\n\n"
            "📎 Menga havola yuboring va men qolganini qilaman.\n\n"
            "📋 <b>Buyruqlar:</b>\n"
            "/help – Yordam\n"
            "/language – Tilni o'zgartirish\n"
            "/cookies – Shaxsiy kontent uchun cookies\n"
            "/myfiles – Yuklangan fayllaringiz\n"
            "/stats – Bot statistikasi (admin)"
        ),
        "help": (
            "🛟 <b>Qanday ishlatish:</b>\n\n"
            "1️⃣ Qo'llab-quvvatlanadigan havolani yuboring\n"
            "2️⃣ Sifatni tanlang: Eng yaxshi / 1080p / 720p / 480p / Audio / Kichik\n"
            "3️⃣ Yuklab olgunimcha kuting\n\n"
            "📌 <b>Shaxsiy Instagram/TikTok uchun:</b> /cookies dan foydalaning\n"
            "📁 <b>O'z fayllaringizni yuklash:</b> faqat yuboring\n"
            "📂 <b>Fayllarni ko'rish:</b> /myfiles\n\n"
            "⚠️ 50 MB dan katta fayllar siqiladi yoki havola sifatida yuboriladi."
        ),
        "choose_quality":   "🎬 <b>{title}</b>\n\nSifatni tanlang:",
        "downloading":      "⏳ Yuklanmoqda… <code>{percent}%</code> {bar}\n{speed} • Qoldi {eta}",
        "download_done":    "✅ Tayyor! Fayl yuborilmoqda…",
        "download_failed":  "❌ Yuklab olish muvaffaqiyatsiz: {error}",
        "retrying":         "⚠️ Tarmoq xatosi… {secs}s dan keyin qayta urinish ({n}/{max})",
        "cancelled":        "❌ Bekor qilindi.",
        "file_too_large":   "⚠️ Fayl hajmi {size}. Telegram chegarasiga moslashtirish uchun siqilmoqda…",
        "compressing":      "🔧 Video siqilmoqda…",
        "compress_failed":  "⚠️ Siqish muvaffaqiyatsiz. Tashqi serverga yuklanmoqda…",
        "external_link":    "📎 Fayl Telegram uchun juda katta.\n\n🔗 <a href='{url}'>Bu yerdan yuklab oling</a>\n\n⏰ Havola 3 kun amal qiladi.",
        "unsupported_url":  "❓ Bu URL ni tanimadim. Qo'llab-quvvatlanadigan sayt ekanligiga ishonch hosil qiling.",
        "too_many_downloads": "⏳ Sizda allaqachon {n} ta faol yuklab olish bor. Iltimos, kuting.",
        "server_busy":      "⏳ Server band. Birozdan keyin urinib ko'ring.",
        "caption":          "{title}\n🔗 {url}\n\n📥 @{bot} orqali yuklab olindi",
        "cookies_prompt":   (
            "🍪 <b>Cookies o'rnatish</b>\n\n"
            "Brauzer cookies faylini <b>Netscape format .txt</b> ko'rinishida eksport qiling "
            "(<i>Get cookies.txt LOCALLY</i> kengaytmasidan foydalaning), keyin fayl yuboring.\n\n"
            "Cookies shifrlangan holda saqlanadi va 30 kundan keyin o'chadi."
        ),
        "cookies_saved":    "✅ Cookies saqlandi! Shaxsiy kontent uchun ishlatiladi.",
        "cookies_invalid":  "❌ Noto'g'ri cookie fayli. Netscape format ekanligiga ishonch hosil qiling.",
        "cookies_cancel":   "❌ Cookies o'rnatish bekor qilindi.",
        "cookies_deleted":  "🗑️ Cookies o'chirildi.",
        "cookies_cancel_btn": "❌ Bekor qilish",
        "language_prompt":  "🌐 Tilni tanlang:",
        "language_set":     "✅ Til o'zbekchaga o'zgartirildi.",
        "myfiles_empty":    "📂 Saqlangan fayllar yo'q.",
        "myfiles_header":   "📂 <b>Fayllaringiz</b> (24 soatdan keyin avtomatik o'chadi):",
        "myfiles_item":     "{n}. <b>{name}</b> – {size} – {date}",
        "file_resent":      "📤 Fayl qayta yuborildi!",
        "file_deleted":     "🗑️ Fayl o'chirildi.",
        "file_not_found":   "❌ Fayl topilmadi yoki muddati o'tdi.",
        "upload_saved":     "✅ <b>{name}</b> fayli saqlandi! /myfiles orqali boshqaring.",
        "upload_too_large": "❌ Fayl juda katta (maksimal {max} MB).",
        "stats": (
            "📊 <b>Bot Statistikasi</b>\n\n"
            "📥 Jami yuklab olishlar: <b>{downloads}</b>\n"
            "❌ Jami xatolar: <b>{errors}</b>\n"
            "👥 Noyob foydalanuvchilar: <b>{users}</b>\n"
            "⏳ Navbat hajmi: <b>{queue}</b>\n"
            "🔄 Faol yuklab olishlar: <b>{active}</b>"
        ),
        "not_admin":        "⛔ Bu buyruqdan foydalanish huquqingiz yo'q.",
    },

    "ru": {
        "start": (
            "👋 Привет, <b>{name}</b>!\n\n"
            "Я умею скачивать видео и аудио из Instagram, TikTok, YouTube, "
            "Twitter/X, Facebook, Vimeo, SoundCloud, Pinterest, Reddit и "
            "<b>1500+ других сайтов</b>.\n\n"
            "📎 Просто пришлите ссылку, я займусь остальным.\n\n"
            "📋 <b>Команды:</b>\n"
            "/help – Помощь\n"
            "/language – Изменить язык\n"
            "/cookies – Куки для приватного контента\n"
            "/myfiles – Ваши загруженные файлы\n"
            "/stats – Статистика бота (admin)"
        ),
        "help": (
            "🛟 <b>Как использовать:</b>\n\n"
            "1️⃣ Отправьте поддерживаемую ссылку\n"
            "2️⃣ Выберите качество: Лучшее / 1080p / 720p / 480p / Аудио / Маленький\n"
            "3️⃣ Подождите пока скачиваю и отправляю файл\n\n"
            "📌 <b>Для приватного Instagram/TikTok:</b> используйте /cookies\n"
            "📁 <b>Загрузить свои файлы:</b> просто отправьте их\n"
            "📂 <b>Посмотреть файлы:</b> /myfiles\n\n"
            "⚠️ Файлы >50 МБ будут сжаты или отправлены как ссылка."
        ),
        "choose_quality":   "🎬 <b>{title}</b>\n\nВыберите качество:",
        "downloading":      "⏳ Загрузка… <code>{percent}%</code> {bar}\n{speed} • Осталось {eta}",
        "download_done":    "✅ Готово! Отправляю файл…",
        "download_failed":  "❌ Ошибка загрузки: {error}",
        "retrying":         "⚠️ Ошибка сети… повтор через {secs}с (попытка {n}/{max})",
        "cancelled":        "❌ Отменено.",
        "file_too_large":   "⚠️ Размер файла {size}. Сжимаю для Telegram…",
        "compressing":      "🔧 Сжимаю видео…",
        "compress_failed":  "⚠️ Сжатие не удалось. Загружаю на внешний хост…",
        "external_link":    "📎 Файл слишком большой для Telegram.\n\n🔗 <a href='{url}'>Скачать здесь</a>\n\n⏰ Ссылка действует 3 дня.",
        "unsupported_url":  "❓ Не удалось распознать URL. Убедитесь, что сайт поддерживается.",
        "too_many_downloads": "⏳ У вас уже {n} активных загрузок. Пожалуйста, подождите.",
        "server_busy":      "⏳ Сервер занят. Пожалуйста, попробуйте позже.",
        "caption":          "{title}\n🔗 {url}\n\n📥 Загружено через @{bot}",
        "cookies_prompt":   (
            "🍪 <b>Установить Cookies</b>\n\n"
            "Экспортируйте куки браузера в формате <b>Netscape .txt</b> "
            "(используйте расширение <i>Get cookies.txt LOCALLY</i>), затем отправьте файл.\n\n"
            "Куки хранятся в зашифрованном виде и истекают через 30 дней."
        ),
        "cookies_saved":    "✅ Куки сохранены! Будут использоваться для приватного контента.",
        "cookies_invalid":  "❌ Неверный файл куки. Убедитесь, что это формат Netscape.",
        "cookies_cancel":   "❌ Настройка куки отменена.",
        "cookies_deleted":  "🗑️ Куки удалены.",
        "cookies_cancel_btn": "❌ Отмена",
        "language_prompt":  "🌐 Выберите язык:",
        "language_set":     "✅ Язык изменён на русский.",
        "myfiles_empty":    "📂 Нет сохранённых файлов.",
        "myfiles_header":   "📂 <b>Ваши файлы</b> (автоудаление через 24ч):",
        "myfiles_item":     "{n}. <b>{name}</b> – {size} – {date}",
        "file_resent":      "📤 Файл повторно отправлен!",
        "file_deleted":     "🗑️ Файл удалён.",
        "file_not_found":   "❌ Файл не найден или истёк.",
        "upload_saved":     "✅ Файл <b>{name}</b> сохранён! Управляйте через /myfiles.",
        "upload_too_large": "❌ Файл слишком большой (макс. {max} МБ).",
        "stats": (
            "📊 <b>Статистика бота</b>\n\n"
            "📥 Всего загрузок: <b>{downloads}</b>\n"
            "❌ Всего ошибок: <b>{errors}</b>\n"
            "👥 Уникальных пользователей: <b>{users}</b>\n"
            "⏳ Размер очереди: <b>{queue}</b>\n"
            "🔄 Активных загрузок: <b>{active}</b>"
        ),
        "not_admin":        "⛔ У вас нет прав для использования этой команды.",
    },
}

_FALLBACK_LANG = "en"


def get_text(key: str, lang: str = "en", **kwargs) -> str:
    """Return translated string with optional format substitution."""
    translations = _TRANSLATIONS.get(lang) or _TRANSLATIONS[_FALLBACK_LANG]
    text = translations.get(key) or _TRANSLATIONS[_FALLBACK_LANG].get(key, f"[{key}]")
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def supported_langs() -> list[str]:
    return list(_TRANSLATIONS.keys())
