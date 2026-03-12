import { useState, useEffect, useCallback } from 'react'
import { getSliderRanges, applyEdits, previewEditsUrl } from '../api/client'

function SliderEditor({ photoId, style, onApplied }) {
  const [sliders, setSliders] = useState(null)
  const [values, setValues] = useState({})
  const [enabled, setEnabled] = useState({})
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(false)
  const [previewing, setPreviewing] = useState(false)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [status, setStatus] = useState(null)
  const [useMin, setUseMin] = useState({})

  useEffect(() => {
    if (!photoId || !style) return
    setLoading(true)
    getSliderRanges(photoId, style)
      .then(data => {
        const s = data.sliders || {}
        setSliders(s)

        const initValues = {}
        const initEnabled = {}
        const initUseMin = {}
        Object.entries(s).forEach(([key, info]) => {
          if (info.is_bool) {
            initValues[key] = info.raw ? 1 : 0
            initEnabled[key] = !!info.raw
          } else {
            initValues[key] = (info.min + info.max) / 2
            initEnabled[key] = true
          }
          initUseMin[key] = false
        })
        setValues(initValues)
        setEnabled(initEnabled)
        setUseMin(initUseMin)
      })
      .catch(() => setSliders(null))
      .finally(() => setLoading(false))
  }, [photoId, style])

  function toggleSlider(key) {
    setEnabled(prev => ({ ...prev, [key]: !prev[key] }))
  }

  function setSliderValue(key, val) {
    setValues(prev => ({ ...prev, [key]: parseFloat(val) }))
  }

  function setToMin(key) {
    if (!sliders[key]) return
    setValues(prev => ({ ...prev, [key]: sliders[key].min }))
    setUseMin(prev => ({ ...prev, [key]: true }))
  }

  function setToMax(key) {
    if (!sliders[key]) return
    setValues(prev => ({ ...prev, [key]: sliders[key].max }))
    setUseMin(prev => ({ ...prev, [key]: false }))
  }

  function getActiveAdjustments() {
    const adjustments = {}
    Object.entries(enabled).forEach(([key, on]) => {
      if (on && sliders[key]) {
        if (sliders[key].is_bool) {
          adjustments[key] = values[key] > 0.5
        } else {
          adjustments[key] = values[key]
        }
      }
    })
    return adjustments
  }

  function enableAll() {
    const next = {}
    Object.keys(sliders).forEach(k => { next[k] = true })
    setEnabled(next)
  }

  function disableAll() {
    const next = {}
    Object.keys(sliders).forEach(k => { next[k] = false })
    setEnabled(next)
  }

  const handlePreview = useCallback(async () => {
    setPreviewing(true)
    setStatus(null)
    try {
      const adj = getActiveAdjustments()
      if (Object.keys(adj).length === 0) {
        setStatus({ type: 'error', message: 'Enable at least one slider' })
        return
      }
      const url = await previewEditsUrl(photoId, adj)
      setPreviewUrl(url)
    } catch (err) {
      setStatus({ type: 'error', message: `Preview failed: ${err.message}` })
    } finally {
      setPreviewing(false)
    }
  }, [photoId, enabled, values, sliders])

  async function handleApply() {
    setApplying(true)
    setStatus(null)
    try {
      const adj = getActiveAdjustments()
      if (Object.keys(adj).length === 0) {
        setStatus({ type: 'error', message: 'Enable at least one slider' })
        return
      }
      const res = await applyEdits(photoId, adj)
      setStatus({ type: 'success', message: `Saved as ${res.filename}` })
      if (onApplied) onApplied(res)
    } catch (err) {
      setStatus({ type: 'error', message: `Apply failed: ${err.message}` })
    } finally {
      setApplying(false)
    }
  }

  if (loading) {
    return <p className="muted">Loading sliders...</p>
  }

  if (!sliders || Object.keys(sliders).length === 0) {
    return <p className="muted">No adjustable sliders for this style</p>
  }

  const enabledCount = Object.values(enabled).filter(Boolean).length

  return (
    <div className="slider-editor">
      <div className="slider-editor-header">
        <h4>Auto-Apply Adjustments</h4>
        <div className="slider-editor-controls">
          <button className="btn btn-small" onClick={enableAll}>All On</button>
          <button className="btn btn-small" onClick={disableAll}>All Off</button>
        </div>
      </div>
      <p className="muted" style={{ marginBottom: 12 }}>
        Toggle sliders on/off. Drag to set values within the recommended range. Click Min/Max to snap to ends.
      </p>

      <div className="slider-editor-list">
        {Object.entries(sliders).map(([key, info]) => {
          if (info.is_bool) {
            return (
              <div key={key} className={`editor-slider-row ${enabled[key] ? '' : 'disabled-slider'}`}>
                <label className="slider-toggle">
                  <input
                    type="checkbox"
                    checked={enabled[key] || false}
                    onChange={() => toggleSlider(key)}
                  />
                  <span className="slider-toggle-label">{info.label}</span>
                </label>
                <span className="slider-range-text">
                  {enabled[key] ? 'On' : 'Off'}
                </span>
              </div>
            )
          }

          const step = Math.abs(info.max - info.min) < 1 ? 0.01
            : Math.abs(info.max - info.min) < 10 ? 0.1
            : 1

          return (
            <div key={key} className={`editor-slider-row ${enabled[key] ? '' : 'disabled-slider'}`}>
              <div className="slider-row-top">
                <label className="slider-toggle">
                  <input
                    type="checkbox"
                    checked={enabled[key] || false}
                    onChange={() => toggleSlider(key)}
                  />
                  <span className="slider-toggle-label">{info.label}</span>
                </label>
                <span className="slider-current-value">
                  {enabled[key] ? values[key]?.toFixed(step < 1 ? 2 : 0) : '—'}
                </span>
              </div>
              {enabled[key] && (
                <div className="slider-row-bottom">
                  <button
                    className="btn btn-tiny"
                    onClick={() => setToMin(key)}
                    title={`Set to ${info.min}`}
                  >
                    {info.min}
                  </button>
                  <input
                    type="range"
                    min={info.min}
                    max={info.max}
                    step={step}
                    value={values[key] ?? info.min}
                    onChange={e => setSliderValue(key, e.target.value)}
                    className="range-input"
                  />
                  <button
                    className="btn btn-tiny"
                    onClick={() => setToMax(key)}
                    title={`Set to ${info.max}`}
                  >
                    {info.max}
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="slider-editor-actions">
        <button
          className="btn btn-action btn-preview"
          onClick={handlePreview}
          disabled={previewing || enabledCount === 0}
        >
          {previewing ? 'Generating...' : 'Preview'}
        </button>
        <button
          className="btn btn-action btn-apply-edits"
          onClick={handleApply}
          disabled={applying || enabledCount === 0}
        >
          {applying ? 'Applying...' : `Apply ${enabledCount} Adjustment${enabledCount !== 1 ? 's' : ''}`}
        </button>
      </div>

      {previewUrl && (
        <div className="edit-preview">
          <h4>Preview</h4>
          <img src={previewUrl} alt="Edit preview" />
        </div>
      )}

      {status && (
        <div className={`action-status ${status.type === 'success' ? 'action-success' : 'action-error'}`}>
          {status.message}
        </div>
      )}
    </div>
  )
}

export default SliderEditor
