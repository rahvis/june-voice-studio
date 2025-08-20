"""
Performance and Load Testing for Voice Cloning System
Tests system performance under various load conditions
"""

import unittest
import time
import threading
import concurrent.futures
import statistics
from typing import Dict, List, Any, Tuple
import json
import requests
from unittest.mock import Mock, patch, MagicMock
import asyncio
import aiohttp
import multiprocessing

# Import the modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from audio_synthesis import AudioSynthesizer
from voice_selection import VoiceSelector
from cache.redis_cache import RedisCache, CacheConfig

class PerformanceMetrics:
    """Performance metrics collection and analysis"""
    
    def __init__(self):
        self.response_times = []
        self.throughput_rates = []
        self.error_rates = []
        self.concurrency_levels = []
        self.start_time = None
        self.end_time = None
    
    def start_test(self):
        """Start performance test timing"""
        self.start_time = time.time()
    
    def end_test(self):
        """End performance test timing"""
        self.end_time = time.time()
    
    def record_response_time(self, response_time: float):
        """Record individual response time"""
        self.response_times.append(response_time)
    
    def record_throughput(self, requests_per_second: float):
        """Record throughput rate"""
        self.throughput_rates.append(requests_per_second)
    
    def record_error_rate(self, error_percentage: float):
        """Record error rate"""
        self.error_rates.append(error_percentage)
    
    def record_concurrency(self, concurrent_users: int):
        """Record concurrency level"""
        self.concurrency_levels.append(concurrent_users)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance test summary"""
        if not self.response_times:
            return {}
        
        total_duration = self.end_time - self.start_time if self.end_time else 0
        
        summary = {
            'total_requests': len(self.response_times),
            'total_duration': total_duration,
            'response_times': {
                'min': min(self.response_times),
                'max': max(self.response_times),
                'mean': statistics.mean(self.response_times),
                'median': statistics.median(self.response_times),
                'p95': self._calculate_percentile(self.response_times, 95),
                'p99': self._calculate_percentile(self.response_times, 99)
            },
            'throughput': {
                'average': statistics.mean(self.throughput_rates) if self.throughput_rates else 0,
                'peak': max(self.throughput_rates) if self.throughput_rates else 0
            },
            'error_rate': {
                'average': statistics.mean(self.error_rates) if self.error_rates else 0,
                'peak': max(self.error_rates) if self.error_rates else 0
            },
            'concurrency': {
                'average': statistics.mean(self.concurrency_levels) if self.concurrency_levels else 0,
                'peak': max(self.concurrency_levels) if self.concurrency_levels else 0
            }
        }
        
        return summary
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

class LoadTestRunner:
    """Load test execution engine"""
    
    def __init__(self, target_url: str, test_config: Dict[str, Any]):
        self.target_url = target_url
        self.test_config = test_config
        self.metrics = PerformanceMetrics()
        self.results = []
    
    def run_concurrent_users_test(self, concurrent_users: int, duration_seconds: int) -> Dict[str, Any]:
        """Run test with specified number of concurrent users"""
        self.metrics.start_test()
        
        # Record concurrency level
        self.metrics.record_concurrency(concurrent_users)
        
        # Create thread pool for concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            # Submit tasks
            future_to_user = {
                executor.submit(self._make_request, user_id): user_id 
                for user_id in range(concurrent_users)
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_user):
                try:
                    result = future.result()
                    self.results.append(result)
                    
                    # Record metrics
                    if result['success']:
                        self.metrics.record_response_time(result['response_time'])
                    else:
                        self.metrics.record_response_time(result['response_time'])
                        
                except Exception as e:
                    self.results.append({
                        'user_id': future_to_user[future],
                        'success': False,
                        'error': str(e),
                        'response_time': 0
                    })
        
        self.metrics.end_test()
        
        # Calculate throughput
        total_requests = len(self.results)
        successful_requests = len([r for r in self.results if r['success']])
        error_rate = ((total_requests - successful_requests) / total_requests) * 100 if total_requests > 0 else 0
        
        throughput = total_requests / duration_seconds if duration_seconds > 0 else 0
        
        self.metrics.record_throughput(throughput)
        self.metrics.record_error_rate(error_rate)
        
        return {
            'concurrent_users': concurrent_users,
            'duration_seconds': duration_seconds,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'error_rate': error_rate,
            'throughput': throughput,
            'metrics': self.metrics.get_summary()
        }
    
    def _make_request(self, user_id: int) -> Dict[str, Any]:
        """Make a single HTTP request"""
        start_time = time.time()
        
        try:
            # Simulate API request
            response = requests.get(f"{self.target_url}/health", timeout=30)
            response_time = time.time() - start_time
            
            return {
                'user_id': user_id,
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'response_time': response_time,
                'response_size': len(response.content)
            }
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            
            return {
                'user_id': user_id,
                'success': False,
                'error': str(e),
                'response_time': response_time
            }
    
    def run_stress_test(self, max_concurrent_users: int, step_size: int = 10) -> List[Dict[str, Any]]:
        """Run stress test with increasing concurrent users"""
        results = []
        
        for concurrent_users in range(step_size, max_concurrent_users + 1, step_size):
            print(f"Testing with {concurrent_users} concurrent users...")
            
            result = self.run_concurrent_users_test(concurrent_users, 60)  # 1 minute per test
            results.append(result)
            
            # Check if system is still responding
            if result['error_rate'] > 50:  # More than 50% errors
                print(f"System overloaded at {concurrent_users} concurrent users")
                break
        
        return results
    
    def run_endurance_test(self, concurrent_users: int, duration_minutes: int) -> Dict[str, Any]:
        """Run endurance test for extended period"""
        print(f"Running endurance test with {concurrent_users} users for {duration_minutes} minutes...")
        
        duration_seconds = duration_minutes * 60
        result = self.run_concurrent_users_test(concurrent_users, duration_seconds)
        
        return result

class AudioSynthesisPerformanceTest(unittest.TestCase):
    """Test audio synthesis performance"""
    
    def setUp(self):
        """Set up test environment"""
        self.synthesizer = AudioSynthesizer()
        self.test_texts = [
            "Hello world",
            "This is a test of the voice cloning system",
            "The quick brown fox jumps over the lazy dog",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit"
        ]
        self.voice_config = {
            "voice_id": "test_voice",
            "language": "en-US",
            "gender": "female"
        }
    
    def test_single_synthesis_performance(self):
        """Test single audio synthesis performance"""
        metrics = PerformanceMetrics()
        
        for text in self.test_texts:
            start_time = time.time()
            
            # Mock synthesis for performance testing
            with patch.object(self.synthesizer, 'synthesize_text') as mock_synthesize:
                mock_synthesize.return_value = Mock(
                    success=True,
                    audio_data=b"test_audio",
                    audio_format="wav"
                )
                
                result = self.synthesizer.synthesize_text(text, self.voice_config)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                metrics.record_response_time(response_time)
                
                self.assertTrue(result.success)
        
        summary = metrics.get_summary()
        
        # Performance assertions
        self.assertLess(summary['response_times']['mean'], 100)  # Less than 100ms average
        self.assertLess(summary['response_times']['p95'], 200)   # Less than 200ms for 95%
    
    def test_batch_synthesis_performance(self):
        """Test batch synthesis performance"""
        metrics = PerformanceMetrics()
        
        start_time = time.time()
        
        # Mock batch synthesis
        with patch.object(self.synthesizer, 'synthesize_batch') as mock_batch:
            mock_batch.return_value = Mock(
                success=True,
                audio_files=["audio1.wav", "audio2.wav", "audio3.wav", "audio4.wav"]
            )
            
            result = self.synthesizer.synthesize_batch(self.test_texts, self.voice_config)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            metrics.record_response_time(response_time)
            
            self.assertTrue(result.success)
            self.assertEqual(len(result.audio_files), 4)
        
        summary = metrics.get_summary()
        
        # Batch processing should be more efficient per item
        avg_time_per_item = summary['response_times']['mean'] / len(self.test_texts)
        self.assertLess(avg_time_per_item, 50)  # Less than 50ms per item
    
    def test_concurrent_synthesis_performance(self):
        """Test concurrent synthesis performance"""
        metrics = PerformanceMetrics()
        concurrent_users = 10
        
        def synthesize_text(text: str) -> float:
            start_time = time.time()
            
            with patch.object(self.synthesizer, 'synthesize_text') as mock_synthesize:
                mock_synthesize.return_value = Mock(
                    success=True,
                    audio_data=b"test_audio",
                    audio_format="wav"
                )
                
                result = self.synthesizer.synthesize_text(text, self.voice_config)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                self.assertTrue(result.success)
                return response_time
        
        # Run concurrent synthesis
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(synthesize_text, text) 
                for text in self.test_texts * 3  # 12 total requests
            ]
            
            for future in concurrent.futures.as_completed(futures):
                response_time = future.result()
                metrics.record_response_time(response_time)
        
        summary = metrics.get_summary()
        
        # Concurrent performance should be reasonable
        self.assertLess(summary['response_times']['mean'], 150)  # Less than 150ms average
        self.assertLess(summary['response_times']['p95'], 300)   # Less than 300ms for 95%

class CachePerformanceTest(unittest.TestCase):
    """Test cache performance"""
    
    def setUp(self):
        """Set up test environment"""
        self.cache_config = CacheConfig(
            host="localhost",
            port=6379,
            db=0
        )
        self.cache = RedisCache(self.cache_config)
        self.test_data = {
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'value3',
            'key4': 'value4',
            'key5': 'value5'
        }
    
    def test_cache_read_performance(self):
        """Test cache read performance"""
        metrics = PerformanceMetrics()
        
        # Populate cache
        for key, value in self.test_data.items():
            self.cache.set(key, value)
        
        # Test read performance
        for _ in range(100):  # 100 read operations
            start_time = time.time()
            
            # Mock cache get operation
            with patch.object(self.cache, 'get') as mock_get:
                mock_get.return_value = 'test_value'
                
                value = self.cache.get('key1')
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                metrics.record_response_time(response_time)
        
        summary = metrics.get_summary()
        
        # Cache reads should be very fast
        self.assertLess(summary['response_times']['mean'], 10)   # Less than 10ms average
        self.assertLess(summary['response_times']['p95'], 20)    # Less than 20ms for 95%
    
    def test_cache_write_performance(self):
        """Test cache write performance"""
        metrics = PerformanceMetrics()
        
        # Test write performance
        for i in range(100):  # 100 write operations
            start_time = time.time()
            
            # Mock cache set operation
            with patch.object(self.cache, 'set') as mock_set:
                mock_set.return_value = True
                
                success = self.cache.set(f'write_key_{i}', f'write_value_{i}')
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                metrics.record_response_time(response_time)
                
                self.assertTrue(success)
        
        summary = metrics.get_summary()
        
        # Cache writes should be fast
        self.assertLess(summary['response_times']['mean'], 15)   # Less than 15ms average
        self.assertLess(summary['response_times']['p95'], 30)    # Less than 30ms for 95%
    
    def test_cache_concurrent_access(self):
        """Test cache performance under concurrent access"""
        metrics = PerformanceMetrics()
        concurrent_users = 20
        
        def cache_operation(operation_id: int) -> float:
            start_time = time.time()
            
            # Mock cache operations
            with patch.object(self.cache, 'get') as mock_get:
                with patch.object(self.cache, 'set') as mock_set:
                    mock_get.return_value = f'value_{operation_id}'
                    mock_set.return_value = True
                    
                    # Perform read and write operations
                    value = self.cache.get(f'key_{operation_id}')
                    success = self.cache.set(f'key_{operation_id}', f'new_value_{operation_id}')
                    
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000
                    
                    self.assertTrue(success)
                    return response_time
        
        # Run concurrent cache operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(cache_operation, i) 
                for i in range(concurrent_users)
            ]
            
            for future in concurrent.futures.as_completed(futures):
                response_time = future.result()
                metrics.record_response_time(response_time)
        
        summary = metrics.get_summary()
        
        # Concurrent cache operations should maintain performance
        self.assertLess(summary['response_times']['mean'], 25)   # Less than 25ms average
        self.assertLess(summary['response_times']['p95'], 50)    # Less than 50ms for 95%

class SystemLoadTest(unittest.TestCase):
    """System-wide load testing"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:8000"  # Mock API endpoint
        self.test_config = {
            'max_concurrent_users': 100,
            'test_duration_minutes': 5,
            'ramp_up_time_minutes': 2
        }
    
    def test_system_load_capacity(self):
        """Test system load capacity"""
        load_runner = LoadTestRunner(self.base_url, self.test_config)
        
        # Run stress test
        results = load_runner.run_stress_test(max_concurrent_users=50, step_size=10)
        
        # Analyze results
        for result in results:
            print(f"Concurrent users: {result['concurrent_users']}")
            print(f"Throughput: {result['throughput']:.2f} req/s")
            print(f"Error rate: {result['error_rate']:.2f}%")
            print(f"Response time (p95): {result['metrics']['response_times']['p95']:.2f}ms")
            print("---")
        
        # Find breaking point
        breaking_point = None
        for result in results:
            if result['error_rate'] > 10:  # More than 10% errors
                breaking_point = result['concurrent_users']
                break
        
        self.assertIsNotNone(breaking_point, "System should have a breaking point")
        print(f"System breaking point: {breaking_point} concurrent users")
    
    def test_system_endurance(self):
        """Test system endurance under sustained load"""
        load_runner = LoadTestRunner(self.base_url, self.test_config)
        
        # Run endurance test
        result = load_runner.run_endurance_test(
            concurrent_users=20,
            duration_minutes=2  # Short duration for testing
        )
        
        # Verify system stability
        self.assertLess(result['error_rate'], 5, "Error rate should be less than 5%")
        self.assertGreater(result['throughput'], 10, "Throughput should be greater than 10 req/s")
        
        print(f"Endurance test completed:")
        print(f"Total requests: {result['total_requests']}")
        print(f"Successful requests: {result['successful_requests']}")
        print(f"Error rate: {result['error_rate']:.2f}%")
        print(f"Throughput: {result['throughput']:.2f} req/s")
    
    def test_system_recovery(self):
        """Test system recovery after overload"""
        load_runner = LoadTestRunner(self.base_url, self.test_config)
        
        # Overload the system
        overload_result = load_runner.run_concurrent_users_test(
            concurrent_users=100,
            duration_seconds=30
        )
        
        # Wait for recovery
        time.sleep(10)
        
        # Test normal load
        recovery_result = load_runner.run_concurrent_users_test(
            concurrent_users=20,
            duration_seconds=30
        )
        
        # Verify recovery
        self.assertLess(recovery_result['error_rate'], overload_result['error_rate'])
        self.assertGreater(recovery_result['throughput'], overload_result['throughput'])

if __name__ == '__main__':
    unittest.main()
