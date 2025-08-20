@description('The name of the resource group')
param resourceGroupName string

@description('The location for all resources')
param location string = resourceGroup().location

@description('The environment name (dev, staging, prod)')
param environment string = 'dev'

@description('The project name')
param projectName string = 'voice-cloning'

@description('Tags to apply to all resources')
param tags object = union({
  Environment: environment
  Project: projectName
  ManagedBy: 'Bicep'
}, tags)

// Generate unique names
var uniqueSuffix = uniqueString(resourceGroup().id, environment)
var speechServiceName = '${projectName}-speech-${uniqueSuffix}'
var translatorServiceName = '${projectName}-translator-${uniqueSuffix}'
var openaiServiceName = '${projectName}-openai-${uniqueSuffix}'
var keyVaultName = '${projectName}-kv-${uniqueSuffix}'
var storageAccountName = '${projectName}storage${uniqueSuffix}'
var cosmosDbName = '${projectName}-cosmos-${uniqueSuffix}'
var vnetName = '${projectName}-vnet-${uniqueSuffix}'
var apiManagementName = '${projectName}-apim-${uniqueSuffix}'
var appInsightsName = '${projectName}-ai-${uniqueSuffix}'

// Virtual Network
resource virtualNetwork 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: ['10.0.0.0/16']
    }
    subnets: [
      {
        name: 'default'
        properties: {
          addressPrefix: '10.0.0.0/24'
          privateEndpointNetworkPolicies: 'Enabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
        }
      }
      {
        name: 'private-endpoints'
        properties: {
          addressPrefix: '10.0.1.0/24'
          privateEndpointNetworkPolicies: 'Enabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
        }
      }
    ]
  }
  tags: tags
}

// Network Security Group
resource networkSecurityGroup 'Microsoft.Network/networkSecurityGroups@2023-09-01' = {
  name: '${projectName}-nsg-${uniqueSuffix}'
  location: location
  properties: {
    securityRules: [
      {
        name: 'AllowHTTPS'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'AllowHTTP'
        properties: {
          priority: 110
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '80'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
  tags: tags
}

// Associate NSG with subnet
resource nsgAssociation 'Microsoft.Network/virtualNetworks/subnets@2023-09-01' = {
  name: 'default'
  parent: virtualNetwork
  properties: {
    addressPrefix: '10.0.0.0/24'
    privateEndpointNetworkPolicies: 'Enabled'
    privateLinkServiceNetworkPolicies: 'Enabled'
    networkSecurityGroup: {
      id: networkSecurityGroup.id
    }
  }
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
      ipRules: []
      virtualNetworkRules: [
        {
          id: virtualNetwork.properties.subnets[0].id
          ignoreMissingVnetServiceEndpoint: false
        }
      ]
    }
    publicNetworkAccess: 'Disabled'
  }
  tags: tags
}

// Storage Account
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
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
      ipRules: []
      virtualNetworkRules: [
        {
          id: virtualNetwork.properties.subnets[0].id
          ignoreMissingVnetServiceEndpoint: false
        }
      ]
    }
    publicNetworkAccess: 'Disabled'
  }
  tags: tags
}

// Blob Container for audio files
resource audioContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/audio-files'
  properties: {
    publicAccess: 'None'
  }
}

// Cosmos DB Account
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: cosmosDbName
  location: location
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    networkAclBypass: 'AzureServices'
    networkAclBypassResourceIds: []
    ipRules: []
    virtualNetworkRules: [
      {
        id: virtualNetwork.properties.subnets[0].id
        ignoreMissingVnetServiceEndpoint: false
      }
    ]
    publicNetworkAccess: 'Disabled'
  }
  tags: tags
}

// Cosmos DB Database
resource cosmosDbDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  name: '${cosmosDbAccount.name}/voice-cloning-db'
  properties: {
    resource: {
      id: 'voice-cloning-db'
    }
  }
}

// Cosmos DB Container for voice metadata
resource voiceMetadataContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  name: '${cosmosDbDatabase.name}/voice-metadata'
  properties: {
    resource: {
      id: 'voice-metadata'
      partitionKey: {
        paths: ['/userId']
        kind: 'Hash'
      }
    }
  }
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

// Deploy Speech Service
module speechService 'speech-service.bicep' = {
  name: 'speech-service-deployment'
  params: {
    speechServiceName: speechServiceName
    location: location
    virtualNetworkName: virtualNetwork.name
    subnetName: 'private-endpoints'
    tags: tags
  }
}

// Deploy Translator Service
module translatorService 'translator-service.bicep' = {
  name: 'translator-service-deployment'
  params: {
    translatorServiceName: translatorServiceName
    location: location
    virtualNetworkName: virtualNetwork.name
    subnetName: 'private-endpoints'
    tags: tags
  }
}

// Deploy OpenAI Service
module openaiService 'openai-service.bicep' = {
  name: 'openai-service-deployment'
  params: {
    openaiServiceName: openaiServiceName
    location: location
    virtualNetworkName: virtualNetwork.name
    subnetName: 'private-endpoints'
    tags: tags
  }
}

// API Management
resource apiManagement 'Microsoft.ApiManagement/service@2023-05-01-preview' = {
  name: apiManagementName
  location: location
  sku: {
    name: 'Developer'
    capacity: 1
  }
  properties: {
    publisherName: 'Voice Cloning Team'
    publisherEmail: 'admin@voicecloning.com'
    virtualNetworkType: 'External'
    virtualNetworkConfiguration: {
      subnetResourceId: virtualNetwork.properties.subnets[0].id
    }
  }
  tags: tags
}

// Outputs
output speechServiceId string = speechService.outputs.speechServiceId
output speechServiceEndpoint string = speechService.outputs.speechServiceEndpoint
output translatorServiceId string = translatorService.outputs.translatorServiceId
output translatorServiceEndpoint string = translatorService.outputs.translatorServiceEndpoint
output openaiServiceId string = openaiService.outputs.openaiServiceId
output openaiServiceEndpoint string = openaiService.outputs.openaiServiceEndpoint
output keyVaultName string = keyVault.name
output storageAccountName string = storageAccount.name
output cosmosDbName string = cosmosDbAccount.name
output virtualNetworkName string = virtualNetwork.name
output apiManagementName string = apiManagement.name
output appInsightsName string = appInsights.name
