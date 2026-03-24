import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import type { DiscoveredService } from '../types'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Search, ExternalLink, Filter } from 'lucide-react'

const statusVariant: Record<string, 'success' | 'warning' | 'destructive' | 'secondary' | 'default'> = {
  active: 'default',
  deletion_requested: 'warning',
  deletion_confirmed: 'warning',
  deleted: 'success',
  ignored: 'secondary',
}

const difficultyLabel: Record<number, string> = {
  1: 'Very Easy',
  2: 'Easy',
  3: 'Medium',
  4: 'Hard',
  5: 'Very Hard',
}

export default function Accounts() {
  const navigate = useNavigate()
  const [services, setServices] = useState<DiscoveredService[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (categoryFilter) params.set('category', categoryFilter)
    if (statusFilter) params.set('status', statusFilter)

    Promise.all([
      api.get<DiscoveredService[]>(`/services/?${params}`),
      api.get<string[]>('/services/categories/list'),
    ]).then(([servRes, catRes]) => {
      setServices(servRes.data)
      setCategories(catRes.data)
      setLoading(false)
    })
  }, [search, categoryFilter, statusFilter])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[hsl(var(--primary))]" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Discovered Accounts</h2>
        <p className="text-[hsl(var(--muted-foreground))] mt-1">
          {services.length} services found across your email accounts
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[hsl(var(--muted-foreground))]" />
          <Input
            placeholder="Search services..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <select
          className="h-10 rounded-md border border-[hsl(var(--input))] bg-transparent px-3 text-sm"
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
        >
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c.replace(/_/g, ' ')}
            </option>
          ))}
        </select>
        <select
          className="h-10 rounded-md border border-[hsl(var(--input))] bg-transparent px-3 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="deletion_requested">Deletion Requested</option>
          <option value="deleted">Deleted</option>
          <option value="ignored">Ignored</option>
        </select>
      </div>

      {/* Services grid */}
      {services.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-[hsl(var(--muted-foreground))]">
              No services found. Run a scan to discover your accounts.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {services.map((svc) => (
            <Card
              key={svc.id}
              className="cursor-pointer hover:border-[hsl(var(--primary))]/50 transition-colors"
              onClick={() => navigate(`/accounts/${svc.id}`)}
            >
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    {svc.service_icon ? (
                      <img
                        src={svc.service_icon}
                        alt=""
                        className="h-8 w-8 rounded"
                        onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                      />
                    ) : (
                      <div className="h-8 w-8 rounded bg-[hsl(var(--secondary))] flex items-center justify-center text-sm font-bold">
                        {svc.service_name[0]}
                      </div>
                    )}
                    <div>
                      <h3 className="font-semibold text-sm">{svc.service_name}</h3>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">
                        {svc.service_domain}
                      </p>
                    </div>
                  </div>
                  <Badge variant={statusVariant[svc.status] || 'secondary'}>
                    {svc.status.replace(/_/g, ' ')}
                  </Badge>
                </div>

                <div className="mt-4 flex items-center gap-2 flex-wrap">
                  {svc.category && (
                    <Badge variant="outline" className="text-xs capitalize">
                      {svc.category.replace(/_/g, ' ')}
                    </Badge>
                  )}
                  <Badge variant="outline" className="text-xs">
                    {svc.detection_method}
                  </Badge>
                  {svc.deletion_difficulty && (
                    <Badge
                      variant={svc.deletion_difficulty <= 2 ? 'success' : svc.deletion_difficulty >= 4 ? 'destructive' : 'warning'}
                      className="text-xs"
                    >
                      {difficultyLabel[svc.deletion_difficulty]}
                    </Badge>
                  )}
                </div>

                {svc.deletion_url && (
                  <div className="mt-3">
                    <a
                      href={svc.deletion_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-[hsl(var(--primary))] hover:underline inline-flex items-center gap-1"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <ExternalLink className="h-3 w-3" />
                      Delete account link
                    </a>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
