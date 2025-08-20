# Production Deployment Script for Voice Cloning System
# This script deploys the production infrastructure using Bicep

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "East US 2",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "prod",
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectName = "voice-cloning",
    
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$WhatIf,
    
    [Parameter(Mandatory=$false)]
    [switch]$ValidateOnly
)

Write-Host "Starting Production Deployment for Voice Cloning System..." -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Cyan
Write-Host "Location: $Location" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "Project: $ProjectName" -ForegroundColor Cyan

# Check if Azure CLI is installed
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI is not installed. Please install it first."
    exit 1
}

# Check if user is logged in
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Logging into Azure..." -ForegroundColor Yellow
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to log into Azure"
        exit 1
    }
}

# Set subscription if provided
if ($SubscriptionId) {
    Write-Host "Setting subscription to: $SubscriptionId" -ForegroundColor Yellow
    az account set --subscription $SubscriptionId
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to set subscription"
        exit 1
    }
}

# Get current subscription
$currentSub = az account show --query "id" -o tsv
Write-Host "Current Subscription: $currentSub" -ForegroundColor Cyan

# Check if resource group exists, create if not
Write-Host "Checking resource group..." -ForegroundColor Yellow
$rg = az group show --name $ResourceGroupName 2>$null | ConvertFrom-Json
if (-not $rg) {
    Write-Host "Creating resource group: $ResourceGroupName" -ForegroundColor Yellow
    az group create --name $ResourceGroupName --location $Location
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create resource group"
        exit 1
    }
}

# Validate Bicep template
Write-Host "Validating Bicep template..." -ForegroundColor Yellow
$validation = az deployment group validate `
    --resource-group $ResourceGroupName `
    --template-file "main.bicep" `
    --parameters environment=$Environment projectName=$ProjectName subscriptionId=$currentSub resourceGroupName=$ResourceGroupName

if ($LASTEXITCODE -ne 0) {
    Write-Error "Bicep template validation failed"
    Write-Host $validation -ForegroundColor Red
    exit 1
}

Write-Host "Bicep template validation passed" -ForegroundColor Green

# If validation only, exit here
if ($ValidateOnly) {
    Write-Host "Validation completed successfully. Use --WhatIf to see deployment preview." -ForegroundColor Green
    exit 0
}

# Show deployment preview if WhatIf is specified
if ($WhatIf) {
    Write-Host "Running deployment preview..." -ForegroundColor Yellow
    $whatIfResult = az deployment group what-if `
        --resource-group $ResourceGroupName `
        --template-file "main.bicep" `
        --parameters environment=$Environment projectName=$ProjectName subscriptionId=$currentSub resourceGroupName=$ResourceGroupName
    
    Write-Host "Deployment Preview:" -ForegroundColor Cyan
    Write-Host $whatIfResult -ForegroundColor White
    
    $continue = Read-Host "Do you want to proceed with the deployment? (y/N)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        Write-Host "Deployment cancelled by user" -ForegroundColor Yellow
        exit 0
    }
}

# Deploy production infrastructure
Write-Host "Deploying production infrastructure..." -ForegroundColor Yellow
$deploymentName = "production-deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

