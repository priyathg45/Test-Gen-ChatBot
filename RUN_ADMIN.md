# How to Run the Genesis Admin System

The newly created Admin system consists of two separate components:
1. **Admin Backend** (runs on port `5001`)
2. **Admin Frontend** (runs on port `5173`)

Both systems run alongside your main application without interfering. 

---

## 1. Running the Admin Backend

The admin backend uses Python and Flask, and connects to your existing MongoDB cluster to access user and chat data.

1. Open a new terminal.
2. Navigate to the `adminbackend` directory:
   ```bash
   cd "D:\Genesis IT Lab\Test-Gen-ChatBot\adminbackend"
   ```
3. Activate the virtual environment:
   ```bash
   .\venv\Scripts\Activate.ps1
   ```
4. Start the Flask server:
   ```bash
   python -m src.api.app
   ```
   *You should see a message indicating it is running on `http://0.0.0.0:5001`.*

---

## 2. Running the Admin Frontend

The admin frontend uses React with Vite for lightning-fast premium rendering.

1. Open a second, separate terminal.
2. Navigate to the `adminfrontend` directory:
   ```bash
   cd "D:\Genesis IT Lab\Test-Gen-ChatBot\adminfrontend"
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *You should see a message indicating the server is available at `http://localhost:5173/`.*

---

## 3. Accessing the System

Once both servers are running:
1. Open your web browser and go to `http://localhost:5173`.
2. You will be greeted by the secure **Admin Login** page.
3. Log in with the default credentials:
   - **Username**: `admin`
   - **Password**: `admin123`

You will then have access to the Dashboard, User Management, System Logs, and the AI Ops Assistant.
