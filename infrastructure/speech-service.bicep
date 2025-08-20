@description('The name of the Speech Service resource')
param speechServiceName string

@description('The location for the Speech Service')
param location string = resourceGroup().location

@description('The pricing tier for the Speech Service')
param sku string = 'S0'

@description('The resource group name')
param resourceGroupName string = resourceGroup().name

@description('The virtual network name for private endpoints')
param virtualNetworkName string

@description('The subnet name for private endpoints')
param subnetName string

@description('Tags to apply to the resource')
param tags object = {}

// Azure AI Speech Service
resource speechService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: speechServiceName
  location: location
  sku: {
    name: sku
  }
  kind: 'SpeechServices'
  properties: {
    customSubDomainName: speechServiceName
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
        name: 'CustomNeuralVoice'
      }
      {
        name: 'SpeakerRecognition'
      }
    ]
  }
  tags: tags
}

// Private Endpoint for Speech Service
resource speechPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-09-01' = {
  name: '${speechServiceName}-pe'
  location: location
  properties: {
    subnet: {
      id: subnet().id
    }
    privateLinkServiceConnections: [
      {
        name: 'speech-service-connection'
        properties: {
          privateLinkServiceId: speechService.id
          groupIds: ['speech'
          requestMessage: 'Request for Speech Service private endpoint'
        }
      }
    ]
  }
  tags: tags
}

// Private DNS Zone for Speech Service
resource speechPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.cognitiveservices.azure.com'
  location: 'global'
}

// Private DNS Zone Group
resource speechPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = {
  name: 'speech-dns-zone-group'
  parent: speechPrivateEndpoint
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'speech-dns-config'
        properties: {
          privateDnsZoneId: speechPrivateDnsZone.id
          recordSets: [
            {
              recordType: 'A'
              recordSetName: speechServiceName
              ttl: 300
              ipAddresses: [
                '10.0.0.1' // This will be replaced with actual IP
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
output speechServiceId string = speechService.id
output speechServiceEndpoint string = speechService.properties.endpoint
output speechServiceKey string = speechService.listKeys().key1
output speechServiceRegion string = location
output privateEndpointId string = speechPrivateEndpoint.id
