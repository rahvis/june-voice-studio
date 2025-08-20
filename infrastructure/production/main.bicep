/**
 * Production Infrastructure for Voice Cloning System
 * Deploys production-ready Azure resources with enhanced security and monitoring
 */

@description('Production environment name')
param environment string = 'prod'

@description('Project name for resource naming')
param projectName string = 'voice-cloning'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Azure subscription ID')
param subscriptionId string = subscription().subscriptionId

@description('Resource group name')
param resourceGroupName string = resourceGroup().name

@description('Production network configuration')
param networkConfig object = {
  vnetAddressPrefix: '10.0.0.0/16'
  subnetConfigs: {
    appGateway: {
      name: 'appgateway-subnet'
      addressPrefix: '10.0.1.0/24'
      serviceEndpoints: ['Microsoft.KeyVault']
    }
    appService: {
      name: 'appservice-subnet'
      addressPrefix: '10.0.2.0/24'
      serviceEndpoints: ['Microsoft.KeyVault', 'Microsoft.Storage', 'Microsoft.Web']
    }
    functions: {
      name: 'functions-subnet'
      addressPrefix: '10.0.3.0/24'
      serviceEndpoints: ['Microsoft.KeyVault', 'Microsoft.Storage', 'Microsoft.Web']
    }
    database: {
      name: 'database-subnet'
      addressPrefix: '10.0.4.0/24'
      serviceEndpoints: ['Microsoft.KeyVault', 'Microsoft.Storage', 'Microsoft.CosmosDB']
    }
    monitoring: {
      name: 'monitoring-subnet'
      addressPrefix: '10.0.5.0/24'
      serviceEndpoints: ['Microsoft.KeyVault', 'Microsoft.Storage', 'Microsoft.OperationalInsights']
    }
  }
}

@description('Production security configuration')
param securityConfig object = {
  enablePrivateEndpoints: true
  enableNetworkSecurityGroups: true
  enableDDoSProtection: true
  enableFirewall: true
  enableWAF: true
  enableKeyVaultFirewall: true
  enableStorageFirewall: true
}

@description('Production scaling configuration')
param scalingConfig object = {
  appServicePlan: {
    sku: 'P1v3'
    tier: 'PremiumV3'
    capacity: 3
    maxCapacity: 10
  }
  functionsPlan: {
    sku: 'P1v3'
    tier: 'PremiumV3'
    capacity: 2
    maxCapacity: 8
  }
  cosmosDB: {
    throughput: 10000
    maxThroughput: 50000
    enableAutoscale: true
  }
  redis: {
    sku: 'Premium'
    capacity: 2
    enableClustering: true
  }
}

@description('Production monitoring configuration')
param monitoringConfig object = {
  enableApplicationInsights: true
  enableLogAnalytics: true
  enableAzureMonitor: true
  enableAlerts: true
  enableDiagnostics: true
  retentionDays: 90
}

@description('Production tags')
param tags object = {
  Environment: environment
  Project: projectName
  ManagedBy: 'Bicep'
  CreatedDate: utcNow('yyyy-MM-dd')
  CostCenter: 'voice-cloning-prod'
  Owner: 'devops-team'
  Compliance: 'GDPR-HIPAA-SOC2'
}

