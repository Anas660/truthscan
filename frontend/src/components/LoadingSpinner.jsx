export default function LoadingSpinner({ color = 'yellow', message }) {
  return (
    <div className="loading-container">
      <div className={`spinner spinner-${color}`} />
      {message && <p className="loading-msg">{message}</p>}
    </div>
  )
}
