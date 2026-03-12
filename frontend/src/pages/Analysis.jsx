import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getRun, listPhotos, batchProcess } from '../api/client'
import PhotoGrid from '../components/PhotoGrid'
import PhotoDetail from '../components/PhotoDetail'

function Analysis() {
  const { runId } = useParams()
  const [run, setRun] = useState(null)
  const [photos, setPhotos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedPhoto, setSelectedPhoto] = useState(null)
  const [selectedResult, setSelectedResult] = useState(null)

  const [selectedIds, setSelectedIds] = useState(new Set())
  const [batchActions, setBatchActions] = useState({ rotate: true, upscale: true, save: false })
  const [batchRunning, setBatchRunning] = useState(false)
  const [batchStatus, setBatchStatus] = useState(null)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const [runData, photoData] = await Promise.all([
          getRun(runId),
          listPhotos(),
        ])
        setRun(runData)
        setPhotos(photoData.photos || [])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [runId])

  function handlePhotoClick(photo, result) {
    setSelectedPhoto(photo)
    setSelectedResult(result)
  }

  function togglePhotoSelection(photoId) {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(photoId)) next.delete(photoId)
      else next.add(photoId)
      return next
    })
  }

  function selectAllNeeding(type) {
    const ids = photos
      .filter(p => type === 'upscale' ? p.needs_upscale : p.needs_rotation)
      .map(p => p.id)
    setSelectedIds(new Set(ids))
  }

  function selectNone() {
    setSelectedIds(new Set())
  }

  async function handleBatchProcess() {
    if (selectedIds.size === 0) return
    setBatchRunning(true)
    setBatchStatus(null)
    try {
      const actions = Object.entries(batchActions)
        .filter(([, on]) => on)
        .map(([action]) => action)
      if (actions.length === 0) {
        setBatchStatus({ type: 'error', message: 'Select at least one action' })
        return
      }
      const res = await batchProcess([...selectedIds], actions)
      const totalActions = res.results.reduce((sum, r) => sum + r.actions.filter(a => a.status === 'ok').length, 0)
      const totalErrors = res.results.reduce((sum, r) => sum + r.actions.filter(a => a.status === 'error').length, 0) + (res.errors?.length || 0)
      setBatchStatus({
        type: totalErrors > 0 ? 'warning' : 'success',
        message: `Processed ${res.results.length} photos: ${totalActions} actions completed${totalErrors > 0 ? `, ${totalErrors} errors` : ''}`,
      })
    } catch (err) {
      setBatchStatus({ type: 'error', message: `Batch processing failed: ${err.message}` })
    } finally {
      setBatchRunning(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-page">
        <h1>Loading results...</h1>
        <p className="muted">Fetching run {runId}</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-page">
        <h1>Error</h1>
        <p className="text-error">{error}</p>
        <Link to="/" className="btn btn-secondary">Back to Dashboard</Link>
      </div>
    )
  }

  if (!run) {
    return (
      <div className="error-page">
        <h1>Run not found</h1>
        <Link to="/" className="btn btn-secondary">Back to Dashboard</Link>
      </div>
    )
  }

  const results = run.results || []
  const errors = run.errors || []

  // Preset distribution
  const presetCounts = {}
  results.forEach(r => {
    const preset = r.preset_recommendation?.preset?.name || 'No recommendation'
    presetCounts[preset] = (presetCounts[preset] || 0) + 1
  })

  const rotationPhotos = photos.filter(p => p.needs_rotation)
  const upscalePhotos = photos.filter(p => p.needs_upscale)
  const needsRotation = rotationPhotos.length
  const needsUpscale = upscalePhotos.length

  return (
    <div className="analysis-page">
      <div className="page-header">
        <div>
          <h1>Preset Recommendations</h1>
          <p className="page-subtitle">
            Run: {run.run_id} &middot; Model: {run.model} &middot; {results.length} photos analyzed
          </p>
        </div>
        <Link to="/" className="btn btn-secondary">Back to Dashboard</Link>
      </div>

      {/* Summary stats */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{run.total_analyzed}</div>
          <div className="stat-label">Analyzed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{Object.keys(presetCounts).length}</div>
          <div className="stat-label">Unique Presets</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">${run.estimated_cost_usd?.toFixed(4)}</div>
          <div className="stat-label">Cost</div>
        </div>
        {needsRotation > 0 && (
          <div className="stat-card stat-warning">
            <div className="stat-value">{needsRotation}</div>
            <div className="stat-label">Need Rotation</div>
          </div>
        )}
        {needsUpscale > 0 && (
          <div className="stat-card stat-warning">
            <div className="stat-value">{needsUpscale}</div>
            <div className="stat-label">Need Upscale</div>
          </div>
        )}
      </div>

      {/* Preset distribution */}
      {Object.keys(presetCounts).length > 0 && (
        <div className="section">
          <h2>Preset Distribution</h2>
          <div className="preset-distribution">
            {Object.entries(presetCounts)
              .sort(([, a], [, b]) => b - a)
              .map(([preset, count]) => (
                <div key={preset} className="preset-dist-item">
                  <span className="preset-dist-name">{preset}</span>
                  <span className="preset-dist-count">{count}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Batch Processing Panel */}
      {(needsRotation > 0 || needsUpscale > 0) && (
        <div className="section">
          <h2>Batch Processing</h2>
          <div className="batch-panel">
            <p className="muted" style={{ marginBottom: 12 }}>
              Select photos to process in batch. Tick the actions to apply, then hit Process.
            </p>

            <div className="batch-select-row">
              <span className="batch-label">Quick select:</span>
              {needsRotation > 0 && (
                <button className="btn btn-small" onClick={() => selectAllNeeding('rotation')}>
                  All needing rotation ({needsRotation})
                </button>
              )}
              {needsUpscale > 0 && (
                <button className="btn btn-small" onClick={() => selectAllNeeding('upscale')}>
                  All needing upscale ({needsUpscale})
                </button>
              )}
              <button className="btn btn-small" onClick={selectNone}>
                Clear selection
              </button>
            </div>

            <div className="batch-photo-list">
              {photos.filter(p => p.needs_rotation || p.needs_upscale).map(p => (
                <label key={p.id} className={`batch-photo-item ${selectedIds.has(p.id) ? 'selected' : ''}`}>
                  <input
                    type="checkbox"
                    checked={selectedIds.has(p.id)}
                    onChange={() => togglePhotoSelection(p.id)}
                  />
                  <img src={p.thumbnail_url} alt={p.filename} className="batch-thumb" />
                  <div className="batch-photo-info">
                    <span className="batch-photo-name">{p.filename.length > 25 ? p.filename.slice(0, 22) + '...' : p.filename}</span>
                    <span className="batch-photo-tags">
                      {p.needs_rotation && <span className="issue-badge rotation-badge inline-badge">R</span>}
                      {p.needs_upscale && <span className="issue-badge upscale-badge inline-badge">U</span>}
                      <span className="muted">{p.width}x{p.height}</span>
                    </span>
                  </div>
                </label>
              ))}
            </div>

            <div className="batch-actions-row">
              <div className="batch-action-toggles">
                <label className="batch-action-toggle">
                  <input
                    type="checkbox"
                    checked={batchActions.rotate}
                    onChange={e => setBatchActions(prev => ({ ...prev, rotate: e.target.checked }))}
                  />
                  Fix Rotation
                </label>
                <label className="batch-action-toggle">
                  <input
                    type="checkbox"
                    checked={batchActions.upscale}
                    onChange={e => setBatchActions(prev => ({ ...prev, upscale: e.target.checked }))}
                  />
                  Upscale Resolution
                </label>
                <label className="batch-action-toggle">
                  <input
                    type="checkbox"
                    checked={batchActions.save}
                    onChange={e => setBatchActions(prev => ({ ...prev, save: e.target.checked }))}
                  />
                  Save Copy
                </label>
              </div>

              <button
                className="btn btn-primary btn-large"
                disabled={batchRunning || selectedIds.size === 0}
                onClick={handleBatchProcess}
              >
                {batchRunning ? 'Processing...' : `Process ${selectedIds.size} Photo${selectedIds.size !== 1 ? 's' : ''}`}
              </button>
            </div>

            {batchStatus && (
              <div className={`action-status ${batchStatus.type === 'success' ? 'action-success' : batchStatus.type === 'warning' ? 'action-warning' : 'action-error'}`}>
                {batchStatus.message}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Errors */}
      {errors.length > 0 && (
        <div className="section">
          <h2 className="text-error">Errors ({errors.length})</h2>
          <div className="error-list">
            {errors.map((err, i) => (
              <div key={i} className="error-item">
                <strong>{err.filename}</strong>: {err.error}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results grid */}
      <div className="section">
        <h2>Your Photos ({results.length})</h2>
        <p className="muted" style={{ marginBottom: 12 }}>
          Click any photo to see its recommended Lightroom preset, crop, or save.
        </p>
        <PhotoGrid
          photos={photos}
          results={results}
          onPhotoClick={handlePhotoClick}
        />
      </div>

      {/* Photo detail modal */}
      {selectedPhoto && (
        <PhotoDetail
          photo={selectedPhoto}
          result={selectedResult}
          runId={runId}
          onClose={() => {
            setSelectedPhoto(null)
            setSelectedResult(null)
          }}
        />
      )}
    </div>
  )
}

export default Analysis
