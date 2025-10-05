import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, ConfusionMatrixDisplay

print("Loading KOI dataset")

df = pd.read_csv(
    "src/data/kepler_koi.csv",
    comment="#",
    sep=",",
    low_memory=False
)

print(f"Dataset loaded successfully: {len(df)} rows, {len(df.columns)} columns")
print(df.head(3))
print("\nColumns:", list(df.columns)[:10], "...")

drop_cols = [
    'rowid','kepid','kepoi_name','kepler_name','koi_comment','koi_disp_prov',
    'koi_parm_prov','koi_sparprov','koi_tce_delivname','koi_datalink_dvr',
    'koi_datalink_dvs','ra','dec'
]
df.drop(columns=drop_cols, inplace=True, errors='ignore')

if 'koi_disposition' not in df.columns:
    raise ValueError("Column 'koi_disposition' not found.")

df['target'] = df['koi_disposition'].apply(lambda x: 1 if x == 'CONFIRMED' else 0)
print("\nTarget variable created successfully.")

feature_cols = [
    'koi_period', 'koi_duration', 'koi_depth', 'koi_ror', 'koi_prad', 'koi_sma',
    'koi_incl', 'koi_teq', 'koi_insol', 'koi_eccen', 'koi_impact', 'koi_srho',
    'koi_steff', 'koi_slogg', 'koi_smet', 'koi_srad', 'koi_smass', 'koi_model_snr'
]

feature_cols = [col for col in feature_cols if col in df.columns]
X = df[feature_cols]
y = df['target']

print(f"Using {len(feature_cols)} numeric features for training: {feature_cols}")

X = X.fillna(X.median())

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training samples: {len(X_train)}, Testing samples: {len(X_test)}")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("\nTraining model")
model = RandomForestClassifier(
    n_estimators=150,
    random_state=42,
    max_depth=12,
    n_jobs=-1
)
model.fit(X_train_scaled, y_train)

y_pred = model.predict(X_test_scaled)

acc = accuracy_score(y_test, y_pred)
print(f"\nModel Accuracy: {acc*100:.2f}%")
print("\nClassification Report:\n", classification_report(y_test, y_pred))

ConfusionMatrixDisplay.from_estimator(model, X_test_scaled, y_test)
plt.title("Exoplanet Classification")
plt.show()

pickle.dump(model, open("src/models/random_forest_model.pkl", "wb"))
pickle.dump(scaler, open("src/models/rf_scaler.pkl", "wb"))
print("\nModel saved as 'random_forest_model.pkl'")
print("Scaler saved as 'scaler.pkl'")

example = np.array([[100.2, 3.1, 1200, 0.02, 1.2, 0.98, 89.3, 500, 1.1, 0.0, 0.5]])
example_scaled = scaler.transform(example)
prediction = model.predict(example_scaled)[0]

label = "CONFIRMED PLANET" if prediction == 1 else "NOT CONFIRMED"
print(f"\nExample prediction {label}")
