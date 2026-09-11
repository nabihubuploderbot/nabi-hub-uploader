# 🚀 Nabi Hub | Uploader — Telegram File Uploader Bot

A professional, scalable Telegram file uploader bot built with **aiogram 3.x**, **PostgreSQL**, **Redis**, and deployable on **Railway**.

## ✨ Features

- **File Upload**: Single file, bulk/album upload, direct link upload
- **Force Join & Reaction Lock**: Channel membership and reaction requirements
- **Advanced Admin Panel**: Glass-button inline keyboards, full management
- **Broadcast System**: Redis-queued broadcast with progress reports
- **Multi-language**: Full Farsi support with i18n
- **FSM**: Finite State Machine for multi-step workflows
- **Rate Limiting**: Redis-backed rate limiting middleware
- **Webhook & Long Polling**: Configurable deployment modes

---

## 📁 Project Structure

```
nabi-hub-uploader/
├── main.py                  # Entry point
├── config.py                # Pydantic Settings
├── requirements.txt
├── Dockerfile
├── railway.json
├── .env.example
├── README.md
│
├── models/
│   ├── __init__.py
│   ├── base.py              # SQLAlchemy Base & engine
│   ├── user.py              # User model
│   ├── file.py              # File model
│   ├── admin.py             # Admin model
│   ├── channel.py           # Channel lock model
│   ├── reaction_lock.py     # Reaction lock model
│   ├── setting.py           # Bot settings model
│   └── broadcast.py         # Broadcast log model
│
├── handlers/
│   ├── __init__.py
│   ├── start.py             # /start + deep link
│   ├── upload.py            # File upload handlers
│   ├── admin_panel.py       # Admin panel navigation
│   ├── admin_settings.py    # Settings handlers
│   ├── admin_broadcast.py   # Broadcast handlers
│   ├── admin_files.py       # File management
│   ├── admin_users.py       # User management
│   ├── force_join.py        # Force join check
│   └── reaction_lock.py     # Reaction lock check
│
├── middlewares/
│   ├── __init__.py
│   ├── auth.py              # Admin auth middleware
│   ├── throttle.py          # Rate limit middleware
│   ├── force_join.py        # Force join middleware
│   ├── db.py                # Database session middleware
│   └── i18n.py              # Internationalization middleware
│
├── keyboards/
│   ├── __init__.py
│   ├── inline.py            # All inline keyboards
│   └── reply.py             # Reply keyboards
│
├── services/
│   ├── __init__.py
│   ├── file_service.py      # File CRUD operations
│   ├── user_service.py      # User CRUD operations
│   ├── admin_service.py     # Admin operations
│   ├── broadcast_service.py # Broadcast queue management
│   ├── channel_service.py   # Channel lock operations
│   └── setting_service.py   # Settings management
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py           # Utility functions
│   ├── deep_link.py         # Deep link generator/decoder
│   └── telegram.py          # Telegram API helpers
│
└── locales/
    ├── fa.json              # Farsi translations
    └── en.json              # English translations
```

---

## 🔧 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Telegram Bot Token |
| `MAIN_ADMIN_ID` | ✅ | Main admin Telegram user ID |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `REDIS_URL` | ✅ | Redis connection string |
| `WEBHOOK_URL` | ❌ | Public webhook URL (e.g., `https://your-app.up.railway.app`) |
| `SECRET_TOKEN` | ❌ | Webhook secret token |
| `USE_WEBHOOK` | ❌ | Set `true` to use webhook mode |
| `WEBHOOK_PATH` | ❌ | Webhook path (default: `/webhook`) |
| `WEBAPP_HOST` | ❌ | Webhook server host (default: `0.0.0.0`) |
| `WEBAPP_PORT` | ❌ | Webhook server port (default: `8000`) |

---

## 🚀 Railway Deployment

### Step 1: Prepare

1. Fork/clone this repo
2. Create a Railway account at [railway.app](https://railway.app)

### Step 2: Add Services

1. **PostgreSQL**: Add a PostgreSQL service from Railway templates
2. **Redis**: Add a Redis service from Railway templates

### Step 3: Deploy

1. Create a new project → Deploy from GitHub repo
2. Add environment variables from `.env.example`
3. Railway auto-detects the `Dockerfile` and deploys

### Step 4: Set Webhook (Optional)

If using webhook mode, set `USE_WEBHOOK=true` and `WEBHOOK_URL` to your Railway public URL.

---

## 💻 Local Development

```bash
# Clone the repo
git clone <your-repo-url>
cd nabi-hub-uploader

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill environment variables
cp .env.example .env
# Edit .env with your values

# Run with Docker Compose (recommended for local)
docker-compose up -d  # starts PostgreSQL + Redis

# Run the bot
python main.py
```

---

## 📝 License

MIT License — Free to use and modify.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first.