// Virtual Network
resource vnet 'Microsoft.Network/virtualNetworks@2023-05-01' = {
  name: '${projectName}-vnet-${environment}'
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [networkConfig.vnetAddressPrefix]
    }
    subnets: [
      {
        name: networkConfig.subnetConfigs.appGateway.name
        properties: {
          addressPrefix: networkConfig.subnetConfigs.appGateway.addressPrefix
          serviceEndpoints: networkConfig.subnetConfigs.appGateway.serviceEndpoints
          networkSecurityGroup: nsgAppGateway.id
        }
      }
      {
        name: networkConfig.subnetConfigs.appService.name
        properties: {
          addressPrefix: networkConfig.subnetConfigs.appService.addressPrefix
          serviceEndpoints: networkConfig.subnetConfigs.appService.serviceEndpoints
          networkSecurityGroup: nsgAppService.id
        }
      }
      {
        name: networkConfig.subnetConfigs.functions.name
        properties: {
          addressPrefix: networkConfig.subnetConfigs.functions.addressPrefix
          serviceEndpoints: networkConfig.subnetConfigs.functions.serviceEndpoints
          networkSecurityGroup: nsgFunctions.id
        }
      }
      {
        name: networkConfig.subnetConfigs.database.name
        properties: {
          addressPrefix: networkConfig.subnetConfigs.database.addressPrefix
          serviceEndpoints: networkConfig.subnetConfigs.database.serviceEndpoints
          networkSecurityGroup: nsgDatabase.id
        }
      }
      {
        name: networkConfig.subnetConfigs.monitoring.name
        properties: {
          addressPrefix: networkConfig.subnetConfigs.monitoring.addressPrefix
          serviceEndpoints: networkConfig.subnetConfigs.monitoring.serviceEndpoints
          networkSecurityGroup: nsgMonitoring.id
        }
      }
    ]
    enableDdosProtection: securityConfig.enableDDoSProtection
    enableVmProtection: false
  }
}

// Network Security Groups
resource nsgAppGateway 'Microsoft.Network/networkSecurityGroups@2023-05-01' = {
  name: '${projectName}-nsg-appgateway-${environment}'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'Allow-HTTP'
        properties: {
          priority: 100
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: 'Internet'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '80'
        }
      }
      {
        name: 'Allow-HTTPS'
        properties: {
          priority: 110
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: 'Internet'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '443'
        }
      }
      {
        name: 'Allow-AzureLoadBalancer'
        properties: {
          priority: 120
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: 'AzureLoadBalancer'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
    ]
  }
}

