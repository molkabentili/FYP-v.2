import { FormEvent, useState } from 'react'
import { Loader2, Lock, Mail, ShieldCheck } from 'lucide-react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { Button } from '../components/ui/Button'

const ADMIN_EMAIL = import.meta.env.VITE_ADMIN_EMAIL || 'admin@ooredoo.com'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { isAuthenticated, login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const redirectTo = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? '/'

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await login(email, password)
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleCredentialRequest() {
    const subject = encodeURIComponent('SmartSeg access credentials request')
    const body = encodeURIComponent(
      'Hello Admin,\n\nPlease create SmartSeg access credentials for me.\n\nName:\nDepartment:\nRole requested: Marketing Analyst\n\nThank you.'
    )
    window.location.href = `mailto:${ADMIN_EMAIL}?subject=${subject}&body=${body}`
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container-page flex min-h-screen items-center justify-center py-10">
        <section className="w-full max-w-lg rounded-lg border border-gray-200 bg-white p-7 shadow-sm">
          <div className="mb-6">
            <div className="mb-6 flex flex-col items-center text-center">
              <img
                src="/ooredoo-seeklogo.png"
                alt="Ooredoo"
                className="mb-5 h-28 w-auto max-w-full object-contain sm:h-36"
              />
              <h1 className="text-2xl font-bold text-slate-950">SmartSeg</h1>
              <p className="text-sm text-slate-600">Customer Intelligence Platform</p>
            </div>
            <div className="rounded-lg border border-[var(--ooredoo-light-pink)] bg-[var(--ooredoo-light-pink)] px-3 py-2 text-sm font-semibold text-[var(--ooredoo-dark-red)]">
              Marketing Analyst
            </div>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Email</span>
              <span className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 focus-within:border-[var(--ooredoo-red)] focus-within:ring-2 focus-within:ring-[var(--ooredoo-light-pink)]">
                <Mail size={18} className="text-slate-400" />
                <input
                  className="w-full border-0 bg-transparent text-sm outline-none"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="email"
                  required
                />
              </span>
            </label>

            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Password</span>
              <span className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 focus-within:border-[var(--ooredoo-red)] focus-within:ring-2 focus-within:ring-[var(--ooredoo-light-pink)]">
                <Lock size={18} className="text-slate-400" />
                <input
                  className="w-full border-0 bg-transparent text-sm outline-none"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                  required
                />
              </span>
            </label>

            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Role</span>
              <span className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-semibold text-slate-700">
                <ShieldCheck size={18} className="text-[var(--ooredoo-red)]" />
                Marketing Analyst
              </span>
            </label>

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-700">
                {error}
              </div>
            )}

            <Button className="flex w-full items-center justify-center gap-2" disabled={isSubmitting} type="submit">
              {isSubmitting && <Loader2 size={16} className="animate-spin" />}
              Sign in
            </Button>
          </form>

          <div className="mt-5 border-t border-gray-100 pt-4">
            <p className="mb-2 text-center text-xs font-medium text-slate-500">No public sign-up. Accounts are created by the administrator.</p>
            <Button className="flex w-full items-center justify-center gap-2" type="button" variant="secondary" onClick={handleCredentialRequest}>
              <Mail size={16} />
              Ask admin for credentials
            </Button>
          </div>
        </section>
      </div>
    </main>
  )
}
