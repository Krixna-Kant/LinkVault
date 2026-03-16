import { useState, useMemo } from 'react'
import { useLinks } from './hooks/useLinks'
import AddLinkForm from './components/AddLinkForm'
import LinkCard from './components/LinkCard'
import FilterBar from './components/FilterBar'
import styles from './App.module.css'

export default function App() {
  const [statusFilter, setStatusFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')

  const { links, loading, error, saveLink, updateLink, deleteLink } = useLinks({
    status: statusFilter || undefined,
    category: categoryFilter || undefined,
  })

  const expiringSoon = useMemo(
    () => links.filter(l => l.expiring_soon && l.status === 'pending').length,
    [links]
  )

  return (
    <div className={styles.app}>
      <div className={styles.bgGlow} />

      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.logo}>
            <span className={styles.logoMark}>⌘</span>
            <span className={styles.logoText}>LinkVault</span>
          </div>
          <p className={styles.tagline}>Save links. Never miss a deadline.</p>
        </div>
      </header>

      <main className={styles.main}>
        <div className={styles.content}>
          <AddLinkForm onSave={saveLink} />

          <section className={styles.listSection}>
            <FilterBar
              status={statusFilter}
              category={categoryFilter}
              onStatusChange={setStatusFilter}
              onCategoryChange={setCategoryFilter}
              total={links.length}
              expiringSoon={expiringSoon}
            />

            {loading && (
              <div className={styles.state}>
                <div className={styles.loadingDots}>
                  <span /><span /><span />
                </div>
                <p>Loading your links…</p>
              </div>
            )}

            {error && !loading && (
              <div className={styles.state}>
                <p className={styles.errorText}>⚠ {error}</p>
              </div>
            )}

            {!loading && !error && links.length === 0 && (
              <div className={styles.empty}>
                <p className={styles.emptyIcon}>🔗</p>
                <p className={styles.emptyTitle}>No links yet</p>
                <p className={styles.emptySubtitle}>
                  Paste a job listing, hackathon page, or anything with a deadline above.
                </p>
              </div>
            )}

            {!loading && links.length > 0 && (
              <div className={styles.grid}>
                {links.map(link => (
                  <LinkCard
                    key={link.id}
                    link={link}
                    onUpdate={updateLink}
                    onDelete={deleteLink}
                  />
                ))}
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  )
}
