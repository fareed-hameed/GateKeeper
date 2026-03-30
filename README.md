# AEGIS

**Advanced Engine for Guardian Intelligence & Security**

Daily-code access control for any URL-triggered action. Wrap any API endpoint, IoT trigger, or webhook behind a rotating daily code with device-based rate limiting.

## How It Works

1. You configure a **protected action URL** (any HTTP endpoint)
2. GateKeeper generates a new **6-digit code every day** (HMAC-based, deterministic)
3. Users enter the code on a mobile-friendly page to trigger the action
4. **Device fingerprinting** tracks unique devices — no accounts needed
5. Rate limiting: configurable max triggers per device, with a time window from first use

The protected URL is never exposed to end users.

## Use Cases

- Building/gate entry via smart lock API
- IoT device triggers (lights, alarms, irrigation)
- Webhook-based workflows with temporary access
- Any API endpoint you want to gate behind a daily code

## Quick Start

### Prerequisites
- Docker and Docker Compose
- (Optional) Nginx for reverse proxy

### Setup

```bash
git clone https://github.com/fareedhameed/gatekeeper.git
cd gatekeeper
cp config.yaml.example config.yaml
# Edit config.yaml with your action URL and secrets
docker compose up -d
```

Visit `http://localhost:5000` for the user page, `http://localhost:5000/admin` for admin.

### First Admin Enrollment

1. Open `/admin` in your browser
2. Enter the `master_pin` from your `config.yaml`
3. Give your device a name
4. Your device is now enrolled as admin and can view daily codes

## Configuration

All settings live in `config.yaml` (gitignored — secrets stay on your server):

| Setting | Default | Description |
|---------|---------|-------------|
| `action_url` | — | The URL to call when a valid code is entered |
| `action_method` | `GET` | HTTP method (GET or POST) |
| `action_label` | `Trigger` | Button/status label shown to users |
| `action_timeout_seconds` | `10` | Timeout for the action URL request |
| `code_secret` | — | Secret for daily code generation (change this!) |
| `code_length` | `6` | Number of digits in the daily code |
| `max_opens_per_device` | `3` | Max successful triggers per device per day |
| `access_window_minutes` | `15` | Minutes from first successful trigger |
| `daily_reset_hour` | `0` | Hour (0-23) when daily counters reset |
| `master_pin` | — | PIN required to enroll new admin devices |

## Deployment with GitHub Actions

The included workflow auto-deploys on push to `main`:

1. Set GitHub Secrets: `VPS_HOST`, `VPS_USER`, `VPS_PASSWORD`
2. Push to `main` — GitHub Actions SSHs into your server, pulls, and rebuilds

## Architecture

```
User Page (/)           Admin Page (/admin)
     |                       |
     v                       v
  Flask App (port 5000)
     |
     v
  SQLite (device tracking, access logs)
     |
     v (if code valid + rate limits OK)
  Protected Action URL
```

## License

MIT
