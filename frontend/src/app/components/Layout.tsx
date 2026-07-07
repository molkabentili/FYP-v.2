import { useState } from 'react'
import { BarChart3, ChevronDown, Download, FileText, History, Home, LogOut, PlayCircle, Settings, Upload } from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { readRunHistory, restoreRunHistoryItem, type SmartSegRunHistoryItem } from '../../services/history'
import { Button } from './ui/Button'

const navItems = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/upload', label: 'Upload Data', icon: Upload },
  { to: '/configure', label: 'Run Segmentation', icon: PlayCircle },
  { to: '/results', label: 'View Results', icon: BarChart3 },
  { to: '/report', label: 'Strategy Report', icon: FileText },
  { to: '/export', label: 'Export', icon: Download }
]

export function Layout() {
  const navigate = useNavigate()
  const { logout, user } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const [historyItems, setHistoryItems] = useState<SmartSegRunHistoryItem[]>([])

  function toggleMenu() {
    setHistoryItems(readRunHistory())
    setMenuOpen((open) => !open)
  }

  function handleParameters() {
    setMenuOpen(false)
    navigate('/configure')
  }

  function handleHistoryRestore(item: SmartSegRunHistoryItem) {
    restoreRunHistoryItem(item)
    setMenuOpen(false)
    navigate('/results')
  }

  function handleLogout() {
    setMenuOpen(false)
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="container-page py-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-3">
                <img
                  src="/ooredoo-seeklogo.png"
                  alt="Ooredoo"
                  className="h-10 w-auto object-contain"
                />
                <h1 className="text-xl font-bold">SmartSeg</h1>
              </div>
              <p className="text-sm text-slate-600">Customer Intelligence Platform</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="badge-brand">Powered by Ooredoo</span>
              <div className="rounded-full bg-gray-200 px-3 py-1 text-sm font-semibold">MA</div>
              <span className="hidden text-sm text-slate-600 sm:inline">{user?.email ?? 'Marketing Analytics'}</span>
              <div className="relative">
                <Button
                  aria-expanded={menuOpen}
                  aria-label="Open account menu"
                  className="flex items-center gap-2"
                  onClick={toggleMenu}
                  type="button"
                  variant="ghost"
                >
                  <Settings size={16} />
                  <span>Menu</span>
                  <ChevronDown size={14} />
                </Button>

                {menuOpen && (
                  <div className="absolute right-0 z-50 mt-2 w-80 rounded-lg border border-gray-200 bg-white p-2 shadow-lg">
                    <button
                      className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm font-medium text-slate-700 hover:bg-gray-50"
                      onClick={handleParameters}
                      type="button"
                    >
                      <Settings size={16} />
                      Parameters
                    </button>

                    <div className="my-2 border-t border-gray-100" />
                    <div className="px-3 pb-2">
                      <div className="flex items-center gap-2 text-xs font-semibold uppercase text-slate-500">
                        <History size={14} />
                        History
                      </div>
                    </div>
                    <div className="max-h-72 overflow-y-auto">
                      {historyItems.length === 0 ? (
                        <p className="px-3 py-2 text-sm text-slate-500">No saved runs yet.</p>
                      ) : (
                        historyItems.map((item) => (
                          <button
                            className="w-full rounded-md px-3 py-2 text-left text-sm hover:bg-gray-50"
                            key={item.id}
                            onClick={() => handleHistoryRestore(item)}
                            type="button"
                          >
                            <span className="block font-semibold text-slate-800">
                              {item.summary.algorithm} · k={item.summary.k}
                            </span>
                            <span className="block text-xs text-slate-500">
                              {new Date(item.createdAt).toLocaleString()} · {item.summary.businessSegments} cards
                            </span>
                          </button>
                        ))
                      )}
                    </div>

                    <div className="my-2 border-t border-gray-100" />
                    <button
                      className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm font-medium text-red-700 hover:bg-red-50"
                      onClick={handleLogout}
                      type="button"
                    >
                      <LogOut size={16} />
                      Logout
                    </button>
                  </div>
                )}
              </div>
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
