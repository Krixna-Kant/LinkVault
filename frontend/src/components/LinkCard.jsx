import { useState } from 'react'
import styles from './LinkCard.module.css'

const CATEGORY_META = {
  job:       { label: 'Job',       color: 'blue',   icon: '💼' },
  hackathon: { label: 'Hackathon', color: 'accent', icon: '⚡' },
  event:     { label: 'Event',     color: 'orange', icon: '📅' },
  article:   { label: 'Article',   color: 'green',  icon: '📄' },
  product:   { label: 'Product',   color: 'yellow', icon: '📦' },
  course:    { label: 'Course',    color: 'green',  icon: '🎓' },
  other:     { label: 'Other',     color: 'dim',    icon: '🔗' },
}

const PRIORITY_META = {
  high:   { label: 'High',   color: 'red'    },
  medium: { label: 'Medium', color: 'yellow' },
  low:    { label: 'Low',    color: 'green'  },
}

function formatDeadline(dateStr) {
  if (!dateStr) return null
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = date - now
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))

  if (diffMs < 0) return { text: 'Expired', urgent: true }
  if (diffDays <= 1) return { text: 'Due today', urgent: true }
  if (diffDays <= 3) return { text: `${diffDays}d left`, urgent: true }
  if (diffDays <= 7) return { text: `${diffDays}d left`, urgent: false }
  return { text: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }), urgent: false }
}

function getDomain(url) {
  try { return new URL(url).hostname.replace('www.', '') }
  catch { return url }
}

export default function LinkCard({ link, onUpdate, onDelete }) {
  const [deleting, setDeleting] = useState(false)
  const [updating, setUpdating] = useState(false)

  const category = CATEGORY_META[link.category] || CATEGORY_META.other
  const priority = PRIORITY_META[link.priority] || PRIORITY_META.medium
  const deadline = formatDeadline(link.deadline)
  const isDone = link.status === 'done'
  const isExpired = link.status === 'expired'

  const handleMarkDone = async () => {
    try {
      setUpdating(true)
      await onUpdate(link.id, { status: isDone ? 'pending' : 'done' })
    } finally {
      setUpdating(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm('Delete this link?')) return
    try {
      setDeleting(true)
      await onDelete(link.id)
    } catch {
      setDeleting(false)
    }
  }

  return (
    <div className={`${styles.card} ${isDone ? styles.done : ''} ${isExpired ? styles.expired : ''} ${link.expiring_soon ? styles.expiringSoon : ''}`}>
      {link.expiring_soon && !isDone && (
        <div className={styles.urgentBanner}>⏰ Expiring soon</div>
      )}

      <div className={styles.top}>
        <div className={styles.meta}>
          <span className={`${styles.categoryBadge} ${styles[`color_${category.color}`]}`}>
            {category.icon} {category.label}
          </span>
          <span className={`${styles.priorityDot} ${styles[`dot_${priority.color}`]}`} title={`${priority.label} priority`} />
          <span className={styles.domain}>{getDomain(link.url)}</span>
        </div>
        <div className={styles.actions}>
          <button
            className={`${styles.doneBtn} ${isDone ? styles.doneBtnActive : ''}`}
            onClick={handleMarkDone}
            disabled={updating || isExpired}
            title={isDone ? 'Mark as pending' : 'Mark as done'}
          >
            {updating ? '…' : isDone ? '✓ Done' : 'Mark done'}
          </button>
          <button className={styles.deleteBtn} onClick={handleDelete} disabled={deleting} title="Delete">
            {deleting ? '…' : '×'}
          </button>
        </div>
      </div>

      <a href={link.url} target="_blank" rel="noopener noreferrer" className={styles.titleLink}>
        <h3 className={styles.title}>{link.title}</h3>
      </a>

      {link.summary && (
        <p className={styles.summary}>{link.summary}</p>
      )}

      {link.notes && (
        <p className={styles.notes}>💬 {link.notes}</p>
      )}

      <div className={styles.bottom}>
        {deadline && (
          <span className={`${styles.deadline} ${deadline.urgent ? styles.deadlineUrgent : ''}`}>
            {isExpired ? '🔴' : deadline.urgent ? '🟡' : '🟢'} {deadline.text}
          </span>
        )}
        <span className={styles.savedAt}>
          Saved {new Date(link.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </span>
      </div>
    </div>
  )
}
