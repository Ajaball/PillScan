# 🏥 PillScan — AI-Powered Medication Identification & Management

**University of Tabuk — Computer Science Department — Graduation Project 2026**

---

## 📋 Overview

PillScan is an AI-powered system designed to identify medications through computer vision and provide comprehensive drug management. It is designed to run efficiently locally for demonstrations and academic presentations.

The system uses a **two-stage AI pipeline** consisting of:
1. **YOLOv8** for real-time pill detection and localization.
2. **EfficientNet-V2-S** for pill classification into specific categories.

---

## 📂 Project Structure

This repository contains the following core components allowed for deployment/delivery:
* **`backend/`** — FastAPI web backend implementing user authentication, SQLite database management, and pill scanning routers.
* **`frontend/`** — Progressive Web App (PWA) built with HTML5, CSS3, and JavaScript, displaying the client dashboard and visual scanning results.
* **`ai/`** — Python microservice hosting model loading via ONNX Runtime and training scripts.

---

## 📊 Dataset Reference

The AI models were trained on the **Visual Pill Identification** dataset:
* **Dataset Source:** Roboflow Universe
* **Link:** [Visual Pill Identification Dataset on Roboflow](https://universe.roboflow.com/medgen/visual-pill-identification)
* **Classes:** Includes `antihistamine` (Claritine), `ibuprofen` (Brufen), and `paracetamol` (Panadol Extra).

---

## 🚀 Getting Started

### 1. AI Inference Microservice (`ai`)
The AI service loads the trained ONNX models and exposes a prediction endpoint.

```bash
cd ai
python -m venv .venv
# Activate virtual environment
# Windows: .\.venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn inference.server:app --port 8001
```

### 2. Web Backend Server (`backend`)
The backend provides APIs for authentication, search, and maps the predicted AI classes to rich Saudi SFDA-registered drug objects.

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

### 3. Web Client (`frontend`)
To view the user dashboard and test image uploads with real-time bounding box canvas overlay:

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
