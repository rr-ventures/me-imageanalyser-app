/*
 * LEARNING NOTE: This is the entry point of the React app.
 *
 * In Python, you'd have: if __name__ == "__main__": main()
 * In React, this file does the same thing — it's the starting point.
 *
 * It takes the <App /> component and "mounts" it into the HTML page
 * (specifically into the <div id="root"> element in index.html).
 *
 * Think of it like plugging your entire app into the web page.
 */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './styles/app.css'

// BrowserRouter enables page navigation (like clicking between Dashboard and Analysis)
// StrictMode helps catch bugs during development (extra checks, doesn't affect production)
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
