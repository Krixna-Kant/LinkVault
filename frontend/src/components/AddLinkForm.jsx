import { useState } from 'react'
import styles from './AddLinkForm.module.css'

export default function AddLinkForm({ onSave }) {
  const [url, setUrl] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showNotes, setShowNotes] = useState(false)

  const handleSubmit = async () => {
    const trimmed = url.trim()
    if (!trimmed) return

    try {
      setLoading(true)
      setError(null)
      await onSave(trimmed, notes.trim())
      setUrl('')
      setNotes('')
      setShowNotes(false)
    } catch (err) {
      const detail = err.response?.data?.details
      if (detail) {
        setError(detail[0]?.msg || 'Invalid URL')
      } else {
        setError(err.response?.data?.error || 'Failed to save link')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) handleSubmit()
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.icon}>⌘</span>
        <h2 className={styles.title}>Save a link</h2>
        <p className={styles.subtitle}>Paste any URL — AI will classify it and extract deadlines</p>
      </div>

      <div className={styles.inputRow}>
        <input
          className={styles.urlInput}
          type="url"
          placeholder="https://linkedin.com/jobs/..."
          value={url}
          onChange={e => setUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          autoFocus
        />
        <button
          className={styles.saveBtn}
          onClick={handleSubmit}
          disabled={loading || !url.trim()}
        >
          {loading ? <span className={styles.spinner} /> : 'Save'}
        </button>
      </div>

      {!showNotes && (
        <button className={styles.addNoteBtn} onClick={() => setShowNotes(true)}>
          + Add a note
        </button>
      )}

      {showNotes && (
        <textarea
          className={styles.notesInput}
          placeholder="Add a note (optional)..."
          value={notes}
          onChange={e => setNotes(e.target.value)}
          rows={2}
        />
      )}

      {error && <p className={styles.error}>⚠ {error}</p>}
    </div>
  )
}
