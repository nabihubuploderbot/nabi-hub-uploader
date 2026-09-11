# 📖 راهنمای نصب و راه‌اندازی — Nabi Hub | Uploader

## گام ۱: پیش‌نیازها

- Python 3.11 یا بالاتر
- PostgreSQL (از Railway یا محلی)
- Redis (از Railway یا محلی)
- توکن ربات تلگرام از [@BotFather](https://t.me/BotFather)

## گام ۲: کلون پروژه

```bash
git clone <your-repo-url>
cd nabi-hub-uploader
```

## گام ۳: محیط مجازی

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

## گام ۴: نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

## گام ۵: تنظیم متغیرهای محیطی

```bash
cp .env.example .env
```

سپس فایل `.env` را ویرایش کنید:

```env
BOT_TOKEN=your-bot-token-from-botfather
MAIN_ADMIN_ID=your-telegram-user-id
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379/0
```

## گام ۶: راه‌اندازی محلی (با Docker Compose)

```bash
docker-compose up -d
```

این دستور PostgreSQL و Redis را به صورت محلی راه‌اندازی می‌کند.

## گام ۷: اجرای ربات

```bash
python main.py
```

---

## 🚀 استقرار روی Railway

### ۱. ساخت پروژه در Railway

1. به [railway.app](https://railway.app) بروید
2. یک پروژه جدید بسازید
3. از گزینه **Deploy from GitHub Repo** استفاده کنید

### ۲. افزودن سرویس‌ها

1. **PostgreSQL**: از بخش Templates، PostgreSQL را اضافه کنید
2. **Redis**: از بخش Templates، Redis را اضافه کنید

### ۳. تنظیم متغیرهای محیطی

در بخش Variables سرویس ربات، متغیرهای زیر را اضافه کنید:

| متغیر | مقدار |
|---|---|
| `BOT_TOKEN` | توکن ربات از BotFather |
| `MAIN_ADMIN_ID` | آیدی عددی شما |
| `DATABASE_URL` | از سرویس PostgreSQL کپی کنید |
| `REDIS_URL` | از سرویس Redis کپی کنید |
| `USE_WEBHOOK` | `true` |
| `WEBHOOK_URL` | URL عمومی Railway |
| `SECRET_TOKEN` | یک رشته تصادفی امن |

### ۴. استقرار

Railway به صورت خودکار Dockerfile را شناسایی و دیپلوی می‌کند.

### ۵. تنظیم Webhook

پس از استقرار موفق، ربات به صورت خودکار webhook را تنظیم می‌کند.

---

## 🔧 دستورات مدیریتی

| دستور | توضیح |
|---|---|
| `/start` | شروع ربات |
| `/help` | راهنما |
| `/admin` | پنل مدیریت |
| `/stats` | آمار ربات |
| `/channels` | لیست کانال‌های قفل |
| `/admins` | لیست ادمین‌ها |
| `/addadmin <id>` | افزودن ادمین |
| `/removeadmin <id>` | حذف ادمین |
| `/addchannel <id>` | افزودن کانال قفل |
| `/removechannel <id>` | حذف کانال قفل |
| `/addreaction` | افزودن قفل واکنش |
| `/setwelcome` | تنظیم پیام خوش‌آمدگویی |
| `/setcaption` | تنظیم کپشن |
| `/setdelay <sec>` | تنظیم تایمر |
| `/setpassword <pass>` | تنظیم پسورد |
| `/clearpassword` | حذف پسورد |
| `/setbtn <text> <url>` | تنظیم دکمه |
| `/togglebtn` | فعال/غیرفعال دکمه |

---

## 📊 معماری پروژه

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Telegram    │────▶│   main.py    │────▶│  Dispatcher │
│  Updates     │     │   (entry)    │     │  (aiogram)  │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                    ┌───────────────────────────┼───────────────────────┐
                    │                           │                       │
              ┌─────▼─────┐             ┌───────▼───────┐      ┌───────▼───────┐
              │Middleware  │             │   Handlers    │      │   Services    │
              │- db        │             │- start        │      │- user         │
              │- throttle  │             │- upload       │      │- file         │
              │- force_join│             │- admin_panel  │      │- admin        │
              │- auth      │             │- broadcast    │      │- broadcast    │
              │- i18n      │             │- files        │      │- channel      │
              └────────────┘             │- users        │      │- setting      │
                                         └───────────────┘      └───────┬───────┘
                                                                        │
                    ┌───────────────────────────────────────────────────┘
                    │
              ┌─────▼─────┐         ┌─────────────┐
              │  Models    │         │   Redis     │
              │ (SQLAlchemy)│        │  (Cache)    │
              └─────┬──────┘         └─────────────┘
                    │
              ┌─────▼──────┐
              │ PostgreSQL  │
              │ (Database)  │
              └────────────┘
```

---

## ⚡ پیشنهادات بهبود

### ۱. امنیت
- رمزنگاری توکن‌ها و file_id در دیتابیس
- محدودیت دسترسی بر اساس IP
- لاگ تمام عملیات حساس

### ۲. مقیاس‌پذیری
- استفاده از Celery برای صف‌های سنگین
- شارد کردن دیتابیس
- Load Balancer برای چند نمونه ربات

### ۳. قابلیت‌های اضافی
- پرداخت درون‌رباتی (Telegram Payments)
- سیستم اشتراک VIP
- آپلود فایل از Google Drive/Dropbox
- تبدیل فرمت فایل
- فشرده‌سازی خودکار ویدیو
- سیستم رفرال و امتیازدهی
- پنل وب برای مدیریت
- API REST برای دسترسی خارجی

### ۴. مانیتورینگ
- اتصال به Sentry برای error tracking
- Prometheus + Grafana برای مانیتورینگ
- Health check endpoint
- Uptime monitoring

---

## 🐛 عیب‌یابی

### خطا: "connection refused"
- مطمئن شوید PostgreSQL و Redis در حال اجرا هستند
- آدرس و پورت را در `.env` بررسی کنید

### خطا: "unauthorized"
- توکن ربات را از BotFather بررسی کنید
- مطمئن شوید توکن صحیح است

### خطا: "database does not exist"
- دیتابیس را به صورت دستی بسازید یا از Railway template استفاده کنید

---

## 📝 نکات مهم

1. **MAIN_ADMIN_ID**: حتماً آیدی عددی خودتان را در متغیر `MAIN_ADMIN_ID` قرار دهید
2. **Webhook**: برای محیط production حتماً از webhook استفاده کنید
3. **Backups**: از دیتابیس به صورت منظم بکاپ بگیرید
4. **Logs**: لاگ‌ها را در `logs/bot.log` بررسی کنید

---

ساخته شده با ❤️ برای جامعه تلگرام فارسی‌زبان
