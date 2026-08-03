import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { prepareStartup } from './startup'
import './index.css'

void prepareStartup().then((startup) => {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <App startup={startup} />
    </React.StrictMode>,
  )
})
