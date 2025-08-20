# Azure Functions for Voice Cloning System

This directory contains Azure Functions that provide serverless, event-driven processing capabilities for the Azure Open AI Voice Cloning system.

## Architecture Overview

The Azure Functions layer provides:
- **HTTP Triggers**: REST API endpoints for voice enrollment and synthesis orchestration
- **Timer Triggers**: Scheduled monitoring and maintenance tasks
- **Blob Triggers**: Automatic audio file processing when files are uploaded
- **Queue Triggers**: Asynchronous processing of voice enrollment and synthesis jobs

## 📁 Project Structure

```
azure-functions/
├── deploy.bicep              # Infrastructure as Code template
├── deploy.ps1                # PowerShell deployment script
├── host.json                 # Functions host configuration
├── local.settings.json       # Local development settings
├── requirements.txt          # Python dependencies
├── shared/                   # Shared utilities
│   ├── __init__.py
│   └── auth.py              # Authentication utilities
├── VoiceEnrollmentHttpTrigger/     # Voice enrollment HTTP endpoint
│   ├── function.json
│   └── __init__.py
├── SynthesisOrchestratorHttpTrigger/  # Synthesis orchestration
│   ├── function.json
│   └── __init__.py
├── WebhookHandlerHttpTrigger/        # Generic webhook handler
│   ├── function.json
│   └── __init__.py
├── HealthCheckHttpTrigger/           # Health monitoring endpoint
│   ├── function.json
│   └── __init__.py
├── TrainingJobMonitorTimerTrigger/   # Scheduled training monitoring
│   ├── function.json
│   └── __init__.py
└── AudioFileProcessorBlobTrigger/    # Audio file processing
    ├── function.json
    └── __init__.py
```

## Features

### HTTP Trigger Functions
- **Voice Enrollment**: Receives enrollment requests and queues them for processing
- **Synthesis Orchestrator**: Routes synthesis requests to appropriate queues
- **Webhook Handler**: Generic webhook receiver with signature verification
- **Health Check**: System health monitoring and status reporting

### Timer & Queue Triggers
- **Training Job Monitor**: Periodically checks training job status
- **Batch Synthesis Processor**: Handles bulk synthesis requests
- **Cleanup Functions**: Automated maintenance and cleanup tasks
- **Scheduled Notifications**: Time-based notification delivery

### Blob Storage Triggers
- **Audio File Processor**: Automatic audio validation and processing
- **File Conversion**: Format conversion and optimization
- **Metadata Extraction**: Audio file metadata analysis
- **Cleanup & Archiving**: File lifecycle management

## Prerequisites

- Azure CLI installed and configured
- Azure subscription with appropriate permissions
- Python 3.9+ for local development
- Azure Functions Core Tools v4 (for local development)

## 🔧 Local Development Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Local Settings**:
   - Copy `local.settings.json.example` to `local.settings.json`
   - Update connection strings and API keys

3. **Start Local Development**:
   ```bash
   func start
   ```

4. **Test Functions**:
   - Use the provided test scripts or Postman collections
   - Monitor logs in the terminal

## Deployment

### Option 1: PowerShell Script (Recommended)
```powershell
.\deploy.ps1 -ResourceGroupName "my-resource-group" -Environment "dev"
```

### Option 2: Azure CLI
```bash
# Deploy infrastructure
az deployment group create \
  --resource-group my-resource-group \
  --template-file deploy.bicep \
  --parameters environment=dev

# Deploy function code
func azure functionapp publish my-function-app --python
```

### Option 3: Azure DevOps Pipeline
```yaml
- task: AzureResourceManagerTemplateDeployment@3
  inputs:
    deploymentScope: 'Resource Group'
    azureResourceManagerConnection: 'Azure Connection'
    subscriptionId: '$(AZURE_SUBSCRIPTION_ID)'
    action: 'Create Or Update Resource Group'
    resourceGroupName: '$(RESOURCE_GROUP_NAME)'
    location: 'East US'
    templateLocation: 'Linked artifact'
    csmFile: '$(System.DefaultWorkingDirectory)/azure-functions/deploy.bicep'
    csmParametersFile: '$(System.DefaultWorkingDirectory)/azure-functions/parameters.json'
    deploymentMode: 'Incremental'
```

## Authentication & Security

### Azure Entra ID Integration
- JWT token validation against Azure Entra ID
- Role-based access control (RBAC)
- Managed Identity support for Azure services

