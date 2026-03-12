function LightroomPlan({ plan, styleName }) {
  if (!plan || Object.keys(plan).length === 0) {
    return <p className="muted">No Lightroom plan available</p>
  }

  const presets = plan.presets || {}
  const sliders = plan.manual_sliders || {}

  const freePresets = [presets.free_1, presets.free_2, presets.free].filter(Boolean)
  const paidPreset = presets.paid || presets.premium

  return (
    <div className="lightroom-plan">
      {freePresets.length > 0 && (
        <div className="preset-section">
          <h4>Free Presets</h4>
          {freePresets.map((preset, i) => (
            <div key={i} className="preset-card free">
              <span className="preset-tier">Free</span>
              <strong>{preset.name}</strong>
              <p>{preset.notes}</p>
            </div>
          ))}
        </div>
      )}

      {paidPreset && (
        <div className="preset-section">
          <h4>Paid Option</h4>
          <div className="preset-card paid">
            <span className="preset-tier">
              Paid{paidPreset.price ? ` · ${paidPreset.price}` : ''}
            </span>
            <strong>{paidPreset.name}</strong>
            <p>{paidPreset.notes}</p>
          </div>
        </div>
      )}

      {Object.keys(sliders).length > 0 && (
        <div className="slider-section">
          <h4>Manual Slider Values</h4>
          <p className="muted">Use these if you don't have the presets above.</p>
          <div className="slider-grid">
            {Object.entries(sliders).map(([key, value]) => (
              <div key={key} className="slider-item">
                <span className="slider-name">
                  {key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </span>
                <span className="slider-value">
                  {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default LightroomPlan