resource nsgAppService 'Microsoft.Network/networkSecurityGroups@2023-05-01' = {
  name: '${projectName}-nsg-appservice-${environment}'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'Allow-AppService'
        properties: {
          priority: 100
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: 'AppService'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
      {
        name: 'Allow-VNet'
        properties: {
          priority: 110
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: vnet.properties.addressSpace.addressPrefixes[0]
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
    ]
  }
}

resource nsgFunctions 'Microsoft.Network/networkSecurityGroups@2023-05-01' = {
  name: '${projectName}-nsg-functions-${environment}'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'Allow-Functions'
        properties: {
          priority: 100
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: 'AppService'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
      {
        name: 'Allow-VNet'
        properties: {
          priority: 110
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: vnet.properties.addressSpace.addressPrefixes[0]
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
    ]
  }
}

resource nsgDatabase 'Microsoft.Network/networkSecurityGroups@2023-05-01' = {
  name: '${projectName}-nsg-database-${environment}'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'Deny-Internet'
        properties: {
          priority: 100
          protocol: '*'
          access: 'Deny'
          direction: 'Inbound'
          sourceAddressPrefix: 'Internet'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
      {
        name: 'Allow-VNet'
        properties: {
          priority: 110
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: vnet.properties.addressSpace.addressPrefixes[0]
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
    ]
  }
}

resource nsgMonitoring 'Microsoft.Network/networkSecurityGroups@2023-05-01' = {
  name: '${projectName}-nsg-monitoring-${environment}'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'Allow-VNet'
        properties: {
          priority: 100
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: vnet.properties.addressSpace.addressPrefixes[0]
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
    ]
  }
}

// Application Gateway
resource appGateway 'Microsoft.Network/applicationGateways@2023-05-01' = {
  name: '${projectName}-appgw-${environment}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'WAF_v2'
      tier: 'WAF_v2'
      capacity: 2
    }
    gatewayIPConfigurations: [
      {
        name: 'gatewayIPConfig'
        properties: {
          subnet: {
            id: subnet(vnet.id, networkConfig.subnetConfigs.appGateway.name)
          }
        }
      }
    ]
    frontendPorts: [
      {
        name: 'httpPort'
        properties: {
          port: 80
        }
      }
      {
        name: 'httpsPort'
        properties: {
          port: 443
        }
      }
    ]
    frontendIPConfigurations: [
      {
        name: 'frontendIPConfig'
        properties: {
          publicIPAddress: {
            id: appGatewayPublicIP.id
          }
        }
      }
    ]
    backendAddressPools: [
      {
        name: 'backendPool'
        properties: {
          backendAddresses: []
        }
      }
    ]
    backendHttpSettingsCollection: [
      {
        name: 'httpSettings'
        properties: {
          port: 80
          protocol: 'Http'
          cookieBasedAffinity: 'Disabled'
          requestTimeout: 30
        }
      }
    ]
    httpListeners: [
      {
        name: 'httpListener'
        properties: {
          frontendIPConfiguration: {
            id: appGateway.properties.frontendIPConfigurations[0].id
          }
          frontendPort: {
            id: appGateway.properties.frontendPorts[0].id
          }
          protocol: 'Http'
        }
      }
      {
        name: 'httpsListener'
        properties: {
          frontendIPConfiguration: {
            id: appGateway.properties.frontendIPConfigurations[0].id
          }
          frontendPort: {
            id: appGateway.properties.frontendPorts[1].id
          }
          protocol: 'Https'
          sslCertificate: {
            id: sslCertificate.id
          }
        }
      }
    ]
    requestRoutingRules: [
      {
        name: 'httpRule'
        properties: {
          ruleType: 'Basic'
          httpListener: {
            id: appGateway.properties.httpListeners[0].id
          }
          backendAddressPool: {
            id: appGateway.properties.backendAddressPools[0].id
          }
          backendHttpSettings: {
            id: appGateway.properties.backendHttpSettingsCollection[0].id
          }
        }
      }
      {
        name: 'httpsRule'
        properties: {
          ruleType: 'Basic'
          httpListener: {
            id: appGateway.properties.httpListeners[1].id
          }
          backendAddressPool: {
            id: appGateway.properties.backendAddressPools[0].id
          }
          backendHttpSettings: {
            id: appGateway.properties.backendHttpSettingsCollection[0].id
          }
        }
      }
    ]
    webApplicationFirewallConfiguration: {
      enabled: securityConfig.enableWAF
      firewallMode: 'Prevention'
      ruleSetType: 'OWASP'
      ruleSetVersion: '3.2'
      maxRequestBodySizeInKb: 128
      fileUploadLimitInMb: 100
    }
  }
}

resource appGatewayPublicIP 'Microsoft.Network/publicIPAddresses@2023-05-01' = {
  name: '${projectName}-appgw-pip-${environment}'
  location: location
  tags: tags
  properties: {
    publicIPAllocationMethod: 'Static'
    publicIPAddressVersion: 'IPv4'
    dnsSettings: {
      domainNameLabel: '${projectName}-appgw-${environment}'
    }
  }
  sku: {
    name: 'Standard'
  }
}

resource sslCertificate 'Microsoft.Network/applicationGatewaySslCertificates@2023-05-01' = {
  parent: appGateway
  name: 'ssl-cert'
  properties: {
    data: 'base64-encoded-certificate-data'
    password: 'certificate-password'
  }
}

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${projectName}-plan-${environment}'
  location: location
  tags: tags
  sku: {
    name: scalingConfig.appServicePlan.sku
    tier: scalingConfig.appServicePlan.tier
    size: scalingConfig.appServicePlan.sku
    family: 'P'
    capacity: scalingConfig.appServicePlan.capacity
  }
  kind: 'linux'
  properties: {
    reserved: true
    perSiteScaling: false
    elasticScaleEnabled: true
    maximumElasticWorkerCount: scalingConfig.appServicePlan.maxCapacity
    targetWorkerCount: scalingConfig.appServicePlan.capacity
  }
}

