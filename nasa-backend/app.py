from flask import Flask, request, jsonify, send_file
import pandas as pd
import numpy as np
import pickle
from io import BytesIO
from huggingface_hub import hf_hub_download
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Data directory for CSV files
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

print("📡 Loading ML model and dependencies from Hugging Face...")

repo_id = "mihaelaMelnic/kepler-exoplanet-model"

model_path = hf_hub_download(repo_id=repo_id, filename="kepler_xgb_optimized.pkl")
scaler_path = hf_hub_download(repo_id=repo_id, filename="xgb_scaler.pkl")
encoder_path = hf_hub_download(repo_id=repo_id, filename="xgb_label_encoder.pkl")

model = pickle.load(open(model_path, "rb"))
scaler = pickle.load(open(scaler_path, "rb"))
label_encoder = pickle.load(open(encoder_path, "rb"))

print("✅ Model, scaler și encoder încărcate cu succes!")

@app.route("/")
def home():
    return jsonify({
        "status": "✅ Flask backend is running",
        "message": "Ready to receive predictions from React frontend.",
        "endpoints": {
            "prediction": ["/predict", "/batch_predict"],
            "nasa_data": [
                "/api/exoplanets/kepler", 
                "/api/exoplanets/tess", 
                "/api/exoplanets/k2", 
                "/api/exoplanets/summary",
                "/api/exoplanets/multi-planet-systems"
            ],
            "utility": ["/api/health"]
        }
    })

def preprocess_input(data):
    df = pd.DataFrame([data])
    scaled = scaler.transform(df)
    return scaled

def make_prediction(data):
    processed = preprocess_input(data)
    prediction = model.predict(processed)[0]
    proba = model.predict_proba(processed)[0]
    label = label_encoder.inverse_transform([prediction])[0]
    return {"label": label, "probabilities": proba.tolist()}

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        print("🔍 Received single prediction data:", data)
        prediction = make_prediction(data)
        return jsonify(prediction)

    except Exception as e:
        print("❌ Error in /predict:", e)
        return jsonify({"error": str(e)}), 400

@app.route("/batch_predict", methods=["POST"])
def batch_predict():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        df = pd.read_csv(file)

        # Selectăm doar coloanele numerice (caracteristici)
        features = df.select_dtypes(include=[np.number])
        scaled_features = scaler.transform(features)
        preds = model.predict(scaled_features)
        probs = model.predict_proba(scaled_features)

        # Adăugăm rezultatele în fișier
        df["Predicted_Label"] = label_encoder.inverse_transform(preds)
        df["CONFIRMED_Prob"] = probs[:, 0]
        df["CANDIDATE_Prob"] = probs[:, 1]
        df["FALSE_POSITIVE_Prob"] = probs[:, 2]

        # Exportăm rezultatul într-un CSV temporar
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="predicted_results.csv",
            mimetype="text/csv"
        )

    except Exception as e:
        print("❌ Error in /batch_predict:", e)
        return jsonify({"error": str(e)}), 400

# Helper functions for CSV data processing
def safe_float(value):
    """Safely convert to float, return None if invalid"""
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (ValueError, TypeError):
        return None

def extract_year_from_date(date_str):
    """Extract year from various date formats"""
    if pd.isna(date_str):
        return None
    try:
        # Handle YYYY-MM-DD format
        if isinstance(date_str, str) and '-' in date_str:
            return int(date_str.split('-')[0])
        # Handle timestamp
        return int(str(date_str)[:4])
    except:
        return None

