# React for Python Developers

A guide to understanding this React codebase if you're coming from Python.

## What is React?

React is a JavaScript library for building user interfaces. Think of it as a way
to create interactive web pages where content updates without reloading.

**The key difference from Streamlit:**
- Streamlit: Python generates HTML. Every interaction reloads the entire page.
- React: JavaScript runs in the browser. Only the changed parts of the page update.

## Project Structure Comparison

```
PYTHON (Streamlit)                    JAVASCRIPT (React + Vite)
─────────────────────                 ──────────────────────────
app.py (one big file)                 src/
                                        App.jsx          (router)
                                        pages/           (one file per screen)
                                          Dashboard.jsx
                                          Analysis.jsx
                                        components/      (reusable UI pieces)
                                          PhotoCard.jsx
                                          StyleBadge.jsx
                                        api/
                                          client.js      (API calls)
                                        styles/
                                          app.css        (all CSS)

requirements.txt                      package.json
pip install                           npm install
streamlit run app.py                  npm run dev
```

## Core Concepts

### 1. Components = Functions that Return HTML

**Python:**
```python
def greet(name):
    return f"<h1>Hello {name}</h1>"
```

**React:**
```jsx
function Greet({ name }) {
  return <h1>Hello {name}</h1>
}
```

The `{ name }` syntax is "destructuring" — it pulls `name` out of the props object.
JSX (the HTML-like syntax) gets converted to real HTML by React.

### 2. Props = Function Arguments

**Python:**
```python
def render_card(photo, on_click):
    return f"<div onclick='{on_click}'>{photo['name']}</div>"
```

**React:**
```jsx
function PhotoCard({ photo, onClick }) {
  return <div onClick={onClick}>{photo.name}</div>
}

// Using it:
<PhotoCard photo={myPhoto} onClick={handleClick} />
```

### 3. State = Variables That Update the UI

This is React's core magic. In Python, changing a variable doesn't update the screen.
In React, changing "state" automatically re-renders the component.

**Python (Streamlit):**
```python
# Streamlit re-runs the entire script on every interaction
count = st.session_state.get("count", 0)
if st.button("Click"):
    st.session_state.count = count + 1
st.write(f"Count: {count}")
```

**React:**
```jsx
function Counter() {
  // useState returns [currentValue, setterFunction]
  const [count, setCount] = useState(0)

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Click</button>
    </div>
  )
}
```

When you call `setCount(1)`, React:
1. Updates the count value
2. Re-renders ONLY this component (not the whole page)
3. The `<p>` now shows "Count: 1"

### 4. useEffect = "Do Something After Rendering"

Used for side effects like API calls, timers, etc.

**Python:**
```python
class Dashboard:
    def __init__(self):
        self.photos = self._load_photos()  # runs on init

    def _load_photos(self):
        return requests.get("/api/photos").json()
```

**React:**
```jsx
function Dashboard() {
  const [photos, setPhotos] = useState([])

  // useEffect runs AFTER the component appears on screen
  useEffect(() => {
    fetch("/api/photos")
      .then(res => res.json())
      .then(data => setPhotos(data.photos))
  }, [])  // [] = run only once (on mount)

  return <div>{photos.length} photos loaded</div>
}
```

### 5. Event Handlers = Callbacks

**Python:**
```python
def on_button_click():
    print("clicked!")

button = Button(command=on_button_click)
```

**React:**
```jsx
function MyButton() {
  function handleClick() {
    console.log("clicked!")
  }

  return <button onClick={handleClick}>Click me</button>
}
```

### 6. Lists = map() Instead of List Comprehension

**Python:**
```python
items = [render_item(x) for x in my_list]
```

**React:**
```jsx
{myList.map(x => <Item key={x.id} data={x} />)}
```

The `key` prop is required — it helps React track which items changed.

### 7. Conditional Rendering = if/else in JSX

**Python:**
```python
if loading:
    st.write("Loading...")
else:
    st.write(f"Found {count} photos")
```

**React:**
```jsx
{loading ? (
  <p>Loading...</p>
) : (
  <p>Found {count} photos</p>
)}

// Or for simple show/hide:
{error && <p className="error">{error}</p>}
```

## How Data Flows in This App

```
User clicks "Analyze" button
    ↓
Dashboard.jsx calls analyzeBatch() from api/client.js
    ↓
client.js sends POST request to FastAPI backend
    ↓
FastAPI calls Gemini, runs selector, saves results
    ↓
client.js receives JSON response
    ↓
Dashboard.jsx navigates to /analysis/{runId}
    ↓
Analysis.jsx loads and fetches results via API
    ↓
PhotoGrid.jsx renders results as cards
    ↓
User clicks a card → PhotoDetail.jsx shows full analysis
```

## How CSS Works

CSS controls appearance. Each component uses class names that map to CSS rules:

```jsx
// In the component:
<div className="photo-card">...</div>

// In app.css:
.photo-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
}
```

`className` (not `class`) is used because `class` is a reserved word in JavaScript.

## Common Patterns in This Codebase

### Loading → Data → Render pattern
```jsx
const [data, setData] = useState(null)
const [loading, setLoading] = useState(true)

useEffect(() => {
  fetchData()
    .then(result => setData(result))
    .finally(() => setLoading(false))
}, [])

if (loading) return <p>Loading...</p>
return <div>{/* render data */}</div>
```

### Parent → Child communication (props)
```jsx
// Parent passes data DOWN via props
<PhotoCard photo={myPhoto} onClick={handleClick} />

// Child receives and uses props
function PhotoCard({ photo, onClick }) { ... }
```

### Child → Parent communication (callback functions)
```jsx
// Parent defines a handler and passes it down
function Dashboard() {
  const [model, setModel] = useState(null)
  return <ModelSelector onModelChange={setModel} />
}

// Child calls the handler when something happens
function ModelSelector({ onModelChange }) {
  return <select onChange={e => onModelChange(e.target.value)}>...</select>
}
```

## Useful Commands

```bash
npm run dev          # Start development server (hot reload)
npm run build        # Build for production
npm run preview      # Preview production build
```

## Next Steps

1. Read through `App.jsx` to see the overall structure
2. Look at `Dashboard.jsx` to see state management in action
3. Follow the data flow from button click → API call → results display
4. Try modifying a component and see hot reload update instantly
