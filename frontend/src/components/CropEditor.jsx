import { useState, useRef, useCallback } from 'react'

const ASPECT_RATIOS = [
  { label: 'Free', value: null },
  { label: '1:1', value: 1 },
  { label: '4:5', value: 4 / 5 },
  { label: '3:4', value: 3 / 4 },
  { label: '9:16', value: 9 / 16 },
]

function CropEditor({ photoId, photoWidth, photoHeight, crop, onCropChange }) {
  const [aspect, setAspect] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [dragStart, setDragStart] = useState(null)
  const imgRef = useRef(null)

  const x = crop?.x ?? 0
  const y = crop?.y ?? 0
  const w = crop?.w ?? 100
  const h = crop?.h ?? 100

  function getRelativePos(e) {
    const rect = imgRef.current.getBoundingClientRect()
    return {
      px: Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100)),
      py: Math.max(0, Math.min(100, ((e.clientY - rect.top) / rect.height) * 100)),
    }
  }

  function handleMouseDown(e) {
    e.preventDefault()
    const pos = getRelativePos(e)
    setDragging(true)
    setDragStart(pos)
  }

  const handleMouseMove = useCallback((e) => {
    if (!dragging || !dragStart) return
    const pos = getRelativePos(e)
    let newX = Math.min(dragStart.px, pos.px)
    let newY = Math.min(dragStart.py, pos.py)
    let newW = Math.abs(pos.px - dragStart.px)
    let newH = Math.abs(pos.py - dragStart.py)

    if (aspect) {
      const imgAspect = photoWidth / photoHeight
      const cropAspectInPx = aspect
      const cropAspectInPct = cropAspectInPx * (photoHeight / photoWidth)
      newH = newW / cropAspectInPct
      if (newY + newH > 100) {
        newH = 100 - newY
        newW = newH * cropAspectInPct
      }
    }

    newW = Math.max(5, Math.min(newW, 100 - newX))
    newH = Math.max(5, Math.min(newH, 100 - newY))

    onCropChange({ x: newX, y: newY, w: newW, h: newH })
  }, [dragging, dragStart, aspect, photoWidth, photoHeight, onCropChange])

  function handleMouseUp() {
    setDragging(false)
    setDragStart(null)
  }

  function handleAspectChange(ratio) {
    setAspect(ratio)
    if (ratio === null) {
      onCropChange({ x: 0, y: 0, w: 100, h: 100 })
      return
    }
    const imgAspect = photoWidth / photoHeight
    const cropAspectInPct = ratio * (photoHeight / photoWidth)
    let newW = 80
    let newH = newW / cropAspectInPct
    if (newH > 80) {
      newH = 80
      newW = newH * cropAspectInPct
    }
    onCropChange({
      x: (100 - newW) / 2,
      y: (100 - newH) / 2,
      w: newW,
      h: newH,
    })
  }

  function resetCrop() {
    setAspect(null)
    onCropChange({ x: 0, y: 0, w: 100, h: 100 })
  }

  const cropPixelW = Math.round(photoWidth * w / 100)
  const cropPixelH = Math.round(photoHeight * h / 100)
  const hasCrop = !(x === 0 && y === 0 && w === 100 && h === 100)

  return (
    <div className="crop-editor">
      <div className="crop-aspects">
        {ASPECT_RATIOS.map(ar => (
          <button
            key={ar.label}
            className={`btn btn-tiny ${aspect === ar.value ? 'btn-tiny-active' : ''}`}
            onClick={() => handleAspectChange(ar.value)}
          >
            {ar.label}
          </button>
        ))}
        {hasCrop && (
          <button className="btn btn-tiny" onClick={resetCrop}>Reset</button>
        )}
      </div>

      <div
        className="crop-canvas"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <img
          ref={imgRef}
          src={`/api/photos/${photoId}/full`}
          alt="Crop"
          draggable={false}
        />
        {hasCrop && (
          <>
            <div className="crop-mask-top" style={{ height: `${y}%` }} />
            <div className="crop-mask-bottom" style={{ height: `${Math.max(0, 100 - y - h)}%`, bottom: 0 }} />
            <div className="crop-mask-left" style={{ top: `${y}%`, height: `${h}%`, width: `${x}%` }} />
            <div className="crop-mask-right" style={{ top: `${y}%`, height: `${h}%`, width: `${Math.max(0, 100 - x - w)}%`, right: 0 }} />
            <div
              className="crop-selection"
              style={{ left: `${x}%`, top: `${y}%`, width: `${w}%`, height: `${h}%` }}
            />
          </>
        )}
        {!hasCrop && (
          <div className="crop-hint">Click and drag to select crop area</div>
        )}
      </div>

      <p className="muted" style={{ marginTop: 6 }}>
        {hasCrop ? `Crop: ${cropPixelW} x ${cropPixelH}px` : 'Full image (no crop)'}
      </p>
    </div>
  )
}

export default CropEditor
