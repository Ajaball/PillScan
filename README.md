# 🏥 PillScan — AI-Powered Medication Identification & Management

**University of Tabuk — Computer Science Department — Graduation Project 2026**

---

## 📋 Overview

PillScan is an AI-powered system designed to identify medications through computer vision and provide comprehensive drug management. It is designed to run efficiently locally for demonstrations and academic presentations.

Pill identification runs entirely on **Google Gemini** (vision-capable LLM) — the backend sends the photo to Gemini, which returns structured candidates that are then matched against the drug database. Up to five Gemini API keys (per-user + server-wide) can be configured with automatic failover.

---

## 📂 Project Structure

This repository contains the following core components allowed for deployment/delivery:
* **`backend/`** — FastAPI web backend implementing user authentication, SQLite database management, and pill scanning routers (identification via Gemini vision LLM).
* **`frontend/`** — Progressive Web App (PWA) built with HTML5, CSS3, and JavaScript, displaying the client dashboard and visual scanning results.

---

## 🚀 Getting Started

### 1. Web Backend Server (`backend`)
The backend provides APIs for authentication, search, and maps the vision-LLM's identification to rich Saudi SFDA-registered drug objects.

```bash
cd backend
python -m venv .venv
# Activate virtual environment
pip install -r requirements.txt

# Seed the database
python -m app.seed

# Start the server on port 8005
python -m uvicorn app.main:app --port 8005 --reload
```

### 📷 Pill Scanning & 📄 Leaflet Summarizer (Vision LLM)

Both pill photo identification and leaflet/prescription summarization
(plain-language **Arabic** summary) run on Gemini.

* **Endpoints:** `POST /api/v1/scan/identify`, `POST /api/v1/leaflet/summarize` (multipart image upload)
* **Screens:** Home → "مسح دواء" / "تلخيص نشرة الدواء" → camera/upload → results page
* **Keys:** set server-wide in `backend/.env`, and/or per-user via the in-app AI Settings page (up to 5 keys, tried in order with automatic failover)

Set at least one key in `backend/.env`:

```bash
GEMINI_API_KEY=your-key-here
# optional additional keys for failover:
# GEMINI_API_KEY_2=...
# GEMINI_API_KEY_3=...
```

If no key is set, both endpoints still respond with a clear setup message
(so the full flow can be demonstrated) instead of failing.

---

## 🆕 الميزات الجديدة (Roles, Approval & Drug Assistant)

### 👤 أدوار المستخدمين وموافقة المدير
* لكل مستخدم **دور** (`role`: `USER` أو `ADMIN`) و**حالة** (`status`: `PENDING` / `APPROVED` / `REJECTED`).
* التسجيل يتطلّب: الاسم + **الجوال (فريد)** + **البريد (فريد)** + كلمة المرور، ويُنشأ الحساب بحالة `PENDING`.
* لا يمكن للمستخدم تسجيل الدخول حتى يوافق عليه المدير:
  * `PENDING` ← «حسابك قيد المراجعة، انتظر موافقة المدير».
  * `REJECTED` ← «تم رفض طلب حسابك».
  * `APPROVED` ← يدخل بنجاح.
* السجلّات القديمة تُرحّل تلقائيًا إلى `APPROVED` عند الإقلاع (بدون فقدان بيانات).
* حساب المدير يُنشأ تلقائيًا من متغيرات البيئة (`ADMIN_EMAIL` / `ADMIN_PHONE` / `ADMIN_PASSWORD`) إن لم يكن موجودًا.
* لترقية مستخدم مسجّل بالفعل إلى مدير (بدل إنشاء واحد من البيئة):
  ```bash
  cd backend && python -m app.make_admin user@example.com
  ```
  يجعل الحساب `role=ADMIN` و`status=APPROVED` (آمن وidempotent، ولا يمسّ كلمة المرور).

### 🛡️ لوحة المدير — `/admin` (مدير فقط)
* عرض الطلبات المعلّقة (الاسم، البريد، الجوال، تاريخ الطلب) مع زرّي **قبول/رفض**.
* جدول بكل المستخدمين وحالاتهم مع إمكانية تغيير الحالة، وتحديث فوري للواجهة.
* **الحماية على الخادم:** كل نقاط النهاية أدناه محمية بدور `ADMIN` وتُرفض أي محاولة من غير مدير من الخادم لا من الواجهة فقط.
  * `GET /api/v1/admin/users?status=PENDING|APPROVED|REJECTED`
  * `PATCH /api/v1/admin/users/{user_id}/status`

### 💊 المساعد الدوائي — `/drug-assistant`
* المستخدم المعتمد يكتب اسم الدواء، ويُستدعى **Gemini** (نفس المفتاح ونفس آلية الـ failover الموجودة) عبر:
  * `POST /api/v1/assistant/drug-info`
* يُعرض الرد في بطاقات منظّمة (دواعي الاستعمال، الجرعة، الآثار الجانبية، موانع الاستعمال، التفاعلات، التخزين، التحذيرات) مع:
  * شريط تنبيه طبّي بارز ودائم أعلى النتيجة.
  * رسالة واضحة «لم يتم التعرف على هذا الدواء بشكل مؤكد» عند `recognized=false`.
  * حالة تحميل واضحة، وتحليل JSON آمن مع fallback عند الفشل.
* مربوط أيضًا من شاشة البحث عن دواء (زر «اسأل المساعد الدوائي»).

### 🔑 متغيرات البيئة المطلوبة
تُضاف إلى `backend/.env` (انظر `backend/.env.example`):

```bash
# حساب المدير (يُنشأ تلقائيًا عند الإقلاع إن لم يوجد)
ADMIN_EMAIL=admin@pillscan.com
ADMIN_PHONE=+966500000000
ADMIN_PASSWORD=admin123
SEED_ON_STARTUP=true

# مفاتيح Gemini (تُستخدم للمساعد الدوائي والتلخيص والتعرّف — نفس المفاتيح)
GEMINI_API_KEY=your-key-here
```

> ملاحظة: لا تُخزَّن أي مفاتيح حقيقية في المستودع — `.env` مستثنى في `.gitignore` و`.env.example` يحوي قيمًا نموذجية فقط.

---

### 2. Web Client (`frontend`)
To view the user dashboard and test image uploads:

```bash
cd frontend
# Serve locally using any basic HTTP server (e.g., live-server, Python http.server, or npm serve)
python -m http.server 3000
```
Then navigate to `http://localhost:3000` in your web browser.

---

## 👥 Academic Team

* **Department:** Computer Science
* **Institution:** University of Tabuk, Kingdom of Saudi Arabia
* **Academic Year:** 2025 - 2026
