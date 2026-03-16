# SmartSeg Frontend Prototype

This folder contains the complete React + TypeScript prototype for the SmartSeg telecom segmentation platform.

## Stack
- React 18 + TypeScript
- React Router (data-mode style with `RouterProvider`)
- Tailwind CSS v4
- Radix UI primitives (tabs, switch, slider)
- Recharts visualizations
- Lucide icons
- Vite

## Run locally
1. Install Node.js 18+ and npm.
2. In this folder, run:
   - `npm install`
   - `npm run dev`
3. Open the local Vite URL.

## Implemented pages
- Home
- Upload Data
- Run Segmentation
- View Results (4 tabs)
- Strategy Report
- Export

## Next phase: backend integration
Suggested backend stack:
- FastAPI or Flask
- scikit-learn for K-Means
- pandas for preprocessing
- upload + clustering REST endpoints
- persistence for run history and exports
