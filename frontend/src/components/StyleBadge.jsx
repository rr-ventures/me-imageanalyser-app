/*
 * LEARNING NOTE: StyleBadge — a small colored label showing the style name.
 *
 * WHAT'S A "PURE" COMPONENT?
 *   This component has no state and no side effects. It just takes
 *   input (props) and returns output (JSX). Like a pure function in Python:
 *
 *   Python:  def badge(style): return f"<span class='{style}'>{style}</span>"
 *   React:   function StyleBadge({ style }) { return <span ...>{label}</span> }
 *
 *   Pure components are the easiest to understand and test.
 */

const STYLE_CONFIG = {
  true_to_life_clean: {
    label: 'True to Life',
    color: '#4ade80',
    bg: '#052e16',
  },
  warm_golden: {
    label: 'Warm Golden',
    color: '#fbbf24',
    bg: '#451a03',
  },
  bright_airy: {
    label: 'Bright & Airy',
    color: '#60a5fa',
    bg: '#172554',
  },
  moody_cinematic: {
    label: 'Moody Cinematic',
    color: '#a78bfa',
    bg: '#2e1065',
  },
  nightlife_contrast: {
    label: 'Nightlife',
    color: '#f472b6',
    bg: '#500724',
  },
  black_white: {
    label: 'Black & White',
    color: '#e5e7eb',
    bg: '#1f2937',
  },
}

function StyleBadge({ style, size = 'normal' }) {
  const config = STYLE_CONFIG[style] || {
    label: style,
    color: '#9ca3af',
    bg: '#374151',
  }

  const sizeClass = size === 'small' ? 'badge-small' : ''

  return (
    <span
      className={`style-badge ${sizeClass}`}
      style={{ color: config.color, backgroundColor: config.bg }}
    >
      {config.label}
    </span>
  )
}

export default StyleBadge