### Webhook Security
- HMAC-SHA256 signature verification
- Configurable secret keys
- Rate limiting and IP filtering

### Network Security
- Private endpoints for Azure services
- Network security groups
- VNet integration

## Monitoring & Logging

### Application Insights
- Request/response telemetry
- Performance monitoring
- Error tracking and alerting
- Custom metrics and events

### Structured Logging
- JSON-formatted logs
- Correlation IDs for request tracing
- Log levels and filtering
- Azure Monitor integration

### Health Monitoring
- System resource monitoring (CPU, Memory, Disk)
- Azure service connectivity checks
- Function uptime tracking
- Custom health indicators

## 🔄 Configuration

### Environment Variables
```bash
# Core Settings
FUNCTIONS_WORKER_RUNTIME=python
FUNCTIONS_EXTENSION_VERSION=~4
ENVIRONMENT=dev

# Azure Services
AZURE_SPEECH_KEY=your_speech_key
AZURE_TRANSLATOR_KEY=your_translator_key
AZURE_OPENAI_KEY=your_openai_key

# Storage & Database
AZURE_STORAGE_CONNECTION_STRING=your_storage_connection
AZURE_COSMOS_DB_CONNECTION_STRING=your_cosmos_connection

# Authentication
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret

# Rate Limiting
RATE_LIMITING_ENABLED=true
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_SYNTHESIS=50
RATE_LIMIT_TRAINING=10
```

### Function-Specific Settings
```json
{
  "bindings": [
    {
      "name": "req",
      "type": "httpTrigger",
      "direction": "in",
      "authLevel": "function",
      "route": "voice-enrollment"
    }
  ]
}
```

## Testing

### Unit Tests
```bash
python -m pytest tests/ -v
```

### Integration Tests
```bash
# Test with Azure Functions Core Tools
func start
# In another terminal
curl -X POST http://localhost:7071/api/voice-enrollment \
  -H "Content-Type: application/json" \
  -d '{"userId": "test-user", "audioUrl": "test-url"}'
```

### Load Testing
```bash
# Using Apache Bench
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" \
  http://localhost:7071/api/health
```

## Performance & Scaling

### Consumption Plan
- Pay-per-execution pricing
- Automatic scaling based on demand
- Cold start optimization

### Premium Plan
- Pre-warmed instances
- VNet integration
- Custom domain support

### Scaling Rules
- CPU utilization thresholds
- Memory pressure monitoring
- Queue depth triggers
- Custom metrics

## Troubleshooting

### Common Issues

1. **Cold Start Delays**:
   - Use Premium plan for production
   - Implement keep-alive mechanisms
   - Optimize function dependencies

2. **Authentication Errors**:
   - Verify Azure Entra ID configuration
   - Check token expiration
   - Validate audience and issuer claims

3. **Storage Connection Issues**:
   - Verify connection strings
   - Check network security rules
   - Validate storage account permissions

4. **Memory Issues**:
   - Monitor memory usage
   - Optimize data processing
   - Use streaming for large files

### Debugging Tools
- Azure Functions Core Tools
- Application Insights Live Metrics
- Azure Monitor Logs
- Function App Logs

## Security Best Practices

1. **Secrets Management**:
   - Use Azure Key Vault for sensitive data
   - Rotate keys regularly
   - Implement least-privilege access

2. **Network Security**:
   - Enable private endpoints
   - Restrict public access
   - Use VNet integration

3. **Authentication**:
   - Implement proper JWT validation
   - Use managed identities
   - Enable audit logging

4. **Data Protection**:
   - Encrypt data at rest and in transit
   - Implement data classification
   - Regular security assessments

## 📚 Additional Resources

- [Azure Functions Documentation](https://docs.microsoft.com/en-us/azure/azure-functions/)
- [Python Azure Functions Guide](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Azure Functions Best Practices](https://docs.microsoft.com/en-us/azure/azure-functions/functions-best-practices)
- [Azure Functions Security](https://docs.microsoft.com/en-us/azure/azure-functions/security-concepts)

## 🤝 Contributing

1. Follow the established code patterns
2. Add comprehensive error handling
3. Include logging for debugging
4. Write unit tests for new functions
5. Update documentation as needed

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review Azure Functions documentation
3. Create an issue in the project repository
4. Contact the development team
