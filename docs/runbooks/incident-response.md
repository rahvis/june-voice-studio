# Incident Response Runbook

## Severity Levels
- P1: Full outage or critical security incident
- P2: Major functionality degraded
- P3: Minor functionality impacted
- P4: Low impact or cosmetic

## Phases
1. Detect: Alerts from Azure Monitor/App Insights
2. Triage: Assign severity, on-call owner
3. Mitigate: Stabilize service (rollback, scale up, purge CDN, etc.)
4. Communicate: Post updates every 30–60 minutes to stakeholders
5. Resolve: Confirm service stability and close incident
6. Review: RCA within 48 hours

## Common Playbooks
- High 5xx: Review latest deployment; swap back slots; check logs
- High latency: Scale out; inspect Redis and Cosmos DB throughput
- Auth failures: Validate Entra ID token issuance/JWKS fetch
- Storage errors: Check account firewall, keys, and network

## Contacts
- On-call: oncall@company.com
- Incident Commander: ic@company.com
- Security: security@company.com
