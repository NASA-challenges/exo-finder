import pickle
from huggingface_hub import hf_hub_download

repo_id = "mihaelaMelnic/kepler-exoplanet-model"

model_path = hf_hub_download(repo_id=repo_id, filename="kepler_xgb_optimized.pkl")
scaler_path = hf_hub_download(repo_id=repo_id, filename="xgb_scaler.pkl")
encoder_path = hf_hub_download(repo_id=repo_id, filename="xgb_label_encoder.pkl")

model = pickle.load(open(model_path, "rb"))
scaler = pickle.load(open(scaler_path, "rb"))
label_encoder = pickle.load(open(encoder_path, "rb"))