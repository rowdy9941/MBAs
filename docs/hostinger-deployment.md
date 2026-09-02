# Hostinger deployment runbook

## Target

Start with a Hostinger KVM 8-class Ubuntu 24.04 VPS in the nearest Indian region. Run Docker Compose; do not introduce Kubernetes in the pilot.

## Before deployment

1. Point `mbas.example.com` and `api.mbas.example.com` A records to the VPS.
2. Open TCP ports 80 and 443. Do **not** expose PostgreSQL or Redis.
3. Install Docker Engine and the Compose plugin on the VPS.
4. Clone this repository and run `MBAS_INSTALL_DIR=$PWD ./install.sh`; it creates `.env` with generated database/auth secrets. Replace domains and configure provider credentials before public use.
5. Configure a real mailbox for Caddy's ACME certificate notices.

Phase 0 stops before production deployment. Before any later approved deployment, generate unique database credentials, keep `.env` outside version control, restrict SSH, enable the host firewall and unattended security updates, arrange encrypted off-server backups, and complete the Phase 1 authentication/RLS work. The placeholder API is not safe for public business data.

## One-shot install

```bash
git clone https://github.com/rowdy9941/MBAs.git
cd MBAs
MBAS_INSTALL_DIR=$PWD ./install.sh
```

The installer is safe to rerun. It does not overwrite an existing `.env`, pulls images, builds the application, starts the stack and verifies both liveness and database readiness.

## Start

```bash
docker compose pull
docker compose up -d --build
docker compose ps
curl -fsS https://api.mbas.example.com/healthz
curl -fsS https://api.mbas.example.com/readyz
```

Use only the base `compose.yaml` on the VPS. `compose.dev.yaml` is a local-development overlay that binds the API and dashboard to `127.0.0.1`; it is not part of the production command above.

To enable the monitoring containers, use `docker compose --profile monitoring up -d` and expose Grafana only through authenticated private access or a VPN.

## Backups

Run a daily encrypted PostgreSQL dump to an off-server object store. Test restoration before onboarding a paying customer. Retain at least 30 daily backups and monitor the backup job independently.

## Before LiveKit / phone calls

Choose the Indian SIP provider, reserve the required RTP/SIP/TURN ports, add a TURN server, configure recording retention and obtain the customer's consent script. Telephony credentials belong in the secret store, never in source code or prompts.