// App Service
resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: '${projectName}-app-${environment}'
  location: location
  tags: tags
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    reserved: true
    httpsOnly: true
    clientAffinityEnabled: false
    siteConfig: {
      linuxFxVersion: 'Python|3.9'
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_URL'
          value: 'https://index.docker.io'
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'ENVIRONMENT'
          value: environment
        }
        {
          name: 'AZURE_SUBSCRIPTION_ID'
          value: subscriptionId
        }
        {
          name: 'AZURE_RESOURCE_GROUP'
          value: resourceGroupName
        }
      ]
      cors: {
        allowedOrigins: [
          'https://${projectName}-frontend-${environment}.azurewebsites.net'
        ]
        supportCredentials: true
      }
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      scmMinTlsVersion: '1.2'
      alwaysOn: true
      numberOfWorkers: scalingConfig.appServicePlan.capacity
      autoHealEnabled: true
      autoHealRules: {
        triggers: {
          privateBytesInKB: 262144
          statusCodes: [
            {
              status: 500
              subStatus: 0
              win32Status: 0
              path: '/api/*'
              count: 10
              timeInterval: '00:01:00'
            }
          ]
        }
        actions: {
          actionType: 'Recycle'
          minProcessExecutionTime: '00:00:30'
        }
      }
    }
    hostingEnvironmentProfile: {
      id: appServiceEnvironment.id
    }
  }
}

// App Service Environment
resource appServiceEnvironment 'Microsoft.Web/hostingEnvironments@2023-01-01' = {
  name: '${projectName}-ase-${environment}'
  location: location
  tags: tags
  properties: {
    name: '${projectName}-ase-${environment}'
    location: location
    virtualNetwork: {
      id: vnet.id
      subnet: subnet(vnet.id, networkConfig.subnetConfigs.appService.name)
    }
    internalLoadBalancingMode: 'Web, Publishing'
    multiSize: 'Standard_D4_v3'
    frontEndScaleFactor: 15
    userWhitelistedIpRanges: []
    allowedMultiSizes: 'Standard_D4_v3,Standard_D8_v3,Standard_D16_v3'
    allowedWorkerSizes: 'Standard_D4_v3,Standard_D8_v3,Standard_D16_v3'
    ipsslAddressCount: 2
    dnsSuffix: '${projectName}-${environment}.internal'
    maximumNumberOfMachines: 10
    upgradeDomains: 5
    upgradePreferences: {
      preUpgradePreferredZone: '1'
      preUpgradePreferredZoneGroup: '1'
    }
  }
}

// Functions App Service Plan
resource functionsPlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${projectName}-functions-plan-${environment}'
  location: location
  tags: tags
  sku: {
    name: scalingConfig.functionsPlan.sku
    tier: scalingConfig.functionsPlan.tier
    size: scalingConfig.functionsPlan.sku
    family: 'P'
    capacity: scalingConfig.functionsPlan.capacity
  }
  kind: 'linux'
  properties: {
    reserved: true
    perSiteScaling: false
    elasticScaleEnabled: true
    maximumElasticWorkerCount: scalingConfig.functionsPlan.maxCapacity
    targetWorkerCount: scalingConfig.functionsPlan.capacity
  }
}

