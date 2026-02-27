# Shreeji Ceramica — Quotation AI

A full-stack Quotation Management System for Shreeji Ceramica built with **FastAPI** (backend) + **React** (frontend).

## Features
- 📄 Search products from Aquant & Kohler catalogs (PDF-indexed)
- 🛒 Add to cart and create professional quotations
- 📊 Auto-generated Quotation Numbers (SC-YYYYMMDD-XXXX)
- 📤 Share via WhatsApp & Gmail with branded messages
- 📥 Download professional PDF with company logo & branding

---

## 🚀 Deploy on Render

### Step 1 — Fork & Connect
1. Fork/clone this repo to your GitHub
2. Go to [render.com](https://render.com) → **New → Blueprint**
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml`

### Step 2 — Set Backend URL in Frontend
After backend deploys, copy its URL (e.g. `https://quotation-ai-backend.onrender.com`) and set it as:
- Frontend env var: `REACT_APP_API_URL = https://quotation-ai-backend.onrender.com`

### Step 3 — Optional: Email & WhatsApp (via Render Dashboard)
Set these env vars in backend service if needed:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

---

## 🖥️ Local Development

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm start
```

> Frontend runs on `http://localhost:3000`, Backend on `http://localhost:8000`

---

## 📁 Project Structure
```
quotation-ai/
├── backend/
│   ├── main.py            # FastAPI app
│   ├── pdf_reader.py      # PDF catalog parser
│   ├── search_engine.py   # Search logic (FAISS)
│   ├── quotation.py       # PDF quotation generator
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── api.js         # Central API URL config
│   │   └── pages/
│   │       ├── dashboard.jsx
│   │       ├── search.jsx
│   │       └── quotation.jsx
│   └── public/
├── render.yaml            # Render deployment config
└── .gitignore
```
