/*
 * LEARNING NOTE: Settings page — model info and app configuration.
 *
 * This is a simple page that displays available models and their pricing.
 * In a full app, this would also have user preferences, API key management, etc.
 *
 * COMPONENT LIFECYCLE:
 *   1. React renders the component → you see "Loading..."
 *   2. useEffect fires → fetches models from API
 *   3. State updates → React re-renders with the model data
 *   4. You see the model cards
 *
 *   This render → fetch → update → re-render cycle is the core
 *   pattern of every React app.
 */
import { useState, useEffect } from 'react'
import { listModels } from '../api/client'

function Settings() {
  const [models, setModels] = useState([])
  const [defaultModel, setDefaultModel] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listModels()
      .then(data => {
        setModels(data.models || [])
        setDefaultModel(data.default || '')
      })
      .catch(err => console.error('Failed to load models:', err))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>Settings</h1>
        <p className="page-subtitle">Available AI models and pricing</p>
      </div>

      {loading ? (
        <p className="muted">Loading models...</p>
      ) : (
        <div className="models-grid">
          {models.map(model => (
            <div
              key={model.id}
              className={`model-card ${model.id === defaultModel ? 'model-default' : ''}`}
            >
              <div className="model-card-header">
                <h3>{model.display_name}</h3>
                {model.id === defaultModel && (
                  <span className="default-badge">Default</span>
                )}
              </div>
              <p className="model-description">{model.description}</p>
              <div className="model-pricing">
                <div className="price-row">
                  <span>Input</span>
                  <span>${model.input_per_1m_tokens} / 1M tokens</span>
                </div>
                <div className="price-row">
                  <span>Output</span>
                  <span>${model.output_per_1m_tokens} / 1M tokens</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="section">
        <h2>About</h2>
        <p>
          Lightroom Preset Selector v3.0 — AI analyzes your dating profile
          photos and recommends the single best Lightroom preset for each one,
          backed by dating market research. Also includes crop, rotation, and
          resolution upscaling tools.
        </p>
        <p className="muted">
          Your photos are processed locally. Only image data is sent to Google's
          Gemini API for analysis. No photos are stored externally.
        </p>
      </div>
    </div>
  )
}

export default Settings
