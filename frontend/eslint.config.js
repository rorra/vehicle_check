/**
 * ESLint Configuration (Flat Config Format)
 *
 * ESLint is a code linter that finds and fixes problems in JavaScript code.
 *
 * What it checks:
 * - JavaScript syntax errors
 * - React best practices
 * - React Hooks rules
 * - Fast Refresh compatibility
 *
 * Run: npm run lint
 */

import js from '@eslint/js'
import globals from 'globals'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'

export default [
  // Ignore build output folder
  { ignores: ['dist'] },

  // Configuration for all JS/JSX files
  {
    files: ['**/*.{js,jsx}'],

    // Language settings
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser, // Browser global variables (window, document, etc.)
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true }, // Enable JSX syntax
        sourceType: 'module', // Enable ES modules (import/export)
      },
    },

    // React version for plugin
    settings: { react: { version: '18.3' } },

    // Linting plugins
    plugins: {
      react,              // React-specific rules
      'react-hooks': reactHooks,     // Hooks rules (useEffect, useState, etc.)
      'react-refresh': reactRefresh, // Fast Refresh compatibility
    },

    // Linting rules
    rules: {
      // Apply recommended rules from each plugin
      ...js.configs.recommended.rules,
      ...react.configs.recommended.rules,
      ...react.configs['jsx-runtime'].rules, // No need to import React in every file
      ...reactHooks.configs.recommended.rules,

      // Custom rule overrides
      'react/jsx-no-target-blank': 'off', // Allow target="_blank" without rel="noopener"
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
      'react/prop-types': 'off', // Disable prop-types check (using TypeScript types instead)
    },
  },
]
