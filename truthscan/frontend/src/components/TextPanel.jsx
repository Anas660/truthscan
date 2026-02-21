import React, { useState } from 'react';

const TextPanel = () => {
    const [textInput, setTextInput] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleInputChange = (e) => {
        setTextInput(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await fetch('http://backend:8000/detect/text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: textInput }),
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
            <h2>Text Detection</h2>
            <form onSubmit={handleSubmit}>
                <textarea
                    value={textInput}
                    onChange={handleInputChange}
                    placeholder="Enter text to analyze"
                    rows="4"
                    cols="50"
                />
                <button type="submit" disabled={loading}>
                    {loading ? 'Analyzing...' : 'Analyze Text'}
                </button>
            </form>
            {error && <p style={{ color: 'red' }}>Error: {error}</p>}
            {result && (
                <div>
                    <h3>Result:</h3>
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

export default TextPanel;