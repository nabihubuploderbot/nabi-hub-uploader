# 🤖 Nabi Hub | Uploader

ربات آپلودر فایل تلگرام — حرفه‌ای، مقیاس‌پذیر و آمادهٔ استقرار روی Railway.

## ✨ امکانات

- **آپلود تک‌فایل** (سند، عکس، ویدیو، صدا، ویس، گیف) با کپشن اختصاصی
- **آپلود گروهی/آلبومی** — چند فایل پشت هم + `/done` (بافر هوشمند media_group)
- **آپلود از لینک مستقیم** (تا ۲۰ مگابایت - محدودیت Bot API)
- **لینک دیپ‌لینک یکتا** برای هر فایل و هر آلبوم: `https://t.me/bot?start=CODE`
- **قفل عضویت اجباری** در چند کانال عمومی/خصوصی + دکمهٔ «بررسی مجدد»
- **قفل واکنش (Reaction Lock)** — کاربر باید روی پست مشخصی واکنش بزند
- **پنل مدیریت کامل Inline** (تنظیمات کلی، پیشرفته، آپلود، آمار، متون، فایل‌ها، کاربران)
- **ارسال همگانی (Broadcast) و فوروارد همگانی** با کنترل نرخ و گزارش پیشرفت
- **مدیریت ادمین‌ها** با محافظت ادمین اصلی
- **پسورد سراسری و پسورد اختصاصی فایل**
- **تایمر ارسال**، روشن/خاموش کردن ربات، کانال ثبت و گروه
- **آمار کامل**: کاربران، فایل‌ها، آلبوم‌ها، ادمین‌ها، دانلودها، کاربران ۲۴ ساعت اخیر
- Webhook (aiohttp) یا Long Polling — قابل تنظیم با `WEBHOOK_URL`
- PostgreSQL + SQLAlchemy 2.0 Async | Redis برای FSM و صف | Loguru

## 📁 ساختار پروژه

```
nabi-hub/
├── main.py                     # نقطهٔ ورود (Polling/Webhook)
├── requirements.txt
├── Dockerfile
├── railway.json
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── script.py.mako
├── .env.example
└── app/
    ├── config.py               # دسترسی یکپارچه به تنظیمات
    ├── core/
    │   ├── settings.py         # pydantic-settings
    │   ├── log.py              # Loguru
    │   ├── db.py               # SQLAlchemy Async
    │   ├── redis.py            # Redis + FSM storage
    │   ├── bot_instance.py     # Bot + DefaultBotProperties
    │   ├── dispatcher.py       # ویرایش روترها و میدلورها
    │   └── handlers_setup.py   # ثبت دستورات منو
    ├── middlewares/
    │   ├── throttling.py       # Rate limit
    │   ├── user_upsert.py      # ثبت/به‌روزرسانی کاربر + چک روشن بودن
    │   ├── admin.py            # فلگ ادمین + فیلتر روتر ادمین
    │   └── force_join.py       # قفل جوین + قفل واکنش
    ├── models/                 # ORM: User, File, Album, Admin, Channel, ...
    ├── services/               # Business logic
    ├── handlers/
    │   ├── admin/              # panel, general_settings, advanced, locks,
    │   │                       # broadcast, upload, texts, stats, files, users
    │   └── user/               # start, download, upload, reactions
    ├── keyboards/              # Inline keyboards (پنل، قفل‌ها، فایل‌ها، ...)
    ├── states/                 # FSM states
    ├── locales/fa.py           # متن‌های فارسی
    └── utils/                  # helpers, pagination
```

## ⚙️ متغیرهای محیطی

| متغیر | الزامی | توضیح |
|---|---|---|
| `BOT_TOKEN` | ✅ | توکن ربات از @BotFather |
| `MAIN_ADMIN_ID` | ✅ | شناسهٔ عددی ادمین اصلی |
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://...` (Railway خودش می‌دهد) |
| `REDIS_URL` | ➖ | برای FSM پایدار و صف (بدون آن حافظهٔ رم) |
| `WEBHOOK_URL` | ➖ | اگر ست شود، Webhook به‌جای Polling |
| `SECRET_TOKEN` | ➖ | امنیت وب‌هوک |
| `WEBAPP_PORT` | ➖ | پیش‌فرض 8080 |

## 🚀 استقرار روی Railway (گام‌به‌گام)

1. ریپو را روی GitHub پوش کنید.
2. در Railway → **New Project** → **Deploy from GitHub repo**.
3. Railway به‌طور خودکار `Dockerfile` و `railway.json` را می‌شناسد.
4. سرویس **PostgreSQL** و (اختیاری) **Redis** را به پروژه اضافه کنید.
5. در تب **Variables** این‌ها را ست کنید:
   - `BOT_TOKEN` → توکن ربات
   - `MAIN_ADMIN_ID` → شناسهٔ عددی شما
   - `DATABASE_URL` → `${{Postgres.DATABASE_URL}}` (رفرنس سرویس)
   - `REDIS_URL` → `${{Redis.REDIS_URL}}`
6. Deploy بزنید. لاگ‌ها باید `🚀 در حال راه‌اندازی` و سپس `▶ شروع Polling` را نشان دهند.
7. در ربات `/start` بزنید و `/panel` برای پنل مدیریت.

### اجرای محلی (تست)
```bash
pip install -r requirements.txt
cp .env.example .env   # مقادیر را پر کنید (DATABASE_URL می‌تواند sqlite+aiosqlite باشد)
python main.py
```

## ⚠️ محدودیت‌های تلگرام (مهم)

- **قفل واکنش قابل Poll نیست**: ربات فقط از طریق آپدیت `message_reaction` می‌فهمد که کاربر واکنش زده — این ربات آن را خودکار در `allowed_updates` ثبت می‌کند. برای کانال‌های خصوصی باید لینک پست را به‌صورت `https://t.me/channel/123` بدهید یا پست را فوروارد کنید.
- **جوین اجباری کانال خصوصی**: ربات باید در آن کانال **ادمین** باشد تا `getChatMember` کار کند.
- **آپلود از لینک**: Bot API فقط تا **۲۰ مگابایت** دانلود دارد (محدودیت رسمی تلگرام).
- **آلبوم‌ها**: تلگرام فایل‌های آلبوم را در چند آپدیت جدا می‌فرستد؛ این ربات با بافر `media_group_id` و تأخیر ۲ ثانیه‌ای آن‌ها را یکجا ثبت می‌کند.

## 🔧 پیشنهادهای توسعهٔ بعدی

- صف Broadcast واقعی با Redis Queue + Worker جدا برای صدها هزار کاربر
- کوتاه‌کنندهٔ لینک داخلی و QR Code برای لینک فایل‌ها
- پشتیبانی چندزبانهٔ کامل (fa/en/ar) با.middleware زبان
- Web App تلگرام برای پنل مدیریتی گرافیکی
- Backup خودکار روزانهٔ دیتابیس به کانال ذخیره
- سیستم شمارش دانلود با نمودار روند هفتگی
- کش لینک دعوت خصوصی کانال‌ها با TTL در Redis
