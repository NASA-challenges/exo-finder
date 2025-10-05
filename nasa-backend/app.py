from flask import Flask, request, jsonify, send_file
import pandas as pd
import numpy as np
import pickle
from io import BytesIO
from huggingface_hub import hf_hub_download
from flask_cors import CORS


app = Flask(__name__)
CORS(app)


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
        "endpoints": ["/predict", "/batch_predict"]
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

if __name__ == "__main__":
    print("🚀 Starting NASA Exoplanet Detection API...")
    app.run(debug=True, port=5000)
