<div align="center">
  <img src="frontend/public/favicon.svg" width="80" height="80" alt="ForgiveCloak" />
  <h1>ForgiveCloak</h1>
  <p><strong>Self-hosted digital footprint scanner &amp; account deletion manager</strong></p>
  <p>
    <a href="#features">Features</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#configuration">Configuration</a> •
    <a href="#screenshots">Screenshots</a> •
    <a href="#contributing">Contributing</a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
    <img src="https://img.shields.io/badge/docker-ready-blue.svg" alt="Docker" />
    <img src="https://img.shields.io/badge/python-3.12-green.svg" alt="Python" />
    <img src="https://img.shields.io/badge/react-18-blue.svg" alt="React" />
  </p>
</div>

---

**ForgiveCloak** is a free, open-source, self-hosted alternative to commercial services like Mine, Deseat.me, and Saymine. It discovers where your email address is registered across the internet, and helps you delete those accounts — all from your own server, with your data never leaving your hands.

## Features

- **Email Inbox Scanning** — Connects to your email via IMAP and scans for signup confirmation emails to discover registered services
- **Breach Detection** — Integrates with [Have I Been Pwned](https://haveibeenpwned.com/) to check if your email appears in known data breaches
- **Direct Site Probing** — Optionally checks registration/forgot-password endpoints on popular services (opt-in only)
- **Account Deletion Manager** — Provides direct deletion links for 70+ services, with difficulty ratings and instructions
- **GDPR/CCPA Email Generator** — Auto-drafts legally compliant data deletion request emails
- **Deletion Tracking** — Track the status of every deletion request from start to completion
- **Modern Dashboard** — Beautiful, responsive UI with real-time scan progress, category breakdowns, and deletion progress tracking
- **Multi-Email Support** — Scan multiple email accounts from one dashboard
- **Data Export** — Export all discovered services as JSON or CSV
- **Dark Mode** — Full dark/light theme support
- **Self-Hosted** — Your data never leaves your server. No cloud. No tracking. No subscriptions.

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/forgivecloak.git
cd forgivecloak
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your secrets:

```bash
# Generate a random secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate a Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Start the application

```bash
docker compose up -d --build
```

### 4. Open the dashboard

Navigate to **http://localhost:3000** in your browser. On first launch, you'll be guided through creating your admin account.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌───────────┐
│   Frontend   │────▶│   Backend    │────▶│   Redis   │
│  (React +    │     │  (FastAPI +  │     │  (Queue)  │
│   Nginx)     │◀────│   Celery)    │◀────│           │
│  :3000       │     │  :8000       │     │  :6379    │
└──────────────┘     └──────┬───────┘     └───────────┘
                            │
                     ┌──────┴───────┐
                     │   SQLite DB  │
                     │  (encrypted  │
                     │  credentials)│
                     └──────────────┘
```

**4 containers:**
- `forgivecloak-frontend` — React dashboard served by Nginx, proxies `/api` to backend
- `forgivecloak-backend` — FastAPI REST API
- `forgivecloak-worker` — Celery worker for background scan jobs
- `forgivecloak-redis` — Redis for the Celery task queue

## Configuration

All configuration is done via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | *(required)* | JWT signing key. Generate a random one. |
| `ENCRYPTION_KEY` | *(required)* | Fernet key for encrypting IMAP credentials at rest. |
| `DATABASE_URL` | `sqlite:///./data/forgivecloak.db` | Database URL |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Allowed CORS origins |
| `HIBP_API_KEY` | *(optional)* | Have I Been Pwned API key |
| `GOOGLE_CLIENT_ID` | *(optional)* | Google OAuth client ID for Gmail scanning |
| `GOOGLE_CLIENT_SECRET` | *(optional)* | Google OAuth client secret |
| `MAX_PROBE_CONCURRENCY` | `5` | Max concurrent site probe requests |
| `IMAP_FETCH_DELAY` | `0.5` | Delay between IMAP fetches (seconds) |
| `IMAP_MAX_EMAILS` | `10000` | Max emails to scan (0 = unlimited) |

### Gmail Setup

For scanning Gmail, you have two options:

**Option A: App Password (Easier)**
1. Go to [Google Account > Security > App Passwords](https://myaccount.google.com/apppasswords)
2. Generate an app password for "Mail"
3. Use this password when adding your Gmail account in ForgiveCloak

**Option B: OAuth (More Secure)**
1. Create a project at [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Gmail API
3. Create OAuth 2.0 credentials (Web application)
4. Set the redirect URI to `http://localhost:8000/api/auth/google/callback`
5. Add the Client ID and Secret in ForgiveCloak Settings

### Have I Been Pwned

1. Purchase an API key at [haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key)
2. Add it in ForgiveCloak Settings page
3. The HIBP scan option will become available

## Detection Methods

| Method | How it works | Accuracy | Setup |
|--------|-------------|----------|-------|
| **IMAP Scan** | Parses signup confirmation emails from your inbox | High | Email credentials |
| **HIBP Check** | Queries breach database for your email | Medium (only breached services) | HIBP API key |
| **Site Probe** | Checks forgot-password/registration endpoints | Variable | None (opt-in) |

## Supported Services

ForgiveCloak includes a curated registry of 70+ popular services with:
- Direct account deletion links
- Deletion difficulty ratings (1-5)
- Step-by-step deletion instructions
- Category classification

Services include: Google, Facebook, Twitter/X, Instagram, LinkedIn, Amazon, Netflix, Spotify, GitHub, Reddit, Discord, Steam, PayPal, and many more.

The registry is community-maintained — contributions are welcome!

## Development

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

### Useful Commands

```bash
make up          # Start all services
make down        # Stop all services
make build       # Build and start
make logs        # View all logs
make logs-backend   # Backend logs only
make shell       # Shell into backend container
make test        # Run tests
```

## Security

- All IMAP passwords are encrypted at rest using Fernet symmetric encryption
- JWT tokens with expiry for authentication
- bcrypt password hashing
- API keys stored encrypted in the database
- No telemetry. No external calls (except to services you explicitly configure)
- All data stays on your server

### Responsible Disclosure

If you discover a security vulnerability, please report it privately by emailing the maintainers. Do not open a public issue.

## Contributing

Contributions are welcome! Here's how you can help:

1. **Add services** — Expand `backend/app/data/services.json` with more services
2. **Improve detection** — Better email pattern matching for service detection
3. **Bug fixes** — Fix issues and improve stability
4. **Documentation** — Improve setup guides and documentation

### Steps

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/add-service-xyz`)
3. Commit your changes
4. Push to the branch and open a Pull Request

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <p>Built with privacy in mind. Your data, your server, your control.</p>
</div>