// Functions App
resource functionsApp 'Microsoft.Web/sites@2023-01-01' = {
  name: '${projectName}-functions-${environment}'
  location: location
  tags: tags
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: functionsPlan.id
    reserved: true
    httpsOnly: true
    clientAffinityEnabled: false
    siteConfig: {
      linuxFxVersion: 'Python|3.9'
      appSettings: [
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'AzureWebJobsFeatureFlags'
          value: 'EnableWorkerIndexing'
        }
        {
          name: 'ENVIRONMENT'
          value: environment
        }
        {
          name: 'AZURE_SUBSCRIPTION_ID'
          value: subscriptionId
        }
        {
          name: 'AZURE_RESOURCE_GROUP'
          value: resourceGroupName
        }
      ]
      cors: {
        allowedOrigins: [
          'https://${projectName}-app-${environment}.azurewebsites.net'
          'https://${projectName}-frontend-${environment}.azurewebsites.net'
        ]
        supportCredentials: true
      }
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      scmMinTlsVersion: '1.2'
      alwaysOn: true
      numberOfWorkers: scalingConfig.functionsPlan.capacity
      autoHealEnabled: true
    }
    hostingEnvironmentProfile: {
      id: appServiceEnvironment.id
    }
  }
}

// Frontend App Service
resource frontendApp 'Microsoft.Web/sites@2023-01-01' = {
  name: '${projectName}-frontend-${environment}'
  location: location
  tags: tags
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    reserved: true
    httpsOnly: true
    clientAffinityEnabled: false
    siteConfig: {
      linuxFxVersion: 'Node|18-lts'
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'NODE_ENV'
          value: 'production'
        }
        {
          name: 'ENVIRONMENT'
          value: environment
        }
        {
          name: 'AZURE_SUBSCRIPTION_ID'
          value: subscriptionId
        }
        {
          name: 'AZURE_RESOURCE_GROUP'
          value: resourceGroupName
        }
      ]
      cors: {
        allowedOrigins: [
          'https://${projectName}-app-${environment}.azurewebsites.net'
        ]
        supportCredentials: true
      }
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      scmMinTlsVersion: '1.2'
      alwaysOn: true
      numberOfWorkers: scalingConfig.appServicePlan.capacity
      autoHealEnabled: true
    }
    hostingEnvironmentProfile: {
      id: appServiceEnvironment.id
    }
  }
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${projectName}-kv-${environment}'
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    networkAcls: {
      defaultAction: securityConfig.enableKeyVaultFirewall ? 'Deny' : 'Allow'
      bypass: 'AzureServices'
      ipRules: []
      virtualNetworkRules: securityConfig.enablePrivateEndpoints ? [
        {
          id: subnet(vnet.id, networkConfig.subnetConfigs.appService.name)
          ignoreMissingVnetServiceEndpoint: false
        }
        {
          id: subnet(vnet.id, networkConfig.subnetConfigs.functions.name)
          ignoreMissingVnetServiceEndpoint: false
        }
      ] : []
    }
  }
}

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${replace(projectName, '-', '')}st${environment}'
  location: location
  tags: tags
  sku: {
    name: 'Standard_GRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    networkAcls: {
      defaultAction: securityConfig.enableStorageFirewall ? 'Deny' : 'Allow'
      bypass: 'AzureServices'
      ipRules: []
      virtualNetworkRules: securityConfig.enablePrivateEndpoints ? [
        {
          id: subnet(vnet.id, networkConfig.subnetConfigs.appService.name)
          ignoreMissingVnetServiceEndpoint: false
        }
        {
          id: subnet(vnet.id, networkConfig.subnetConfigs.functions.name)
          ignoreMissingVnetServiceEndpoint: false
        }
      ] : []
    }
    encryption: {
      services: {
        blob: {
          enabled: true
        }
        file: {
          enabled: true
        }
        queue: {
          enabled: true
        }
        table: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

// Cosmos DB Account
resource cosmosDB 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: '${projectName}-cosmos-${environment}'
  location: location
  tags: tags
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
      maxStalenessPrefix: 100000
      maxIntervalInSeconds: 300
    }
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    enableMultipleWriteLocations: false
    enableAutomaticFailover: false
    networkAcls: {
      defaultAction: 'Deny'
      ipRules: []
      virtualNetworkRules: [
        {
          id: subnet(vnet.id, networkConfig.subnetConfigs.database.name)
          ignoreMissingVnetServiceEndpoint: false
        }
      ]
    }
    enableVirtualNetwork: true
    enableFreeTier: false
    apiProperties: {
      serverVersion: '4.0'
    }
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 240
        backupRetentionIntervalInHours: 8
        backupStorageRedundancy: 'Geo'
      }
    }
  }
}

