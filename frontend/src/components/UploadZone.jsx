import { useState, useRef } from 'react'

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function UploadZone({ accept, maxBytes, formats, sizeLabel, accentColor, onFile }) {
  const [dragOver, setDragOver] = useState(false)
  const [file, setFile]         = useState(null)
  const inputRef                = useRef(null)

  const handleFile = (f) => {
    if (!f) return
    if (f.size > maxBytes) {
      onFile(null, `File too large. Max size is ${sizeLabel}.`)
      return
    }
    setFile(f)
    onFile(f, null)
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files?.[0]
    if (f) handleFile(f)
  }

  const onChange = (e) => {
    const f = e.target.files?.[0]
    if (f) handleFile(f)
  }

  // % of maxBytes for visual bar (capped at 100%)
  const fillPct = file ? Math.min((file.size / maxBytes) * 100, 100) : 0

  return (
    <>
      <div
        className={`upload-zone${dragOver ? ' drag-over' : ''}`}
        style={{ '--accent-color': accentColor }}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={onChange}
          onClick={(e) => e.stopPropagation()}
        />
        <span className="upload-icon">📂</span>
        <p className="upload-title">Drag & drop or click to upload</p>
        <p className="upload-hint">Click anywhere in this area to browse</p>
        <p className="upload-formats">{formats} · Max {sizeLabel}</p>
      </div>

      {file && (
        <div className="file-preview">
          <p className="file-preview-name">📄 {file.name}</p>
          <p className="file-preview-size">{formatBytes(file.size)}</p>
          <div className="file-progress-bar">
            <div
              className="file-progress-fill"
              style={{ width: `${fillPct}%`, background: accentColor }}
            />
          </div>
        </div>
      )}
    </>
  )
}
