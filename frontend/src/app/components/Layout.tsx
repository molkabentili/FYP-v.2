import { BarChart3, Download, FileText, Home, PlayCircle, Upload } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/upload', label: 'Upload Data', icon: Upload },
  { to: '/configure', label: 'Run Segmentation', icon: PlayCircle },
  { to: '/results', label: 'View Results', icon: BarChart3 },
  { to: '/report', label: 'Strategy Report', icon: FileText },
  { to: '/export', label: 'Export', icon: Download }
]

export function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="container-page py-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg brand-gradient" />
                <h1 className="text-xl font-bold">SmartSeg</h1>
              </div>
              <p className="text-sm text-slate-600">Customer Intelligence Platform</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="badge-brand">Powered by Ooredoo</span>
              <div className="rounded-full bg-gray-200 px-3 py-1 text-sm font-semibold">MA</div>
              <span className="text-sm text-slate-600">Marketing Analytics</span>
            </div>
          </div>
        </div>
        <nav className="border-t bg-white">
          <div className="container-page py-0">
            <ul className="flex flex-wrap gap-1">
              {navItems.map(({ to, label, icon: Icon }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    className={({ isActive }) =>
                      `flex items-center gap-2 border-b-2 px-3 py-3 text-sm font-medium transition ${
                        isActive
                          ? 'border-[var(--ooredoo-red)] bg-[var(--ooredoo-light-pink)] text-[var(--ooredoo-dark-red)]'
                          : 'border-transparent text-slate-600 hover:text-slate-900'
                      }`
                    }
                  >
                    <Icon size={16} />
                    <span>{label}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        </nav>
      </header>

      <main>
        <Outlet />
      </main>

      <footer className="mt-10 border-t bg-white">
        <div className="container-page flex flex-col justify-between gap-2 py-4 text-sm text-slate-600 md:flex-row">
          <span>© 2026 SmartSeg Platform | Confidential & Proprietary</span>
          <span>Ooredoo Analytics</span>
        </div>
      </footer>
    </div>
  )
}