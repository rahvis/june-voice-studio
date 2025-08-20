@description('The name of the Translator Service resource')
param translatorServiceName string

@description('The location for the Translator Service')
param location string = resourceGroup().location

@description('The pricing tier for the Translator Service')
param sku string = 'S1'

@description('The virtual network name for private endpoints')
param virtualNetworkName string

@description('The subnet name for private endpoints')
param subnetName string

@description('Tags to apply to the resource')
param tags object = {}

// Azure AI Translator Service
resource translatorService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: translatorServiceName
  location: location
  sku: {
    name: sku
  }
  kind: 'TextTranslation'
  properties: {
    customSubDomainName: translatorServiceName
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
        name: 'TextTranslation'
      }
    ]
  }
  tags: tags
}

// Private Endpoint for Translator Service
resource translatorPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-09-01' = {
  name: '${translatorServiceName}-pe'
  location: location
  properties: {
    subnet: {
      id: subnet().id
    }
    privateLinkServiceConnections: [
      {
        name: 'translator-service-connection'
        properties: {
          privateLinkServiceId: translatorService.id
          groupIds: ['texttranslation']
          requestMessage: 'Request for Translator Service private endpoint'
        }
      }
    ]
  }
  tags: tags
}

// Private DNS Zone for Translator Service
resource translatorPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.cognitiveservices.azure.com'
  location: 'global'
}

// Private DNS Zone Group
resource translatorPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = {
  name: 'translator-dns-zone-group'
  parent: translatorPrivateEndpoint
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'translator-dns-config'
        properties: {
          privateDnsZoneId: translatorPrivateDnsZone.id
          recordSets: [
            {
              recordType: 'A'
              recordSetName: translatorServiceName
              ttl: 300
              ipAddresses: [
                '10.0.0.2' // This will be replaced with actual IP
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
output translatorServiceId string = translatorService.id
output translatorServiceEndpoint string = translatorService.properties.endpoint
output translatorServiceKey string = translatorService.listKeys().key1
output translatorServiceRegion string = location
output privateEndpointId string = translatorPrivateEndpoint.id
