import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api/client'
import type { DiscoveredService, DeletionRequest } from '../types'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import {
  ArrowLeft, ExternalLink, Mail, Copy, Check, ShieldCheck, Clock,
} from 'lucide-react'

const statusVariant: Record<string, 'success' | 'warning' | 'destructive' | 'secondary' | 'default'> = {
  active: 'default',
  deletion_requested: 'warning',
  deleted: 'success',
  ignored: 'secondary',
}

export default function AccountDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [service, setService] = useState<DiscoveredService | null>(null)
  const [deletionRequests, setDeletionRequests] = useState<DeletionRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    Promise.all([
      api.get<DiscoveredService>(`/services/${id}`),
      api.get<DeletionRequest[]>('/deletion/requests'),
    ]).then(([svcRes, delRes]) => {
      setService(svcRes.data)
      setDeletionRequests(delRes.data.filter((d) => d.discovered_service_id === Number(id)))
      setLoading(false)
    })
  }, [id])

  const generateDeletionEmail = async (method: 'gdpr_email' | 'ccpa_email') => {
    setGenerating(true)
    try {
      const { data } = await api.post<DeletionRequest>('/deletion/request', {
        discovered_service_id: Number(id),
        method,
      })
      setDeletionRequests((prev) => [data, ...prev])
      // Refresh service status
      const { data: updated } = await api.get<DiscoveredService>(`/services/${id}`)
      setService(updated)
    } finally {
      setGenerating(false)
    }
  }

  const markStatus = async (requestId: number, status: string) => {
    const { data } = await api.patch<DeletionRequest>(`/deletion/${requestId}/status`, { status })
    setDeletionRequests((prev) => prev.map((d) => (d.id === requestId ? data : d)))
    const { data: updated } = await api.get<DiscoveredService>(`/services/${id}`)
    setService(updated)
  }

  const updateServiceStatus = async (status: string) => {
    const { data } = await api.patch<DiscoveredService>(`/services/${id}/status`, { status })
    setService(data)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (loading || !service) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[hsl(var(--primary))]" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Button variant="ghost" onClick={() => navigate('/accounts')} className="mb-2">
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Accounts
      </Button>

      {/* Service header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          {service.service_icon ? (
            <img
              src={service.service_icon}
              alt=""
              className="h-12 w-12 rounded-lg"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
          ) : (
            <div className="h-12 w-12 rounded-lg bg-[hsl(var(--secondary))] flex items-center justify-center text-lg font-bold">
              {service.service_name[0]}
            </div>
          )}
          <div>
            <h2 className="text-2xl font-bold">{service.service_name}</h2>
            <p className="text-[hsl(var(--muted-foreground))]">{service.service_domain}</p>
          </div>
        </div>
        <Badge variant={statusVariant[service.status] || 'secondary'} className="text-sm px-3 py-1">
          {service.status.replace(/_/g, ' ')}
        </Badge>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-[hsl(var(--muted-foreground))]">Detection Method</span>
              <span className="font-medium uppercase">{service.detection_method}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[hsl(var(--muted-foreground))]">Detected</span>
              <span>{new Date(service.detected_at).toLocaleDateString()}</span>
            </div>
            {service.category && (
              <div className="flex justify-between text-sm">
                <span className="text-[hsl(var(--muted-foreground))]">Category</span>
                <span className="capitalize">{service.category.replace(/_/g, ' ')}</span>
              </div>
            )}
            {service.deletion_difficulty && (
              <div className="flex justify-between text-sm">
                <span className="text-[hsl(var(--muted-foreground))]">Deletion Difficulty</span>
                <span>{service.deletion_difficulty}/5</span>
              </div>
            )}
            {service.breach_date && (
              <div className="flex justify-between text-sm">
                <span className="text-[hsl(var(--muted-foreground))]">Breach Date</span>
                <span>{new Date(service.breach_date).toLocaleDateString()}</span>
              </div>
            )}
            {service.deletion_notes && (
              <div className="pt-2 border-t border-[hsl(var(--border))]">
                <p className="text-sm text-[hsl(var(--muted-foreground))]">{service.deletion_notes}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Delete Account</CardTitle>
            <CardDescription>Choose how to request account deletion</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {service.deletion_url && (
              <a
                href={service.deletion_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between rounded-lg border p-3 hover:bg-[hsl(var(--accent))] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <ExternalLink className="h-4 w-4 text-[hsl(var(--primary))]" />
                  <div>
                    <p className="text-sm font-medium">Direct Deletion Link</p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">
                      Go directly to the account deletion page
                    </p>
                  </div>
                </div>
              </a>
            )}

            <button
              onClick={() => generateDeletionEmail('gdpr_email')}
              disabled={generating}
              className="w-full flex items-center justify-between rounded-lg border p-3 hover:bg-[hsl(var(--accent))] transition-colors disabled:opacity-50 text-left"
            >
              <div className="flex items-center gap-3">
                <Mail className="h-4 w-4 text-[hsl(var(--primary))]" />
                <div>
                  <p className="text-sm font-medium">Generate GDPR Email</p>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">
                    Draft a GDPR Article 17 deletion request
                  </p>
                </div>
              </div>
            </button>

            <button
              onClick={() => generateDeletionEmail('ccpa_email')}
              disabled={generating}
              className="w-full flex items-center justify-between rounded-lg border p-3 hover:bg-[hsl(var(--accent))] transition-colors disabled:opacity-50 text-left"
            >
              <div className="flex items-center gap-3">
                <Mail className="h-4 w-4 text-[hsl(var(--primary))]" />
                <div>
                  <p className="text-sm font-medium">Generate CCPA Email</p>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">
                    Draft a CCPA deletion request
                  </p>
                </div>
              </div>
            </button>

            {service.status === 'active' && (
              <Button
                variant="outline"
                className="w-full"
                onClick={() => updateServiceStatus('ignored')}
              >
                Ignore this service
              </Button>
            )}
            {service.status !== 'deleted' && service.status !== 'active' && (
              <Button
                variant="default"
                className="w-full"
                onClick={() => updateServiceStatus('deleted')}
              >
                <ShieldCheck className="h-4 w-4 mr-2" />
                Mark as Deleted
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Deletion requests */}
      {deletionRequests.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Deletion Requests</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {deletionRequests.map((req) => (
              <div key={req.id} className="rounded-lg border p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant={req.status === 'confirmed' ? 'success' : 'warning'}>
                      {req.status.replace(/_/g, ' ')}
                    </Badge>
                    <span className="text-xs text-[hsl(var(--muted-foreground))]">
                      {req.method.replace(/_/g, ' ').toUpperCase()} &middot;{' '}
                      {new Date(req.requested_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    {req.status !== 'confirmed' && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => markStatus(req.id, 'email_sent')}
                        >
                          Mark Sent
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => markStatus(req.id, 'confirmed')}
                        >
                          <Check className="h-3 w-3 mr-1" />
                          Confirm Deleted
                        </Button>
                      </>
                    )}
                  </div>
                </div>

                {req.generated_email_subject && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <p className="text-sm">
                        <strong>To:</strong> {req.recipient_email}
                      </p>
                      {req.recipient_email && (
                        <a
                          href={`mailto:${req.recipient_email}?subject=${encodeURIComponent(req.generated_email_subject)}&body=${encodeURIComponent(req.generated_email_body || '')}`}
                          className="text-xs text-[hsl(var(--primary))] hover:underline"
                        >
                          Open in email client
                        </a>
                      )}
                    </div>
                    <p className="text-sm">
                      <strong>Subject:</strong> {req.generated_email_subject}
                    </p>
                    <div className="relative">
                      <pre className="text-xs bg-[hsl(var(--secondary))] p-3 rounded-md whitespace-pre-wrap max-h-48 overflow-auto">
                        {req.generated_email_body}
                      </pre>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="absolute top-2 right-2"
                        onClick={() => copyToClipboard(req.generated_email_body || '')}
                      >
                        {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
