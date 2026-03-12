/*
 * LEARNING NOTE: Dashboard — the home page / main screen.
 *
 * This page handles:
 * 1. Scanning for photos in to_process/
 * 2. Letting you choose the AI model
 * 3. Starting analysis (single or batch)
 * 4. Showing past runs
 *
 * REACT STATE MANAGEMENT:
 *   This component has several pieces of state:
 *   - photos: the list of photos found in to_process/
 *   - model: which Gemini model to use
 *   - analyzing: whether analysis is currently running
 *   - error: any error message to display
 *
 *   Each piece of state is independent. When one changes,
 *   React only re-renders the parts of the UI that depend on it.
 *
 * ASYNC/AWAIT IN REACT:
 *   API calls in React work the same as in Python:
 *   Python:  result = await analyze_batch(model, limit)
 *   JS:     const result = await analyzeBatch(model, limit)
 *
 *   The difference: in React, we call these inside useEffect() or
 *   event handlers, and update state when the response arrives.
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { listPhotos, analyzeBatch, listRuns } from '../api/client'
import PhotoGrid from '../components/PhotoGrid'
import ModelSelector from '../components/ModelSelector'
import CostEstimate from '../components/CostEstimate'

function Dashboard() {
  // State variables (like Python instance variables, but React-aware)
  const [photos, setPhotos] = useState([])
  const [model, setModel] = useState(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState(null)
  const [runs, setRuns] = useState([])
  const [batchLimit, setBatchLimit] = useState(0)

  // useNavigate lets us redirect to another page programmatically
  const navigate = useNavigate()

  // Load photos and past runs when the page first appears
  useEffect(() => {
    loadPhotos()
    loadRuns()
  }, [])

  async function loadPhotos() {
    setLoading(true)
    setError(null)
    try {
      const data = await listPhotos()
      setPhotos(data.photos || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadRuns() {
    try {
      const data = await listRuns()
      setRuns(data.runs || [])
    } catch {
      // Past runs are non-critical, ignore errors
    }
  }

  async function handleAnalyze() {
    setAnalyzing(true)
    setError(null)
    try {
      const limit = batchLimit > 0 ? batchLimit : undefined
      const result = await analyzeBatch(model, limit)
      // Redirect to the analysis results page
      navigate(`/analysis/${result.run_id}`)
    } catch (err) {
      setError(err.message)
      setAnalyzing(false)
    }
  }

  const photoCount = photos.length

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p className="page-subtitle">
          AI-powered Lightroom preset recommendations for dating profile photos
        </p>
      </div>

      {/* Error display */}
      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
          <button onClick={() => setError(null)} className="alert-dismiss">Dismiss</button>
        </div>
      )}

      {/* Analysis controls */}
      <div className="dashboard-controls">
        <div className="control-card">
          <h2>Photos</h2>
          {loading ? (
            <p className="muted">Scanning for photos...</p>
          ) : (
            <>
              <div className="stat-big">{photoCount}</div>
              <p className="muted">photos in to_process/</p>
              <button onClick={loadPhotos} className="btn btn-secondary">
                Refresh
              </button>
            </>
          )}
        </div>

        <div className="control-card">
          <h2>Model</h2>
          <ModelSelector
            selectedModel={model}
            onModelChange={setModel}
          />
        </div>

        <div className="control-card">
          <h2>Batch Size</h2>
          <input
            type="number"
            min="0"
            max={photoCount}
            value={batchLimit}
            onChange={e => setBatchLimit(parseInt(e.target.value) || 0)}
            className="number-input"
            placeholder="0 = all"
          />
          <p className="muted">
            {batchLimit > 0
              ? `Analyze first ${batchLimit} of ${photoCount} photos`
              : `Analyze all ${photoCount} photos`}
          </p>
          <CostEstimate
            model={model}
            numImages={batchLimit > 0 ? batchLimit : photoCount}
          />
        </div>

        <div className="control-card">
          <h2>Go</h2>
          <button
            onClick={handleAnalyze}
            disabled={analyzing || photoCount === 0 || !model}
            className="btn btn-primary btn-large"
          >
            {analyzing ? 'Analyzing...' : `Analyze ${batchLimit > 0 ? batchLimit : photoCount} Photos`}
          </button>
          {analyzing && (
            <p className="muted">
              This may take a minute. Results will appear when ready.
            </p>
          )}
        </div>
      </div>

      {/* Past runs */}
      {runs.length > 0 && (
        <div className="section">
          <h2>Past Runs</h2>
          <div className="runs-list">
            {runs.map(run => (
              <div
                key={run.run_id}
                className="run-card"
                onClick={() => navigate(`/analysis/${run.run_id}`)}
              >
                <div className="run-card-header">
                  <strong>{run.run_id}</strong>
                  <span className="run-model">{run.model}</span>
                </div>
                <div className="run-card-stats">
                  <span>{run.total_analyzed} analyzed</span>
                  {run.total_errors > 0 && (
                    <span className="text-error">{run.total_errors} errors</span>
                  )}
                  <span>${run.estimated_cost_usd?.toFixed(4)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Photo grid preview */}
      {photos.length > 0 && !analyzing && (
        <div className="section">
          <h2>Photos Preview</h2>
          <PhotoGrid photos={photos} />
        </div>
      )}

      {/* Empty state */}
      {!loading && photos.length === 0 && (
        <div className="empty-state-large">
          <h2>No photos found</h2>
          <p>
            Drop your dating profile photos into the <code>data/to_process/</code> folder,
            then click Refresh.
          </p>
        </div>
      )}
    </div>
  )
}

export default Dashboard
