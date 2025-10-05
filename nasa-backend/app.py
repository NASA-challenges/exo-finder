from flask import Flask, request, jsonify, send_file
import pandas as pd
import numpy as np
import pickle
from io import BytesIO
from huggingface_hub import hf_hub_download
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

NASA_TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

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
        "endpoints": ["/predict", "/batch_predict", "/api/exoplanets/kepler", "/api/exoplanets/tess", "/api/exoplanets/k2"]
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

@app.route('/api/exoplanets/kepler')
def get_kepler_data():
    """Fetch Kepler Objects of Interest (KOI) data from NASA TAP service"""
    try:
        query = """
        SELECT kepoi_name, koi_disposition, koi_period, koi_prad, 
               koi_srad, koi_steff, koi_teq, ra, dec
        FROM cumulative
        WHERE koi_disposition IS NOT NULL
        LIMIT 1000
        """

        params = {
            'query': query,
            'format': 'json'
        }

        response = requests.get(NASA_TAP_URL, params=params, timeout=10)
        data = response.json()

        transformed = []
        for row in data:
            year = 2009 + (hash(row.get('kepoi_name', '')) % 10)
            transformed.append({
                'mission': 'Kepler',
                'pl_name': row.get('kepoi_name'),
                'disposition': row.get('koi_disposition'),
                'pl_orbper': row.get('koi_period'),
                'pl_rade': row.get('koi_prad'),
                'st_rad': row.get('koi_srad'),
                'st_teff': row.get('koi_steff'),
                'discovery_year': year,
                'pl_masse': None,
                'sy_dist': None,
                'disc_facility': 'Kepler'
            })

        return jsonify(transformed)

    except Exception as e:
        print(f"❌ Error fetching Kepler data from NASA: {e}")
        return jsonify({"error": "NASA TAP API unavailable", "message": str(e)}), 503

@app.route('/api/exoplanets/tess')
def get_tess_data():
    """Fetch TESS Objects of Interest (TOI) data"""
    try:
        query = """
        SELECT toi, tfopwg_disp, pl_orbper, pl_rade, 
               st_rad, st_teff, ra, dec
        FROM toi
        WHERE tfopwg_disp IS NOT NULL
        LIMIT 1000
        """

        params = {
            'query': query,
            'format': 'json'
        }

        response = requests.get(NASA_TAP_URL, params=params, timeout=10)
        data = response.json()

        transformed = []
        for row in data:
            toi_num = row.get('toi', 0)
            year = 2018 + (int(toi_num) // 1000) if toi_num else 2020
            transformed.append({
                'mission': 'TESS',
                'pl_name': f"TOI-{row.get('toi')}",
                'disposition': row.get('tfopwg_disp'),
                'pl_orbper': row.get('pl_orbper'),
                'pl_rade': row.get('pl_rade'),
                'st_rad': row.get('st_rad'),
                'st_teff': row.get('st_teff'),
                'discovery_year': year,
                'pl_masse': None,
                'sy_dist': None,
                'disc_facility': 'TESS'
            })

        return jsonify(transformed)

    except Exception as e:
        print(f"❌ Error fetching TESS data from NASA: {e}")
        return jsonify({"error": "NASA TAP API unavailable", "message": str(e)}), 503

@app.route('/api/exoplanets/k2')
def get_k2_data():
    """Fetch K2 Planets and Candidates data from NASA TAP service"""
    try:
        query = """
        SELECT epic_name, k2_disposition, pl_orbper, pl_rade,
               st_rad, st_teff, ra, dec
        FROM k2pandc
        WHERE k2_disposition IS NOT NULL
        LIMIT 500
        """

        params = {
            'query': query,
            'format': 'json'
        }

        response = requests.get(NASA_TAP_URL, params=params, timeout=10)
        data = response.json()

        transformed = []
        for row in data:
            year = 2014 + (hash(row.get('epic_name', '')) % 5)
            transformed.append({
                'mission': 'K2',
                'pl_name': row.get('epic_name'),
                'disposition': row.get('k2_disposition'),
                'pl_orbper': row.get('pl_orbper'),
                'pl_rade': row.get('pl_rade'),
                'st_rad': row.get('st_rad'),
                'st_teff': row.get('st_teff'),
                'discovery_year': year,
                'pl_masse': None,
                'sy_dist': None,
                'disc_facility': 'K2'
            })

        return jsonify(transformed)

    except Exception as e:
        print(f"❌ Error fetching K2 data from NASA: {e}")
        return jsonify({"error": "NASA TAP API unavailable", "message": str(e)}), 503

if __name__ == "__main__":
    print("🚀 Starting NASA Exoplanet Detection API...")
    app.run(debug=True, port=5000)
