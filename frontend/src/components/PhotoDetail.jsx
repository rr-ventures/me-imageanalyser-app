import { useState, useEffect, useCallback } from 'react'
import CropEditor from './CropEditor'
import {
  processPhoto,
  previewPhotoUrl,
  getPresetRecommendation,
  getCropOptions,
  upscalePreviewUrl,
} from '../api/client'

function PhotoDetail({ photo, result, runId, onClose }) {
  const [previewSrc, setPreviewSrc] = useState(null)
  const originalSrc = `/api/photos/${photo.id}/full`

  // Preset recommendation
  const [recommendation, setRecommendation] = useState(null)
  const [dangerZones, setDangerZones] = useState([])
  const [recLoading, setRecLoading] = useState(false)

  // Crop options (2-3 presets)
  const [cropOptions, setCropOptions] = useState([])
  const [cropOptsLoading, setCropOptsLoading] = useState(false)

  // Crop state
  const [cropMode, setCropMode] = useState(false)
  const [crop, setCrop] = useState({ x: 0, y: 0, w: 100, h: 100 })
  const [appliedCrop, setAppliedCrop] = useState(null)
  const [appliedCropLabel, setAppliedCropLabel] = useState(null)
  const [cropLoading, setCropLoading] = useState(false)

  // Upscale state
  const [upscaleApplied, setUpscaleApplied] = useState(false)
  const [upscaleLoading, setUpscaleLoading] = useState(false)
  const [upscaleSrc, setUpscaleSrc] = useState(null)

  // Adjustments
  const [appliedAdjustments, setAppliedAdjustments] = useState(null)

  // Filename
  const [filename, setFilename] = useState('')

  // Save state
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState(null)

  // Default filename
  useEffect(() => {
    if (!result) {
      setFilename(photo.filename.replace(/\.[^.]+$/, ''))
      return
    }
    const scene = result.metadata?.scene_type || 'photo'
    const date = new Date().toISOString().slice(0, 10)
    setFilename(`${scene}_${result.primary_style || 'edited'}_${date}`)
  }, [photo, result])

  // Load preset + crop recommendations
  useEffect(() => {
    if (!photo?.id) return
    setRecLoading(true)
    setCropOptsLoading(true)

    getPresetRecommendation(photo.id, runId)
      .then(data => {
        setRecommendation(data.recommendation)
        setDangerZones(data.danger_zones || [])
      })
      .catch(() => setRecommendation(null))
      .finally(() => setRecLoading(false))

    getCropOptions(photo.id, runId)
      .then(data => setCropOptions(data.crop_options || []))
      .catch(() => setCropOptions([]))
      .finally(() => setCropOptsLoading(false))
  }, [photo?.id, runId])

  // Refresh preview (crop + adjustments, NOT upscale)
  const refreshPreview = useCallback(async (cropVal, adjVal) => {
    setUpscaleApplied(false)
    setUpscaleSrc(null)

    const hasCrop = cropVal && !(cropVal.x === 0 && cropVal.y === 0 && cropVal.w === 100 && cropVal.h === 100)
    if (!hasCrop && !adjVal) {
      setPreviewSrc(null)
      return
    }
    try {
      const url = await previewPhotoUrl(photo.id, {
        crop: hasCrop ? cropVal : null,
        adjustments: adjVal,
      })
      setPreviewSrc(url)
    } catch {
      /* fall back */
    }
  }, [photo.id])

  // ── Crop preset actions ──
  async function applyCropPreset(option) {
    setCropLoading(true)
    const cropCoords = option.crop
    setCrop(cropCoords)
    setAppliedCrop(cropCoords)
    setAppliedCropLabel(option.scenario_name)
    setCropMode(false)
    await refreshPreview(cropCoords, appliedAdjustments)
    setCropLoading(false)
    setStatus({ type: 'info', message: `"${option.scenario_name}" crop applied.` })
  }

  // Manual crop apply
  async function applyManualCrop() {
    const hasCrop = !(crop.x === 0 && crop.y === 0 && crop.w === 100 && crop.h === 100)
    if (!hasCrop) return
    setCropLoading(true)
    setAppliedCrop(crop)
    setAppliedCropLabel('Manual crop')
    setCropMode(false)
    await refreshPreview(crop, appliedAdjustments)
    setCropLoading(false)
    setStatus({ type: 'info', message: 'Manual crop applied.' })
  }

  function revertCrop() {
    setAppliedCrop(null)
    setAppliedCropLabel(null)
    setCrop({ x: 0, y: 0, w: 100, h: 100 })
    setCropMode(false)
    refreshPreview(null, appliedAdjustments)
    setStatus(null)
  }

  // ── Upscale actions ──
  async function applyUpscale() {
    setUpscaleLoading(true)
    setStatus({ type: 'info', message: 'Upscaling — this takes 10-30 seconds...' })
    try {
      const hasCrop = appliedCrop && !(appliedCrop.x === 0 && appliedCrop.y === 0 && appliedCrop.w === 100 && appliedCrop.h === 100)
      const url = await upscalePreviewUrl(photo.id, {
        crop: hasCrop ? appliedCrop : null,
        adjustments: appliedAdjustments,
      })
      setUpscaleSrc(url)
      setUpscaleApplied(true)
      setStatus({ type: 'info', message: 'Upscale applied to preview.' })
    } catch (err) {
      setStatus({ type: 'error', message: `Upscale failed: ${err.message}` })
    } finally {
      setUpscaleLoading(false)
    }
  }

  function revertUpscale() {
    setUpscaleApplied(false)
    setUpscaleSrc(null)
    setStatus(null)
  }

  // Displayed image priority: upscale > edited preview > original
  const displaySrc = upscaleSrc || previewSrc || originalSrc

  // ── Save ──
  async function handleSave() {
    setSaving(true)
    setStatus(null)
    try {
      const hasCrop = appliedCrop && !(appliedCrop.x === 0 && appliedCrop.y === 0 && appliedCrop.w === 100 && appliedCrop.h === 100)
      const res = await processPhoto(photo.id, {
        rotate: true,
        crop: hasCrop ? appliedCrop : null,
        adjustments: appliedAdjustments,
        upscale: upscaleApplied,
        output_filename: filename || null,
      })
      setStatus({ type: 'success', message: `Saved as ${res.filename}` })
    } catch (err) {
      setStatus({ type: 'error', message: err.message })
    } finally {
      setSaving(false)
    }
  }

  const hasEdits = !!appliedCrop || !!appliedAdjustments || upscaleApplied

  // No analysis results
  if (!result) {
    return (
      <div className="photo-detail-overlay" onClick={onClose}>
        <div className="photo-detail" onClick={e => e.stopPropagation()}>
          <div className="detail-header">
            <h2>{photo.filename}</h2>
            <button className="close-btn" onClick={onClose}>Close</button>
          </div>
          <p className="muted">No analysis results yet. Run analysis from the Dashboard.</p>
          <img src={originalSrc} alt={photo.filename} style={{ width: '100%', borderRadius: 8, marginTop: 16 }} />
        </div>
      </div>
    )
  }

  const preset = recommendation?.preset
  const scenarioName = recommendation?.name

  return (
    <div className="photo-detail-overlay" onClick={onClose}>
      <div className="photo-detail photo-detail-wide" onClick={e => e.stopPropagation()}>
        <div className="detail-header">
          <h2>{photo.filename}</h2>
          <button className="close-btn" onClick={onClose}>Close</button>
        </div>

        <div className="detail-body">
          {/* Left: Photo preview */}
          <div className="detail-photo">
            {cropMode ? (
              <CropEditor
                photoId={photo.id}
                photoWidth={photo.width}
                photoHeight={photo.height}
                crop={crop}
                onCropChange={setCrop}
              />
            ) : (
              <img src={displaySrc} alt={photo.filename} />
            )}

            {hasEdits && !cropMode && (
              <div className="preview-badge">
                {[
                  appliedCrop && 'Cropped',
                  appliedAdjustments && 'Styled',
                  upscaleApplied && 'Upscaled',
                ].filter(Boolean).join(' + ')}
              </div>
            )}
          </div>

          {/* Right: Controls */}
          <div className="detail-info">

            {/* ═══ HERO: Preset Recommendation ═══ */}
            <div className="preset-hero">
              {recLoading ? (
                <p className="muted">Loading recommendation...</p>
              ) : preset ? (
                <>
                  <div className="preset-hero-label">Recommended Lightroom Preset</div>
                  <h3 className="preset-hero-name">{preset.name}</h3>
                  <div className="preset-hero-path">{preset.path}</div>

                  <div className="preset-hero-evidence">
                    <div className="evidence-label">Why this preset works</div>
                    <p>{preset.evidence}</p>
                  </div>

                  {preset.also_apply && (
                    <div className="preset-hero-also">
                      <span className="also-label">Also consider:</span> {preset.also_apply}
                    </div>
                  )}

                  {preset.avoid && (
                    <div className="preset-hero-avoid">
                      <span className="avoid-label">Avoid:</span> {preset.avoid}
                    </div>
                  )}

                  {scenarioName && (
                    <div className="preset-hero-scenario">
                      Detected scenario: <strong>{scenarioName}</strong>
                    </div>
                  )}
                </>
              ) : (
                <p className="muted">No preset recommendation available.</p>
              )}
            </div>

            {/* ═══ CROP PRESETS ═══ */}
            <div className="edit-section">
              <div className="edit-section-header">
                <h3>Crop</h3>
                <div className="edit-section-actions">
                  {appliedCrop && !cropMode && (
                    <>
                      <span className="edit-applied-tag">{appliedCropLabel || 'Applied'}</span>
                      <button className="btn btn-small" onClick={() => setCropMode(true)}>Adjust</button>
                      <button className="btn btn-small btn-danger" onClick={revertCrop}>Revert</button>
                    </>
                  )}
                  {cropMode && (
                    <>
                      <button className="btn btn-small btn-primary" onClick={applyManualCrop} disabled={cropLoading}>
                        {cropLoading ? 'Applying...' : 'Apply'}
                      </button>
                      <button className="btn btn-small" onClick={() => setCropMode(false)}>Cancel</button>
                    </>
                  )}
                  {!appliedCrop && !cropMode && (
                    <button className="btn btn-small" onClick={() => setCropMode(true)}>Manual Crop</button>
                  )}
                </div>
              </div>

              {/* Crop preset cards */}
              {!cropMode && !appliedCrop && (
                <div className="crop-presets">
                  {cropOptsLoading ? (
                    <p className="muted" style={{ padding: '8px 0' }}>Loading crop options...</p>
                  ) : cropOptions.length > 0 ? (
                    cropOptions.map((opt, i) => (
                      <div key={opt.scenario_id} className="crop-preset-card">
                        <div className="crop-preset-header">
                          <div className="crop-preset-title">
                            {i === 0 && <span className="crop-recommended-tag">Recommended</span>}
                            <strong>{opt.scenario_name}</strong>
                            <span className="crop-aspect-tag">{opt.aspect_label}</span>
                          </div>
                          <button
                            className={`btn btn-small ${i === 0 ? 'btn-primary' : ''}`}
                            onClick={() => applyCropPreset(opt)}
                            disabled={cropLoading}
                          >
                            {cropLoading ? '...' : 'Apply'}
                          </button>
                        </div>
                        <p className="crop-preset-evidence">{opt.evidence}</p>
                        {opt.platform_note && (
                          <p className="crop-preset-platform">{opt.platform_note}</p>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="muted" style={{ padding: '8px 0' }}>No crop recommendations for this photo.</p>
                  )}
                </div>
              )}

              {/* Applied crop evidence */}
              {appliedCrop && !cropMode && (() => {
                const matched = cropOptions.find(o =>
                  Math.abs(o.crop.x - appliedCrop.x) < 1 &&
                  Math.abs(o.crop.y - appliedCrop.y) < 1
                )
                if (!matched) return null
                return (
                  <div className="crop-applied-evidence">
                    <p className="crop-preset-evidence">{matched.evidence}</p>
                  </div>
                )
              })()}
            </div>

            {/* ═══ RESOLUTION UPSCALE ═══ */}
            <div className="edit-section">
              <div className="edit-section-header">
                <h3>Resolution Upscale</h3>
                <div className="edit-section-actions">
                  {!upscaleApplied && (
                    <button
                      className="btn btn-small btn-primary"
                      onClick={applyUpscale}
                      disabled={upscaleLoading}
                    >
                      {upscaleLoading ? 'Upscaling...' : 'Apply Upscale'}
                    </button>
                  )}
                  {upscaleApplied && (
                    <>
                      <span className="edit-applied-tag">Applied</span>
                      <button className="btn btn-small btn-danger" onClick={revertUpscale}>Revert</button>
                    </>
                  )}
                </div>
              </div>
              <p className="muted" style={{ fontSize: '0.8rem', marginTop: 6 }}>
                {photo.needs_upscale
                  ? `Short side is ${photo.short_side}px — upscale recommended (min 1080px for dating apps).`
                  : `Resolution OK (${photo.width}x${photo.height}). Apply for extra sharpness.`}
              </p>
              {upscaleLoading && (
                <div className="upscale-progress">
                  <div className="upscale-spinner" />
                  <span>AI upscaling in progress — 10-30 seconds...</span>
                </div>
              )}
            </div>

            {/* ═══ Quick metadata ═══ */}
            <details className="detail-section meta-details">
              <summary className="meta-summary">Photo Analysis Details</summary>
              <div className="metadata-grid" style={{ marginTop: 8 }}>
                <MetaItem label="Scene" value={result.metadata?.scene_type} />
                <MetaItem label="Lighting" value={result.metadata?.lighting} />
                <MetaItem label="Quality" value={`${result.metadata?.photo_quality}/10`} />
                <MetaItem label="Colors" value={result.metadata?.color_quality} />
                <MetaItem label="Face" value={result.metadata?.face_visible} />
                <MetaItem label="Expression" value={result.metadata?.expression} />
              </div>
            </details>

            {/* ═══ Danger Zones ═══ */}
            {dangerZones.length > 0 && (
              <details className="detail-section meta-details">
                <summary className="meta-summary">Presets to Use with Caution</summary>
                <div style={{ padding: '8px 14px' }}>
                  {dangerZones.map((dz, i) => (
                    <div key={i} className="danger-zone-item">
                      <strong>{dz.preset}</strong>
                      <p className="danger-risk">{dz.risk}</p>
                      <p className="danger-safe">{dz.safe_usage}</p>
                    </div>
                  ))}
                </div>
              </details>
            )}

            {/* ═══ SAVE BAR ═══ */}
            <div className="save-bar">
              <div className="filename-row">
                <label className="filename-label">Save as:</label>
                <input
                  type="text"
                  className="filename-input"
                  value={filename}
                  onChange={e => setFilename(e.target.value)}
                />
                <span className="filename-ext">.jpg</span>
              </div>

              <button
                className="btn btn-primary btn-large save-btn"
                onClick={handleSave}
                disabled={saving}
              >
                {saving
                  ? 'Processing...'
                  : hasEdits
                    ? 'Save to Processed'
                    : 'Save Original to Processed'
                }
              </button>
            </div>

            {status && (
              <div className={`action-status ${
                status.type === 'success' ? 'action-success'
                  : status.type === 'error' ? 'action-error'
                    : 'action-info'
              }`}>
                {status.message}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function MetaItem({ label, value }) {
  return (
    <div className="meta-item">
      <span className="meta-label">{label}</span>
      <span className="meta-value">{value ?? '—'}</span>
    </div>
  )
}

export default PhotoDetail
