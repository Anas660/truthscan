import { useState } from 'react'
import axios from 'axios'
import LoadingSpinner from './LoadingSpinner'
import ResultCard from './ResultCard'

const API = 'http://localhost:8000/detect/text'

export default function TextPanel({ onError }) {
  const [text, setText]       = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)

  const words = text.trim() ? text.trim().split(/\s+/).length : 0
  const chars = text.length
  const tooFew = words > 0 && words < 20

  const handleScan = async () => {
    if (!text.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const res = await axios.post(API, { text })
      setResult(res.data)
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        'Request failed'
      onError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <textarea
        className="text-textarea"
        placeholder="Paste the text you want to analyze... works best with 50+ words"
        value={text}
        onChange={e => { setText(e.target.value); setResult(null) }}
        disabled={loading}
      />

      <div className="text-meta">
        <span>{words} words</span>
        <span>{chars} characters</span>
      </div>

      {tooFew && (
        <p className="text-warning">⚠ For best results, use 50+ words</p>
      )}

      {loading ? (
        <LoadingSpinner color="yellow" message="Analyzing linguistic patterns..." />
      ) : (
        <button
          className="scan-btn scan-btn-yellow"
          onClick={handleScan}
          disabled={!text.trim() || loading}
        >
          SCAN FOR AI
        </button>
      )}

      {result && !loading && <ResultCard result={result} />}
    </div>
  )
}
