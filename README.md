# Azure OpenAI Voice Cloning System

## Overview
An Azure-first, enterprise-grade voice cloning system that leverages Azure AI Speech (including Custom Neural Voice), Azure OpenAI (including gpt-4o-mini-tts), and Azure Translator. The platform provides secure voice enrollment, model training, real-time and batch text-to-speech synthesis, translation, and end-to-end observability, with strong security and compliance foundations.

## Key Features
- Voice Enrollment with consent capture and audit trail
- Custom Neural Voice (CNV) training orchestration
- Real-time and batch synthesis with SSML support
- Multi-language translation and language detection
- Advanced voice selection and fallbacks (Azure Speech, Azure OpenAI TTS)
- Robust audio processing, quality checks, and format conversion
- End-to-end monitoring, alerting, and dashboards (Azure Monitor, App Insights)
- Business intelligence: usage, cost, and quality metrics
- Security and compliance baked-in (GDPR, HIPAA, SOC 2)
- CI/CD pipelines with staged rollouts, manual approvals, health checks, and rollback

## Architecture
High-level components and their responsibilities:
- Frontend (Next.js 14, TypeScript): Auth, enrollment UI, synthesis UI, dashboard
- Backend (FastAPI, Python): REST APIs, consent, synthesis orchestration
- Azure Functions (Python): HTTP triggers, timers, blob triggers for async jobs
- Data: Azure Blob Storage (audio), Cosmos DB (metadata), Redis (cache)
- Observability: Application Insights, Log Analytics, Azure Monitor
- Networking & Security: VNet, NSGs, Private Endpoints, Application Gateway (WAF)
- Edge: Azure CDN for static and audio delivery

See `infrastructure_README.md`, `backend_README.md`, `frontend_README.md`, and `azure-functions_README.md` for deeper component-level details.

## Repository Structure
- `app/` FastAPI application (routers, middleware)
- `backend/` Backend service code and requirements
- `frontend/` Next.js application
- `azure-functions/` Serverless functions (HTTP, Timer, Blob triggers)
- `infrastructure/` Bicep templates and deployment scripts
- `tests/` Unit, integration, performance, security, and compliance tests
- `docs/` User/admin guides, troubleshooting, support, and runbooks

## Prerequisites
- Azure subscription with permissions to create resources
- Azure CLI and Bicep CLI
- Node.js 18 LTS and npm
- Python 3.11 and pip
- Terraform (optional if you prefer IaC via Terraform)

## Environment Configuration
Required environment variables and secrets are managed in Azure Key Vault and application settings. For local development, create a `.env` for backend and set Next.js environment variables.

Common settings:
- Azure OpenAI: endpoint, deployment names, API keys (if applicable)
- Azure AI Speech: region, key or managed identity
- Azure Translator: region, key
- Storage Account: connection string or SAS
- Cosmos DB: endpoint and key
- Redis Cache: connection string
- Microsoft Entra ID (Azure AD): tenant ID, client ID, authority, audience

Never commit secrets to source control. Use Key Vault and environment-specific app settings.

## Infrastructure Deployment (Production)
Production Bicep templates and scripts are under `infrastructure/production/`.

- Deploy core production infrastructure:
  - Template: `infrastructure/production/main.bicep`
  - Parameters: `infrastructure/production/parameters.json`
  - Script: `infrastructure/production/deploy.ps1`

Example deployment:
```powershell
cd infrastructure/production
./deploy.ps1 -ResourceGroupName "voice-cloning-prod" -Location "East US 2" -Environment "prod"
```

Disaster Recovery and Monitoring:
- DR: `infrastructure/production/disaster-recovery.bicep`
- Dashboard and alerts: `infrastructure/production/monitoring-dashboard.bicep`

## Application Deployment
### Backend (FastAPI)
Local run:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (Next.js)
Local run:
```bash
cd frontend
npm ci
npm run dev
```

### Azure Functions
Local run:
```bash
cd azure-functions
pip install -r requirements.txt
func start
```

## CI/CD
Two options are provided:

1) Azure DevOps Pipeline: `infrastructure/production/azure-pipelines.yml`
- Validate, test, security scan
- Build artifacts (backend, functions, frontend)
- Deploy infrastructure
- Deploy to staging slots, run health checks
- Manual approval gate and slot swap to production
- Rollback on failure

2) GitHub Actions Workflow: `infrastructure/production/.github/workflows/production-deploy.yml`
- Similar stages with OIDC-based Azure login
- Staging slot deployment, manual approval, swap and post-swap health

Uptime monitor workflow: `infrastructure/production/.github/workflows/uptime-monitor.yml` (scheduled health checks)

## Security & Compliance
- Authentication: Azure Entra ID (frontend via MSAL, backend JWT validation)
- Authorization: Role-based access control and resource ownership checks
- Data Protection: Encryption in transit (TLS 1.2+), encryption at rest
- Secrets: Azure Key Vault; no secrets in code or repo
- Network Security: VNet, NSG, private endpoints, WAF
- Compliance: GDPR, HIPAA, SOC 2 controls (see `tests/compliance/`)

## Monitoring & Observability
- Application Insights: distributed tracing, requests, dependencies, exceptions
- Log Analytics: centralized logging and Kusto queries
- Azure Monitor: metrics, alerts, autoscale rules
- Dashboards: Portal dashboard deployed via Bicep

## Testing
Test suites live in `tests/` and include:
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Performance/load tests: `tests/performance/`
- Security tests: `tests/security/`
- Compliance validation: `tests/compliance/`

Run locally:
```bash
pip install -r tests/requirements.txt
pytest -v
```

A combined test runner and configuration are provided:
- Runner: `tests/test_runner.py`
- Config: `tests/test_config.json`

## Troubleshooting and Support
- Troubleshooting: `docs/troubleshooting.md`
- Support operations and ticket templates: `docs/support/README.md`
- Runbooks: `docs/runbooks/maintenance.md`, `docs/runbooks/incident-response.md`

## Operational Readiness
- User guide: `docs/user/guide.md`
- Admin guide: `docs/admin/admin-guide.md`
- Go-live artifacts for training, documentation, support, and monitoring are included

## Coding Standards
- Python: type hints, flake8, black, mypy
- TypeScript: ESLint, type-checking
- Avoid inline comments that explain the obvious; prefer clear naming
- No emojis anywhere in code or documentation

## Contribution
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Open a pull request referencing the related issue

## License
See LICENSE (if applicable).
