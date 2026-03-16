import { useState, useEffect, useCallback } from 'react'
import { linkApi } from '../services/api'

export function useLinks(filters = {}) {
  const [links, setLinks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchLinks = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await linkApi.list(filters)
      setLinks(data)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load links')
    } finally {
      setLoading(false)
    }
  }, [filters.status, filters.category])

  useEffect(() => {
    fetchLinks()
  }, [fetchLinks])

  const saveLink = async (url, notes) => {
    const link = await linkApi.save(url, notes)
    setLinks(prev => [link, ...prev])
    return link
  }

  const updateLink = async (id, data) => {
    const updated = await linkApi.update(id, data)
    setLinks(prev => prev.map(l => l.id === id ? updated : l))
    return updated
  }

  const deleteLink = async (id) => {
    await linkApi.delete(id)
    setLinks(prev => prev.filter(l => l.id !== id))
  }

  return { links, loading, error, saveLink, updateLink, deleteLink, refetch: fetchLinks }
}
