import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, ConfusionMatrixDisplay
from xgboost import XGBClassifier

print("Loading dataset")

df = pd.read_csv(
    "src/data/kepler_koi.csv",
    comment="#",
    sep=",",
    low_memory=False
)

print(f"Dataset loaded successfully: {len(df)} rows, {len(df.columns)} columns")

drop_cols = [
    'rowid','kepid','kepoi_name','kepler_name','koi_comment','koi_disp_prov',
    'koi_parm_prov','koi_sparprov','koi_tce_delivname','koi_datalink_dvr',
    'koi_datalink_dvs','ra','dec'
]
df.drop(columns=drop_cols, inplace=True, errors='ignore')

print("\nUnique disposition labels:", df['koi_disposition'].unique())

le = LabelEncoder()
df['target'] = le.fit_transform(df['koi_disposition'])
label_mapping = dict(zip(le.transform(le.classes_), le.classes_))
print("Label mapping:", label_mapping)

feature_cols = [
    'koi_period', 'koi_duration', 'koi_depth', 'koi_prad',
    'koi_teq', 'koi_insol', 'koi_impact',
    'koi_steff', 'koi_slogg', 'koi_srad', 'koi_model_snr',
    'koi_fpflag_nt', 'koi_fpflag_ss', 'koi_fpflag_co', 'koi_fpflag_ec'
]

feature_cols = [c for c in feature_cols if c in df.columns]

X = df[feature_cols].fillna(df[feature_cols].median())
y = df['target']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("\nSkipping SMOTE balancing")

print("\nTraining model")

model = XGBClassifier(
    n_estimators=1200,
    learning_rate=0.03,
    max_depth=6,
    subsample=0.9,
    colsample_bytree=0.9,
    gamma=0.2,
    reg_lambda=1.2,
    min_child_weight=3,
    random_state=42,
    objective='multi:softprob',
    num_class=3,
    tree_method='hist',
    eval_metric='mlogloss'
)

model.fit(X_train_scaled, y_train)

y_pred = model.predict(X_test_scaled)
acc = accuracy_score(y_test, y_pred)

print(f"\nModel Accuracy: {acc*100:.2f}%")
print("\nClassification Report:\n", classification_report(y_test, y_pred, target_names=le.classes_))

ConfusionMatrixDisplay.from_estimator(model, X_test_scaled, y_test, display_labels=le.classes_)
plt.title("XGBoost multiclass classification")
plt.show()

pickle.dump(model, open("src/models/kepler_xgb_optimized.pkl", "wb"))
pickle.dump(scaler, open("src/models/xgb_scaler.pkl", "wb"))
pickle.dump(le, open("src/models/xgb_label_encoder.pkl", "wb"))

print("\nModel saved as 'src/models/kepler_xgb_optimized.pkl'")
print("Scaler saved as 'src/models/scaler.pkl'")
print("Label Encoder saved as 'src/models/label_encoder.pkl'")

example = np.array([[49.18394185, 11.3364, 1646.2, 8.2, 669.0, 47.4, 0.035, 5626.0, 3.907, 2.057, 355.7, 0, 0, 0, 0]])
example_scaled = scaler.transform(example)
pred_class = model.predict(example_scaled)[0]
pred_label = le.inverse_transform([pred_class])[0]

print(f"\nExample prediction {pred_label}")

importance = model.feature_importances_
sorted_idx = np.argsort(importance)[::-1]

plt.figure(figsize=(9,6))
plt.barh(np.array(feature_cols)[sorted_idx], importance[sorted_idx])
plt.title("Feature Importance")
plt.gca().invert_yaxis()
plt.show()

test_df = X_test.copy()
test_df['true_label'] = le.inverse_transform(y_test)
test_df['predicted_label'] = le.inverse_transform(y_pred)

test_df.to_csv("src/data/kepler_test_set.csv", index=False)
print("\nTest dataset saved as 'kepler_test_set.csv'")