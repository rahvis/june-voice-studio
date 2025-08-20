@description('Name of the resource group')
param resourceGroupName string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Project name')
param projectName string = 'voice-cloning'

@description('Azure Functions app name')
param functionAppName string = '${projectName}-functions-${environment}'

@description('Storage account name for Azure Functions')
param storageAccountName string = '${replace(projectName, '-', '')}func${environment}'

@description('Application Insights name')
param appInsightsName string = '${projectName}-ai-${environment}'

@description('Service plan name')
param servicePlanName string = '${projectName}-plan-${environment}'

@description('Python version for Azure Functions')
param pythonVersion string = '3.9'

@description('Function app settings')
param functionAppSettings object = {
  FUNCTIONS_WORKER_RUNTIME: 'python'
  FUNCTIONS_EXTENSION_VERSION: '~4'
  AzureWebJobsFeatureFlags: 'EnableWorkerIndexing'
  ENVIRONMENT: environment
  APP_VERSION: '1.0.0'
  LOG_LEVEL: 'INFO'
  RATE_LIMITING_ENABLED: 'true'
  RATE_LIMIT_DEFAULT: '100'
  RATE_LIMIT_SYNTHESIS: '50'
  RATE_LIMIT_TRAINING: '10'
}

@description('Tags for resources')
param tags object = {
  Environment: environment
  Project: projectName
  ManagedBy: 'Bicep'
  CreatedDate: utcNow('yyyy-MM-dd')
}

// Storage Account for Azure Functions
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
  }
  tags: tags
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: ''
  }
  tags: tags
}

// App Service Plan
resource servicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: servicePlanName
  location: location
  sku: {
    name: environment == 'prod' ? 'P1v3' : 'B1'
    tier: environment == 'prod' ? 'PremiumV3' : 'Basic'
    size: environment == 'prod' ? 'P1v3' : 'B1'
    family: environment == 'prod' ? 'P' : 'B'
    capacity: environment == 'prod' ? 2 : 1
  }
  kind: 'linux'
  properties: {
    reserved: true
    perSiteScaling: false
    elasticScaleEnabled: false
    maximumElasticWorkerCount: environment == 'prod' ? 10 : 1
  }
  tags: tags
}

// Azure Functions App
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: servicePlan.id
    reserved: true
    siteConfig: {
      linuxFxVersion: 'Python|${pythonVersion}'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: storageAccount.properties.primaryEndpoints.blob
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTION'
          value: storageAccount.properties.primaryEndpoints.file
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower(functionAppName)
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'AzureWebJobsFeatureFlags'
          value: 'EnableWorkerIndexing'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'ENVIRONMENT'
          value: environment
        }
        {
          name: 'APP_VERSION'
          value: '1.0.0'
        }
        {
          name: 'LOG_LEVEL'
          value: 'INFO'
        }
        {
          name: 'RATE_LIMITING_ENABLED'
          value: 'true'
        }
        {
          name: 'RATE_LIMIT_DEFAULT'
          value: '100'
        }
        {
          name: 'RATE_LIMIT_SYNTHESIS'
          value: '50'
        }
        {
          name: 'RATE_LIMIT_TRAINING'
          value: '10'
        }
      ]
      cors: {
        allowedOrigins: [
          'https://${projectName}-frontend-${environment}.azurewebsites.net'
          'http://localhost:3000'
        ]
        supportCredentials: true
      }
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      scmMinTlsVersion: '1.2'
    }
    httpsOnly: true
    clientAffinityEnabled: false
  }
  tags: tags
}

// Storage Account Network Rules
resource storageAccountNetworkRules 'Microsoft.Storage/storageAccounts/networkRuleSets@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    defaultAction: 'Deny'
    ipRules: []
    virtualNetworkRules: []
    bypass: 'AzureServices'
  }
}

// Storage Account Private Endpoint (if needed)
resource storageAccountPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = if (environment == 'prod') {
  name: '${storageAccountName}-pe'
  location: location
  properties: {
    subnet: {
      id: ''
    }
    privateLinkServiceConnections: [
      {
        name: '${storageAccountName}-pls'
        properties: {
          privateLinkServiceId: storageAccount.id
          groupIds: [
            'blob'
            'file'
            'queue'
            'table'
          ]
        }
      }
    ]
  }
  tags: tags
}

// Outputs
output functionAppName string = functionApp.name
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output storageAccountName string = storageAccount.name
output appInsightsName string = appInsights.name
output servicePlanName string = servicePlan.name
output functionAppId string = functionApp.id
