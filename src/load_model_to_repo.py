from huggingface_hub import HfApi, upload_file


api = HfApi()

repo_id = "mihaelaMelnic/kepler-exoplanet-model"
api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)

upload_file(
    path_or_fileobj="src/models/kepler_xgb_optimized.pkl",
    path_in_repo="kepler_xgb_optimized.pkl",
    repo_id=repo_id,
    repo_type="model"
)

upload_file(
    path_or_fileobj="src/models/xgb_scaler.pkl",
    path_in_repo="xgb_scaler.pkl",
    repo_id=repo_id,
    repo_type="model"
)

upload_file(
    path_or_fileobj="src/models/xgb_label_encoder.pkl",
    path_in_repo="xgb_label_encoder.pkl",
    repo_id=repo_id,
    repo_type="model"
)

upload_file(
    path_or_fileobj="src/models/random_forest_model.pkl",
    path_in_repo="random_forest_model.pkl",
    repo_id=repo_id,
    repo_type="model"
)

upload_file(
    path_or_fileobj="src/models/rf_scaler.pkl",
    path_in_repo="rf_scaler.pkl",
    repo_id=repo_id,
    repo_type="model"
)

print(f"✅ All files uploaded to https://huggingface.co/{repo_id}")
