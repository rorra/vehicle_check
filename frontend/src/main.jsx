/**
 * React Main Entry Point
 *
 * This file initializes the React application and mounts it to the DOM.
 * It wraps the app with ChakraProvider for Chakra UI theming and components.
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { ChakraProvider } from '@chakra-ui/react'
import App from './App.jsx'
import './index.css'

// Create React root and render the app
// ReactDOM.createRoot is the React 18+ API for rendering
ReactDOM.createRoot(document.getElementById('root')).render(
  // StrictMode helps identify potential problems in the app during development
  <React.StrictMode>
    {/* ChakraProvider enables Chakra UI components and theming throughout the app */}
    <ChakraProvider>
      <App />
    </ChakraProvider>
  </React.StrictMode>,
)
