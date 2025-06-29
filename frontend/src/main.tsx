import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

const root = document.getElementById('root')!
root.style.height = '100vh'
root.style.overflow = 'hidden'

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
)