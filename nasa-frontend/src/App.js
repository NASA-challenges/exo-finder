import React, { useState } from 'react';
import './App.css';

const ExoplanetDashboard = () => {
  const [formData, setFormData] = useState({
    koi_period: "",
    koi_duration: "",
    koi_depth: "",
    koi_prad: "",
    koi_teq: "",
    koi_insol: "",
    koi_impact: "",
    koi_steff: "",
    koi_slogg: "",
    koi_srad: "",
    koi_model_snr: "",
    koi_fpflag_nt: 0,
    koi_fpflag_ss: 0,
    koi_fpflag_co: 0,
    koi_fpflag_ec: 0,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [activeTab, setActiveTab] = useState('single');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: parseFloat(e.target.value) || 0 });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:5000/predict", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setResult({ error: err.message });
    }
    setLoading(false);
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setUploadMessage("");
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadMessage("⚠️ Please select a CSV file first.");
      return;
    }

    setUploadLoading(true);
    setUploadMessage("🛰️ Processing file...");

    const formDataUpload = new FormData();
    formDataUpload.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:5000/batch_predict", {
        method: 'POST',
        body: formDataUpload,
      });

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "predicted_results.csv");
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);

      setUploadMessage("✅ File processed successfully! Downloading results...");
    } catch (error) {
      setUploadMessage("❌ Error: " + error.message);
    } finally {
      setUploadLoading(false);
    }
  };

  const inputFields = [
    { name: 'koi_period', label: 'Orbital Period', unit: 'days' },
    { name: 'koi_duration', label: 'Transit Duration', unit: 'hours' },
    { name: 'koi_depth', label: 'Transit Depth', unit: 'ppm' },
    { name: 'koi_prad', label: 'Planet Radius', unit: 'Earth radii' },
    { name: 'koi_teq', label: 'Equilibrium Temp', unit: 'K' },
    { name: 'koi_insol', label: 'Insolation Flux', unit: 'Earth flux' },
    { name: 'koi_impact', label: 'Impact Parameter', unit: '' },
    { name: 'koi_steff', label: 'Stellar Temp', unit: 'K' },
    { name: 'koi_slogg', label: 'Stellar Surface Gravity', unit: 'log10(cm/s²)' },
    { name: 'koi_srad', label: 'Stellar Radius', unit: 'Solar radii' },
    { name: 'koi_model_snr', label: 'Signal-to-Noise Ratio', unit: '' }
  ];

  const flagFields = [
    { name: 'koi_fpflag_nt', label: 'Not Transit-Like' },
    { name: 'koi_fpflag_ss', label: 'Stellar Eclipse' },
    { name: 'koi_fpflag_co', label: 'Centroid Offset' },
    { name: 'koi_fpflag_ec', label: 'Ephemeris Match' }
  ];

  return (
    <div className="app-container">
      <div className="stars-background"></div>

      <div className="content-wrapper">
        <header className="header">
          <div className="header-content">
            <span className="star-icon rotating">⭐</span>
            <h1 className="title">NASA Exoplanet Detection</h1>
            <span className="star-icon rotating-reverse">🌟</span>
          </div>
          <p className="subtitle">Advanced Machine Learning Model for Kepler Mission Data</p>
        </header>

        <div className="tab-navigation">
          <button
            onClick={() => setActiveTab('single')}
            className={`tab-button ${activeTab === 'single' ? 'active' : ''}`}
          >
            🚀 Single Prediction
          </button>
          <button
            onClick={() => setActiveTab('batch')}
            className={`tab-button ${activeTab === 'batch' ? 'active-batch' : ''}`}
          >
            📂 Batch Processing
          </button>
        </div>

        {activeTab === 'single' && (
          <div className="form-container">
            <div className="card">
              <h2 className="card-title">Enter Exoplanet Parameters</h2>

              <form onSubmit={handleSubmit}>
                <div className="input-grid">
                  {inputFields.map(field => (
                    <div key={field.name} className="input-group">
                      <label className="input-label">
                        {field.label}
                        {field.unit && <span className="unit-label"> ({field.unit})</span>}
                      </label>
                      <input
                        type="number"
                        step="any"
                        name={field.name}
                        value={formData[field.name]}
                        onChange={handleChange}
                        className="input-field"
                        placeholder="0.0"
                      />
                    </div>
                  ))}
                </div>

                <div className="flags-section">
                  <h3 className="flags-title">False Positive Flags</h3>
                  <div className="flags-grid">
                    {flagFields.map(field => (
                      <label key={field.name} className="checkbox-label">
                        <input
                          type="checkbox"
                          name={field.name}
                          checked={formData[field.name] === 1}
                          onChange={(e) => setFormData({ ...formData, [field.name]: e.target.checked ? 1 : 0 })}
                          className="checkbox-input"
                        />
                        <span>{field.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="submit-button"
                >
                  {loading ? '⏳ Analyzing...' : '🚀 Predict Exoplanet Status'}
                </button>
              </form>
            </div>

            {result && (
              <div className="result-card">
                {result.error ? (
                  <div className="error-message">
                    ⚠️ {result.error}
                  </div>
                ) : (
                  <div>
                    <div className="result-header">
                      <span className="check-icon">✅</span>
                      <div>
                        <h3 className="result-label">Prediction Result:</h3>
                        <p className={`result-value ${result.label.toLowerCase()}`}>
                          {result.label}
                        </p>
                      </div>
                    </div>

                    <div className="probabilities-grid">
                      {result.probabilities.map((prob, idx) => (
                        <div key={idx} className="probability-card">
                          <div className="probability-label">
                            {['CONFIRMED', 'CANDIDATE', 'FALSE POSITIVE'][idx]}
                          </div>
                          <div className="probability-value">
                            {(prob * 100).toFixed(1)}%
                          </div>
                          <div className="progress-bar">
                            <div
                              className="progress-fill"
                              style={{ width: `${prob * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'batch' && (
          <div className="batch-container">
            <div className="card">
              <h2 className="card-title-batch">Batch CSV Processing</h2>
              <p className="batch-description">
                Upload your Kepler Exoplanet CSV file to predict all entries automatically.
              </p>

              <div className="upload-area">
                <div className="upload-icon">📂</div>
                <label className="file-label">
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="file-input"
                  />
                  <span className="file-text">
                    {file ? `📄 ${file.name}` : 'Click to select CSV file'}
                  </span>
                </label>
              </div>

              <button
                onClick={handleUpload}
                disabled={uploadLoading || !file}
                className="upload-button"
              >
                {uploadLoading ? '⏳ Processing...' : '🚀 Upload & Predict'}
              </button>

              {uploadMessage && (
                <div className="upload-message">
                  {uploadMessage}
                </div>
              )}
            </div>
          </div>
        )}

        <footer className="footer">
          <p>© 2025 Malic Vladislava, Melnic Mihaela — A World Away: Hunting for Exoplanets with AI</p>
          <p className="footer-subtitle">Powered by XGBoost & React</p>
        </footer>
      </div>
    </div>
  );
};

export default ExoplanetDashboard;