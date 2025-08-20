# Administrator Guide (Production)

## Access & Roles
- Authentication: Azure Entra ID
- RBAC: Assign application roles (User, Reviewer, Admin) via Entra ID groups

## Secrets & Configuration
- Secrets in Azure Key Vault (see `infrastructure/production/main.bicep` outputs)
- App settings automatically configured by `infrastructure/production/deploy.ps1`
- Rotate secrets using runbook `docs/runbooks/maintenance.md`

## Networking & Security
- Private endpoints for core services
- WAF-enabled Application Gateway
- NSGs per subnet
- HTTPS-only enforcement; TLS 1.2+

## Scaling & Performance
- App Service Plans: Premium v3 with autoscale
- Functions: Premium v3 with autoscale
- Cosmos DB: Autoscale throughput
- Redis: Premium with clustering

## Monitoring
- Application Insights for APM
- Log Analytics workspace for logs/queries
- Azure Monitor alerts and action groups
- Portal dashboard deployed via `monitoring-dashboard.bicep`

## Backups & DR
- Daily backups for WebApps
- Geo-redundant storage for data
- Recovery Services vaults
- Disaster recovery plan in `disaster-recovery.bicep`

## Deployments
- Azure DevOps pipeline `infrastructure/production/azure-pipelines.yml`
- GitHub Actions workflow `infrastructure/production/.github/workflows/production-deploy.yml`
- Staging slot deployments, manual approval, slot swap, rollback

## Incident Response
Use `docs/runbooks/incident-response.md` for detection, triage, communication, mitigation, and post-incident review.

## Compliance
- Data residency and encryption enforced
- Audit logs via Log Analytics and App Insights
- Periodic reviews aligned with GDPR/HIPAA/SOC 2

## Change Management
- PR-based changes with automated tests
- Manual approval gates for production swaps
- Post-deployment health checks
