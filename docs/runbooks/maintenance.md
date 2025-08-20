# Maintenance Runbook

## Weekly
- Review App Insights failures and slow traces
- Check Redis memory and fragmentation
- Validate Cosmos DB RU usage and indexes
- Rotate application logs and archive to storage

## Monthly
- Rotate secrets in Key Vault (automate where possible)
- Patch OS and runtime versions in App Service/Functions
- Validate backups and perform restore test
- Review WAF and NSG rules

## Quarterly
- DR drill using `disaster-recovery.bicep`
- Cost optimization review
- Compliance audit sampling (GDPR/HIPAA/SOC 2)

## Procedures
### Secret Rotation
1. Generate new secret
2. Update Key Vault secret
3. Trigger slot swap or restart apps
4. Validate functionality

### Scale Adjustment
1. Review load trends
2. Update autoscale rules or plan capacity
3. Monitor post-change metrics
