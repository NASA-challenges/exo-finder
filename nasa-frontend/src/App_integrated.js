import React, { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, ScatterChart, Scatter, ZAxis } from 'recharts';
import { Filter, Rocket, Globe, Calendar, TrendingUp, Database } from 'lucide-react';
import './App.css';

const ExoplanetDashboard = () => {
  // Original prediction form state
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
  
  // Main tab state: 'predict' (single + batch) or 'explore' (NASA data)
  const [mainTab, setMainTab] = useState('predict');
  const [predictTab, setPredictTab] = useState('single');
  
  // NASA Explorer state
  const [selectedMission, setSelectedMission] = useState('ALL');
  const [selectedDisposition, setSelectedDisposition] = useState('ALL');
  const [selectedYearRange, setSelectedYearRange] = useState([2009, 2024]);
  const [exploreView, setExploreView] = useState('overview');
  const [nasaLoading, setNasaLoading] = useState(false);
  const [keplerData, setKeplerData] = useState([]);
  const [tessData, setTessData] = useState([]);
  const [k2Data, setK2Data] = useState([]);
  const [error, setError] = useState(null);

  // Fetch NASA data when switching to explore tab
  useEffect(() => {
    if (mainTab === 'explore' && keplerData.length === 0) {
      fetchNASAData();
    }
  }, [mainTab]);

  const fetchNASAData = async () => {
    setNasaLoading(true);
    setError(null);
    
    try {
      const responses = await Promise.all([
        fetch('http://127.0.0.1:5000/api/exoplanets/kepler').catch(() => null),
        fetch('http://127.0.0.1:5000/api/exoplanets/tess').catch(() => null),
        fetch('http://127.0.0.1:5000/api/exoplanets/k2').catch(() => null)
      ]);

      // If Flask endpoints don't work or return errors, use sample data
      if (!responses[0] || !responses[0].ok) {
        setError('NASA API unavailable. Using sample data for demonstration.');
        setKeplerData(generateSampleNASAData('Kepler', 2009, 2018));
        setTessData(generateSampleNASAData('TESS', 2018, 2024));
        setK2Data(generateSampleNASAData('K2', 2014, 2018));
      } else {
        const [kepler, tess, k2] = await Promise.all(
          responses.map(r => r.json())
        );
        
        // Check if response is an error object
        if (kepler.error) {
          setError('NASA API unavailable. Using sample data.');
          setKeplerData(generateSampleNASAData('Kepler', 2009, 2018));
        } else {
          setKeplerData(kepler);
        }
        
        if (tess.error) {
          setTessData(generateSampleNASAData('TESS', 2018, 2024));
        } else {
          setTessData(tess);
        }
        
        if (k2.error) {
          setK2Data(generateSampleNASAData('K2', 2014, 2018));
        } else {
          setK2Data(k2);
        }
      }
    } catch (err) {
      setError('Error loading NASA data. Using sample data.');
      setKeplerData(generateSampleNASAData('Kepler', 2009, 2018));
      setTessData(generateSampleNASAData('TESS', 2018, 2024));
      setK2Data(generateSampleNASAData('K2', 2014, 2018));
    } finally {
      setNasaLoading(false);
    }
  };

  // Generate sample data matching NASA's data structure
  const generateSampleNASAData = (mission, startYear, endYear) => {
    const data = [];
    const dispositions = ['CONFIRMED', 'CANDIDATE', 'FALSE POSITIVE'];
    
    for (let year = startYear; year <= endYear; year++) {
      dispositions.forEach(disp => {
        const baseCount = mission === 'Kepler' ? 200 : mission === 'TESS' ? 120 : 80;
        const yearFactor = (year - startYear + 1) / (endYear - startYear + 1);
        const dispFactor = disp === 'CONFIRMED' ? 0.6 : disp === 'CANDIDATE' ? 1 : 0.2;
        const count = Math.floor(baseCount * yearFactor * dispFactor + Math.random() * 30);
        
        for (let i = 0; i < count; i++) {
          data.push({
            mission: mission,
            disposition: disp,
            discovery_year: year,
            pl_name: `${mission}-${year}-${i}`,
            pl_orbper: 10 + Math.random() * 500,
            pl_rade: 0.5 + Math.random() * 20,
            pl_masse: Math.random() * 500,
            st_rad: 0.5 + Math.random() * 3,
            st_teff: 3000 + Math.random() * 4000,
            sy_dist: 100 + Math.random() * 2000,
            disc_facility: mission
          });
        }
      });
    }
    return data;
  };

  // Combine all mission data
  const allData = useMemo(() => {
    return [...keplerData, ...tessData, ...k2Data];
  }, [keplerData, tessData, k2Data]);

  // Filter data based on selections
  const filteredData = useMemo(() => {
    return allData.filter(d => {
      const missionMatch = selectedMission === 'ALL' || d.mission === selectedMission;
      const dispositionMatch = selectedDisposition === 'ALL' || d.disposition === selectedDisposition;
      const yearMatch = d.discovery_year >= selectedYearRange[0] && d.discovery_year <= selectedYearRange[1];
      return missionMatch && dispositionMatch && yearMatch;
    });
  }, [allData, selectedMission, selectedDisposition, selectedYearRange]);

  // Aggregate data for charts
  const timeSeriesData = useMemo(() => {
    const yearMap = {};
    filteredData.forEach(d => {
      const year = d.discovery_year;
      if (!yearMap[year]) {
        yearMap[year] = { year, Kepler: 0, TESS: 0, K2: 0, total: 0 };
      }
      yearMap[year][d.mission] = (yearMap[year][d.mission] || 0) + 1;
      yearMap[year].total += 1;
    });
    return Object.values(yearMap).sort((a, b) => a.year - b.year);
  }, [filteredData]);

  const dispositionData = useMemo(() => {
    const dispMap = {};
    filteredData.forEach(d => {
      if (!dispMap[d.disposition]) {
        dispMap[d.disposition] = { name: d.disposition, count: 0 };
      }
      dispMap[d.disposition].count += 1;
    });
    return Object.values(dispMap);
  }, [filteredData]);

  const missionData = useMemo(() => {
    const missionMap = {};
    filteredData.forEach(d => {
      if (!missionMap[d.mission]) {
        missionMap[d.mission] = { mission: d.mission, count: 0 };
      }
      missionMap[d.mission].count += 1;
    });
    return Object.values(missionMap);
  }, [filteredData]);

  const scatterData = useMemo(() => {
    return filteredData
      .filter(d => d.pl_orbper && d.pl_rade)
      .slice(0, 500)
      .map(d => ({
        period: d.pl_orbper,
        radius: d.pl_rade,
        disposition: d.disposition,
        mission: d.mission,
        name: d.pl_name
      }));
  }, [filteredData]);

  // Original prediction form handlers
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

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <p className="tooltip-label">{payload[0].name}</p>
          <p className="tooltip-value">{payload[0].value}</p>
        </div>
      );
    }
    return null;
  };

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

        {/* Main navigation: Predict vs Explore */}
        <div className="main-tab-navigation">
          <button
            onClick={() => setMainTab('predict')}
            className={`main-tab-button ${mainTab === 'predict' ? 'active' : ''}`}
          >
            <Rocket className="tab-icon" />
            ML Prediction
          </button>
          <button
            onClick={() => setMainTab('explore')}
            className={`main-tab-button ${mainTab === 'explore' ? 'active' : ''}`}
          >
            <Globe className="tab-icon" />
            NASA Data Explorer
          </button>
        </div>

        {/* Prediction Tab Content */}
        {mainTab === 'predict' && (
          <>
            <div className="tab-navigation">
              <button
                onClick={() => setPredictTab('single')}
                className={`tab-button ${predictTab === 'single' ? 'active' : ''}`}
              >
                🚀 Single Prediction
              </button>
              <button
                onClick={() => setPredictTab('batch')}
                className={`tab-button ${predictTab === 'batch' ? 'active-batch' : ''}`}
              >
                📂 Batch Processing
              </button>
            </div>

            {predictTab === 'single' && (
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

            {predictTab === 'batch' && (
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
          </>
        )}

        {/* NASA Data Explorer Tab Content */}
        {mainTab === 'explore' && (
          <div className="nasa-explorer">
            {nasaLoading ? (
              <div className="loading-container">
                <Rocket className="loading-icon" />
                <p className="loading-text">Loading NASA Exoplanet Data...</p>
              </div>
            ) : (
              <>
                {error && (
                  <div className="error-banner">
                    <p>{error}</p>
                  </div>
                )}

                <div className="explorer-header">
                  <div className="explorer-title">
                    <Globe className="title-icon" />
                    <div>
                      <h2>NASA Exoplanet Explorer</h2>
                      <p className="explorer-subtitle">
                        Real-time data from NASA Exoplanet Archive • Kepler, TESS & K2 Missions
                      </p>
                    </div>
                  </div>
                  <div className="data-count">
                    <Database className="count-icon" />
                    <span>{allData.length.toLocaleString()} objects</span>
                  </div>
                </div>

                {/* Sub-navigation for explore views */}
                <div className="explore-nav">
                  <button
                    onClick={() => setExploreView('overview')}
                    className={`explore-tab ${exploreView === 'overview' ? 'active' : ''}`}
                  >
                    <TrendingUp className="explore-icon" />
                    Overview
                  </button>
                  <button
                    onClick={() => setExploreView('timeseries')}
                    className={`explore-tab ${exploreView === 'timeseries' ? 'active' : ''}`}
                  >
                    <Calendar className="explore-icon" />
                    Time Series
                  </button>
                </div>

                {/* Filters */}
                <div className="filters-section">
                  <div className="filters-header">
                    <Filter className="filter-icon" />
                    <h3>Filters</h3>
                  </div>
                  
                  <div className="filters-grid">
                    <div className="filter-group">
                      <label className="filter-label">Mission</label>
                      <select
                        value={selectedMission}
                        onChange={(e) => setSelectedMission(e.target.value)}
                        className="filter-select"
                      >
                        <option value="ALL">All Missions</option>
                        <option value="Kepler">Kepler</option>
                        <option value="TESS">TESS</option>
                        <option value="K2">K2</option>
                      </select>
                    </div>

                    <div className="filter-group">
                      <label className="filter-label">Disposition</label>
                      <select
                        value={selectedDisposition}
                        onChange={(e) => setSelectedDisposition(e.target.value)}
                        className="filter-select"
                      >
                        <option value="ALL">All Types</option>
                        <option value="CONFIRMED">Confirmed</option>
                        <option value="CANDIDATE">Candidate</option>
                        <option value="FALSE POSITIVE">False Positive</option>
                      </select>
                    </div>

                    <div className="filter-group">
                      <label className="filter-label">
                        Year Range: {selectedYearRange[0]} - {selectedYearRange[1]}
                      </label>
                      <div className="range-inputs">
                        <input
                          type="range"
                          min="2009"
                          max="2024"
                          value={selectedYearRange[0]}
                          onChange={(e) => setSelectedYearRange([parseInt(e.target.value), selectedYearRange[1]])}
                          className="range-slider"
                        />
                        <input
                          type="range"
                          min="2009"
                          max="2024"
                          value={selectedYearRange[1]}
                          onChange={(e) => setSelectedYearRange([selectedYearRange[0], parseInt(e.target.value)])}
                          className="range-slider"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Charts and visualizations */}
                {exploreView === 'overview' && (
                  <div className="charts-container">
                    {/* Stats Cards */}
                    <div className="stats-grid">
                      <div className="stat-card stat-total">
                        <div className="stat-label">Total Discoveries</div>
                        <div className="stat-value">{filteredData.length.toLocaleString()}</div>
                      </div>
                      {dispositionData.map(d => (
                        <div key={d.name} className="stat-card">
                          <div className="stat-label">{d.name}</div>
                          <div className="stat-value">{d.count.toLocaleString()}</div>
                        </div>
                      ))}
                    </div>

                    <div className="charts-row">
                      {/* Disposition Breakdown */}
                      <div className="chart-card">
                        <h3 className="chart-title">Disposition Breakdown</h3>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={dispositionData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                            <YAxis stroke="#94a3b8" />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>

                      {/* Mission Comparison */}
                      <div className="chart-card">
                        <h3 className="chart-title">Mission Distribution</h3>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={missionData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="mission" stroke="#94a3b8" />
                            <YAxis stroke="#94a3b8" />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="count" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Scatter plot */}
                    <div className="chart-card-full">
                      <h3 className="chart-title">Planet Characteristics: Orbital Period vs Radius</h3>
                      <ResponsiveContainer width="100%" height={400}>
                        <ScatterChart>
                          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                          <XAxis 
                            dataKey="period" 
                            name="Orbital Period" 
                            unit=" days" 
                            stroke="#94a3b8"
                            type="number"
                            domain={['dataMin', 'dataMax']}
                            label={{ value: 'Orbital Period (days)', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
                          />
                          <YAxis 
                            dataKey="radius" 
                            name="Radius" 
                            unit=" R⊕" 
                            stroke="#94a3b8"
                            label={{ value: 'Planet Radius (Earth Radii)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
                          />
                          <ZAxis range={[20, 200]} />
                          <Tooltip 
                            cursor={{ strokeDasharray: '3 3' }}
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                const data = payload[0].payload;
                                return (
                                  <div className="scatter-tooltip">
                                    <p className="tooltip-name">{data.name}</p>
                                    <p className="tooltip-detail">Period: {data.period.toFixed(2)} days</p>
                                    <p className="tooltip-detail">Radius: {data.radius.toFixed(2)} R⊕</p>
                                    <p className="tooltip-detail">Mission: {data.mission}</p>
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                          <Legend />
                          <Scatter name="Kepler" data={scatterData.filter(d => d.mission === 'Kepler')} fill="#8b5cf6" />
                          <Scatter name="TESS" data={scatterData.filter(d => d.mission === 'TESS')} fill="#3b82f6" />
                          <Scatter name="K2" data={scatterData.filter(d => d.mission === 'K2')} fill="#10b981" />
                        </ScatterChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {exploreView === 'timeseries' && (
                  <div className="chart-card-full">
                    <div className="timeseries-header">
                      <h3 className="chart-title">Exoplanet Discoveries Over Time</h3>
                      <p className="chart-description">Cumulative discoveries by mission year</p>
                    </div>
                    <ResponsiveContainer width="100%" height={500}>
                      <LineChart data={timeSeriesData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis 
                          dataKey="year" 
                          stroke="#94a3b8"
                          label={{ value: 'Year', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
                        />
                        <YAxis 
                          stroke="#94a3b8"
                          label={{ value: 'Number of Discoveries', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#1e293b', 
                            border: '1px solid #334155', 
                            borderRadius: '8px' 
                          }}
                        />
                        <Legend />
                        <Line 
                          type="monotone" 
                          dataKey="Kepler" 
                          stroke="#8b5cf6" 
                          strokeWidth={3}
                          dot={{ fill: '#8b5cf6', r: 4 }}
                          activeDot={{ r: 6 }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="TESS" 
                          stroke="#3b82f6" 
                          strokeWidth={3}
                          dot={{ fill: '#3b82f6', r: 4 }}
                          activeDot={{ r: 6 }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="K2" 
                          stroke="#10b981" 
                          strokeWidth={3}
                          dot={{ fill: '#10b981', r: 4 }}
                          activeDot={{ r: 6 }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="total" 
                          stroke="#f59e0b" 
                          strokeWidth={2}
                          strokeDasharray="5 5"
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        <footer className="footer">
          <p>© 2025 Malic Vladislava, Melnic Mihaela — A World Away: Hunting for Exoplanets with AI</p>
          <p className="footer-subtitle">Powered by XGBoost, React, Recharts & NASA Exoplanet Archive</p>
        </footer>
      </div>
    </div>
  );
};

export default ExoplanetDashboard;
