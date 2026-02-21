import { useState } from 'react'
import axios from 'axios'
import UploadZone from './UploadZone'
import LoadingSpinner from './LoadingSpinner'
import ResultCard from './ResultCard'

const API = 'http://localhost:8000/detect/video'
const MAX_BYTES = 500 * 1024 * 1024

export default function VideoPanel({ onError }) {
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
        timeout: 120000, // 2 min — video takes longer
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
        accept="video/mp4,video/quicktime,video/webm"
        maxBytes={MAX_BYTES}
        formats="MP4 · MOV · WEBM"
        sizeLabel="500 MB"
        accentColor="var(--text-pink)"
        onFile={handleFile}
      />

      {fileError && <p className="error-msg">{fileError}</p>}

      {loading ? (
        <LoadingSpinner color="pink" message="Analyzing frames for deepfakes..." />
      ) : (
        <button
          className="scan-btn scan-btn-pink"
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
