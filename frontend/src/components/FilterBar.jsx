import styles from './FilterBar.module.css'

const STATUS_FILTERS = [
  { value: '', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'done', label: 'Done' },
  { value: 'expired', label: 'Expired' },
]

const CATEGORY_FILTERS = [
  { value: '', label: 'All types' },
  { value: 'job', label: '💼 Jobs' },
  { value: 'hackathon', label: '⚡ Hackathons' },
  { value: 'event', label: '📅 Events' },
  { value: 'article', label: '📄 Articles' },
  { value: 'course', label: '🎓 Courses' },
  { value: 'other', label: '🔗 Other' },
]

export default function FilterBar({ status, category, onStatusChange, onCategoryChange, total, expiringSoon }) {
  return (
    <div className={styles.container}>
      <div className={styles.left}>
        <div className={styles.group}>
          {STATUS_FILTERS.map(f => (
            <button
              key={f.value}
              className={`${styles.pill} ${status === f.value ? styles.active : ''}`}
              onClick={() => onStatusChange(f.value)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className={styles.divider} />
        <select
          className={styles.select}
          value={category}
          onChange={e => onCategoryChange(e.target.value)}
        >
          {CATEGORY_FILTERS.map(f => (
            <option key={f.value} value={f.value}>{f.label}</option>
          ))}
        </select>
      </div>

      <div className={styles.right}>
        {expiringSoon > 0 && (
          <span className={styles.urgentChip}>⏰ {expiringSoon} expiring soon</span>
        )}
        <span className={styles.count}>{total} link{total !== 1 ? 's' : ''}</span>
      </div>
    </div>
  )
}
