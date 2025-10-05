import React, { useState } from "react";
import axios from "axios";
import "./UploadCSV.css";

function UploadCSV() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setMessage("");
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setMessage("Please select a CSV file first.");
      return;
    }

    setLoading(true);
    setMessage("Uploading file to NASA model...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://127.0.0.1:5000/batch_predict", formData, {
        responseType: "blob",
        headers: { "Content-Type": "multipart/form-data" },
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "predicted_results.csv");
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);

      setMessage("File processed successfully. Downloading results...");
    } catch (error) {
      setMessage("Error: " + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <h2>Batch Prediction Mode</h2>
      <p>Upload your <b>Kepler Exoplanet CSV</b> file to predict all entries automatically.</p>

      <form onSubmit={handleUpload}>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="file-input"
        />
        <button type="submit" disabled={loading}>
          {loading ? "Processing..." : "Upload & Predict"}
        </button>
      </form>

      {message && <div className="status">{message}</div>}
    </div>
  );
}

export default UploadCSV;
