# Run Backend + Frontend Together

## Quick overview

| Part      | Tech           | Port | Purpose |
|----------|----------------|------|---------|
| **Backend** | Python, Flask | 5000 | Chat API, product data, embeddings, optional MongoDB |
| **Frontend** | React (CRA)   | 3000 | AAW website + floating chatbot that calls backend |

The frontend chatbot sends `POST /chat` to `http://localhost:5000` (configurable via `REACT_APP_CHAT_API_URL`).

---

## 1. Backend (run first)

### Prerequisites
- Python 3.8+
- Optional: MongoDB (for history/attachments); app can fall back to CSV + in-memory history

### Option A: One-click (Windows)

From the **project root** (or anywhere), double‑click or run:

```bat
backend\run_backend.bat
```

Or from a terminal (project root):

```bat
cd "D:\Genesis IT Lab\Test-Gen-ChatBot\backend"
run_backend.bat
```

The script creates `venv` if missing, installs deps, and starts the API.

### Option B: Manual steps

**If your terminal is already in the `backend` folder** (e.g. `PS D:\...\Test-Gen-ChatBot\backend>`), do **not** run `cd backend` again (that would try to open `backend\backend` and fail). Run:

```powershell
# Create venv (only first time)
python -m venv venv

# Activate (PowerShell)
.\venv\Scripts\Activate.ps1

# If Activate.ps1 is disabled, use Command Prompt (cmd) and run: venv\Scripts\activate.bat

# Install deps (only first time)
pip install -r requirements.txt

# Start API
python -m src.api.app
```

**If you start from the project root**, first go into backend:

```powershell
cd "D:\Genesis IT Lab\Test-Gen-ChatBot\backend"
```

Then run the same venv/activate/pip/python commands as above.

Optional: copy `backend\.env.example` to `backend\.env` and set `DATA_PATH`, `MONGO_URI`, etc. Defaults work for local CSV.

You should see the app listen on **http://localhost:5000**. First run may download ML models (sentence-transformers); health: **http://localhost:5000/health**.

---

## 2. Frontend

### Prerequisites
- Node.js 18+ and npm

### Steps

```bash
cd frontend
npm install
```

### Start dev server

```bash
npm start
```

Browser should open **http://localhost:3000**. The floating chat widget calls the backend at `http://localhost:5000` by default.

To use another backend URL, create `frontend/.env`:

```
REACT_APP_CHAT_API_URL=http://localhost:5000
```

---

## 3. Run both (two terminals)

**Terminal 1 – Backend**

```bash
cd backend
venv\Scripts\activate
python -m src.api.app
```

**Terminal 2 – Frontend**

```bash
cd frontend
npm start
```

Then open http://localhost:3000 and use the chat; replies come from the backend.

---

## Backend summary

- **Entry (API):** `backend/src/api/app.py` — Flask app, CORS enabled, port 5000.
- **Entry (CLI):** `backend/src/main.py` — interactive terminal chatbot (no HTTP).
- **Data:** CSV under `backend/data/` (e.g. `aluminum_products.csv` or preprocessed); optional MongoDB for history/attachments.
- **Endpoints:** `GET /`, `GET /health`, `POST /chat`, `GET /history`, `POST /clear-history`, `GET /stats`, `GET /products`, `POST /upload`, etc.

## Frontend summary

- **Entry:** `frontend/src/index.js` → `App.js` (React Router + Layout).
- **Chat:** `frontend/src/shared/Chatbot.js` — POSTs to `CHAT_API_URL/chat` with `message` and `session_id`; shows reply or error.
- **Config:** `frontend/src/config.js` — `CHAT_API_URL` from env or `http://localhost:5000`.
