#!/usr/bin/env pwsh

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

# Ensure Azure CLI is installed and logged in
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI is not installed. Please install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

# Check if user is logged in
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Please log in to Azure..."
    az login
}

# Create resource group if it doesn't exist
$rg = az group show --name $ResourceGroupName 2>$null | ConvertFrom-Json
if (-not $rg) {
    Write-Host "Creating resource group: $ResourceGroupName"
    az group create --name $ResourceGroupName --location $Location
} else {
    Write-Host "Resource group already exists: $ResourceGroupName"
}

# Deploy the infrastructure
Write-Host "Deploying infrastructure..."
$deploymentName = "voice-cloning-deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file "main.bicep" `
    --parameters "parameters.json" `
    --name $deploymentName `
    --verbose

if ($LASTEXITCODE -eq 0) {
    Write-Host "Infrastructure deployment completed successfully!"
    
    # Get deployment outputs
    $outputs = az deployment group show `
        --resource-group $ResourceGroupName `
        --name $deploymentName `
        --query "properties.outputs" `
        --output json | ConvertFrom-Json
    
    Write-Host "`nDeployment Outputs:"
    Write-Host "Speech Service ID: $($outputs.speechServiceId.value)"
    Write-Host "Translator Service ID: $($outputs.translatorServiceId.value)"
    Write-Host "OpenAI Service ID: $($outputs.openaiServiceId.value)"
    Write-Host "Key Vault Name: $($outputs.keyVaultName.value)"
    Write-Host "Storage Account Name: $($outputs.storageAccountName.value)"
    Write-Host "Cosmos DB Name: $($outputs.cosmosDbName.value)"
    Write-Host "Virtual Network Name: $($outputs.virtualNetworkName.value)"
    Write-Host "API Management Name: $($outputs.apiManagementName.value)"
    Write-Host "Application Insights Name: $($outputs.appInsightsName.value)"
    
} else {
    Write-Error "Infrastructure deployment failed!"
    exit 1
}
