/*
 * LEARNING NOTE: CostEstimate — shows batch cost before processing.
 *
 * WHAT'S useEffect WITH DEPENDENCIES?
 *   useEffect(() => { ... }, [model, numImages])
 *
 *   The second argument [model, numImages] is the "dependency array."
 *   It means: "re-run this effect whenever model or numImages changes."
 *
 *   Think of it like a Python property with a watcher:
 *     @watch('model', 'num_images')
 *     def update_cost(self):
 *         self.cost = estimate(self.model, self.num_images)
 */
import { useState, useEffect } from 'react'
import { estimateCost } from '../api/client'

function CostEstimate({ model, numImages }) {
  const [estimate, setEstimate] = useState(null)

  useEffect(() => {
    if (!model || !numImages || numImages <= 0) {
      setEstimate(null)
      return
    }

    estimateCost(model, numImages)
      .then(data => setEstimate(data))
      .catch(() => setEstimate(null))
  }, [model, numImages])

  if (!estimate) return null

  return (
    <div className="cost-estimate">
      <span className="cost-label">Estimated cost:</span>
      <span className="cost-value">${estimate.estimated_cost_usd.toFixed(4)}</span>
      <span className="cost-detail">
        ({estimate.estimated_input_tokens.toLocaleString()} input +{' '}
        {estimate.estimated_output_tokens.toLocaleString()} output tokens)
      </span>
    </div>
  )
}

export default CostEstimate
