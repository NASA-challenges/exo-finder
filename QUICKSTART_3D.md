# 🚀 Quick Start Guide - 3D Multi-Planet Systems

## Prerequisites
- Python 3.8+ with Flask backend running
- Node.js 14+ with npm
- CSV data files in `nasa-backend/data/`:
  - `kepler_koi.csv`
  - `k2_candidates.csv`
  - `tess_toi.csv`

## Setup & Run (5 minutes)

### Step 1: Install Frontend Dependencies
```bash
cd nasa-frontend
npm install
```

This will install Three.js and other required packages.

### Step 2: Start Backend (Terminal 1)
```bash
cd nasa-backend
python app.py
```

**Expected Output:**
```
🚀 Starting NASA Exoplanet Detection API...
📂 Data directory: C:\Users\...\nasa-backend\data
✅ Kepler data: Found
✅ TESS data: Found
✅ K2 data: Found
 * Running on http://127.0.0.1:5000
```

### Step 3: Start Frontend (Terminal 2)
```bash
cd nasa-frontend
npm start
```

Browser will automatically open to `http://localhost:3000`

## Using the 3D Visualization

1. **Click** the "Explore NASA Data" main tab
2. **Click** the "3D Systems" sub-tab
3. **View** multi-planet systems in 3D!

### What You'll See:
- Real multi-planet systems from your CSV data
- Animated planets orbiting their stars
- Color-coded by planet type (rocky, gas giant, etc.)
- Mission badges (Kepler/K2)
- Planet legends with sizes

### Controls:
- The camera auto-rotates for a cinematic view
- Hover over system cards for highlights
- Scroll to see more systems

## Verification Checklist

✅ Backend shows: `✅ Found X multi-planet systems`  
✅ Frontend shows systems grid in 3D Systems tab  
✅ Planets are orbiting smoothly  
✅ Colors match planet types  
✅ Mission badges appear (Kepler/K2)  

## Troubleshooting

### Backend Issues
**Problem:** `FileNotFoundError: kepler_koi.csv`  
**Solution:** Ensure CSV files are in `nasa-backend/data/` folder

**Problem:** `No multi-planet systems found`  
**Solution:** Check CSV files contain confirmed planets with disposition='CONFIRMED'

### Frontend Issues
**Problem:** `Cannot find module 'three'`  
**Solution:** Run `npm install` again in nasa-frontend directory

**Problem:** Black/empty 3D canvas  
**Solution:** Check browser console for WebGL errors, try refreshing

**Problem:** No systems showing  
**Solution:** Backend should fallback to TRAPPIST-1 and Kepler-90 if CSV data unavailable

## Testing the API Directly

```bash
# Test multi-planet systems endpoint
curl http://127.0.0.1:5000/api/exoplanets/multi-planet-systems

# Expected response: JSON array of systems with planets
```

## Next Steps

- Explore different multi-planet systems
- Compare orbital architectures
- Notice how closer planets orbit faster (Kepler's laws!)
- Read `3D_VISUALIZATION_IMPLEMENTATION.md` for full technical details

---

**Need Help?**
Check the full implementation guide in `3D_VISUALIZATION_IMPLEMENTATION.md`

**Enjoy exploring the cosmos! 🌌🪐✨**
