# Azure Voice Cloning Infrastructure

This directory contains the Infrastructure as Code (IaC) templates for deploying the Azure Voice Cloning system.

## Prerequisites

- Azure CLI installed and configured
- Azure subscription with appropriate permissions
- PowerShell 7+ (for Windows/macOS) or Bash (for Linux)

## Architecture Overview

The infrastructure includes:

- **Azure AI Speech Service**: For voice cloning and text-to-speech
- **Azure AI Translator**: For multi-language support
- **Azure OpenAI Service**: For fallback TTS capabilities
- **Azure Key Vault**: For secure secret management
- **Azure Storage**: For audio file storage
- **Azure Cosmos DB**: For metadata storage
- **Azure API Management**: For API gateway and management
- **Azure Application Insights**: For monitoring and observability
- **Virtual Network**: With private endpoints for security

## Deployment

### 1. Deploy Infrastructure

```powershell
# Navigate to infrastructure directory
cd infrastructure

# Deploy with PowerShell
.\deploy.ps1 -ResourceGroupName "rg-voice-cloning-dev"

# Or deploy manually with Azure CLI
az deployment group create \
  --resource-group "rg-voice-cloning-dev" \
  --template-file "main.bicep" \
  --parameters "parameters.json"
```

### 2. Verify Deployment

Check the deployment outputs for service endpoints and IDs:

```bash
az deployment group show \
  --resource-group "rg-voice-cloning-dev" \
  --name "voice-cloning-deployment-YYYYMMDD-HHMMSS" \
  --query "properties.outputs"
```

### 3. Configure Services

After deployment, you'll need to:

1. **Configure Custom Neural Voice access** in the Speech Service
2. **Deploy models** to the OpenAI Service
3. **Set up API Management policies** for rate limiting and authentication
4. **Configure Application Insights** for monitoring

## Security Features

- **Private Endpoints**: All services are accessible only through the virtual network
- **Network Security Groups**: Restrict traffic to necessary ports
- **Key Vault**: Centralized secret management with RBAC
- **Storage Encryption**: All data encrypted at rest and in transit

## Cost Optimization

- **Serverless Cosmos DB**: Pay-per-use pricing
- **Standard Storage**: Cost-effective storage for audio files
- **Developer API Management**: Lower cost for development environments

## Monitoring

- **Application Insights**: Application performance monitoring
- **Azure Monitor**: Infrastructure metrics and alerts
- **Log Analytics**: Centralized logging and querying

## Troubleshooting

### Common Issues

1. **Private Endpoint Connection Failed**
   - Verify virtual network configuration
   - Check DNS resolution in private zones

2. **Service Access Denied**
   - Verify network ACLs and virtual network rules
   - Check service principal permissions

3. **Deployment Failures**
   - Review Azure activity logs
   - Check resource provider registrations

### Support

For issues with this infrastructure:
1. Check Azure status page
2. Review deployment logs
3. Contact Azure support if needed

## Next Steps

After infrastructure deployment:
1. Configure application secrets in Key Vault
2. Set up CI/CD pipelines
3. Deploy application code
4. Configure monitoring and alerting
