/*
 * LEARNING NOTE: ModelSelector — dropdown to choose the Gemini model.
 *
 * WHAT'S useEffect()?
 *   useEffect runs code AFTER the component renders.
 *   It's used for "side effects" like fetching data from an API.
 *
 *   Python analogy:
 *     class ModelSelector:
 *         def __init__(self):
 *             self.models = []
 *             self._fetch_models()  # runs after init
 *
 *   React:
 *     useEffect(() => { fetchModels() }, [])
 *     The [] means "run this only once, when the component first appears."
 *
 * WHAT'S onChange?
 *   It's an event handler — a function that runs when the user
 *   selects a different option in the dropdown.
 *   Python equivalent: a callback function.
 */
import { useState, useEffect } from 'react'
import { listModels } from '../api/client'

function ModelSelector({ selectedModel, onModelChange }) {
  // State: the list of available models (loaded from the API)
  const [models, setModels] = useState([])
  const [loading, setLoading] = useState(true)

  // Load models from the backend when this component first appears
  useEffect(() => {
    listModels()
      .then(data => {
        setModels(data.models || [])
        if (!selectedModel && data.default) {
          onModelChange(data.default)
        }
      })
      .catch(err => console.error('Failed to load models:', err))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <span className="muted">Loading models...</span>
  }

  return (
    <div className="model-selector">
      <label htmlFor="model-select">Analysis Model</label>
      <select
        id="model-select"
        value={selectedModel || ''}
        onChange={e => onModelChange(e.target.value)}
        className="select-input"
      >
        {models.map(model => (
          <option key={model.id} value={model.id}>
            {model.display_name} — ${model.input_per_1m_tokens}/1M in, ${model.output_per_1m_tokens}/1M out
          </option>
        ))}
      </select>
      {selectedModel && models.length > 0 && (
        <p className="model-description">
          {models.find(m => m.id === selectedModel)?.description}
        </p>
      )}
    </div>
  )
}

export default ModelSelector
