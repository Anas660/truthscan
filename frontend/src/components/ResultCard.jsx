import { useEffect, useState } from 'react'

const VERDICT_META = {
  ai:    { badge: 'AI-GENERATED', badgeClass: 'badge-ai',    titleClass: 'verdict-ai',    title: 'AI-Generated Content' },
  human: { badge: 'LIKELY HUMAN', badgeClass: 'badge-human', titleClass: 'verdict-human', title: 'Likely Human-Made' },
  mixed: { badge: 'UNCERTAIN',    badgeClass: 'badge-mixed', titleClass: 'verdict-mixed', title: 'Mixed / Uncertain' },
  error: { badge: 'ERROR',        badgeClass: 'badge-error', titleClass: 'verdict-error', title: 'Detection Failed' },
}

export default function ResultCard({ result }) {
  const [aiWidth, setAiWidth]       = useState(0)
  const [humanWidth, setHumanWidth] = useState(0)

  useEffect(() => {
    // Brief delay so CSS transition fires after mount
    const timer = setTimeout(() => {
      setAiWidth(Math.round((result.ai_probability ?? 0) * 100))
      setHumanWidth(Math.round((result.human_probability ?? 0) * 100))
    }, 80)
    return () => clearTimeout(timer)
  }, [result])

  const meta = VERDICT_META[result.verdict] ?? VERDICT_META.error

  return (
    <div className="result-card">
      {/* Verdict */}
      <span className={`verdict-badge ${meta.badgeClass}`}>{meta.badge}</span>
      <h2 className={`verdict-title ${meta.titleClass}`}>{meta.title}</h2>

      {/* Error message */}
      {result.verdict === 'error' && result.message && (
        <p className="error-msg">{result.message}</p>
      )}

      {/* Probability bars — only for non-error */}
      {result.verdict !== 'error' && (
        <div className="prob-bars">
          <div className="prob-row">
            <div className="prob-label-row">
              <span className="prob-label">AI Probability</span>
              <span className="prob-pct verdict-ai">{aiWidth}%</span>
            </div>
            <div className="prob-track">
              <div className="prob-fill prob-fill-ai" style={{ width: `${aiWidth}%` }} />
            </div>
          </div>

          <div className="prob-row">
            <div className="prob-label-row">
              <span className="prob-label">Human Probability</span>
              <span className="prob-pct verdict-human">{humanWidth}%</span>
            </div>
            <div className="prob-track">
              <div className="prob-fill prob-fill-human" style={{ width: `${humanWidth}%` }} />
            </div>
          </div>
        </div>
      )}

      {/* Signals */}
      {result.signals && result.signals.length > 0 && (
        <div className="signals-section">
          <p className="signals-title">Detection Signals</p>
          <div className="signals-list">
            {result.signals.map((sig, i) => (
              <span key={i} className={`signal-chip signal-${sig.severity}`}>
                <span className="signal-dot" />
                {sig.label}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Meta info */}
      <div className="result-meta">
        {result.model_used && <span>Model: {result.model_used}</span>}
        {result.confidence != null && result.verdict !== 'error' && (
          <span>Confidence: {result.confidence}%</span>
        )}
        {result.processing_time_ms != null && (
          <span>Time: {result.processing_time_ms}ms</span>
        )}
      </div>

      <p className="disclaimer">
        Results are probabilistic and intended as guidance only.
      </p>
    </div>
  )
}
