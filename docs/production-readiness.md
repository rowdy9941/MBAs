# Production readiness

Before onboarding a customer, verify all of the following:

- `AUTH_SECRET`, database password, domain and ACME email are unique production values.
- HTTPS is valid for both configured domains and PostgreSQL/Redis are not public.
- `GET /readyz` and `GET /v1/provider-health` are healthy from the deployment host.
- A daily encrypted database backup runs with `scripts/backup-postgres.sh`; restore a backup into an isolated environment at least once.
- WhatsApp app approval, SIP provisioning, recording consent wording, Sarvam credentials and Razorpay keys are configured only when their associated integration is enabled.
- Owner accounts use strong passwords; production roles have been reviewed; no development access tokens remain.
- Monitoring, on-call contact and incident/rollback owner are documented.

The one-shot installer initializes infrastructure but does not make external providers legally or commercially active. Those require the relevant account approval and customer-consent process.
