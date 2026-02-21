import React, { useState } from 'react';

const ImagePanel = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!selectedFile) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://backend:8000/detect/image', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Image Detection</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" accept="image/*" onChange={handleFileChange} />
        <button type="submit" disabled={loading}>
          {loading ? 'Uploading...' : 'Upload Image'}
        </button>
      </form>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {result && (
        <div>
          <h3>Detection Result</h3>
          <p>Verdict: {result.verdict}</p>
          <p>AI Probability: {result.ai_probability}</p>
          <p>Human Probability: {result.human_probability}</p>
          <p>Confidence: {result.confidence}%</p>
          <h4>Signals:</h4>
          <ul>
            {result.signals.map((signal, index) => (
              <li key={index}>
                {signal.label} (Severity: {signal.severity})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ImagePanel;