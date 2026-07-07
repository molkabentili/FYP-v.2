import { RouterProvider } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext.tsx'
import { router } from './routes.tsx'

export function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  )
}
