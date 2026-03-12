/*
 * LEARNING NOTE: PhotoGrid — displays a grid of photo thumbnails.
 *
 * PYTHON COMPARISON:
 *   In Streamlit: cols = st.columns(4); for i, img in enumerate(images): ...
 *   In React: we use CSS Grid + map() to render each photo as a card.
 *
 * WHAT'S map()?
 *   JavaScript's map() is like Python's list comprehension:
 *   Python:  [render_card(photo) for photo in photos]
 *   JS:     photos.map(photo => <PhotoCard ... />)
 *
 * WHAT'S A "KEY"?
 *   When rendering a list, React needs a unique "key" for each item
 *   so it can efficiently update only the items that changed.
 *   It's like giving each item a name tag.
 *
 * PERFORMANCE:
 *   For 500+ photos, we only render what's visible on screen.
 *   As you scroll down, more photos load. This is called "pagination."
 */
import { useState } from 'react'
import PhotoCard from './PhotoCard'

const PHOTOS_PER_PAGE = 48

function PhotoGrid({ photos, results, onPhotoClick }) {
  const [page, setPage] = useState(0)

  if (!photos || photos.length === 0) {
    return <div className="empty-state">No photos found</div>
  }

  const totalPages = Math.ceil(photos.length / PHOTOS_PER_PAGE)
  const startIdx = page * PHOTOS_PER_PAGE
  const visiblePhotos = photos.slice(startIdx, startIdx + PHOTOS_PER_PAGE)

  // Build a lookup map: photo_id -> analysis result (if available)
  const resultMap = {}
  if (results) {
    results.forEach(r => { resultMap[r.image_id] = r })
  }

  return (
    <div>
      {/* Photo count and pagination */}
      <div className="grid-header">
        <span className="photo-count">{photos.length} photos</span>
        {totalPages > 1 && (
          <div className="pagination">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="btn btn-small"
            >
              Previous
            </button>
            <span className="page-info">
              Page {page + 1} of {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="btn btn-small"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* The actual grid of photo cards */}
      <div className="photo-grid">
        {visiblePhotos.map(photo => (
          <PhotoCard
            key={photo.id}
            photo={photo}
            result={resultMap[photo.id]}
            onClick={() => onPhotoClick && onPhotoClick(photo, resultMap[photo.id])}
          />
        ))}
      </div>
    </div>
  )
}

export default PhotoGrid
