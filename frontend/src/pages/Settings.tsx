import { useState, useEffect } from 'react'
import api from '../api/client'
import { useAuth } from '../hooks/useAuth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { Download, Save, Key, Shield } from 'lucide-react'

export default function SettingsPage() {
  const { user } = useAuth()
  const [settings, setSettings] = useState<{
    hibp_api_key_configured: boolean
    google_oauth_configured: boolean
  } | null>(null)
  const [hibpKey, setHibpKey] = useState('')
  const [googleId, setGoogleId] = useState('')
  const [googleSecret, setGoogleSecret] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api.get('/settings/').then(({ data }) => setSettings(data))
  }, [])

  const saveSettings = async () => {
    setSaving(true)
    try {
      const payload: Record<string, string> = {}
      if (hibpKey) payload.hibp_api_key = hibpKey
      if (googleId) payload.google_client_id = googleId
      if (googleSecret) payload.google_client_secret = googleSecret

      await api.put('/settings/', payload)
      setSaved(true)
      setHibpKey('')
      setGoogleId('')
      setGoogleSecret('')
      const { data } = await api.get('/settings/')
      setSettings(data)
      setTimeout(() => setSaved(false), 3000)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-[hsl(var(--muted-foreground))] mt-1">
          Configure integrations and manage your data
        </p>
      </div>

      {/* HIBP API Key */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <Key className="h-5 w-5" />
                Have I Been Pwned
              </CardTitle>
              <CardDescription>
                Required for breach detection scanning.{' '}
                <a
                  href="https://haveibeenpwned.com/API/Key"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[hsl(var(--primary))] hover:underline"
                >
                  Get an API key
                </a>
              </CardDescription>
            </div>
            {settings && (
              <Badge variant={settings.hibp_api_key_configured ? 'success' : 'secondary'}>
                {settings.hibp_api_key_configured ? 'Configured' : 'Not configured'}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Input
              type="password"
              placeholder="Enter HIBP API key"
              value={hibpKey}
              onChange={(e) => setHibpKey(e.target.value)}
              className="flex-1"
            />
          </div>
        </CardContent>
      </Card>

      {/* Google OAuth */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Gmail OAuth
              </CardTitle>
              <CardDescription>
                Optional. Allows scanning Gmail without an app password.{' '}
                <a
                  href="https://console.cloud.google.com/apis/credentials"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[hsl(var(--primary))] hover:underline"
                >
                  Create OAuth credentials
                </a>
              </CardDescription>
            </div>
            {settings && (
              <Badge variant={settings.google_oauth_configured ? 'success' : 'secondary'}>
                {settings.google_oauth_configured ? 'Configured' : 'Not configured'}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            type="password"
            placeholder="Google Client ID"
            value={googleId}
            onChange={(e) => setGoogleId(e.target.value)}
          />
          <Input
            type="password"
            placeholder="Google Client Secret"
            value={googleSecret}
            onChange={(e) => setGoogleSecret(e.target.value)}
          />
        </CardContent>
      </Card>

      {/* Save button */}
      <div className="flex gap-3">
        <Button onClick={saveSettings} disabled={saving || (!hibpKey && !googleId && !googleSecret)}>
          <Save className="h-4 w-4 mr-2" />
          {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Settings'}
        </Button>
      </div>

      {/* Data Export */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Export Data</CardTitle>
          <CardDescription>
            Download all your discovered services data
          </CardDescription>
        </CardHeader>
        <CardContent className="flex gap-3">
          <a href="/api/settings/export/json" download>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export JSON
            </Button>
          </a>
          <a href="/api/settings/export/csv" download>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
          </a>
        </CardContent>
      </Card>

      {/* Account info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-[hsl(var(--muted-foreground))]">Username</span>
            <span>{user?.username}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[hsl(var(--muted-foreground))]">Email</span>
            <span>{user?.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[hsl(var(--muted-foreground))]">Role</span>
            <Badge variant={user?.is_admin ? 'default' : 'secondary'}>
              {user?.is_admin ? 'Admin' : 'User'}
            </Badge>
          </div>
          <div className="flex justify-between">
            <span className="text-[hsl(var(--muted-foreground))]">Member since</span>
            <span>{user && new Date(user.created_at).toLocaleDateString()}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
