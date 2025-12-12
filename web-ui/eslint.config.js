import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    rules: {
      // AI Generated Code by Deloitte + Cursor (BEGIN)
      'no-unused-vars': [
        'error',
        {
          varsIgnorePattern: '^[A-Z_]',
          argsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
      // This rule is too strict for common patterns like initializing component state from
      // server-provided data in effects. Keep hooks best-practices via exhaustive-deps instead.
      'react-hooks/set-state-in-effect': 'off',
      // AI Generated Code by Deloitte + Cursor (END)
    },
  },
  // AI Generated Code by Deloitte + Cursor (BEGIN)
  // Node/CommonJS globals for config + e2e test files.
  {
    files: [
      'playwright.config.js',
      'tests/**/*.js',
      '**/*.config.js',
      '**/*.config.cjs',
      '**/*.config.mjs',
    ],
    languageOptions: {
      globals: {
        ...globals.node,
        ...globals.commonjs,
      },
    },
  },
  // AI Generated Code by Deloitte + Cursor (END)
])
