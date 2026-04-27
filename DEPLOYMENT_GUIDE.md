# 🥛 DudhWala — Complete Deployment Guide

## YOUR FILES
```
dudhwala/
├── main.py              ← Python server (FastAPI + PostgreSQL)
├── requirements.txt     ← Python packages
├── Procfile             ← How Railway starts the app
├── runtime.txt          ← Python version
├── .gitignore           ← Files to exclude from GitHub
└── static/
    └── index.html       ← Complete frontend (all 3 roles)
```

---

## STEP 1 — Install Software on Your Laptop

### Install Python 3.11
→ https://www.python.org/downloads/
✅ During install: tick "Add Python to PATH"

### Install Git
→ https://git-scm.com/downloads
✅ Install with default settings

### Install PostgreSQL
→ https://www.postgresql.org/download/
✅ During install:
   - Set password: remember this (e.g. mypassword123)
   - Port: 5432 (default, don't change)

---

## STEP 2 — Create Local Database

Open "SQL Shell (psql)" — installed with PostgreSQL.
When it asks for password, enter the one you set above.
Then type:

```sql
CREATE DATABASE dudhwala;
\q
```

---

## STEP 3 — Configure Database Connection

Open `main.py` and find this line near the top:

```python
"postgresql://postgres:password@localhost:5432/dudhwala"
```

Replace `password` with your actual PostgreSQL password:

```python
"postgresql://postgres:mypassword123@localhost:5432/dudhwala"
```

---

## STEP 4 — Run Locally

Open terminal / command prompt in your `dudhwala` folder:

```bash
# Install Python packages
pip install -r requirements.txt

# Start the server
python main.py
```

Open browser → http://localhost:8000

✅ App is running! Test everything before deploying.

---

## STEP 5 — Put Code on GitHub

### Create GitHub account
→ https://github.com → Sign up (free)

### Create new repository
1. Click "+" → "New repository"
2. Name: `dudhwala`
3. Keep Public
4. Do NOT add README (you have one)
5. Click "Create repository"
6. Copy the URL shown: `https://github.com/YOURNAME/dudhwala.git`

### Upload your code
Open terminal in your `dudhwala` folder:

```bash
git init
git add .
git commit -m "DudhWala milk delivery app"
git branch -M main
git remote add origin https://github.com/YOURNAME/dudhwala.git
git push -u origin main
```

Enter GitHub username + password when asked.
✅ Refresh GitHub — all files should be there.

---

## STEP 6 — Free Cloud Database (Supabase)

### Create account
→ https://supabase.com → "Start for free" → Sign in with GitHub

### Create project
1. Click "New Project"
2. Name: `dudhwala`
3. Set a Database Password → SAVE IT
4. Region: South Asia (Mumbai)
5. Click "Create new project" — wait ~2 minutes

### Get connection string
1. Go to: Settings → Database
2. Scroll to "Connection string" → URI tab
3. Copy the string (looks like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
4. Replace `[YOUR-PASSWORD]` with your password
5. SAVE THIS STRING — needed in Step 7

---

## STEP 7 — Deploy on Railway (Free Hosting)

### Create account
→ https://railway.app → Login with GitHub

### Deploy
1. Click "New Project"
2. Click "Deploy from GitHub repo"
3. Select your `dudhwala` repository
4. Railway starts deploying automatically (~2 minutes)

### Add database
1. Click your project → "Variables" tab
2. Click "New Variable"
3. Name: `DATABASE_URL`
4. Value: paste your Supabase connection string from Step 6
5. Click "Add" → Railway redeploys automatically

### Get your public URL
1. Go to "Settings" tab
2. Click "Generate Domain"
3. Your app is live at something like:
   `https://dudhwala-production.up.railway.app`

---

## STEP 8 — Test on Multiple Devices

Open your Railway URL on:
- Laptop browser ✅
- Phone browser ✅
- Any device anywhere ✅

All data is shared from the same PostgreSQL database on Supabase.

---

## UPDATING THE APP LATER

Any time you change a file:
```bash
git add .
git commit -m "what I changed"
git push
```
Railway auto-redeploys in ~30 seconds. Done.

---

## LOGIN DETAILS (OTP is always 1234 in demo mode)

| Role     | How to login                              |
|----------|-------------------------------------------|
| Vendor   | Any phone number → OTP 1234              |
| Milkman  | Phone → OTP 1234, OR enter vendor code   |
| Customer | Must be added by Vendor first            |

---

## API DOCUMENTATION
Visit: `https://your-railway-url/api/docs`
Interactive docs — test all endpoints directly in browser.
