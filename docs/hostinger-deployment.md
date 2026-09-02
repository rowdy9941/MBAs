# Hostinger deployment runbook

## Target

Start with a Hostinger KVM 8-class Ubuntu 24.04 VPS in the nearest Indian region. Run Docker Compose; do not introduce Kubernetes in the pilot.

## Before deployment

1. Point `mbas.example.com` and `api.mbas.example.com` A records to the VPS.
2. Open TCP ports 80 and 443. Do **not** expose PostgreSQL or Redis.
3. Install Docker Engine and the Compose plugin on the VPS.
4. Clone this repository, copy `.env.example` to `.env`, and replace all sample secrets.
5. Configure a real mailbox for Caddy's ACME certificate notices.

## Start

```bash
docker compose pull
docker compose up -d --build
docker compose ps
curl -fsS https://api.mbas.example.com/healthz
```

To enable the monitoring containers, use `docker compose --profile monitoring up -d` and expose Grafana only through authenticated private access or a VPN.

## Backups

Run a daily encrypted PostgreSQL dump to an off-server object store. Test restoration before onboarding a paying customer. Retain at least 30 daily backups and monitor the backup job independently.

## Before LiveKit / phone calls

Choose the Indian SIP provider, reserve the required RTP/SIP/TURN ports, add a TURN server, configure recording retention and obtain the customer's consent script. Telephony credentials belong in the secret store, never in source code or prompts.

