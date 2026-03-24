import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useTheme } from '../hooks/useTheme'
import {
  LayoutDashboard, Search, Globe, Settings, LogOut, Moon, Sun, Shield,
} from 'lucide-react'
import { Button } from './ui/Button'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/scan', icon: Search, label: 'Scan' },
  { to: '/accounts', icon: Globe, label: 'Accounts' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const { dark, toggle } = useTheme()

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 border-r border-[hsl(var(--border))] bg-[hsl(var(--card))] flex flex-col">
        <div className="p-6 flex items-center gap-3">
          <Shield className="h-8 w-8 text-[hsl(var(--primary))]" />
          <h1 className="text-xl font-bold">ForgiveCloak</h1>
        </div>

        <nav className="flex-1 px-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-[hsl(var(--primary))]/10 text-[hsl(var(--primary))]'
                    : 'text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--accent))] hover:text-[hsl(var(--accent-foreground))]'
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-[hsl(var(--border))] space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-[hsl(var(--muted-foreground))] truncate">
              {user?.username}
            </span>
            <div className="flex gap-1">
              <Button variant="ghost" size="icon" onClick={toggle} className="h-8 w-8">
                {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </Button>
              <Button variant="ghost" size="icon" onClick={logout} className="h-8 w-8">
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
