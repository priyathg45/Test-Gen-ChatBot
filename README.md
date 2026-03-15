# Test-Gen-ChatBot

Full-stack aluminum products chatbot with React frontend and Flask backend (auth, admin, chat).

## Run both backend and frontend

Use **two terminals**: one for the backend, one for the frontend.

### Terminal 1 – Backend (Flask API, port 5000)

**Option A – run script (from repo root):**
```powershell
.\backend\run.ps1
```

**Option B – manual:**
```powershell
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
python -m src.api.app
```

- API: **http://localhost:5000**
- Needs MongoDB (or set `USE_MONGO=false` and use CSV-only mode).

### Terminal 2 – Frontend (React, port 3000)

**Option A – run script (from repo root):**
```powershell
.\frontend\run.ps1
```

**Option B – manual:**
```powershell
cd frontend
npm install
npm run dev
```

- App: **http://localhost:3000**
- Uses backend at `http://localhost:5000` (set `REACT_APP_CHAT_API_URL` in `.env` if your backend is on another URL).

### Quick check

1. **Start the backend first**, then start the frontend.
2. Backend: open **http://localhost:5000/health** → should return `{"status":"healthy",...}`. In the backend terminal you should see `>>> API GET /health` and `<<< API GET /health -> 200` when you hit that URL.
3. Frontend: open **http://localhost:3000** → use **Register** or **Sign In**. In the backend terminal you should see `>>> API POST /auth/register` (or `/auth/login`) and a response line. In the browser console (F12) you should see `[API] POST /auth/register` and `[API] 200 /auth/register` on success.

**If you see "Failed to fetch" or "Cannot reach the server":**
- Ensure the backend is running in a separate terminal (you should see "Running on http://0.0.0.0:5000" or similar).
- Restart the frontend after pulling (so the proxy in `package.json` is active). Do not set `REACT_APP_CHAT_API_URL` in frontend `.env` unless your backend is on a different URL.

### First admin user

To create an admin account on first run, set in `backend/.env` (or your shell):

- `INIT_ADMIN_EMAIL=admin@example.com`
- `INIT_ADMIN_PASSWORD=your-secure-password`

Then start the backend once; remove these after the first run if you prefer.