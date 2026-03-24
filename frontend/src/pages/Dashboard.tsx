import { useState, useEffect } from 'react'
import api from '../api/client'
import type { DashboardStats } from '../types'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Globe, ShieldCheck, Trash2, Clock, Activity } from 'lucide-react'

const statusColors: Record<string, string> = {
  completed: 'success',
  running: 'warning',
  pending: 'secondary',
  failed: 'destructive',
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<DashboardStats>('/dashboard/stats')
      .then(({ data }) => setStats(data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[hsl(var(--primary))]" />
      </div>
    )
  }

  if (!stats) return null

  const statCards = [
    { label: 'Services Found', value: stats.total_accounts_found, icon: Globe, color: 'text-blue-500' },
    { label: 'Active Accounts', value: stats.active_accounts, icon: Activity, color: 'text-green-500' },
    { label: 'Deleted', value: stats.deleted_accounts, icon: ShieldCheck, color: 'text-emerald-500' },
    { label: 'Pending Deletion', value: stats.pending_deletions, icon: Clock, color: 'text-yellow-500' },
  ]

  const deletionProgress = stats.total_accounts_found > 0
    ? Math.round((stats.deleted_accounts / stats.total_accounts_found) * 100)
    : 0

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-[hsl(var(--muted-foreground))] mt-1">
          Your digital footprint overview
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map(({ label, value, icon: Icon, color }) => (
          <Card key={label}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{label}</CardTitle>
              <Icon className={`h-4 w-4 ${color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Deletion progress */}
      {stats.total_accounts_found > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Deletion Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="relative h-4 w-full overflow-hidden rounded-full bg-[hsl(var(--secondary))]">
                  <div
                    className="h-full bg-gradient-to-r from-[hsl(var(--primary))] to-emerald-500 transition-all duration-500 rounded-full"
                    style={{ width: `${deletionProgress}%` }}
                  />
                </div>
              </div>
              <span className="text-sm font-medium w-16 text-right">
                {deletionProgress}%
              </span>
            </div>
            <p className="text-sm text-[hsl(var(--muted-foreground))] mt-2">
              {stats.deleted_accounts} of {stats.total_accounts_found} accounts cleaned up
            </p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* Categories breakdown */}
        {Object.keys(stats.categories).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">By Category</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(stats.categories)
                  .sort((a, b) => b[1] - a[1])
                  .map(([cat, count]) => (
                    <div key={cat} className="flex items-center justify-between">
                      <span className="text-sm capitalize">{cat.replace(/_/g, ' ')}</span>
                      <Badge variant="secondary">{count}</Badge>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recent scans */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Scans</CardTitle>
          </CardHeader>
          <CardContent>
            {stats.recent_scans.length === 0 ? (
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                No scans yet. Go to the Scan page to start.
              </p>
            ) : (
              <div className="space-y-3">
                {stats.recent_scans.map((scan) => (
                  <div key={scan.id} className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium uppercase">{scan.scan_type}</span>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">
                        {scan.services_found} services found
                      </p>
                    </div>
                    <Badge variant={statusColors[scan.status] as any || 'secondary'}>
                      {scan.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