$deployment = az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file "main.bicep" `
    --name $deploymentName `
    --parameters environment=$Environment projectName=$ProjectName subscriptionId=$currentSub resourceGroupName=$ResourceGroupName `
    --verbose

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to deploy production infrastructure"
    exit 1
}

# Parse deployment outputs
$deploymentOutput = $deployment | ConvertFrom-Json
$outputs = $deploymentOutput.properties.outputs

Write-Host "Production deployment completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Deployment Summary:" -ForegroundColor Cyan
Write-Host "  Deployment Name: $deploymentName" -ForegroundColor White
Write-Host "  Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "  Environment: $Environment" -ForegroundColor White
Write-Host "  Project: $ProjectName" -ForegroundColor White
Write-Host ""

Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "  App Service: $($outputs.appServiceUrl.value)" -ForegroundColor White
Write-Host "  Functions: $($outputs.functionsUrl.value)" -ForegroundColor White
Write-Host "  Frontend: $($outputs.frontendUrl.value)" -ForegroundColor White
Write-Host "  App Gateway: $($outputs.appGatewayUrl.value)" -ForegroundColor White
Write-Host "  CDN Endpoint: $($outputs.cdnEndpointUrl.value)" -ForegroundColor White
Write-Host ""

Write-Host "Security Resources:" -ForegroundColor Cyan
Write-Host "  Key Vault: $($outputs.keyVaultName.value)" -ForegroundColor White
Write-Host "  Virtual Network: $($outputs.vnetName.value)" -ForegroundColor White
Write-Host ""

Write-Host "Data Resources:" -ForegroundColor Cyan
Write-Host "  Storage Account: $($outputs.storageAccountName.value)" -ForegroundColor White
Write-Host "  Cosmos DB: $($outputs.cosmosDBName.value)" -ForegroundColor White
Write-Host "  Redis Cache: $($outputs.redisCacheName.value)" -ForegroundColor White
Write-Host ""

Write-Host "Monitoring Resources:" -ForegroundColor Cyan
Write-Host "  Application Insights: $($outputs.appInsightsName.value)" -ForegroundColor White
Write-Host "  Log Analytics: $($outputs.logAnalyticsWorkspaceName.value)" -ForegroundColor White
Write-Host ""

# Get connection strings and secrets
Write-Host "Getting connection strings..." -ForegroundColor Yellow

# Storage connection string
$storageKeys = az storage account keys list --resource-group $ResourceGroupName --account-name $($outputs.storageAccountName.value) | ConvertFrom-Json
$storageConnectionString = "DefaultEndpointsProtocol=https;AccountName=$($outputs.storageAccountName.value);AccountKey=$($storageKeys[0].value);EndpointSuffix=core.windows.net"

# Cosmos DB connection string
$cosmosKeys = az cosmosdb keys list --resource-group $ResourceGroupName --name $($outputs.cosmosDBName.value) | ConvertFrom-Json
$cosmosConnectionString = $cosmosKeys.primaryMasterKey

# Redis connection string
$redisKeys = az redis list-keys --resource-group $ResourceGroupName --name $($outputs.redisCacheName.value) | ConvertFrom-Json
$redisConnectionString = "$($outputs.redisCacheName.value).redis.cache.windows.net:6380,password=$($redisKeys.primaryKey),ssl=True,abortConnect=False"

Write-Host "Connection Strings:" -ForegroundColor Cyan
Write-Host "  Storage: $storageConnectionString" -ForegroundColor White
Write-Host "  Cosmos DB Primary Key: $cosmosConnectionString" -ForegroundColor White
Write-Host "  Redis: $redisConnectionString" -ForegroundColor White
Write-Host ""

# Store secrets in Key Vault
Write-Host "Storing secrets in Key Vault..." -ForegroundColor Yellow

# Set Key Vault access policy for current user
$currentUser = az account show --query "user.name" -o tsv
az keyvault set-policy --name $($outputs.keyVaultName.value) --upn $currentUser --secret-permissions get set list delete

# Store secrets
az keyvault secret set --vault-name $($outputs.keyVaultName.value) --name "StorageConnectionString" --value $storageConnectionString
az keyvault secret set --vault-name $($outputs.keyVaultName.value) --name "CosmosDBConnectionString" --value $cosmosConnectionString
az keyvault secret set --vault-name $($outputs.keyVaultName.value) --name "RedisConnectionString" --value $redisConnectionString
az keyvault secret set --vault-name $($outputs.keyVaultName.value) --name "Environment" --value $Environment
az keyvault secret set --vault-name $($outputs.keyVaultName.value) --name "ProjectName" --value $ProjectName

Write-Host "Secrets stored in Key Vault" -ForegroundColor Green

# Configure App Service settings
Write-Host "Configuring App Service settings..." -ForegroundColor Yellow

# App Service settings
az webapp config appsettings set --resource-group $ResourceGroupName --name $($outputs.appServiceUrl.value.Split('/')[2]) --settings @- <<EOF
{
  "AZURE_KEY_VAULT_NAME": "$($outputs.keyVaultName.value)",
  "AZURE_STORAGE_ACCOUNT": "$($outputs.storageAccountName.value)",
  "AZURE_COSMOS_DB_NAME": "$($outputs.cosmosDBName.value)",
  "AZURE_REDIS_CACHE_NAME": "$($outputs.redisCacheName.value)",
  "AZURE_APP_INSIGHTS_NAME": "$($outputs.appInsightsName.value)",
  "ENVIRONMENT": "$Environment",
  "PROJECT_NAME": "$ProjectName"
}
EOF

# Functions App settings
az webapp config appsettings set --resource-group $ResourceGroupName --name $($outputs.functionsUrl.value.Split('/')[2]) --settings @- <<EOF
{
  "AZURE_KEY_VAULT_NAME": "$($outputs.keyVaultName.value)",
  "AZURE_STORAGE_ACCOUNT": "$($outputs.storageAccountName.value)",
  "AZURE_COSMOS_DB_NAME": "$($outputs.cosmosDBName.value)",
  "AZURE_REDIS_CACHE_NAME": "$($outputs.redisCacheName.value)",
  "AZURE_APP_INSIGHTS_NAME": "$($outputs.appInsightsName.value)",
  "ENVIRONMENT": "$Environment",
  "PROJECT_NAME": "$ProjectName"
}
EOF

# Frontend App settings
az webapp config appsettings set --resource-group $ResourceGroupName --name $($outputs.frontendUrl.value.Split('/')[2]) --settings @- <<EOF
{
  "AZURE_KEY_VAULT_NAME": "$($outputs.keyVaultName.value)",
  "AZURE_STORAGE_ACCOUNT": "$($outputs.storageAccountName.value)",
  "AZURE_APP_INSIGHTS_NAME": "$($outputs.appInsightsName.value)",
  "ENVIRONMENT": "$Environment",
  "PROJECT_NAME": "$ProjectName",
  "NODE_ENV": "production"
}
EOF

Write-Host "App Service settings configured" -ForegroundColor Green

# Configure monitoring and alerts
Write-Host "Configuring monitoring and alerts..." -ForegroundColor Yellow

# Create additional alert rules
$alertRules = @(
    @{
        name = "HighMemoryUsage"
        metricName = "MemoryPercentage"
        operator = "GreaterThan"
        threshold = 80
        description = "Alert when memory usage is high"
    },
    @{
        name = "HighResponseTime"
        metricName = "HttpResponseTime"
        operator = "GreaterThan"
        threshold = 2000
        description = "Alert when response time is high"
    },
    @{
        name = "HighErrorRate"
        metricName = "Http5xx"
        operator = "GreaterThan"
        threshold = 5
        description = "Alert when error rate is high"
    }
)

foreach ($rule in $alertRules) {
    az monitor metrics alert create `
        --resource-group $ResourceGroupName `
        --name "$($ProjectName)-alert-$($rule.name)-$Environment" `
        --description $rule.description `
        --scopes $($outputs.appServiceUrl.value.Split('/')[2]) `
        --condition "total $($rule.metricName) > $($rule.threshold)" `
        --window-size 15m `
        --evaluation-frequency 5m `
        --action $($outputs.actionGroupName.value)
}

Write-Host "Monitoring and alerts configured" -ForegroundColor Green

# Configure backup policies
Write-Host "Configuring backup policies..." -ForegroundColor Yellow

# App Service backup
az webapp config backup create `
    --resource-group $ResourceGroupName `
    --webapp-name $($outputs.appServiceUrl.value.Split('/')[2]) `
    --backup-name "daily-backup" `
    --frequency 1d `
    --retention 30

