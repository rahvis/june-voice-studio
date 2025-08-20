@description('The name of the OpenAI Service resource')
param openaiServiceName string

@description('The location for the OpenAI Service')
param location string = resourceGroup().location

@description('The virtual network name for private endpoints')
param virtualNetworkName string

@description('The subnet name for private endpoints')
param subnetName string

@description('Tags to apply to the resource')
param tags object = {}

// Azure OpenAI Service
resource openaiService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openaiServiceName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'OpenAI'
  properties: {
    customSubDomainName: openaiServiceName
    networkAcls: {
      defaultAction: 'Deny'
      virtualNetworkRules: [
        {
          id: subnet().id
          ignoreMissingVnetServiceEndpoint: false
        }
      ]
      ipRules: []
    }
    publicNetworkAccess: 'Disabled'
    capabilities: [
      {
        name: 'TextGeneration'
      }
      {
        name: 'TextToSpeech'
      }
    ]
  }
  tags: tags
}

// Private Endpoint for OpenAI Service
resource openaiPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-09-01' = {
  name: '${openaiServiceName}-pe'
  location: location
  properties: {
    subnet: {
      id: subnet().id
    }
    privateLinkServiceConnections: [
      {
        name: 'openai-service-connection'
        properties: {
          privateLinkServiceId: openaiService.id
          groupIds: ['openai']
          requestMessage: 'Request for OpenAI Service private endpoint'
        }
      }
    ]
  }
  tags: tags
}

// Private DNS Zone for OpenAI Service
resource openaiPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.openai.azure.com'
  location: 'global'
}

// Private DNS Zone Group
resource openaiPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = {
  name: 'openai-dns-zone-group'
  parent: openaiPrivateEndpoint
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'openai-dns-config'
        properties: {
          privateDnsZoneId: openaiPrivateDnsZone.id
          recordSets: [
            {
              recordType: 'A'
              recordSetName: openaiServiceName
              ttl: 300
              ipAddresses: [
                '10.0.0.3' // This will be replaced with actual IP
              ]
            }
          ]
        }
      }
    ]
  }
}

// Get subnet reference
resource subnet 'Microsoft.Network/virtualNetworks/subnets@2023-09-01' existing = {
  name: subnetName
  parent: resource('Microsoft.Network/virtualNetworks@2023-09-01', virtualNetworkName)
}

// Outputs
output openaiServiceId string = openaiService.id
output openaiServiceEndpoint string = openaiService.properties.endpoint
output openaiServiceKey string = openaiService.listKeys().key1
output openaiServiceRegion string = location
output privateEndpointId string = openaiPrivateEndpoint.id
