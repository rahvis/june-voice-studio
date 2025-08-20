# Support & Operations

## How to Contact Support
- Email: support@company.com
- Slack: #voice-cloning-support
- Hours: 24x5 with on-call rotation for P1 incidents

## Ticket Workflow
1. User submits ticket via email or portal
2. Triage within 15 minutes for P1/P2
3. Assign owner and severity (P1–P4)
4. Acknowledge and communicate ETA
5. Resolve and document RCA

## SLAs
- P1: 15m response, 4h mitigation
- P2: 1h response, 8h mitigation
- P3: 4h response, next release
- P4: 1d response, backlog

## Templates
### Incident Ticket
- Title: [Severity] Short description
- Affected Services: Backend/Functions/Frontend/CDN
- Start Time (UTC):
- Impact:
- Logs/Trace IDs:
- Steps to Reproduce:
- Temporary Mitigation:

### Service Request
- Title: Request type
- Description:
- Business Justification:
- Approvals:

## Escalation
- On-call Engineer → Team Lead → SRE Manager → Incident Commander

## Tools
- Azure Monitor, App Insights, Log Analytics
- Runbooks: `docs/runbooks/*`
- Dashboards: Azure Portal dashboard deployed in production
