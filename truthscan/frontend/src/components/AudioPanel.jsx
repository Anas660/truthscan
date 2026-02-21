import React, { useState } from 'react';

const AudioPanel = () => {
  const [audioFile, setAudioFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (event) => {
    setAudioFile(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!audioFile) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', audioFile);

    try {
      const response = await fetch('http://backend:8000/detect/audio', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error detecting audio:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Audio Detection</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" accept="audio/*" onChange={handleFileChange} />
        <button type="submit" disabled={loading}>
          {loading ? 'Detecting...' : 'Detect Audio'}
        </button>
      </form>
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

export default AudioPanel;