# Functions backup
az webapp config backup create `
    --resource-group $ResourceGroupName `
    --webapp-name $($outputs.functionsUrl.value.Split('/')[2]) `
    --backup-name "daily-backup" `
    --frequency 1d `
    --retention 30

Write-Host "Backup policies configured" -ForegroundColor Green

# Configure SSL certificates
Write-Host "Configuring SSL certificates..." -ForegroundColor Yellow

# Note: SSL certificates need to be uploaded manually or through Let's Encrypt
Write-Host "SSL certificates need to be configured manually:" -ForegroundColor Yellow
Write-Host "  1. Upload SSL certificate to App Service" -ForegroundColor White
Write-Host "  2. Configure custom domain bindings" -ForegroundColor White
Write-Host "  3. Update Application Gateway SSL certificate" -ForegroundColor White

# Generate deployment summary report
$deploymentReport = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    deploymentName = $deploymentName
    resourceGroup = $ResourceGroupName
    environment = $Environment
    projectName = $ProjectName
    services = @{
        appService = $($outputs.appServiceUrl.value)
        functions = $($outputs.functionsUrl.value)
        frontend = $($outputs.frontendUrl.value)
        appGateway = $($outputs.appGatewayUrl.value)
        cdn = $($outputs.cdnEndpointUrl.value)
    }
    resources = @{
        keyVault = $($outputs.keyVaultName.value)
        storage = $($outputs.storageAccountName.value)
        cosmosDB = $($outputs.cosmosDBName.value)
        redis = $($outputs.redisCacheName.value)
        appInsights = $($outputs.appInsightsName.value)
        logAnalytics = $($outputs.logAnalyticsWorkspaceName.value)
        vnet = $($outputs.vnetName.value)
    }
    connectionStrings = @{
        storage = $storageConnectionString
        cosmosDB = $cosmosConnectionString
        redis = $redisConnectionString
    }
}

$reportPath = "deployment-report-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
$deploymentReport | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportPath -Encoding UTF8

Write-Host "Deployment report saved to: $reportPath" -ForegroundColor Green

# Final summary
Write-Host ""
Write-Host "Production deployment completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Deploy application code to App Services" -ForegroundColor White
Write-Host "2. Configure custom domains and SSL certificates" -ForegroundColor White
Write-Host "3. Set up CI/CD pipelines" -ForegroundColor White
Write-Host "4. Configure monitoring dashboards" -ForegroundColor White
Write-Host "5. Test all endpoints and functionality" -ForegroundColor White
Write-Host "6. Set up disaster recovery procedures" -ForegroundColor White
Write-Host ""
Write-Host "Useful links:" -ForegroundColor Cyan
Write-Host "  Azure Portal: https://portal.azure.com/#@$($account.user.name)/resource$($outputs.appServiceUrl.value)" -ForegroundColor White
Write-Host "  App Service: $($outputs.appServiceUrl.value)" -ForegroundColor White
Write-Host "  Functions: $($outputs.functionsUrl.value)" -ForegroundColor White
Write-Host "  Frontend: $($outputs.frontendUrl.value)" -ForegroundColor White
Write-Host "  Key Vault: https://portal.azure.com/#@$($account.user.name)/resource$($outputs.keyVaultName.value)" -ForegroundColor White
Write-Host ""
Write-Host "Monitoring:" -ForegroundColor Cyan
Write-Host "  Application Insights: https://portal.azure.com/#@$($account.user.name)/resource$($outputs.appInsightsName.value)" -ForegroundColor White
Write-Host "  Log Analytics: https://portal.azure.com/#@$($account.user.name)/resource$($outputs.logAnalyticsWorkspaceName.value)" -ForegroundColor White
Write-Host ""
Write-Host "Deployment completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green

