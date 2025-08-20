'use client';

import React, { useState, useRef, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/contexts/AuthContext';
import { Button, Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui';
import { LoadingSpinner } from '@/components/ui';
import { motion } from 'framer-motion';
import { Mic, MicOff, Upload, Play, Pause, Stop, Trash2, CheckCircle, AlertCircle } from 'lucide-react';

interface AudioChunk {
  id: string;
  blob: Blob;
  duration: number;
  transcription?: string;
  quality?: 'good' | 'fair' | 'poor';
}

interface ConsentForm {
  voiceCloning: boolean;
  dataProcessing: boolean;
  thirdPartySharing: boolean;
  retentionPeriod: boolean;
  withdrawalRights: boolean;
}

export default function VoiceEnrollmentPage() {
  const { user } = useAuth();
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [audioChunks, setAudioChunks] = useState<AudioChunk[]>([]);
  const [currentRecording, setCurrentRecording] = useState<Blob | null>(null);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [recordingStartTime, setRecordingStartTime] = useState<number | null>(null);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [consentForm, setConsentForm] = useState<ConsentForm>({
    voiceCloning: false,
    dataProcessing: false,
    thirdPartySharing: false,
    retentionPeriod: false,
    withdrawalRights: false,
  });
  const [currentStep, setCurrentStep] = useState<'consent' | 'recording' | 'upload' | 'review' | 'complete'>('consent');
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });
      
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setCurrentRecording(audioBlob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };
      
      recorder.start(1000); // Collect data every second
      setMediaRecorder(recorder);
      setIsRecording(true);
      setIsPaused(false);
      setRecordingStartTime(Date.now());
      
      // Start duration timer
      intervalRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
      
    } catch (err) {
      setError('Failed to access microphone. Please check permissions.');
      console.error('Recording error:', err);
    }
  }, []);

  // Pause recording
  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }
  }, [isRecording]);

  
  // Resume recording
  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && isPaused) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      intervalRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    }
  }, [isPaused]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }
  }, [isRecording]);

  // Save current recording
  const saveRecording = useCallback(() => {
    if (currentRecording) {
      const chunk: AudioChunk = {
        id: `chunk-${Date.now()}`,
        blob: currentRecording,
        duration: recordingDuration,
      };
      
      setAudioChunks(prev => [...prev, chunk]);
      setCurrentRecording(null);
      setRecordingDuration(0);
      setRecordingStartTime(null);
    }
  }, [currentRecording, recordingDuration]);

  // Delete audio chunk
  const deleteChunk = useCallback((id: string) => {
    setAudioChunks(prev => prev.filter(chunk => chunk.id !== id));
  }, []);

  // Handle consent form changes
  const handleConsentChange = useCallback((field: keyof ConsentForm) => {
    setConsentForm(prev => ({
      ...prev,
      [field]: !prev[field],
    }));
  }, []);

  // Check if all consent is given
  const isConsentComplete = Object.values(consentForm).every(Boolean);

  // Format duration
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle file upload
  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      Array.from(files).forEach(file => {
        if (file.type.startsWith('audio/')) {
          const chunk: AudioChunk = {
            id: `upload-${Date.now()}-${Math.random()}`,
            blob: file,
            duration: 0, // Will be calculated when processed
          };
          setAudioChunks(prev => [...prev, chunk]);
        }
      });
    }
  }, []);

  // Next step
  const nextStep = useCallback(() => {
    if (currentStep === 'consent' && isConsentComplete) {
      setCurrentStep('recording');
    } else if (currentStep === 'recording' && audioChunks.length > 0) {
      setCurrentStep('upload');
    } else if (currentStep === 'upload') {
      setCurrentStep('review');
    }
  }, [currentStep, isConsentComplete, audioChunks.length]);

  // Previous step
  const prevStep = useCallback(() => {
    if (currentStep === 'recording') {
      setCurrentStep('consent');
    } else if (currentStep === 'upload') {
      setCurrentStep('recording');
    } else if (currentStep === 'review') {
      setCurrentStep('upload');
    }
  }, [currentStep]);

  // Submit enrollment
  const submitEnrollment = useCallback(async () => {
    if (audioChunks.length === 0) return;
    
    setIsUploading(true);
    setUploadProgress(0);
    
    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      setUploadProgress(100);
      setCurrentStep('complete');
      
    } catch (err) {
      setError('Failed to submit enrollment. Please try again.');
    } finally {
      setIsUploading(false);
    }
  }, [audioChunks.length]);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-8"
          >
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Voice Enrollment
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Create your custom voice model by recording high-quality audio samples
            </p>
          </motion.div>

          {/* Progress Steps */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <div className="flex items-center justify-between">
              {[
                { key: 'consent', label: 'Consent', icon: CheckCircle },
                { key: 'recording', label: 'Recording', icon: Mic },
                { key: 'upload', label: 'Upload', icon: Upload },
                { key: 'review', label: 'Review', icon: AlertCircle },
                { key: 'complete', label: 'Complete', icon: CheckCircle },
              ].map((step, index) => {
                const Icon = step.icon;
                const isActive = currentStep === step.key;
                const isCompleted = ['consent', 'recording', 'upload', 'review', 'complete'].indexOf(currentStep) > index;
                
                return (
                  <div key={step.key} className="flex flex-col items-center">
                    <div className={`
                      w-10 h-10 rounded-full flex items-center justify-center mb-2 transition-colors
                      ${isActive ? 'bg-blue-600 text-white' : 
                        isCompleted ? 'bg-green-500 text-white' : 
                        'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}
                    `}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className={`
                      text-sm font-medium
                      ${isActive ? 'text-blue-600 dark:text-blue-400' : 
                        isCompleted ? 'text-green-600 dark:text-green-400' : 
                        'text-gray-500 dark:text-gray-400'}
                    `}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </motion.div>

          {/* Step Content */}
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {/* Consent Step */}
            {currentStep === 'consent' && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Consent and Authorization</CardTitle>
                  <CardDescription>
                    Please review and accept the following terms to proceed with voice enrollment
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {Object.entries({
                    voiceCloning: 'I consent to the creation and use of a custom neural voice model based on my voice recordings',
                    dataProcessing: 'I authorize the processing of my audio data for voice model training purposes',
                    thirdPartySharing: 'I understand that my voice model may be used for text-to-speech synthesis',
                    retentionPeriod: 'I acknowledge that my voice data will be retained according to our data retention policy',
                    withdrawalRights: 'I understand that I can withdraw my consent and request data deletion at any time',
                  }).map(([key, text]) => (
                    <label key={key} className="flex items-start space-x-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={consentForm[key as keyof ConsentForm]}
                        onChange={() => handleConsentChange(key as keyof ConsentForm)}
                        className="mt-1 w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">{text}</span>
                    </label>
                  ))}
                </CardContent>
                <CardFooter>
                  <Button
                    onClick={nextStep}
                    disabled={!isConsentComplete}
                    className="w-full"
                  >
                    Continue to Recording
                  </Button>
                </CardFooter>
              </Card>
            )}

            {/* Recording Step */}
            {currentStep === 'recording' && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Record Your Voice</CardTitle>
                  <CardDescription>
                    Record clear audio samples in a quiet environment. Aim for at least 10-15 minutes of high-quality audio.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Recording Controls */}
                  <div className="text-center">
                    <div className="mb-4">
                      <div className="text-4xl font-mono text-blue-600 dark:text-blue-400 mb-2">
                        {formatDuration(recordingDuration)}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {isRecording ? 'Recording...' : isPaused ? 'Paused' : 'Ready to record'}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-center space-x-4">
                      {!isRecording ? (
                        <Button
                          onClick={startRecording}
                          size="lg"
                          leftIcon={<Mic className="w-5 h-5" />}
                        >
                          Start Recording
                        </Button>
                      ) : (
                        <>
                          {isPaused ? (
                            <Button
                              onClick={resumeRecording}
                              variant="secondary"
                              size="lg"
                              leftIcon={<Play className="w-5 h-5" />}
                            >
                              Resume
                            </Button>
                          ) : (
                            <Button
                              onClick={pauseRecording}
                              variant="secondary"
                              size="lg"
                              leftIcon={<Pause className="w-5 h-5" />}
                            >
                              Pause
                            </Button>
                          )}
                          
                          <Button
                            onClick={stopRecording}
                            variant="outline"
                            size="lg"
                            leftIcon={<Stop className="w-5 h-5" />}
                          >
                            Stop
                          </Button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Current Recording */}
                  {currentRecording && (
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-blue-900 dark:text-blue-100">
                            Current Recording
                          </h4>
                          <p className="text-sm text-blue-700 dark:text-blue-300">
                            Duration: {formatDuration(recordingDuration)}
                          </p>
                        </div>
                        <Button
                          onClick={saveRecording}
                          variant="outline"
                          size="sm"
                        >
                          Save Recording
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* File Upload */}
                  <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
                    <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-400 mb-2">
                      Or upload existing audio files
                    </p>
                    <input
                      type="file"
                      accept="audio/*"
                      multiple
                      onChange={handleFileUpload}
                      className="hidden"
                      id="audio-upload"
                    />
                    <label htmlFor="audio-upload">
                      <Button variant="outline" asChild>
                        <span>Choose Files</span>
                      </Button>
                    </label>
                  </div>
                </CardContent>
                <CardFooter className="flex justify-between">
                  <Button variant="outline" onClick={prevStep}>
                    Back
                  </Button>
                  <Button
                    onClick={nextStep}
                    disabled={audioChunks.length === 0}
                  >
                    Continue to Upload
                  </Button>
                </CardFooter>
              </Card>
            )}

            {/* Upload Step */}
            {currentStep === 'upload' && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Review and Upload</CardTitle>
                  <CardDescription>
                    Review your audio recordings before submitting for processing
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {audioChunks.map((chunk, index) => (
                      <div
                        key={chunk.id}
                        className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                            <span className="text-blue-600 dark:text-blue-400 font-medium">
                              {index + 1}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">
                              Audio Sample {index + 1}
                            </p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              Duration: {chunk.duration > 0 ? formatDuration(chunk.duration) : 'Unknown'}
                            </p>
                          </div>
                        </div>
                        
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteChunk(chunk.id)}
                          leftIcon={<Trash2 className="w-4 h-4" />}
                        >
                          Remove
                        </Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
                <CardFooter className="flex justify-between">
                  <Button variant="outline" onClick={prevStep}>
                    Back
                  </Button>
                  <Button onClick={nextStep}>
                    Continue to Review
                  </Button>
                </CardFooter>
              </Card>
            )}

            {/* Review Step */}
            {currentStep === 'review' && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Final Review</CardTitle>
                  <CardDescription>
                    Review your enrollment details and submit for processing
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">User Information</h4>
                      <div className="space-y-2 text-sm">
                        <p><span className="text-gray-500 dark:text-gray-400">Name:</span> {user?.displayName}</p>
                        <p><span className="text-gray-500 dark:text-gray-400">Email:</span> {user?.email}</p>
                        <p><span className="text-gray-500 dark:text-gray-400">User ID:</span> {user?.id}</p>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Audio Samples</h4>
                      <div className="space-y-2 text-sm">
                        <p><span className="text-gray-500 dark:text-gray-400">Total Samples:</span> {audioChunks.length}</p>
                        <p><span className="text-gray-500 dark:text-gray-400">Total Duration:</span> {formatDuration(audioChunks.reduce((acc, chunk) => acc + chunk.duration, 0))}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
                      <div className="text-sm text-blue-800 dark:text-blue-200">
                        <p className="font-medium mb-1">Important Notes:</p>
                        <ul className="space-y-1 list-disc list-inside">
                          <li>Voice model training typically takes 24-48 hours</li>
                          <li>You will receive email notifications about training progress</li>
                          <li>Your voice model will be available for synthesis once training is complete</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="flex justify-between">
                  <Button variant="outline" onClick={prevStep}>
                    Back
                  </Button>
                  <Button
                    onClick={submitEnrollment}
                    loading={isUploading}
                    disabled={isUploading}
                  >
                    Submit Enrollment
                  </Button>
                </CardFooter>
              </Card>
            )}

            {/* Complete Step */}
            {currentStep === 'complete' && (
              <Card className="mb-6">
                <CardHeader className="text-center">
                  <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
                  </div>
                  <CardTitle>Enrollment Submitted Successfully!</CardTitle>
                  <CardDescription>
                    Your voice enrollment has been submitted and is now being processed
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-center">
                  <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 mb-6">
                    <p className="text-green-800 dark:text-green-200 text-sm">
                      You will receive email updates about your voice model training progress. 
                      Once complete, you can start using your custom voice for text-to-speech synthesis.
                    </p>
                  </div>
                  
                  <div className="grid md:grid-cols-3 gap-4 text-sm">
                    <div className="text-center">
                      <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-2">
                        <span className="text-blue-600 dark:text-blue-400 font-medium">1</span>
                      </div>
                      <p className="font-medium text-gray-900 dark:text-white">Processing</p>
                      <p className="text-gray-500 dark:text-gray-400">Audio analysis and preparation</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="w-8 h-8 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center mx-auto mb-2">
                        <span className="text-yellow-600 dark:text-yellow-400 font-medium">2</span>
                      </div>
                      <p className="font-medium text-gray-900 dark:text-white">Training</p>
                      <p className="text-gray-500 dark:text-gray-400">Neural model training</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-2">
                        <span className="text-green-600 dark:text-green-400 font-medium">3</span>
                      </div>
                      <p className="font-medium text-gray-900 dark:text-white">Ready</p>
                      <p className="text-gray-500 dark:text-gray-400">Voice model available</p>
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="flex justify-center">
                  <Button onClick={() => window.location.href = '/dashboard'}>
                    Go to Dashboard
                  </Button>
                </CardFooter>
              </Card>
            )}
          </motion.div>

          {/* Error Display */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6"
            >
              <div className="flex items-center space-x-3">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                <p className="text-red-800 dark:text-red-200">{error}</p>
              </div>
            </motion.div>
          )}

          {/* Upload Progress */}
          {isUploading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            >
              <Card className="w-96">
                <CardContent className="p-6 text-center">
                  <LoadingSpinner size="lg" className="mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    Submitting Enrollment
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-4">
                    Please wait while we process your voice enrollment...
                  </p>
                  
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {uploadProgress}% Complete
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
