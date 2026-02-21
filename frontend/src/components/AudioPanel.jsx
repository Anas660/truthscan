import { useState } from 'react'
import axios from 'axios'
import UploadZone from './UploadZone'
import LoadingSpinner from './LoadingSpinner'
import ResultCard from './ResultCard'

const API = 'http://localhost:8000/detect/audio'
const MAX_BYTES = 100 * 1024 * 1024

export default function AudioPanel({ onError }) {
  const [file, setFile]       = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)
  const [fileError, setFileError] = useState(null)

  const handleFile = (f, err) => {
    setResult(null)
    if (err) { setFileError(err); setFile(null); return }
    setFileError(null)
    setFile(f)
  }

  const handleScan = async () => {
    if (!file) return
    setLoading(true)
    setResult(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await axios.post(API, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      })
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
      <UploadZone
        accept="audio/mpeg,audio/wav,audio/aac,audio/flac,audio/x-flac,audio/mp3"
        maxBytes={MAX_BYTES}
        formats="MP3 · WAV · AAC · FLAC"
        sizeLabel="100 MB"
        accentColor="var(--text-cyan)"
        onFile={handleFile}
      />

      {fileError && <p className="error-msg">{fileError}</p>}

      {loading ? (
        <LoadingSpinner color="cyan" message="Running waveform analysis..." />
      ) : (
        <button
          className="scan-btn scan-btn-cyan"
          onClick={handleScan}
          disabled={!file || loading}
        >
          SCAN FOR AI
        </button>
      )}

      {result && !loading && <ResultCard result={result} />}
    </div>
  )
}
