# Fortigate Policy Toggler

A mobile-friendly web app for toggling internet access per kid by flipping Fortigate firewall deny policies on and off.

Built with FastAPI + vanilla JS. Runs in Docker.

---

## How it works

Each toggle controls a **deny policy** on your Fortigate:

| Toggle state | Deny policy | Result |
|---|---|---|
| ON (Internet enabled) | `disable` | Kid has internet |
| OFF (Internet disabled) | `enable` | Kid is blocked |

On startup the app queries Fortigate to sync real policy states, so the UI always reflects what's actually on the firewall.

---

## Requirements

- Docker + Docker Compose
- Fortigate firewall with REST API enabled
- A REST API admin token (read/write on Firewall Policy)

---

## Fortigate API setup

1. In FortiOS go to **System → Administrators → Create New → REST API Admin**
2. Assign a profile with **read/write** access to **Firewall Policy**
3. Copy the generated token — you'll put it in `.env` as `FORTIGATE_API_KEY`

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/fortigate-policy-toggler.git
cd fortigate-policy-toggler
```

### 2. Create your `.env` file

```bash
cp .env.example .env
nano .env
```

Fill in your values:

```env
FORTIGATE_HOST=192.168.1.1
FORTIGATE_PORT=443
FORTIGATE_API_KEY=your-api-key-here
FORTIGATE_VDOM=root
FORTIGATE_VERIFY_SSL=false
```

### 3. Edit `config/config.json`

This is where you define who gets a toggle and which Fortigate policy controls them. Add as many entries as you need — the UI will automatically render one card per entry.

```json
{
  "fortigate": {
    "host": "192.168.1.1",
    "port": 443,
    "verify_ssl": false,
    "vdom": "root"
  },
  "toggles": [
    {
      "id": "user1",
      "label": "User 1 Internet Access",
      "policy_id": 5
    },
    {
      "id": "user2",
      "label": "User 2 Internet Access",
      "policy_id": 6
    }
  ]
}
```

`id` must be unique and URL-safe (no spaces). `label` is what appears on the card in the UI. `policy_id` is the Fortigate deny policy ID to control.

### 4. Build and run

```bash
docker compose up -d
```

App will be available at `http://<your-server-ip>:8080`

To check logs:

```bash
docker compose logs -f
```

---

## Configuration reference

### Environment variables (`.env`)

Fortigate connection settings and secrets go here. Environment variables always override their `config.json` equivalents.

| Variable | Config key | Description | Default |
|---|---|---|---|
| `FORTIGATE_HOST` | `fortigate.host` | Fortigate IP or hostname | `192.168.1.1` |
| `FORTIGATE_PORT` | `fortigate.port` | HTTPS port | `443` |
| `FORTIGATE_API_KEY` | *(env only)* | REST API token | — |
| `FORTIGATE_VDOM` | `fortigate.vdom` | VDOM name | `root` |
| `FORTIGATE_VERIFY_SSL` | `fortigate.verify_ssl` | Verify TLS certificate | `false` |

### Toggle definitions (`config/config.json`)

Toggles are defined **only** in `config/config.json` — there are no per-user environment variables. Each entry in the `toggles` array produces one card in the UI.

| Field | Description |
|---|---|
| `id` | Unique identifier, URL-safe (no spaces) |
| `label` | Display name shown on the card |
| `policy_id` | Fortigate deny policy ID to control |

Add, remove, or rename entries freely — the frontend adapts automatically.

---

## Project structure

```
fortigate-policy-toggler/
├── app/
│   ├── main.py          # FastAPI app — startup sync + API endpoints
│   ├── config.py        # Config loader (JSON + env var overrides)
│   ├── fortigate.py     # Async Fortigate REST API client
│   └── static/
│       └── index.html   # Single-page frontend
├── config/
│   └── config.json      # Non-secret defaults
├── .env.example         # Template — copy to .env
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Serves the frontend |
| `GET` | `/api/status` | Returns current toggle states |
| `POST` | `/api/toggle/{id}` | Sets a toggle (`{"enabled": true/false}`) |

---

## Updating

```bash
git pull
docker compose up -d --build
```

---

## Security notes

- `.env` is gitignored — your API key will never be committed
- SSL verification is off by default since Fortigate uses a self-signed cert; set `FORTIGATE_VERIFY_SSL=true` if you have a valid cert
- The app has no authentication of its own — run it on your internal network only, or put it behind a reverse proxy with auth (e.g. Nginx + basic auth, or Authelia)
