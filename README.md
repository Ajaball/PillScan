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
* **`ai/`** — Legacy local CV model (YOLOv8 + EfficientNet) training/inference code. No longer used by the running app; kept for reference only.

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
