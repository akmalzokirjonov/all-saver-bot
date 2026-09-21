# All Saver Bot 🤖

> Telegram media downloader bot — Instagram, TikTok, YouTube, Twitter/X, Facebook, Vimeo, SoundCloud, Pinterest, Reddit + 1500+ sites via yt-dlp.

---

## 📋 Features

- 🎬 Download from **1500+ sites** via yt-dlp
- 📊 Quality selection: Best / 1080p / 720p / 480p / Audio MP3 / Low size
- 🔄 Auto-retry with exponential backoff (up to 10 attempts)
- 📦 Auto-compression via ffmpeg if file >50 MB
- 🔗 External upload (catbox.moe) as final fallback
- 🍪 Per-user cookies for private/restricted content
- 📁 User file upload & 24h temporary storage
- 🌐 Multi-language: English, O'zbek, Русский
- 🛡️ Throttling middleware + concurrency limits
- 📊 Admin `/stats` command
- 🐳 Docker + docker-compose ready

---

## 🚀 Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/akmalzokirjonov/all-saver-bot.git
cd all-saver-bot
cp .env.example .env
```

Edit `.env`:
```env
BOT_TOKEN=your_bot_token_from_BotFather
ADMIN_IDS=your_telegram_user_id
```

### 2. Run with Docker (recommended)

```bash
docker-compose up -d --build
```

View logs:
```bash
docker-compose logs -f bot
```

Stop:
```bash
docker-compose down
```

### 3. Run locally (dev)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start Redis (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# Update .env: REDIS_URL=redis://localhost:6379/0
python main.py
```

---

## ⚙️ Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `BOT_TOKEN` | **required** | Token from @BotFather |
| `ADMIN_IDS` | `""` | Comma-separated admin user IDs |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `DOWNLOAD_DIR` | `/tmp/tg_downloads` | Temp download directory |
| `MAX_FILE_SIZE_MB` | `50` | Telegram upload limit |
| `MAX_CONCURRENT_PER_USER` | `2` | Max simultaneous downloads per user |
| `MAX_PLAYLIST_VIDEOS` | `5` | Max videos from playlists |
| `COOKIE_EXPIRE_DAYS` | `30` | Cookie storage TTL |
| `FILE_EXPIRE_HOURS` | `24` | User file storage TTL |
| `DEFAULT_LANG` | `en` | Default language (`en`/`uz`/`ru`) |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## 📱 Commands

| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/help` | Usage guide |
| `/language` | Change interface language |
| `/cookies` | Upload browser cookies (.txt) for private content |
| `/deletecookies` | Remove stored cookies |
| `/myfiles` | View & manage uploaded files |
| `/stats` | Bot statistics *(admin only)* |

---

## 🍪 Using Cookies (Private Content)

To download private Instagram reels, TikTok private videos, etc.:

1. Install browser extension: **[Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)**
2. Visit the site (Instagram, TikTok, etc.) while logged in
3. Click the extension → Export cookies → Save as `.txt`
4. Send `/cookies` to the bot → upload the `.txt` file

Cookies expire after **30 days** and can be removed with `/deletecookies`.

---

## 🏗️ Project Structure

```
Telegram-Bot/
├── main.py                  # Bot entrypoint
├── config.py                # pydantic-settings config
├── states.py                # aiogram FSM states
├── queue.py                 # asyncio concurrency management
├── handlers/
│   ├── start.py             # /start, /help, /language
│   ├── download.py          # URL detection + download flow
│   ├── upload.py            # User file uploads
│   ├── cookies.py           # /cookies FSM
│   ├── myfiles.py           # /myfiles
│   └── admin.py             # /stats
├── utils/
│   ├── downloader.py        # yt-dlp core + retries + progress
│   ├── compressor.py        # ffmpeg compression
│   ├── uploader.py          # catbox.moe / file.io fallback
│   ├── redis_client.py      # Redis operations
│   └── i18n.py              # EN / UZ / RU translations
├── middlewares/
│   └── throttling.py        # Rate limiting
├── keyboards/
│   └── __init__.py          # Inline keyboards
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🛠️ Tech Stack

- **Python 3.12+**
- **aiogram 3.13+** — async Telegram Bot API framework
- **yt-dlp** — media downloader (1500+ sites)
- **redis.asyncio** — async Redis client
- **tenacity** — retry logic with exponential backoff
- **ffmpeg** — video/audio compression
- **pydantic-settings** — environment configuration
- **structlog** — structured logging
- **aiofiles / aiohttp** — async I/O

---

## 📦 Supported Platforms (partial list)

Instagram · TikTok · YouTube · Twitter/X · Facebook · Vimeo · SoundCloud · Pinterest · Reddit · Dailymotion · Twitch · Bilibili · NicoVideo · VK · OK.ru · and **1500+ more**.

---

---

# All Saver Bot 🤖 (O'zbekcha)

> Telegram media yuklovchi bot — Instagram, TikTok, YouTube, Twitter/X, Facebook, Vimeo, SoundCloud, Pinterest, Reddit va yt-dlp orqali 1500+ sayt.

## 🚀 Tezkor ishga tushirish

### Docker bilan (tavsiya etiladi)

```bash
git clone https://github.com/akmalzokirjonov/all-saver-bot.git
cd all-saver-bot
cp .env.example .env
nano .env   # BOT_TOKEN va ADMIN_IDS ni kiriting

docker-compose up -d --build
```

Loglarni ko'rish:
```bash
docker-compose logs -f bot
```

### Lokal ishga tushirish

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Redis ishga tushirish
docker run -d -p 6379:6379 redis:7-alpine

# .env faylida: REDIS_URL=redis://localhost:6379/0
python main.py
```

## Buyruqlar

| Buyruq | Tavsif |
|---|---|
| `/start` | Botni boshlash |
| `/help` | Yordam |
| `/language` | Tilni o'zgartirish |
| `/cookies` | Shaxsiy kontent uchun cookies yuklash |
| `/deletecookies` | Saqlangan cookies o'chirish |
| `/myfiles` | Yuklangan fayllarni boshqarish |
| `/stats` | Statistika *(faqat admin)* |

## 🍪 Cookies (Shaxsiy kontent)

Shaxsiy Instagram reels, TikTok videolarini yuklab olish uchun:

1. Chrome kengaytmasini o'rnating: **Get cookies.txt LOCALLY**
2. Saytga kiring (Instagram, TikTok va h.k.)
3. Kengaytmani bosing → Export cookies → `.txt` sifatida saqlang
4. Botga `/cookies` yuboring → `.txt` faylni yuboring

Cookies **30 kun** saqlanadi.
