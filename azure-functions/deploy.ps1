# Azure Functions Deployment Script
# This script deploys the Azure Functions infrastructure using Bicep

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "East US",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectName = "voice-cloning"
)

Write-Host "Starting Azure Functions deployment..." -ForegroundColor Green
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

# Deploy Azure Functions infrastructure
Write-Host "Deploying Azure Functions infrastructure..." -ForegroundColor Yellow
$deploymentName = "functions-deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

$deployment = az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file "deploy.bicep" `
    --name $deploymentName `
    --parameters `
        resourceGroupName=$ResourceGroupName `
        location=$Location `
        environment=$Environment `
        projectName=$ProjectName `
    --verbose

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to deploy Azure Functions infrastructure"
    exit 1
}

# Parse deployment outputs
$deploymentOutput = $deployment | ConvertFrom-Json
$outputs = $deploymentOutput.properties.outputs

Write-Host "Azure Functions deployment completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Deployment Summary:" -ForegroundColor Cyan
Write-Host "  Function App Name: $($outputs.functionAppName.value)" -ForegroundColor White
Write-Host "  Function App URL: $($outputs.functionAppUrl.value)" -ForegroundColor White
Write-Host "  Storage Account: $($outputs.storageAccountName.value)" -ForegroundColor White
Write-Host "  App Insights: $($outputs.appInsightsName.value)" -ForegroundColor White
Write-Host "  Service Plan: $($outputs.servicePlanName.value)" -ForegroundColor White
Write-Host ""

# Get connection strings
Write-Host "Getting connection strings..." -ForegroundColor Yellow
$storageKeys = az storage account keys list --resource-group $ResourceGroupName --account-name $($outputs.storageAccountName.value) | ConvertFrom-Json
$storageConnectionString = "DefaultEndpointsProtocol=https;AccountName=$($outputs.storageAccountName.value);AccountKey=$($storageKeys[0].value);EndpointSuffix=core.windows.net"

Write-Host "Connection Strings:" -ForegroundColor Cyan
Write-Host "  Storage Connection String: $storageConnectionString" -ForegroundColor White
Write-Host ""

# Deploy function code (if available)
if (Test-Path "VoiceEnrollmentHttpTrigger") {
    Write-Host "Deploying function code..." -ForegroundColor Yellow
    
    # Install Azure Functions Core Tools if not available
    if (-not (Get-Command func -ErrorAction SilentlyContinue)) {
        Write-Host "Installing Azure Functions Core Tools..." -ForegroundColor Yellow
        npm install -g azure-functions-core-tools@4 --unsafe-perm true
    }
    
    # Deploy functions
    Write-Host "Deploying functions to Azure..." -ForegroundColor Yellow
    func azure functionapp publish $($outputs.functionAppName.value) --python
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Function code deployed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Warning: Function code deployment failed. You can deploy manually later." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Azure Functions deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Configure environment variables in Azure Portal" -ForegroundColor White
Write-Host "2. Set up authentication and authorization" -ForegroundColor White
Write-Host "3. Test the deployed functions" -ForegroundColor White
Write-Host "4. Monitor with Application Insights" -ForegroundColor White
Write-Host ""
Write-Host "Function App URL: $($outputs.functionAppUrl.value)" -ForegroundColor Green
Write-Host "Azure Portal: https://portal.azure.com/#@$($account.user.name)/resource$($outputs.functionAppId.value)" -ForegroundColor Green
