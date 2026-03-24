import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import type { EmailAccount, ScanJob } from '../types'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Progress } from '../components/ui/Progress'
import { Plus, Play, Trash2, Mail, RefreshCw } from 'lucide-react'

export default function Scan() {
  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [jobs, setJobs] = useState<ScanJob[]>([])
  const [showAdd, setShowAdd] = useState(false)
  const [loading, setLoading] = useState(true)

  // Add account form
  const [newEmail, setNewEmail] = useState('')
  const [newHost, setNewHost] = useState('')
  const [newPort, setNewPort] = useState(993)
  const [newPassword, setNewPassword] = useState('')
  const [newProvider, setNewProvider] = useState('custom_imap')
  const [addError, setAddError] = useState('')

  // Scan options
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null)
  const [scanTypes, setScanTypes] = useState<Record<string, boolean>>({
    imap: true,
    hibp: false,
    probe: false,
  })

  const fetchData = useCallback(async () => {
    const [accountsRes, jobsRes] = await Promise.all([
      api.get<EmailAccount[]>('/scans/email-accounts'),
      api.get<ScanJob[]>('/scans/jobs'),
    ])
    setAccounts(accountsRes.data)
    setJobs(jobsRes.data)
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Poll for active scan progress
  useEffect(() => {
    const hasActive = jobs.some((j) => j.status === 'pending' || j.status === 'running')
    if (!hasActive) return
    const interval = setInterval(fetchData, 2000)
    return () => clearInterval(interval)
  }, [jobs, fetchData])

  const addAccount = async (e: React.FormEvent) => {
    e.preventDefault()
    setAddError('')
    try {
      await api.post('/scans/email-accounts', {
        email_address: newEmail,
        provider: newProvider,
        imap_host: newHost || undefined,
        imap_port: newPort,
        password: newPassword || undefined,
      })
      setNewEmail('')
      setNewHost('')
      setNewPort(993)
      setNewPassword('')
      setShowAdd(false)
      fetchData()
    } catch (err: any) {
      setAddError(err.response?.data?.detail || 'Failed to add account')
    }
  }

  const deleteAccount = async (id: number) => {
    await api.delete(`/scans/email-accounts/${id}`)
    fetchData()
  }

  const startScan = async () => {
    if (!selectedAccount) return
    const types = Object.entries(scanTypes)
      .filter(([, v]) => v)
      .map(([k]) => k)
    if (types.length === 0) return

    await api.post('/scans/start', {
      email_account_id: selectedAccount,
      scan_types: types,
    })
    fetchData()
  }

  const providerDefaults: Record<string, { host: string; port: number }> = {
    gmail: { host: 'imap.gmail.com', port: 993 },
    outlook: { host: 'outlook.office365.com', port: 993 },
    yahoo: { host: 'imap.mail.yahoo.com', port: 993 },
    custom_imap: { host: '', port: 993 },
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[hsl(var(--primary))]" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Scan</h2>
          <p className="text-[hsl(var(--muted-foreground))] mt-1">
            Add email accounts and scan for registered services
          </p>
        </div>
        <Button onClick={() => setShowAdd(!showAdd)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Email Account
        </Button>
      </div>

      {/* Add email account form */}
      {showAdd && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Add Email Account</CardTitle>
            <CardDescription>
              Connect your email to scan for signup confirmation emails
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={addAccount} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Email Provider</label>
                  <select
                    className="flex h-10 w-full rounded-md border border-[hsl(var(--input))] bg-transparent px-3 py-2 text-sm"
                    value={newProvider}
                    onChange={(e) => {
                      setNewProvider(e.target.value)
                      const defaults = providerDefaults[e.target.value]
                      if (defaults) {
                        setNewHost(defaults.host)
                        setNewPort(defaults.port)
                      }
                    }}
                  >
                    <option value="gmail">Gmail</option>
                    <option value="outlook">Outlook / Hotmail</option>
                    <option value="yahoo">Yahoo</option>
                    <option value="custom_imap">Custom IMAP</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Email Address</label>
                  <Input
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">IMAP Host</label>
                  <Input
                    value={newHost}
                    onChange={(e) => setNewHost(e.target.value)}
                    placeholder="imap.example.com"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">IMAP Port</label>
                  <Input
                    type="number"
                    value={newPort}
                    onChange={(e) => setNewPort(Number(e.target.value))}
                  />
                </div>

                <div className="space-y-2 md:col-span-2">
                  <label className="text-sm font-medium">
                    Password / App Password
                  </label>
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Use an app-specific password for Gmail"
                  />
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">
                    For Gmail, use an App Password (Google Account &gt; Security &gt; App Passwords).
                    Credentials are encrypted at rest.
                  </p>
                </div>
              </div>

              {addError && (
                <p className="text-sm text-[hsl(var(--destructive))]">{addError}</p>
              )}

              <div className="flex gap-2">
                <Button type="submit">Add Account</Button>
                <Button type="button" variant="outline" onClick={() => setShowAdd(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Email accounts list */}
      {accounts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Your Email Accounts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {accounts.map((acc) => (
                <div
                  key={acc.id}
                  className={`flex items-center justify-between rounded-lg border p-4 cursor-pointer transition-colors ${
                    selectedAccount === acc.id
                      ? 'border-[hsl(var(--primary))] bg-[hsl(var(--primary))]/5'
                      : 'border-[hsl(var(--border))] hover:border-[hsl(var(--primary))]/50'
                  }`}
                  onClick={() => setSelectedAccount(acc.id)}
                >
                  <div className="flex items-center gap-3">
                    <Mail className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
                    <div>
                      <p className="text-sm font-medium">{acc.email_address}</p>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">
                        {acc.provider} &middot; {acc.last_scanned
                          ? `Last scanned ${new Date(acc.last_scanned).toLocaleDateString()}`
                          : 'Never scanned'}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => { e.stopPropagation(); deleteAccount(acc.id) }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Scan controls */}
      {selectedAccount && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Start a Scan</CardTitle>
            <CardDescription>
              Select which detection methods to use
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-3">
              {[
                { key: 'imap', label: 'Email Scan (IMAP)', desc: 'Scan inbox for signup emails' },
                { key: 'hibp', label: 'Breach Check (HIBP)', desc: 'Check breach databases' },
                { key: 'probe', label: 'Site Probing', desc: 'Check registration endpoints' },
              ].map(({ key, label, desc }) => (
                <label
                  key={key}
                  className={`flex items-start gap-3 rounded-lg border p-4 cursor-pointer transition-colors ${
                    scanTypes[key]
                      ? 'border-[hsl(var(--primary))] bg-[hsl(var(--primary))]/5'
                      : 'border-[hsl(var(--border))]'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={scanTypes[key]}
                    onChange={(e) => setScanTypes({ ...scanTypes, [key]: e.target.checked })}
                    className="mt-0.5"
                  />
                  <div>
                    <p className="text-sm font-medium">{label}</p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">{desc}</p>
                  </div>
                </label>
              ))}
            </div>

            {scanTypes.probe && (
              <div className="rounded-md bg-yellow-500/10 p-3 text-sm text-yellow-700 dark:text-yellow-400">
                <strong>Note:</strong> Site probing sends requests to external websites to check
                for email registration. This may trigger rate limits or notification
                emails from those services. Use with caution.
              </div>
            )}

            <Button onClick={startScan} disabled={!Object.values(scanTypes).some(Boolean)}>
              <Play className="h-4 w-4 mr-2" />
              Start Scan
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Scan history */}
      {jobs.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">Scan History</CardTitle>
            <Button variant="ghost" size="sm" onClick={fetchData}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between rounded-lg border border-[hsl(var(--border))] p-4"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium uppercase">{job.scan_type}</span>
                      <Badge
                        variant={
                          job.status === 'completed' ? 'success'
                          : job.status === 'running' ? 'warning'
                          : job.status === 'failed' ? 'destructive'
                          : 'secondary'
                        }
                      >
                        {job.status}
                      </Badge>
                    </div>
                    {(job.status === 'running' || job.status === 'pending') && (
                      <div className="mt-2 space-y-1">
                        <Progress value={job.progress} className="" />
                        <p className="text-xs text-[hsl(var(--muted-foreground))]">
                          {job.status === 'pending'
                            ? 'Waiting for worker to pick up the task…'
                            : job.status_message || `Scanning… ${job.progress}%`}
                        </p>
                      </div>
                    )}
                    <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">
                      {job.status === 'completed' && job.status_message
                        ? job.status_message
                        : `${job.services_found} services found`}
                      {job.error_message && ` · Error: ${job.error_message}`}
                    </p>
                  </div>
                  <span className="text-xs text-[hsl(var(--muted-foreground))]">
                    {new Date(job.created_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