// Redis Cache
resource redisCache 'Microsoft.Cache/Redis@2023-08-01' = {
  name: '${projectName}-redis-${environment}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: scalingConfig.redis.sku
      family: 'P'
      capacity: scalingConfig.redis.capacity
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    redisConfiguration: {
      maxmemoryPolicy: 'allkeys-lru'
      enableRdbBackup: true
      rdbBackupMaxSnapshotCount: 1
      rdbBackupFrequency: '15'
      enableAofBackup: false
      maxmemoryReserved: 50
      maxfragmentationmemoryReserved: 50
      maxmemoryDelta: 50
    }
    replicasPerMaster: scalingConfig.redis.enableClustering ? 1 : 0
    shardCount: scalingConfig.redis.enableClustering ? 2 : 0
    subnetId: subnet(vnet.id, networkConfig.subnetConfigs.appService.name)
    staticIP: '10.0.2.100'
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${projectName}-ai-${environment}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    DisableIpMasking: false
    EnableAccessInference: true
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${projectName}-logs-${environment}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: monitoringConfig.retentionDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Azure Monitor Action Group
resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: '${projectName}-ag-${environment}'
  location: 'Global'
  tags: tags
  properties: {
    groupShortName: 'voice-cloning'
    enabled: true
    emailReceivers: [
      {
        name: 'devops-team'
        emailAddress: 'devops@company.com'
        useCommonAlertSchema: true
      }
    ]
    smsReceivers: []
    webhookReceivers: []
    itsmReceivers: []
    azureAppPushReceivers: []
    automationRunbookReceivers: []
    voiceReceivers: []
    logicAppReceivers: []
    azureFunctionReceivers: []
    armRoleReceivers: []
    eventHubReceivers: []
  }
}

// Azure Monitor Alert Rules
resource alertRule 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${projectName}-alert-cpu-${environment}'
  location: 'Global'
  tags: tags
  properties: {
    description: 'Alert when CPU usage is high'
    severity: 2
    enabled: true
    scopes: [
      appService.id
      functionsApp.id
    ]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'HighCPUUsage'
          metricName: 'CpuPercentage'
          operator: 'GreaterThan'
          threshold: 80
          timeAggregation: 'Average'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroup.id
        webhookProperties: {}
      }
    ]
  }
}

// CDN Profile
resource cdnProfile 'Microsoft.Cdn/profiles@2023-05-01' = {
  name: '${projectName}-cdn-${environment}'
  location: 'Global'
  tags: tags
  sku: {
    name: 'Standard_Microsoft'
  }
}

