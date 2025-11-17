# 🚀 Setup Instructions - Draft Analyzer

Complete setup guide for the League of Legends Draft Analyzer with React frontend and FastAPI backend.

---

## Prerequisites

You need to install these before proceeding:

### 1. Python 3.8 or higher

- **Download**: <https://www.python.org/downloads/>
- **Installation**: Check "Add Python to PATH" during installation
- **Verify**: Open PowerShell and run `python --version`

### 2. Node.js 16 or higher

- **Download**: <https://nodejs.org/> (LTS version recommended)
- **Installation**: Use default settings
- **Verify**: Open PowerShell and run `node --version` and `npm --version`

---

## Installation Steps

### Step 1: Install Python Dependencies

Open PowerShell in the project directory:

```powershell
cd C:\Users\marin\Desktop\Draft_Analyzer_Project

# Install required packages
pip install pandas numpy scikit-learn fastapi uvicorn pydantic
```

**Expected output**: All packages installed successfully without errors.

---

### Step 2: Install React Dependencies

```powershell
# Navigate to frontend directory
cd frontend

# Install all Node.js packages
npm install

# Go back to project root
cd ..
```

**Expected output**:

- `node_modules/` folder created in `frontend/`
- `package-lock.json` created
- No errors (warnings are okay)

**This will take 2-3 minutes** as npm downloads ~200 packages.

---

### Step 3: Verify Data Files

Check that these files exist:

```powershell
# Champion data (should exist)
Test-Path "data\processed\champion_archetypes.json"
# Output: True

# Trained models (should exist)
Test-Path "data\simulations\trained_models.pkl"
# Output: True

# Frontend copy of champion data (should exist after earlier copy)
Test-Path "frontend\public\champion_archetypes.json"
# Output: True
```

If any show `False`, the file is missing. The champion data should have been copied earlier, but verify it's there.

---

## Running the Application

You need **TWO terminal windows** open simultaneously.

### Terminal 1: Backend API

```powershell
cd C:\Users\marin\Desktop\Draft_Analyzer_Project

# Start FastAPI server
python backend/draft_api.py
```

**Expected output**:

```text
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**API Endpoints available at**:

- `http://localhost:8000/` - Basic status ping
- `http://localhost:8000/health` - Health metrics (model load state, telemetry backlog, last calibration timestamp)
- `http://localhost:8000/champions` - List all champions
- `http://localhost:8000/draft/analyze` - Analyze 5v5 composition
- `http://localhost:8000/draft/recommend` - Get AI recommendations
- `http://localhost:8000/archetypes` - List all archetypes

**Leave this terminal running!**

---

### Terminal 2: React Frontend

Open a NEW PowerShell window:

```powershell
cd C:\Users\marin\Desktop\Draft_Analyzer_Project\frontend

# Start React dev server
npm start
```

**Expected output**:

```text
Compiled successfully!

You can now view draft-analyzer in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

**Your browser will automatically open** to `http://localhost:3000`.

**Leave this terminal running!**

---

## Using the Draft Board

### Interface Overview

1. **Left Panel**: Draft Board (5v5 picks + bans)
2. **Right Top**: AI Recommendations (top 5 champions)
3. **Right Bottom**: Champion Selector (search/pick)
4. **Bottom**: Analysis Panel (appears after 5v5 complete)

### Draft Workflow

#### Step 1: Select Side

- Click **"Blue Side"** or **"Red Side"** button at top
- Current team indicator shows at top of draft board

#### Step 2: Follow the Guided Phase

- The phase chip in the controls bar now announces whether the lobby is in **Pick** or **Ban** plus the exact turn (B1, R1, etc.).
- Draft order auto-advances through the LCS sequence, so you always know whose turn it is without toggling buttons.
- During ban turns, the new Ban Control panel becomes active; during pick turns, the inline slot inputs and recommendation cards unlock automatically.

#### Step 3: Filter by Role (Optional)

- Click role buttons: **TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY**
- Recommendations update to show only that role
- Click **"ALL ROLES"** to reset filter

#### Step 4: Pick/Ban Champion

Two ways to act on your turn:

- **Pick Windows**: Click a recommendation card or type directly into the active slot’s inline selector.
- **Ban Windows**: Use the Ban Control search to find any champion, then click **Ban** or select one of the quick cards.

Champion is added to draft board and turn automatically advances.

#### Step 5: Complete Draft

- Continue alternating picks/bans
- After **10 picks** (5 blue + 5 red), analysis appears

#### Step 6: View Analysis

- **Winner Prediction**: Blue/Red with confidence %
- **Probability Bars**: Visual comparison of win chances
- **Model Consensus**: See predictions from all 3 ML models
- **Archetypal Insights**: Reasoning bullets explaining the prediction
- **Composition Details**: Blue/Red composition types and archetypes

#### Step 7: Start New Draft

- Click **"Reset Draft"** to clear everything

---

## Features Guide

### AI Recommendations

Each recommendation card shows:

- **Rank**: #1-5 based on AI score
- **Champion Name**: e.g., "Lee Sin"
- **Archetype**: e.g., "skirmisher"
- **Score Bar**: Visual representation (0-100%)
- **Reasoning**: Up to 2 bullets explaining why

**How it works**:

- Analyzes current draft state (picks + bans)
- Considers role synergies (e.g., TOP-JUNGLE dive potential)
- Evaluates composition balance (burst, tank, poke, etc.)
- Filters out already picked/banned champions

### Champion Selector

- **Search**: Type to filter champions (e.g., "lee" finds "Lee Sin")
- **Grid**: Shows all available champions
- **Color Coding**:
  - Blue border in Pick mode
  - Red border in Ban mode
- **Click**: Instantly pick/ban that champion

### Ban Control

