import { createBrowserRouter, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { UploadPage } from './pages/UploadPage'
import { ConfigurePage } from './pages/ConfigurePage'
import { ResultsPage } from './pages/ResultsPage'
import { ReportPage } from './pages/ReportPage'
import { ExportPage } from './pages/ExportPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'upload', element: <UploadPage /> },
      { path: 'configure', element: <ConfigurePage /> },
      { path: 'results', element: <ResultsPage /> },
      { path: 'report', element: <ReportPage /> },
      { path: 'export', element: <ExportPage /> },
      { path: '*', element: <Navigate to="/" replace /> }
    ]
  }
])