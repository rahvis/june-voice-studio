/**
 * Disaster Recovery Configuration for Voice Cloning System
 * Implements backup, replication, and recovery procedures
 */

@description('Primary region for disaster recovery')
param primaryRegion string = 'East US 2'

@description('Secondary region for disaster recovery')
param secondaryRegion string = 'West US 2'

@description('Project name for resource naming')
param projectName string = 'voice-cloning'

@description('Environment name')
param environment string = 'prod'

// Geo-redundant storage for critical data
resource geoRedundantStorage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${projectName}geodr${environment}'
  location: secondaryRegion
  sku: {
    name: 'Standard_GRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
    networkAcls: {
      defaultAction: 'Deny'
      ipRules: []
      virtualNetworkRules: []
    }
  }
}

// Backup vault for comprehensive backup
resource backupVault 'Microsoft.RecoveryServices/vaults@2023-02-01' = {
  name: '${projectName}-backup-${environment}'
  location: primaryRegion
  sku: {
    name: 'Standard'
  }
  properties: {
    publicNetworkAccess: 'Disabled'
  }
}

// Recovery Services vault in secondary region
resource secondaryBackupVault 'Microsoft.RecoveryServices/vaults@2023-02-01' = {
  name: '${projectName}-backup-${environment}-dr'
  location: secondaryRegion
  sku: {
    name: 'Standard'
  }
  properties: {
    publicNetworkAccess: 'Disabled'
  }
}

// Site Recovery vault for VM replication
resource siteRecoveryVault 'Microsoft.RecoveryServices/vaults@2023-02-01' = {
  name: '${projectName}-asr-${environment}'
  location: primaryRegion
  sku: {
    name: 'Standard'
  }
  properties: {
    publicNetworkAccess: 'Disabled'
  }
}

// Backup policies
resource backupPolicy 'Microsoft.RecoveryServices/vaults/backupPolicies@2023-02-01' = {
  parent: backupVault
  name: 'DefaultPolicy'
  properties: {
    backupManagementType: 'AzureIaasVM'
    schedulePolicy: {
      schedulePolicyType: 'SimpleSchedulePolicy'
      scheduleRunFrequency: 'Daily'
      scheduleRunTimes: ['02:00']
    }
    retentionPolicy: {
      retentionPolicyType: 'SimpleRetentionPolicy'
      retentionDuration: {
        count: 30
        durationType: 'Days'
      }
    }
  }
}

// Site Recovery replication policy
resource replicationPolicy 'Microsoft.RecoveryServices/vaults/replicationPolicies@2023-02-01' = {
  parent: siteRecoveryVault
  name: 'DefaultReplicationPolicy'
  properties: {
    providerSpecificInput: {
      instanceType: 'HyperVReplicaAzurePolicyInput'
      recoveryPointHistoryDuration: 24
      applicationConsistentSnapshotFrequencyInHours: 4
      replicationIntervalInSeconds: 300
      onlineReplicationStartTime: '00:00:00'
      encryption: 'Disabled'
    }
  }
}

// Recovery plan template
resource recoveryPlan 'Microsoft.RecoveryServices/vaults/recoveryPlans@2023-02-01' = {
  parent: siteRecoveryVault
  name: 'VoiceCloningRecoveryPlan'
  properties: {
    friendlyName: 'Voice Cloning System Recovery Plan'
    groups: [
      {
        groupType: 'Shutdown'
        replicationProtectedItems: []
        startGroupActions: []
        endGroupActions: []
      }
      {
        groupType: 'Failover'
        replicationProtectedItems: []
        startGroupActions: []
        endGroupActions: []
      }
      {
        groupType: 'Boot'
        replicationProtectedItems: []
        startGroupActions: []
        endGroupActions: []
      }
    ]
  }
}

// Outputs
output geoRedundantStorageName string = geoRedundantStorage.name
output backupVaultName string = backupVault.name
output secondaryBackupVaultName string = secondaryBackupVault.name
output siteRecoveryVaultName string = siteRecoveryVault.name
output recoveryPlanName string = recoveryPlan.name

