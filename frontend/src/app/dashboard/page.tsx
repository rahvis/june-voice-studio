'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/contexts/AuthContext';
import { Button, Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui';
import { LoadingSpinner } from '@/components/ui';
import { motion } from 'framer-motion';
import { 
  Mic, 
  Play, 
  Settings, 
  Download, 
  Trash2, 
  Plus, 
  BarChart3, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  TrendingUp,
  Volume2,
  FileAudio,
  Users,
  Activity
} from 'lucide-react';
import Link from 'next/link';

interface VoiceModel {
  id: string;
  name: string;
  language: string;
  gender: 'male' | 'female' | 'neutral';
  status: 'training' | 'ready' | 'failed' | 'processing';
  quality: 'high' | 'medium' | 'low';
  trainingProgress: number;
  createdAt: Date;
  lastUsed: Date;
  totalSynthesis: number;
  totalDuration: number;
}

interface SynthesisStats {
  totalSynthesis: number;
  totalDuration: number;
  averageQuality: number;
  mostUsedVoice: string;
  recentActivity: Array<{
    id: string;
    text: string;
    voice: string;
    duration: number;
    timestamp: Date;
  }>;
}

interface SystemStatus {
  azureServices: {
    speech: 'healthy' | 'degraded' | 'down';
    translator: 'healthy' | 'degraded' | 'down';
    openai: 'healthy' | 'degraded' | 'down';
  };
  storage: {
    used: number;
    total: number;
    percentage: number;
  };
  performance: {
    averageResponseTime: number;
    uptime: number;
    errorRate: number;
  };
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [voiceModels, setVoiceModels] = useState<VoiceModel[]>([]);
  const [synthesisStats, setSynthesisStats] = useState<SynthesisStats | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock data loading
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setIsLoading(true);
        
        // Simulate API calls
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Mock voice models
        const mockVoiceModels: VoiceModel[] = [
          {
            id: 'voice-1',
            name: 'John\'s Voice',
            language: 'en-US',
            gender: 'male',
            status: 'ready',
            quality: 'high',
            trainingProgress: 100,
            createdAt: new Date('2024-01-15'),
            lastUsed: new Date('2024-01-20'),
            totalSynthesis: 45,
            totalDuration: 1800,
          },
          {
            id: 'voice-2',
            name: 'Sarah\'s Voice',
            language: 'en-US',
            gender: 'female',
            status: 'training',
            quality: 'high',
            trainingProgress: 75,
            createdAt: new Date('2024-01-18'),
            lastUsed: new Date('2024-01-19'),
            totalSynthesis: 12,
            totalDuration: 480,
          },
          {
            id: 'voice-3',
            name: 'David\'s Voice',
            language: 'en-US',
            gender: 'male',
            status: 'failed',
            quality: 'medium',
            trainingProgress: 0,
            createdAt: new Date('2024-01-10'),
            lastUsed: new Date('2024-01-12'),
            totalSynthesis: 8,
            totalDuration: 320,
          },
        ];

        // Mock synthesis stats
        const mockSynthesisStats: SynthesisStats = {
          totalSynthesis: 65,
          totalDuration: 2600,
          averageQuality: 4.2,
          mostUsedVoice: 'John\'s Voice',
          recentActivity: [
            {
              id: 'act-1',
              text: 'Welcome to our advanced text-to-speech system...',
              voice: 'John\'s Voice',
              duration: 45,
              timestamp: new Date('2024-01-20T10:30:00'),
            },
            {
              id: 'act-2',
              text: 'This is a sample text for testing voice synthesis...',
              voice: 'Sarah\'s Voice',
              duration: 32,
              timestamp: new Date('2024-01-20T09:15:00'),
            },
          ],
        };

        // Mock system status
        const mockSystemStatus: SystemStatus = {
          azureServices: {
            speech: 'healthy',
            translator: 'healthy',
            openai: 'healthy',
          },
          storage: {
            used: 2.4,
            total: 10.0,
            percentage: 24,
          },
          performance: {
            averageResponseTime: 1.2,
            uptime: 99.8,
            errorRate: 0.1,
          },
        };

        setVoiceModels(mockVoiceModels);
        setSynthesisStats(mockSynthesisStats);
        setSystemStatus(mockSystemStatus);
        
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error('Dashboard loading error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
      case 'healthy':
        return 'text-green-600 dark:text-green-400';
      case 'training':
      case 'processing':
      case 'degraded':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'failed':
      case 'down':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
      case 'healthy':
        return <CheckCircle className="w-4 h-4" />;
      case 'training':
      case 'processing':
        return <Clock className="w-4 h-4" />;
      case 'degraded':
        return <AlertCircle className="w-4 h-4" />;
      case 'failed':
      case 'down':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  // Format duration
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center">
        <LoadingSpinner size="xl" text="Loading dashboard..." />
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-2">
                  Welcome back, {user?.displayName}!
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-400">
                  Manage your voice models and monitor system performance
                </p>
              </div>
              <Link href="/voice-enrollment">
                <Button size="lg" leftIcon={<Plus className="w-5 h-5" />}>
                  Create New Voice
                </Button>
              </Link>
            </div>
          </motion.div>

          {/* Stats Overview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid md:grid-cols-4 gap-6 mb-8"
          >
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                    <Mic className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {voiceModels.length}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Voice Models
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                    <Volume2 className="w-6 h-6 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {synthesisStats?.totalSynthesis || 0}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Total Synthesis
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                    <FileAudio className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {formatDuration(synthesisStats?.totalDuration || 0)}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Total Duration
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
                    <Activity className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {systemStatus?.performance.uptime || 0}%
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      System Uptime
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Voice Models */}
            <div className="lg:col-span-2">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Mic className="w-5 h-5" />
                      <span>Voice Models</span>
                    </CardTitle>
                    <CardDescription>
                      Manage your custom voice models and training status
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {voiceModels.map((model) => (
                        <div
                          key={model.id}
                          className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                        >
                          <div className="flex items-center space-x-4">
                            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                              <Mic className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                            </div>
                            <div>
                              <h4 className="font-medium text-gray-900 dark:text-white">
                                {model.name}
                              </h4>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                {model.language} • {model.gender} • Quality: {model.quality}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                Created: {model.createdAt.toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-3">
                            <div className="text-right">
                              <div className="flex items-center space-x-2">
                                {getStatusIcon(model.status)}
                                <span className={`text-sm font-medium ${getStatusColor(model.status)}`}>
                                  {model.status}
                                </span>
                              </div>
                              {model.status === 'training' && (
                                <div className="text-xs text-gray-500 dark:text-gray-400">
                                  {model.trainingProgress}% complete
                                </div>
                              )}
                            </div>
                            
                            <div className="flex space-x-2">
                              {model.status === 'ready' && (
                                <>
                                  <Link href="/synthesis">
                                    <Button variant="outline" size="sm" leftIcon={<Play className="w-4 h-4" />}>
                                      Use
                                    </Button>
                                  </Link>
                                  <Button variant="outline" size="sm" leftIcon={<Settings className="w-4 h-4" />}>
                                    Settings
                                  </Button>
                                </>
                              )}
                              <Button variant="outline" size="sm" leftIcon={<Trash2 className="w-4 h-4" />}>
                                Delete
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Recent Activity */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <BarChart3 className="w-5 h-5" />
                      <span>Recent Activity</span>
                    </CardTitle>
                    <CardDescription>
                      Your latest voice synthesis activities
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {synthesisStats?.recentActivity.map((activity) => (
                        <div
                          key={activity.id}
                          className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                        >
                          <div className="flex-1">
                            <p className="text-sm text-gray-900 dark:text-white font-medium">
                              {activity.text.substring(0, 60)}...
                            </p>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {activity.voice} • {formatDuration(activity.duration)}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {activity.timestamp.toLocaleTimeString()}
                            </p>
                            <Button variant="ghost" size="sm" leftIcon={<Play className="w-3 h-3" />}>
                              Replay
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            {/* System Status Sidebar */}
            <div className="space-y-6">
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Activity className="w-5 h-5" />
                      <span>System Status</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Azure Services */}
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Azure Services</h4>
                      <div className="space-y-2">
                        {Object.entries(systemStatus?.azureServices || {}).map(([service, status]) => (
                          <div key={service} className="flex items-center justify-between">
                            <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                              {service} Service
                            </span>
                            <div className="flex items-center space-x-2">
                              {getStatusIcon(status)}
                              <span className={`text-sm font-medium ${getStatusColor(status)}`}>
                                {status}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Storage */}
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Storage Usage</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            Used: {systemStatus?.storage.used} GB
                          </span>
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            {systemStatus?.storage.percentage}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${systemStatus?.storage.percentage || 0}%` }}
                          />
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          Total: {systemStatus?.storage.total} GB
                        </p>
                      </div>
                    </div>

                    {/* Performance */}
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Performance</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Avg Response Time:</span>
                          <span className="text-gray-900 dark:text-white">
                            {systemStatus?.performance.averageResponseTime}ms
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Uptime:</span>
                          <span className="text-gray-900 dark:text-white">
                            {systemStatus?.performance.uptime}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Error Rate:</span>
                          <span className="text-gray-900 dark:text-white">
                            {systemStatus?.performance.errorRate}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Quick Actions */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle>Quick Actions</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <Link href="/synthesis" className="w-full">
                      <Button variant="outline" fullWidth leftIcon={<Play className="w-4 h-4" />}>
                        Start Synthesis
                      </Button>
                    </Link>
                    <Link href="/voice-enrollment" className="w-full">
                      <Button variant="outline" fullWidth leftIcon={<Mic className="w-4 h-4" />}>
                        Create Voice Model
                      </Button>
                    </Link>
                    <Button variant="outline" fullWidth leftIcon={<Settings className="w-4 h-4" />}>
                      System Settings
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
            >
              <div className="flex items-center space-x-3">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                <p className="text-red-800 dark:text-red-200">{error}</p>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
