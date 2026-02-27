import axios from "axios";
import { useState } from "react";

const BASE = "http://127.0.0.1:8000";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const uploadPDF = async () => {
    if (!file || !(file instanceof File)) {
      alert("Pehle ek PDF file select karein.");
      return;
    }
    setLoading(true);
    setStatus("🚀 Handshaking with server and uploading...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      await axios.post(`${BASE}/upload`, formData);
      setStatus("✅ SUCCESS! Your catalog is being processed in the background.");
      setFile(null);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Unknown server error";
      setStatus(`❌ UPLOAD FAILED: ${msg}`);
    }
    setLoading(false);
  };

  const syncCatalogs = async () => {
    setSyncing(true);
    setStatus("🔄 Full system re-indexing in progress...");
    try {
      await axios.get(`${BASE}/refresh`);
      setStatus("✅ INDEX REFRESHED! You can now search for new items.");
    } catch (err) {
      setStatus("❌ SYNC ERROR. Please verify if the backend engine is running.");
    }
    setSyncing(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type === "application/pdf") {
      setFile(dropped);
    } else {
      alert("Invalid format. Pelase use PDF files only.");
    }
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2.5rem' }}>
        <div>
          <h2 style={{ fontSize: "2rem", fontWeight: 800, margin: 0 }}>Catalog Data Core</h2>
          <p style={{ color: "var(--text-secondary)", marginTop: '0.5rem' }}>Feed the neural engine with new PDF price lists.</p>
        </div>
        <button
          onClick={syncCatalogs}
          disabled={syncing}
          style={{ background: 'rgba(14, 165, 233, 0.1)', color: 'var(--accent-color)', border: '1px solid rgba(14, 165, 233, 0.2)', padding: '0.75rem 1.5rem', borderRadius: '1rem', fontWeight: 700, cursor: 'pointer' }}
        >
          {syncing ? "SYNCING..." : "REFRESH INDEX"}
        </button>
      </div>

      {/* Modern Drag & Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById("pdf-input").click()}
        style={{
          border: `3px dashed ${dragOver ? "var(--primary-color)" : "var(--border-color)"}`,
          borderRadius: "2rem",
          padding: "5rem 2rem",
          textAlign: "center",
          cursor: "pointer",
          background: dragOver ? "rgba(190, 30, 45, 0.02)" : "white",
          transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
          marginBottom: "2.5rem",
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <input
          id="pdf-input"
          type="file"
          accept=".pdf"
          style={{ display: "none" }}
          onChange={(e) => setFile(e.target.files[0])}
        />
        <div style={{ fontSize: "4.5rem", marginBottom: "1.5rem", animation: dragOver ? 'bounce 0.5s infinite alternate' : 'none' }}>📦</div>
        <style>{`@keyframes bounce { from { transform: translateY(0); } to { transform: translateY(-10px); } }`}</style>

        {file ? (
          <div>
            <div style={{ color: "var(--primary-color)", fontWeight: 800, fontSize: "1.2rem" }}>
              {file.name}
            </div>
            <div style={{ color: "var(--text-dim)", fontSize: "0.9rem", marginTop: "0.5rem" }}>
              {(file.size / 1024 / 1024).toFixed(2)} MB • Ready to ingest
            </div>
          </div>
        ) : (
          <div>
            <div style={{ color: "var(--text-primary)", fontWeight: 700, fontSize: '1.2rem' }}>Drop PDF Catalog here</div>
            <div style={{ color: "var(--text-dim)", fontSize: "0.95rem", marginTop: "0.5rem" }}>or click to browse local files</div>
          </div>
        )}
      </div>

      <button
        onClick={uploadPDF}
        disabled={loading || !file}
        className="search-btn-main"
        style={{
          width: '100%',
          height: '65px',
          background: 'var(--primary-gradient) !important',
          fontSize: '1.1rem',
          letterSpacing: '0.05em',
          opacity: loading || !file ? 0.5 : 1
        }}
      >
        {loading ? "PROCESSING..." : "PROCESS CATALOG"}
      </button>

      {status && (
        <div style={{
          marginTop: "2rem",
          padding: "1.25rem 1.5rem",
          borderRadius: "1.25rem",
          background: status.includes("❌") ? "rgba(239,68,68,0.05)" : "rgba(16, 185, 129, 0.05)",
          border: `1px solid ${status.includes("❌") ? "rgba(239, 68, 68, 0.2)" : "rgba(16, 185, 129, 0.2)"}`,
          color: status.includes("❌") ? "#ef4444" : "#059669",
          fontSize: "0.95rem",
          fontWeight: 600,
          textAlign: 'center',
          animation: 'fadeIn 0.3s ease-out'
        }}>
          {status}
        </div>
      )}

      {/* Documentation Card */}
      <div style={{
        marginTop: "3rem",
        padding: "2rem",
        borderRadius: "1.5rem",
        background: "var(--text-primary)",
        color: 'white'
      }}>
        <div style={{ color: 'var(--accent-color)', fontWeight: 800, marginBottom: "1rem", fontSize: "0.9rem", textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          Data Pipeline Info
        </div>
        <ul style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.95rem", lineHeight: "2.2", paddingLeft: "1.5rem", margin: 0 }}>
          <li>Neural engine performs OCR and semantic mapping.</li>
          <li>System auto-extracts <b style={{ color: 'white' }}>Model Numbers, Materials, & Current MRP</b>.</li>
          <li>Indexing typically completes within 45-60 seconds.</li>
          <li>Once processed, products are globally searchable.</li>
        </ul>
      </div>
    </div>
  );
}