@app.route('/api/exoplanets/kepler')
def get_kepler_data():
    """Fetch Kepler KOI data from CSV"""
    try:
        # Read the CSV file
        df = pd.read_csv(
            os.path.join(DATA_DIR, 'kepler_koi.csv'),
            comment='#',  # Skip comment lines starting with #
            low_memory=False
        )
        
        # Filter out rows with missing critical data
        df = df[df['koi_disposition'].notna()]
        
        # Transform to match frontend format
        transformed = []
        for _, row in df.iterrows():
            # Extract discovery year from various date columns
            year = extract_year_from_date(row.get('koi_vet_date'))
            if not year:
                # Fallback: estimate from KOI name or use default
                year = 2011  # Kepler mission prime years
            
            # Normalize disposition names
            disposition = str(row.get('koi_disposition', '')).upper()
            if 'CONFIRMED' in disposition or disposition == 'CONFIRMED':
                disposition = 'CONFIRMED'
            elif 'CANDIDATE' in disposition or disposition == 'CANDIDATE':
                disposition = 'CANDIDATE'
            elif 'FALSE' in disposition or disposition == 'FALSE POSITIVE':
                disposition = 'FALSE POSITIVE'
            else:
                disposition = 'CANDIDATE'
            
            transformed.append({
                'mission': 'Kepler',
                'pl_name': str(row.get('kepoi_name', '')),
                'kepler_name': str(row.get('kepler_name', '')),
                'disposition': disposition,
                'discovery_year': year,
                'pl_orbper': safe_float(row.get('koi_period')),
                'pl_rade': safe_float(row.get('koi_prad')),
                'st_rad': safe_float(row.get('koi_srad')),
                'st_teff': safe_float(row.get('koi_steff')),
                'st_mass': safe_float(row.get('koi_smass')),
                'pl_insol': safe_float(row.get('koi_insol')),
                'pl_eqt': safe_float(row.get('koi_teq')),
                'ra': safe_float(row.get('ra')),
                'dec': safe_float(row.get('dec')),
                'koi_score': safe_float(row.get('koi_score')),
                'disc_facility': 'Kepler'
            })
        
        return jsonify(transformed)
    
    except FileNotFoundError:
        return jsonify({
            'error': 'Kepler data file not found',
            'message': 'Please ensure kepler_koi.csv is in nasa-backend/data/'
        }), 404
    except Exception as e:
        print(f"❌ Error loading Kepler data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/exoplanets/tess')
def get_tess_data():
    """Fetch TESS TOI data from CSV"""
    try:
        df = pd.read_csv(
            os.path.join(DATA_DIR, 'tess_toi.csv'),
            comment='#',
            low_memory=False
        )
        
        # Filter out rows with missing critical data
        df = df[df['tfopwg_disp'].notna()]
        
        transformed = []
        for _, row in df.iterrows():
            # Extract year from TOI creation date
            year = extract_year_from_date(row.get('toi_created'))
            if not year:
                year = 2019  # TESS started discovering in 2018-2019
            
            # Normalize disposition
            disposition = str(row.get('tfopwg_disp', '')).upper()
            if disposition == 'CP':
                disposition = 'CONFIRMED'
            elif disposition == 'PC':
                disposition = 'CANDIDATE'
            elif disposition == 'FP':
                disposition = 'FALSE POSITIVE'
            elif disposition == 'KP':
                disposition = 'CONFIRMED'  # Known Planet
            else:
                disposition = 'CANDIDATE'
            
            transformed.append({
                'mission': 'TESS',
                'pl_name': f"TOI-{row.get('toi', '')}",
                'disposition': disposition,
                'discovery_year': year,
                'pl_orbper': safe_float(row.get('pl_orbper')),
                'pl_rade': safe_float(row.get('pl_rade')),
                'st_rad': safe_float(row.get('st_rad')),
                'st_teff': safe_float(row.get('st_teff')),
                'st_dist': safe_float(row.get('st_dist')),
                'pl_insol': safe_float(row.get('pl_insol')),
                'pl_eqt': safe_float(row.get('pl_eqt')),
                'ra': safe_float(row.get('ra')),
                'dec': safe_float(row.get('dec')),
                'toi': str(row.get('toi', '')),
                'disc_facility': 'TESS'
            })
        
        return jsonify(transformed)
    
    except FileNotFoundError:
        return jsonify({
            'error': 'TESS data file not found',
            'message': 'Please ensure tess_toi.csv is in nasa-backend/data/'
        }), 404
    except Exception as e:
        print(f"❌ Error loading TESS data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/exoplanets/k2')
def get_k2_data():
    """Fetch K2 Planets and Candidates data from CSV"""
    try:
        df = pd.read_csv(
            os.path.join(DATA_DIR, 'k2_candidates.csv'),
            comment='#',
            low_memory=False
        )
        
        # Filter out rows with missing critical data
        df = df[df['disposition'].notna()]
        
        transformed = []
        for _, row in df.iterrows():
            # Extract year from discovery year column
            year = safe_float(row.get('disc_year'))
            if not year or pd.isna(year):
                year = 2015  # K2 mission years
            else:
                year = int(year)
            
            # Normalize disposition
            disposition = str(row.get('disposition', '')).upper()
            if 'CONFIRMED' in disposition:
                disposition = 'CONFIRMED'
            elif 'CANDIDATE' in disposition:
                disposition = 'CANDIDATE'
            elif 'FALSE' in disposition:
                disposition = 'FALSE POSITIVE'
            else:
                disposition = 'CANDIDATE'
            
            transformed.append({
                'mission': 'K2',
                'pl_name': str(row.get('pl_name', '')),
                'k2_name': str(row.get('k2_name', '')),
                'disposition': disposition,
                'discovery_year': year,
                'pl_orbper': safe_float(row.get('pl_orbper')),
                'pl_rade': safe_float(row.get('pl_rade')),
                'st_rad': safe_float(row.get('st_rad')),
                'st_teff': safe_float(row.get('st_teff')),
                'st_mass': safe_float(row.get('st_mass')),
                'pl_insol': safe_float(row.get('pl_insol')),
                'pl_eqt': safe_float(row.get('pl_eqt')),
                'ra': safe_float(row.get('ra')),
                'dec': safe_float(row.get('dec')),
                'disc_facility': 'K2'
            })
        
        return jsonify(transformed)
    
    except FileNotFoundError:
        return jsonify({
            'error': 'K2 data file not found',
            'message': 'Please ensure k2_candidates.csv is in nasa-backend/data/'
        }), 404
    except Exception as e:
        print(f"❌ Error loading K2 data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/exoplanets/summary', methods=['GET'])
def get_summary():
    """Get summary statistics across all missions"""
    try:
        # Load all data
        kepler = pd.read_csv(os.path.join(DATA_DIR, 'kepler_koi.csv'), comment='#')
        tess = pd.read_csv(os.path.join(DATA_DIR, 'tess_toi.csv'), comment='#')
        k2 = pd.read_csv(os.path.join(DATA_DIR, 'k2_candidates.csv'), comment='#')
        
        summary = {
            'kepler': {
                'total': len(kepler),
                'confirmed': len(kepler[kepler['koi_disposition'].str.contains('CONFIRMED', na=False, case=False)]),
                'candidates': len(kepler[kepler['koi_disposition'].str.contains('CANDIDATE', na=False, case=False)]),
                'false_positives': len(kepler[kepler['koi_disposition'].str.contains('FALSE', na=False, case=False)])
            },
            'tess': {
                'total': len(tess),
                'confirmed': len(tess[tess['tfopwg_disp'].isin(['CP', 'KP'])]),
                'candidates': len(tess[tess['tfopwg_disp'] == 'PC']),
                'false_positives': len(tess[tess['tfopwg_disp'] == 'FP'])
            },
            'k2': {
                'total': len(k2),
                'confirmed': len(k2[k2['disposition'].str.contains('CONFIRMED', na=False, case=False)]),
                'candidates': len(k2[k2['disposition'].str.contains('CANDIDATE', na=False, case=False)]),
                'false_positives': len(k2[k2['disposition'].str.contains('FALSE', na=False, case=False)])
            }
        }
        
        return jsonify(summary)
    
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        return jsonify({'error': str(e)}), 500

def assign_planet_color(radius):
    """Assign color based on planet size (Earth radii)"""
    if radius < 1.25:
        return '#e74c3c'  # Rocky planets (red)
    elif radius < 2.0:
        return '#3498db'  # Super-Earth (blue)
    elif radius < 6.0:
        return '#9b59b6'  # Neptune-like (purple)
    elif radius < 12.0:
        return '#f39c12'  # Jupiter-like (orange)
    else:
        return '#1abc9c'  # Large gas giant (teal)

@app.route('/api/exoplanets/multi-planet-systems')
def get_multi_planet_systems():
    """Find multi-planet systems from Kepler and K2 CSV data"""
    try:
        systems = []
        
        # Process Kepler data
        try:
            kepler = pd.read_csv(os.path.join(DATA_DIR, 'kepler_koi.csv'), comment='#', low_memory=False)
            kepler_confirmed = kepler[
                kepler['koi_disposition'].str.contains('CONFIRMED', na=False, case=False)
            ].copy()
            
            # Group by star (extract star ID from KOI name like K00001 from K00001.01)
            star_groups = {}
            for _, row in kepler_confirmed.iterrows():
                kepoi_name = row.get('kepoi_name')
                if pd.notna(kepoi_name) and isinstance(kepoi_name, str) and '.' in kepoi_name:
                    star_id = kepoi_name.split('.')[0]
                    if star_id not in star_groups:
                        star_groups[star_id] = []
                    star_groups[star_id].append(row)
            
            # Build multi-planet systems
            for star_id, planets_data in star_groups.items():
                if len(planets_data) >= 2:  # Multi-planet system
                    planets = []
                    first_planet = planets_data[0]
                    
                    # Get system name
                    kepler_name = first_planet.get('kepler_name')
                    if pd.notna(kepler_name) and isinstance(kepler_name, str) and ' ' in kepler_name:
                        system_name = kepler_name.rsplit(' ', 1)[0]
                    else:
                        system_name = star_id
                    
                    for planet in planets_data:
                        period = safe_float(planet.get('koi_period'))
                        radius = safe_float(planet.get('koi_prad'))
                        sma = safe_float(planet.get('koi_sma'))  # Semi-major axis in AU
                        
                        if period and radius and sma:
                            # Normalize distance for visualization
                            distance = sma * 215  # Scale for visualization
                            
                            kepoi_name = planet.get('kepoi_name', '')
                            planet_letter = kepoi_name.split('.')[-1] if '.' in str(kepoi_name) else str(len(planets) + 1)
                            
                            planets.append({
                                'name': planet_letter,
                                'distance': distance,
                                'size': radius,
                                'period': period,
                                'mass': None,
                                'color': assign_planet_color(radius)
                            })
                    
                    if len(planets) >= 2:
                        systems.append({
                            'name': system_name,
                            'star_temp': safe_float(first_planet.get('koi_steff')) or 5778,
                            'star_radius': safe_float(first_planet.get('koi_srad')) or 1.0,
                            'planet_count': len(planets),
                            'planets': sorted(planets, key=lambda p: p['distance'])[:8],  # Max 8 planets
                            'mission': 'Kepler'
                        })
        except FileNotFoundError:
            print("⚠️ Kepler CSV not found for multi-planet systems")
        except Exception as e:
            print(f"⚠️ Error processing Kepler data: {e}")
        
        # Process K2 data
        try:
            k2 = pd.read_csv(os.path.join(DATA_DIR, 'k2_candidates.csv'), comment='#', low_memory=False)
            k2_confirmed = k2[
                k2['disposition'].str.contains('CONFIRMED', na=False, case=False)
            ].copy()
            
            # Group by hostname
            if 'hostname' in k2_confirmed.columns:
                for hostname in k2_confirmed['hostname'].dropna().unique():
                    star_planets = k2_confirmed[k2_confirmed['hostname'] == hostname]
                    
                    if len(star_planets) >= 2:
                        planets = []
                        
                        for _, planet in star_planets.iterrows():
                            period = safe_float(planet.get('pl_orbper'))
                            radius = safe_float(planet.get('pl_rade'))
                            sma = safe_float(planet.get('pl_orbsmax'))
                            
                            if period and radius and sma:
                                distance = sma * 215
                                letter = planet.get('pl_letter', str(len(planets) + 1))
                                
                                planets.append({
                                    'name': letter if letter else str(len(planets) + 1),
                                    'distance': distance,
                                    'size': radius,
                                    'period': period,
                                    'mass': safe_float(planet.get('pl_masse')),
                                    'color': assign_planet_color(radius)
                                })
                        
                        if len(planets) >= 2:
                            systems.append({
                                'name': hostname,
                                'star_temp': safe_float(star_planets.iloc[0].get('st_teff')) or 5778,
                                'star_radius': safe_float(star_planets.iloc[0].get('st_rad')) or 1.0,
                                'planet_count': len(planets),
                                'planets': sorted(planets, key=lambda p: p['distance'])[:8],
                                'mission': 'K2'
                            })
        except FileNotFoundError:
            print("⚠️ K2 CSV not found for multi-planet systems")
        except Exception as e:
            print(f"⚠️ Error processing K2 data: {e}")
        
        # Remove duplicates and sort by planet count
        unique_systems = {sys['name']: sys for sys in systems}
        sorted_systems = sorted(
            unique_systems.values(), 
            key=lambda s: s['planet_count'], 
            reverse=True
        )
        
        # Return top 20 systems
        print(f"✅ Found {len(sorted_systems)} multi-planet systems")
        return jsonify(sorted_systems[:20])
    
    except Exception as e:
        print(f"❌ Error in multi-planet systems endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'data_files': {
            'kepler': os.path.exists(os.path.join(DATA_DIR, 'kepler_koi.csv')),
            'tess': os.path.exists(os.path.join(DATA_DIR, 'tess_toi.csv')),
            'k2': os.path.exists(os.path.join(DATA_DIR, 'k2_candidates.csv'))
        }
    })

if __name__ == "__main__":
    print("🚀 Starting NASA Exoplanet Detection API...")
    print(f"📂 Data directory: {DATA_DIR}")
    print(f"✅ Kepler data: {'Found' if os.path.exists(os.path.join(DATA_DIR, 'kepler_koi.csv')) else 'Missing'}")
    print(f"✅ TESS data: {'Found' if os.path.exists(os.path.join(DATA_DIR, 'tess_toi.csv')) else 'Missing'}")
    print(f"✅ K2 data: {'Found' if os.path.exists(os.path.join(DATA_DIR, 'k2_candidates.csv')) else 'Missing'}")
    app.run(debug=True, port=5000)
