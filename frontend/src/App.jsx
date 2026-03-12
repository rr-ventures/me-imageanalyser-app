/*
 * LEARNING NOTE: App.jsx is the "root component" — the top-level container.
 *
 * PYTHON COMPARISON:
 *   In Python/Streamlit, you had one big app.py with all the screens.
 *   In React, each screen is a separate "page component", and App.jsx
 *   is the router that decides which page to show based on the URL.
 *
 * WHAT'S A COMPONENT?
 *   A component is a reusable piece of UI. It's like a Python function
 *   that returns HTML instead of a value.
 *
 *   Python:  def greet(name): return f"Hello {name}"
 *   React:   function Greet({ name }) { return <h1>Hello {name}</h1> }
 *
 * WHAT'S JSX?
 *   JSX is the HTML-like syntax you see below. It looks like HTML but it's
 *   actually JavaScript. React converts it to real HTML behind the scenes.
 */
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Analysis from './pages/Analysis'
import Settings from './pages/Settings'

function App() {
  // Routes define which component shows for which URL path.
  // "/" = Dashboard, "/analysis" = Analysis results, "/settings" = Settings
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/analysis/:runId" element={<Analysis />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
