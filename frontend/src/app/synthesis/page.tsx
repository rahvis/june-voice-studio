'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/contexts/AuthContext';
import { Button, Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui';
import { LoadingSpinner } from '@/components/ui';
import { motion } from 'framer-motion';
import { Play, Pause, Stop, Volume2, Download, Settings, Mic, MicOff, Languages, Type, AlertCircle } from 'lucide-react';

interface Voice {
  id: string;
  name: string;
  language: string;
  gender: 'male' | 'female' | 'neutral';
  type: 'custom' | 'stock' | 'openai';
  quality: 'high' | 'medium' | 'low';
  available: boolean;
}

interface SynthesisRequest {
  text: string;
  voiceId: string;
  language: string;
  speed: number;
  pitch: number;
  volume: number;
  format: 'wav' | 'mp3' | 'ogg';
}

interface SynthesisResult {
  id: string;
  audioUrl: string;
  duration: number;
  wordCount: number;
  timestamp: Date;
  status: 'completed' | 'processing' | 'failed';
}

export default function SynthesisPage() {
  const { user } = useAuth();
  const [text, setText] = useState('');
  const [selectedVoice, setSelectedVoice] = useState<Voice | null>(null);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [synthesisHistory, setSynthesisHistory] = useState<SynthesisResult[]>([]);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  const [synthesisSettings, setSynthesisSettings] = useState({
    speed: 1.0,
    pitch: 1.0,
    volume: 1.0,
    format: 'wav' as const,
  });
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);

  // Mock voices data
  const availableVoices: Voice[] = [
    {
      id: 'voice-1',
      name: 'Custom Voice - John',
      language: 'en-US',
      gender: 'male',
      type: 'custom',
      quality: 'high',
      available: true,
    },
    {
      id: 'voice-2',
      name: 'Custom Voice - Sarah',
      language: 'en-US',
      gender: 'female',
      type: 'custom',
      quality: 'high',
      available: true,
    },
    {
      id: 'voice-3',
      name: 'Stock Voice - David',
      language: 'en-US',
      gender: 'male',
      type: 'stock',
      quality: 'medium',
      available: true,
    },
    {
      id: 'voice-4',
      name: 'OpenAI TTS - Emma',
      language: 'en-US',
      gender: 'female',
      type: 'openai',
      quality: 'high',
      available: true,
    },
  ];

  // Initialize with first available voice
  useEffect(() => {
    if (availableVoices.length > 0 && !selectedVoice) {
      setSelectedVoice(availableVoices[0]);
    }
  }, [availableVoices, selectedVoice]);

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (currentAudio) {
        currentAudio.pause();
        currentAudio.src = '';
      }
    };
  }, [currentAudio]);

  // Start synthesis
  const startSynthesis = useCallback(async () => {
    if (!text.trim() || !selectedVoice) {
      setError('Please enter text and select a voice');
      return;
    }

    setIsSynthesizing(true);
    setError(null);

    try {
      // Simulate synthesis API call
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Create mock result
      const result: SynthesisResult = {
        id: `synthesis-${Date.now()}`,
        audioUrl: '/api/mock-audio', // Mock URL
        duration: Math.ceil(text.length / 150), // Rough estimate
        wordCount: text.split(' ').length,
        timestamp: new Date(),
        status: 'completed',
      };

      setSynthesisHistory(prev => [result, ...prev]);
      
      // Auto-play the result
      playAudio(result);
      
    } catch (err) {
      setError('Synthesis failed. Please try again.');
      console.error('Synthesis error:', err);
    } finally {
      setIsSynthesizing(false);
    }
  }, [text, selectedVoice]);

  // Play audio
  const playAudio = useCallback((result: SynthesisResult) => {
    if (currentAudio) {
      currentAudio.pause();
    }

    const audio = new Audio(result.audioUrl);
    audio.volume = synthesisSettings.volume;
    audio.playbackRate = synthesisSettings.speed;
    
    audio.onplay = () => setIsPlaying(true);
    audio.onpause = () => setIsPlaying(false);
    audio.onended = () => setIsPlaying(false);
    audio.onerror = () => {
      setError('Failed to play audio');
      setIsPlaying(false);
    };

    setCurrentAudio(audio);
  }, [currentAudio, synthesisSettings.volume, synthesisSettings.speed]);

  // Pause audio
  const pauseAudio = useCallback(() => {
    if (currentAudio && isPlaying) {
      currentAudio.pause();
    }
  }, [currentAudio, isPlaying]);

  // Stop audio
  const stopAudio = useCallback(() => {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      setIsPlaying(false);
    }
  }, [currentAudio]);

  // Download audio
  const downloadAudio = useCallback((result: SynthesisResult) => {
    // Mock download functionality
    const link = document.createElement('a');
    link.href = result.audioUrl;
    link.download = `synthesis-${result.id}.${synthesisSettings.format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [synthesisSettings.format]);

  // Handle text input
  const handleTextChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    setError(null);
  }, []);

  // Handle voice selection
  const handleVoiceChange = useCallback((voice: Voice) => {
    setSelectedVoice(voice);
    setError(null);
  }, []);

  // Handle settings change
  const handleSettingChange = useCallback((setting: keyof typeof synthesisSettings, value: number | string) => {
    setSynthesisSettings(prev => ({
      ...prev,
      [setting]: value,
    }));
  }, []);

  // Clear text
  const clearText = useCallback(() => {
    setText('');
    setError(null);
  }, []);

  // Sample texts
  const sampleTexts = [
    'Hello, this is a sample text for voice synthesis testing.',
    'The quick brown fox jumps over the lazy dog.',
    'Welcome to our advanced text-to-speech system powered by Azure AI.',
    'This voice cloning technology creates natural-sounding speech from text input.',
  ];

  const insertSampleText = useCallback((sample: string) => {
    setText(sample);
    setError(null);
  }, []);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-8"
          >
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Voice Synthesis
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Transform text into natural speech using your custom voice models
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main Synthesis Panel */}
            <div className="lg:col-span-2 space-y-6">
              {/* Voice Selection */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Mic className="w-5 h-5" />
                    <span>Select Voice</span>
                  </CardTitle>
                  <CardDescription>
                    Choose from your custom voices or stock options
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid sm:grid-cols-2 gap-3">
                    {availableVoices.map((voice) => (
                      <button
                        key={voice.id}
                        onClick={() => handleVoiceChange(voice)}
                        className={`
                          p-4 rounded-lg border-2 transition-all duration-200 text-left
                          ${selectedVoice?.id === voice.id
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                          }
                        `}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-900 dark:text-white">
                            {voice.name}
                          </span>
                          <span className={`
                            px-2 py-1 text-xs rounded-full
                            ${voice.type === 'custom' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                              voice.type === 'stock' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                              'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400'}
                          `}>
                            {voice.type}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          <p>{voice.language} • {voice.gender}</p>
                          <p>Quality: {voice.quality}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Text Input */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Type className="w-5 h-5" />
                    <span>Text Input</span>
                  </CardTitle>
                  <CardDescription>
                    Enter the text you want to convert to speech
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="relative">
                    <textarea
                      value={text}
                      onChange={handleTextChange}
                      placeholder="Enter your text here..."
                      className="w-full h-32 p-4 border border-gray-300 dark:border-gray-600 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-slate-800 dark:text-white"
                    />
                    <div className="absolute bottom-2 right-2 text-xs text-gray-500 dark:text-gray-400">
                      {text.length} characters
                    </div>
                  </div>
                  
                  {/* Sample Texts */}
                  <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Try these sample texts:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {sampleTexts.map((sample, index) => (
                        <button
                          key={index}
                          onClick={() => insertSampleText(sample)}
                          className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                        >
                          Sample {index + 1}
                        </button>
                      ))}
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="flex justify-between">
                  <Button variant="outline" onClick={clearText}>
                    Clear Text
                  </Button>
                  <Button
                    onClick={startSynthesis}
                    loading={isSynthesizing}
                    disabled={isSynthesizing || !text.trim() || !selectedVoice}
                    leftIcon={<Play className="w-4 h-4" />}
                  >
                    {isSynthesizing ? 'Synthesizing...' : 'Start Synthesis'}
                  </Button>
                </CardFooter>
              </Card>

              {/* Audio Controls */}
              {currentAudio && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Volume2 className="w-5 h-5" />
                      <span>Audio Controls</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-center space-x-4">
                      <Button
                        onClick={isPlaying ? pauseAudio : playAudio}
                        variant="outline"
                        size="lg"
                        leftIcon={isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                      >
                        {isPlaying ? 'Pause' : 'Play'}
                      </Button>
                      
                      <Button
                        onClick={stopAudio}
                        variant="outline"
                        size="lg"
                        leftIcon={<Stop className="w-5 h-5" />}
                      >
                        Stop
                      </Button>
                      
                      <Button
                        onClick={() => downloadAudio(synthesisHistory[0])}
                        variant="outline"
                        size="lg"
                        leftIcon={<Download className="w-5 h-5" />}
                      >
                        Download
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Settings and History Sidebar */}
            <div className="space-y-6">
              {/* Synthesis Settings */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Settings className="w-5 h-5" />
                    <span>Settings</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Speed: {synthesisSettings.speed}x
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="2.0"
                      step="0.1"
                      value={synthesisSettings.speed}
                      onChange={(e) => handleSettingChange('speed', parseFloat(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Pitch: {synthesisSettings.pitch}x
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="2.0"
                      step="0.1"
                      value={synthesisSettings.pitch}
                      onChange={(e) => handleSettingChange('pitch', parseFloat(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Volume: {Math.round(synthesisSettings.volume * 100)}%
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={synthesisSettings.volume}
                      onChange={(e) => handleSettingChange('volume', parseFloat(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Format
                    </label>
                    <select
                      value={synthesisSettings.format}
                      onChange={(e) => handleSettingChange('format', e.target.value)}
                      className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-slate-800 dark:text-white"
                    >
                      <option value="wav">WAV</option>
                      <option value="mp3">MP3</option>
                      <option value="ogg">OGG</option>
                    </select>
                  </div>
                </CardContent>
              </Card>

              {/* Synthesis History */}
              <Card>
                <CardHeader>
                  <CardTitle>Synthesis History</CardTitle>
                  <CardDescription>
                    Recent synthesis results
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {synthesisHistory.length === 0 ? (
                      <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                        No synthesis history yet
                      </p>
                    ) : (
                      synthesisHistory.map((result) => (
                        <div
                          key={result.id}
                          className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                          onClick={() => playAudio(result)}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              {result.wordCount} words
                            </span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {result.timestamp.toLocaleTimeString()}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                            {text.substring(0, 50)}...
                          </p>
                          <div className="flex items-center justify-between mt-2">
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {result.duration}s
                            </span>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                downloadAudio(result);
                              }}
                            >
                              <Download className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
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
                <div className="w-5 h-5 text-red-600 dark:text-red-400">
                  <AlertCircle className="w-5 h-5" />
                </div>
                <p className="text-red-800 dark:text-red-200">{error}</p>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