// CDN Endpoint
resource cdnEndpoint 'Microsoft.Cdn/profiles/endpoints@2023-05-01' = {
  parent: cdnProfile
  name: '${projectName}-endpoint-${environment}'
  location: 'Global'
  tags: tags
  properties: {
    originHostHeader: appService.properties.defaultHostName
    isHttpAllowed: false
    isHttpsAllowed: true
    isCompressionEnabled: true
    contentTypesToCompress: [
      'text/plain'
      'text/html'
      'text/css'
      'text/javascript'
      'application/javascript'
      'application/json'
      'application/xml'
    ]
    queryStringCachingBehavior: 'IgnoreQueryString'
    optimizationType: 'GeneralWebDelivery'
    geoFilters: []
    urlSigningKeys: []
    deliveryPolicy: {
      description: 'Delivery policy for voice cloning system'
      rules: [
        {
          name: 'CacheControl'
          order: 1
          conditions: [
            {
              name: 'UrlFileExtension'
              parameters: {
                operator: 'Any'
                extensions: [
                  'js'
                  'css'
                  'png'
                  'jpg'
                  'jpeg'
                  'gif'
                  'ico'
                  'svg'
                  'woff'
                  'woff2'
                  'ttf'
                  'eot'
                ]
              }
            }
          ]
          actions: [
            {
              name: 'CacheExpiration'
              parameters: {
                cacheBehavior: 'Override'
                cacheType: 'All'
                cacheDuration: '365.00:00:00'
              }
            }
          ]
        }
        {
          name: 'AudioFiles'
          order: 2
          conditions: [
            {
              name: 'UrlFileExtension'
              parameters: {
                operator: 'Any'
                extensions: [
                  'wav'
                  'mp3'
                  'm4a'
                  'ogg'
                  'flac'
                ]
              }
            }
          ]
          actions: [
            {
              name: 'CacheExpiration'
              parameters: {
                cacheBehavior: 'Override'
                cacheType: 'All'
                cacheDuration: '30.00:00:00'
              }
            }
          ]
        }
      ]
    }
  }
}

// Private Endpoints (if enabled)
resource appServicePrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = if (securityConfig.enablePrivateEndpoints) {
  name: '${projectName}-app-pe-${environment}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: subnet(vnet.id, networkConfig.subnetConfigs.appService.name)
    }
    privateLinkServiceConnections: [
      {
        name: 'app-service-connection'
        properties: {
          privateLinkServiceId: appService.id
          groupIds: [
            'sites'
          ]
        }
      }
    ]
  }
}

resource functionsPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = if (securityConfig.enablePrivateEndpoints) {
  name: '${projectName}-functions-pe-${environment}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: subnet(vnet.id, networkConfig.subnetConfigs.functions.name)
    }
    privateLinkServiceConnections: [
      {
        name: 'functions-connection'
        properties: {
          privateLinkServiceId: functionsApp.id
          groupIds: [
            'sites'
          ]
        }
      }
    ]
  }
}

resource keyVaultPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = if (securityConfig.enablePrivateEndpoints) {
  name: '${projectName}-kv-pe-${environment}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: subnet(vnet.id, networkConfig.subnetConfigs.appService.name)
    }
    privateLinkServiceConnections: [
      {
        name: 'keyvault-connection'
        properties: {
          privateLinkServiceId: keyVault.id
          groupIds: [
            'vault'
          ]
        }
      }
    ]
  }
}

resource storagePrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = if (securityConfig.enablePrivateEndpoints) {
  name: '${projectName}-storage-pe-${environment}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: subnet(vnet.id, networkConfig.subnetConfigs.appService.name)
    }
    privateLinkServiceConnections: [
      {
        name: 'storage-connection'
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
}

resource cosmosDBPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = if (securityConfig.enablePrivateEndpoints) {
  name: '${projectName}-cosmos-pe-${environment}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: subnet(vnet.id, networkConfig.subnetConfigs.database.name)
    }
    privateLinkServiceConnections: [
      {
        name: 'cosmos-connection'
        properties: {
          privateLinkServiceId: cosmosDB.id
          groupIds: [
            'Sql'
          ]
        }
      }
    ]
  }
}

// Outputs
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'
output functionsUrl string = 'https://${functionsApp.properties.defaultHostName}'
output frontendUrl string = 'https://${frontendApp.properties.defaultHostName}'
output appGatewayUrl string = 'https://${appGatewayPublicIP.properties.dnsSettings.fqdn}'
output keyVaultName string = keyVault.name
output storageAccountName string = storageAccount.name
output cosmosDBName string = cosmosDB.name
output redisCacheName string = redisCache.name
output appInsightsName string = appInsights.name
output logAnalyticsWorkspaceName string = logAnalyticsWorkspace.name
output vnetName string = vnet.name
output vnetId string = vnet.id
output cdnEndpointUrl string = 'https://${cdnEndpoint.properties.hostName}'