- **Guided Turns**: Displays the current ban slot (B1-R5) so you always know whose removal is up.
- **Search + Ban**: Type any champion name, hit **Ban**, or click one of the quick cards to lock it instantly.
- **History**: Blue/Red ban rows update live so coaches can confirm the pool at a glance.
- **Availability-Aware**: Only champions still in the pool appear, preventing double bans.

### Analysis Panel

Appears automatically after 5v5 complete.

**Prediction Section**:

- Winner badge (🔵 BLUE TEAM or 🔴 RED TEAM)
- Confidence percentage (how sure the model is)
- Probability bars (blue vs red win chances)
- Model breakdown (logistic, random_forest, gradient_boosting)

**Archetypal Insights**:

- Strategic reasoning (e.g., "Blue has stronger engage with Lee Sin + Thresh")
- Composition analysis (e.g., "Red lacks backline protection")

**Composition Details**:

- **Composition Type**: burst, poke, front_to_back, dive, split_push, pick
- **Archetype Tags**: burst_mage, marksman, engage_tank, etc.

---

## Troubleshooting

### Backend Won't Start

**Problem**: `python: command not found` or `ModuleNotFoundError`

**Solution**:

```powershell
# Check Python installed
python --version

# If not found, install Python from https://www.python.org/downloads/
# Make sure to check "Add Python to PATH"

# Reinstall packages
pip install pandas numpy scikit-learn fastapi uvicorn pydantic
```

---

### Frontend Won't Start

**Problem**: `npm: command not recognized`

**Solution**:

```powershell
# Check Node.js installed
node --version
npm --version

# If not found, install Node.js from https://nodejs.org/
# Choose LTS version

# After installing, close and reopen PowerShell
cd C:\Users\marin\Desktop\Draft_Analyzer_Project\frontend
npm install
```

**Problem**: `ECONNREFUSED` errors in browser console

**Solution**:

- Backend API is not running or crashed
- Start backend in Terminal 1: `python backend/draft_api.py`
- Check `http://localhost:8000/health` shows `predictor_loaded: true` and a recent `generated_at`

---

### No Recommendations Showing

**Problem**: Recommendations panel shows "No recommendations yet"

**Solution**:

1. Make sure you're in **Pick mode** (not Ban mode)
2. Check that API is running: `http://localhost:8000/health` (look for `status: "online"`)
3. Open browser DevTools (F12) → Console tab
4. Look for API errors (red text)
5. Verify champion data loaded: Check if Champion Selector shows champions

---

### Champion Data Not Loading

**Problem**: Champion Selector is empty or says "No champions found"

**Solution**:

```powershell
# Copy champion data to frontend
Copy-Item "data\processed\champion_archetypes.json" "frontend\public\champion_archetypes.json"

# Restart frontend server
# Press Ctrl+C in Terminal 2
cd frontend
npm start
```

---

### Port Already in Use

**Problem**: `Error: listen EADDRINUSE: address already in use :::8000`

**Solution**:

```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill that process (replace <PID> with number from above)
taskkill /PID <PID> /F

# Or change port in backend/draft_api.py (line ~300):
# uvicorn.run(app, host="0.0.0.0", port=8001)  # Change 8000 to 8001

# Also update frontend/package.json proxy:
# "proxy": "http://localhost:8001"
```

---

### Browser Shows Blank Page

**Problem**: `http://localhost:3000` is blank or shows error

**Solution**:

1. Check Terminal 2 for compilation errors
2. Press Ctrl+C to stop frontend
3. Delete cache and restart:

   ```powershell
   cd frontend
   Remove-Item -Recurse -Force node_modules
   npm install
   npm start
   ```

---

## Advanced Configuration

### Change API Port

Edit `backend/draft_api.py` (line ~300):

```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change 8000 to 8001
```

Update `frontend/package.json`:

```json
"proxy": "http://localhost:8001"
```

### Enable CORS (if needed)

Already configured in `backend/draft_api.py`. If you need different origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.1.100:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Production Build

For deployment (not needed for development):

```powershell
cd frontend
npm run build
# Creates optimized production build in frontend/build/
```

---

## Quick Reference

### Start Both Servers (After Initial Setup)

**Terminal 1 (Backend)**:

```powershell
cd C:\Users\marin\Desktop\Draft_Analyzer_Project
python backend/draft_api.py
```

**Terminal 2 (Frontend)**:

```powershell
cd C:\Users\marin\Desktop\Draft_Analyzer_Project\frontend
npm start
```

**Access Application**: `http://localhost:3000`

---

## Architecture Overview

```text
Browser (localhost:3000)
    ↓ HTTP Requests
React Frontend
    ↓ axios (proxied to :8000)
FastAPI Backend
    ↓ Load models
Trained ML Models (.pkl)
    ↓ Make predictions
Ensemble Predictor
    ↓ Return JSON
Frontend Display
```

---

## Performance Notes

- **First pick**: ~100-200ms (cold start)
- **Subsequent picks**: ~50-100ms
- **Analysis (5v5)**: ~150-300ms (ensemble prediction)
- **Champion search**: Instant (client-side)

---

## Data Files Used

| File | Purpose | Size |
|------|---------|------|
| `trained_models.pkl` | 3 ML models (LR, RF, GB) | ~2 MB |
| `champion_archetypes.json` | 171 champions + attributes | ~150 KB |
| `frontend/build/` | Production React app | ~500 KB |

---

## Need Help?

1. Check Terminal 1 for backend errors
2. Check Terminal 2 for frontend errors
3. Check browser console (F12) for client errors
4. Verify all data files exist
5. Try restarting both servers
6. Try clearing browser cache (Ctrl+Shift+Delete)

---

**You're all set! Enjoy drafting with AI-powered recommendations!** 🎮✨

**Theory over meta. Archetypes over win rates.**
