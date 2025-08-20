/**
 * Production Monitoring Dashboard for Voice Cloning System
 * Implements comprehensive monitoring, alerting, and visualization
 */

@description('Project name for resource naming')
param projectName string = 'voice-cloning'

@description('Environment name')
param environment string = 'prod'

@description('Location for resources')
param location string = resourceGroup().location

@description('Log Analytics workspace resource ID')
param logAnalyticsWorkspaceId string

@description('Application Insights resource ID')
param appInsightsId string

@description('Action group for alerts')
param actionGroupId string

// Dashboard for production monitoring
resource monitoringDashboard 'Microsoft.Portal/dashboards@2020-09-01-preview' = {
  name: '${projectName}-monitoring-${environment}'
  location: location
  properties: {
    lenses: [
      {
        order: 0
        parts: [
          {
            position: {
              x: 0
              y: 0
              rowSpan: 2
              colSpan: 3
            }
            metadata: {
              inputs: [
                {
                  name: 'queryInputs'
                  isOptional: true
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  Query: 'AzureMetrics | where ResourceProvider == "Microsoft.Web/sites" | where MetricName == "HttpResponseTime" | summarize avg(Total) by bin(TimeGenerated, 5m) | render timechart'
                  PartTitle: 'Response Time Trends'
                  PartSubTitle: 'Average HTTP response time over time'
                }
              }
            }
          }
          {
            position: {
              x: 3
              y: 0
              rowSpan: 2
              colSpan: 3
            }
            metadata: {
              inputs: [
                {
                  name: 'queryInputs'
                  isOptional: true
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  Query: 'AzureMetrics | where ResourceProvider == "Microsoft.Web/sites" | where MetricName == "Http5xx" | summarize sum(Total) by bin(TimeGenerated, 5m) | render timechart'
                  PartTitle: 'Error Rate Trends'
                  PartSubTitle: 'HTTP 5xx errors over time'
                }
              }
            }
          }
          {
            position: {
              x: 6
              y: 0
              rowSpan: 2
              colSpan: 3
            }
            metadata: {
              inputs: [
                {
                  name: 'queryInputs'
                  isOptional: true
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  Query: 'AzureMetrics | where ResourceProvider == "Microsoft.Web/sites" | where MetricName == "Requests" | summarize sum(Total) by bin(TimeGenerated, 5m) | render timechart'
                  PartTitle: 'Request Volume'
                  PartSubTitle: 'Total requests over time'
                }
              }
            }
          }
          {
            position: {
              x: 0
              y: 2
              rowSpan: 2
              colSpan: 3
            }
            metadata: {
              inputs: [
                {
                  name: 'queryInputs'
                  isOptional: true
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  Query: 'AzureMetrics | where ResourceProvider == "Microsoft.Web/sites" | where MetricName == "MemoryPercentage" | summarize avg(Total) by bin(TimeGenerated, 5m) | render timechart'
                  PartTitle: 'Memory Usage'
                  PartSubTitle: 'Average memory percentage over time'
                }
              }
            }
          }
          {
            position: {
              x: 3
              y: 2
              rowSpan: 2
              colSpan: 3
            }
            metadata: {
              inputs: [
                {
                  name: 'queryInputs'
                  isOptional: true
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  Query: 'AzureMetrics | where ResourceProvider == "Microsoft.Web/sites" | where MetricName == "CpuPercentage" | summarize avg(Total) by bin(TimeGenerated, 5m) | render timechart'
                  PartTitle: 'CPU Usage'
                  PartSubTitle: 'Average CPU percentage over time'
                }
              }
            }
          }
          {
            position: {
              x: 6
              y: 2
              rowSpan: 2
              colSpan: 3
            }
            metadata: {
              inputs: [
                {
                  name: 'queryInputs'
                  isOptional: true
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  Query: 'AzureMetrics | where ResourceProvider == "Microsoft.Storage/storageAccounts" | where MetricName == "Transactions" | summarize sum(Total) by bin(TimeGenerated, 5m) | render timechart'
                  PartTitle: 'Storage Transactions'
                  PartSubTitle: 'Storage account transactions over time'
                }
              }
            }
          }
        ]
      }
    ]
    metadata: {
      model: {
        timeRange: {
          relative: {
            duration: 24
            timeUnit: 1
          }
        }
        filterLocale: 'en-us'
        timeContext: {
          relative: {
            duration: 24
            timeUnit: 1
          }
        }
        __metadata: {
          model: {
            timeRange: {
              relative: {
                duration: 24
                timeUnit: 1
              }
            }
            filterLocale: 'en-us'
            timeContext: {
              relative: {
                duration: 24
                timeUnit: 1
              }
            }
          }
        }
      }
    }
  }
}

// Alert rules for critical metrics
resource responseTimeAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${projectName}-response-time-alert-${environment}'
  location: 'global'
  properties: {
    description: 'Alert when HTTP response time is high'
    severity: 2
    enabled: true
    scopes: [
      appInsightsId
    ]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'HighResponseTime'
          metricName: 'HttpResponseTime'
          operator: 'GreaterThan'
          threshold: 2000
          timeAggregation: 'Average'
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroupId
        webhookProperties: {}
      }
    ]
  }
}

resource errorRateAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${projectName}-error-rate-alert-${environment}'
  location: 'global'
  properties: {
    description: 'Alert when HTTP error rate is high'
    severity: 1
    enabled: true
    scopes: [
      appInsightsId
    ]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'HighErrorRate'
          metricName: 'Http5xx'
          operator: 'GreaterThan'
          threshold: 5
          timeAggregation: 'Total'
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroupId
        webhookProperties: {}
      }
    ]
  }
}

resource memoryUsageAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${projectName}-memory-usage-alert-${environment}'
  location: 'global'
  properties: {
    description: 'Alert when memory usage is high'
    severity: 2
    enabled: true
    scopes: [
      appInsightsId
    ]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'HighMemoryUsage'
          metricName: 'MemoryPercentage'
          operator: 'GreaterThan'
          threshold: 80
          timeAggregation: 'Average'
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroupId
        webhookProperties: {}
      }
    ]
  }
}

// Log Analytics query packs for advanced monitoring
resource queryPack 'Microsoft.OperationalInsights/queryPacks@2019-09-01' = {
  name: '${projectName}-queries-${environment}'
  location: location
  properties: {
    queryPackId: guid('${projectName}-${environment}')
    timeCreated: utcNow()
    timeModified: utcNow()
  }
}

// Saved searches for common monitoring queries
resource savedSearch 'Microsoft.OperationalInsights/workspaces/savedSearches@2020-08-01' = {
  parent: logAnalyticsWorkspaceId
  name: 'VoiceCloningSystemErrors'
  properties: {
    category: 'Voice Cloning System'
    displayName: 'System Errors and Exceptions'
    query: 'Event | where EventLevelName == "Error" or EventLevelName == "Critical" | summarize count() by bin(TimeGenerated, 1h) | render timechart'
    functionAlias: 'VoiceCloningErrors'
    functionParameters: '{}'
    version: 1
  }
}

// Outputs
output dashboardName string = monitoringDashboard.name
output dashboardUrl string = 'https://portal.azure.com/#blade/Microsoft_Azure_Portal/DashboardBlade/name/${monitoringDashboard.name}'
output queryPackName string = queryPack.name

