"""
Comprehensive Test Runner for Voice Cloning System
Runs all unit, integration, performance, security, and compliance tests
"""

import unittest
import sys
import os
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class TestResult:
    """Test result container"""
    
    def __init__(self, test_name: str, test_class: str, status: str, duration: float, 
                 error_message: str = None, details: Dict[str, Any] = None):
        self.test_name = test_name
        self.test_class = test_class
        self.status = status  # 'passed', 'failed', 'error', 'skipped'
        self.duration = duration
        self.error_message = error_message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

class TestSuiteRunner:
    """Comprehensive test suite runner"""
    
    def __init__(self, test_config: Dict[str, Any] = None):
        self.test_config = test_config or self._get_default_config()
        self.results = []
        self.start_time = None
        self.end_time = None
        self.test_suites = {
            'unit': 'tests.unit',
            'integration': 'tests.integration',
            'performance': 'tests.performance',
            'security': 'tests.security',
            'compliance': 'tests.compliance'
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        print("Starting comprehensive test suite execution...")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Run each test suite
        suite_results = {}
        for suite_name, suite_module in self.test_suites.items():
            if self.test_config.get(f'run_{suite_name}', True):
                print(f"\nRunning {suite_name.upper()} tests...")
                suite_results[suite_name] = self._run_test_suite(suite_name, suite_module)
            else:
                print(f"\nSkipping {suite_name.upper()} tests (disabled in config)")
                suite_results[suite_name] = {'status': 'skipped', 'tests': 0, 'passed': 0, 'failed': 0, 'errors': 0}
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report(suite_results)
        
        # Save results
        self._save_test_results(report)
        
        return report
    
    def _run_test_suite(self, suite_name: str, suite_module: str) -> Dict[str, Any]:
        """Run a specific test suite"""
        try:
            # Discover and run tests
            loader = unittest.TestLoader()
            suite = loader.discover(suite_module, pattern='test_*.py')
            
            # Create test runner
            runner = unittest.TextTestRunner(
                verbosity=2,
                stream=sys.stdout,
                descriptions=True
            )
            
            # Run tests
            result = runner.run(suite)
            
            # Collect results
            suite_result = {
                'status': 'completed',
                'tests': result.testsRun,
                'passed': result.testsRun - len(result.failures) - len(result.errors),
                'failed': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
                'duration': time.time() - self.start_time if self.start_time else 0,
                'failures': [str(failure[0]) for failure in result.failures],
                'errors': [str(error[0]) for error in result.errors]
            }
            
            # Print summary
            self._print_suite_summary(suite_name, suite_result)
            
            return suite_result
            
        except Exception as e:
            print(f"❌ Error running {suite_name} tests: {str(e)}")
            return {
                'status': 'error',
                'tests': 0,
                'passed': 0,
                'failed': 0,
                'errors': 1,
                'duration': 0,
                'error_message': str(e)
            }
    
    def _print_suite_summary(self, suite_name: str, result: Dict[str, Any]):
        """Print test suite summary"""
        status_emoji = "OK" if result['status'] == 'completed' and result['failed'] == 0 and result['errors'] == 0 else "WARN"
        
        print(f"\n{status_emoji} {suite_name.upper()} Test Summary:")
        print(f"   Tests Run: {result['tests']}")
        print(f"   Passed: {result['passed']}")
        print(f"   Failed: {result['failed']}")
        print(f"   Errors: {result['errors']}")
        print(f"   Duration: {result['duration']:.2f}s")
        
        if result['failed'] > 0:
            print(f"   Failures: {', '.join(result['failures'][:3])}")
            if len(result['failures']) > 3:
                print(f"   ... and {len(result['failures']) - 3} more")
        
        if result['errors'] > 0:
            print(f"   Errors: {', '.join(result['errors'][:3])}")
            if len(result['errors']) > 3:
                print(f"   ... and {len(result['errors']) - 3} more")
    
    def _generate_comprehensive_report(self, suite_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = sum(result.get('tests', 0) for result in suite_results.values())
        total_passed = sum(result.get('passed', 0) for result in suite_results.values())
        total_failed = sum(result.get('failed', 0) for result in suite_results.values())
        total_errors = sum(result.get('errors', 0) for result in suite_results.values())
        
        # Calculate success rate
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Determine overall status
        if total_failed == 0 and total_errors == 0:
            overall_status = "PASSED"
            status_emoji = "OK"
        elif total_failed > 0:
            overall_status = "FAILED"
            status_emoji = "❌"
        else:
            overall_status = "ERRORS"
            status_emoji = "WARN"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'success_rate': round(success_rate, 2),
            'summary': {
                'total_tests': total_tests,
                'total_passed': total_passed,
                'total_failed': total_failed,
                'total_errors': total_errors,
                'total_duration': self.end_time - self.start_time if self.end_time and self.start_time else 0
            },
            'suite_results': suite_results,
            'recommendations': self._generate_recommendations(suite_results)
        }
        
        # Print comprehensive summary
        self._print_comprehensive_summary(report, status_emoji)
        
        return report
    
    def _print_comprehensive_summary(self, report: Dict[str, Any], status_emoji: str):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print(f"{status_emoji} COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {report['overall_status']}")
        print(f"Success Rate: {report['success_rate']}%")
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Total Passed: {report['summary']['total_passed']}")
        print(f"Total Failed: {report['summary']['total_failed']}")
        print(f"Total Errors: {report['summary']['total_errors']}")
        print(f"Total Duration: {report['summary']['total_duration']:.2f}s")
        
        print(f"\nSuite Results:")
        for suite_name, result in report['suite_results'].items():
            status = result.get('status', 'unknown')
            tests = result.get('tests', 0)
            passed = result.get('passed', 0)
            failed = result.get('failed', 0)
            errors = result.get('errors', 0)
            
            print(f"  {suite_name.upper()}: {status} - {tests} tests, {passed} passed, {failed} failed, {errors} errors")
        
        if report['recommendations']:
            print(f"\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
    
    def _generate_recommendations(self, suite_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for suite_name, result in suite_results.items():
            if result.get('status') == 'error':
                recommendations.append(f"Investigate errors in {suite_name} test suite")
            
            if result.get('failed', 0) > 0:
                recommendations.append(f"Fix {result['failed']} failing tests in {suite_name} suite")
            
            if result.get('errors', 0) > 0:
                recommendations.append(f"Resolve {result['errors']} errors in {suite_name} suite")
            
            if result.get('tests', 0) == 0:
                recommendations.append(f"Add tests to {suite_name} suite")
        
        # Performance recommendations
        if 'performance' in suite_results:
            perf_result = suite_results['performance']
            if perf_result.get('passed', 0) < perf_result.get('tests', 0):
                recommendations.append("Review and optimize performance bottlenecks")
        
        # Security recommendations
        if 'security' in suite_results:
            sec_result = suite_results['security']
            if sec_result.get('failed', 0) > 0:
                recommendations.append("Address security vulnerabilities immediately")
        
        # Compliance recommendations
        if 'compliance' in suite_results:
            comp_result = suite_results['compliance']
            if comp_result.get('failed', 0) > 0:
                recommendations.append("Ensure regulatory compliance requirements are met")
        
        if not recommendations:
            recommendations.append("All test suites are passing - excellent work!")
        
        return recommendations
    
    def _save_test_results(self, report: Dict[str, Any]):
        """Save test results to file"""
        try:
            # Create results directory if it doesn't exist
            results_dir = "test_results"
            os.makedirs(results_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"
            filepath = os.path.join(results_dir, filename)
            
            # Save results
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\n📁 Test results saved to: {filepath}")
            
        except Exception as e:
            print(f"Warning: Could not save test results: {str(e)}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default test configuration"""
        return {
            'run_unit': True,
            'run_integration': True,
            'run_performance': True,
            'run_security': True,
            'run_compliance': True,
            'verbose': True,
            'stop_on_failure': False,
            'parallel_execution': False,
            'test_timeout': 300,  # 5 minutes
            'coverage_report': True
        }

class PerformanceTestRunner:
    """Specialized performance test runner"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.performance_metrics = {}
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests with detailed metrics"""
        print("Starting performance test execution...")
        
        # Import performance test modules
        try:
            from tests.performance.load_testing import (
                AudioSynthesisPerformanceTest,
                CachePerformanceTest,
                SystemLoadTest
            )
            
            # Run performance tests
            test_classes = [
                AudioSynthesisPerformanceTest,
                CachePerformanceTest,
                SystemLoadTest
            ]
            
            results = {}
            for test_class in test_classes:
                suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
                runner = unittest.TextTestRunner(verbosity=2)
                result = runner.run(suite)
                
                results[test_class.__name__] = {
                    'tests': result.testsRun,
                    'passed': result.testsRun - len(result.failures) - len(result.errors),
                    'failed': len(result.failures),
                    'errors': len(result.errors)
                }
            
            return results
            
        except ImportError as e:
            print(f"❌ Error importing performance tests: {str(e)}")
            return {'error': str(e)}
    
    def generate_performance_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed performance report"""
        # Mock performance report generation
        return {
            'timestamp': datetime.now().isoformat(),
            'performance_metrics': {
                'response_time_p95': '150ms',
                'throughput': '1000 req/s',
                'concurrent_users': '100',
                'error_rate': '0.1%'
            },
            'recommendations': [
                'Optimize database queries',
                'Implement connection pooling',
                'Add caching layers'
            ]
        }

class SecurityTestRunner:
    """Specialized security test runner"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.security_metrics = {}
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests with vulnerability assessment"""
        print("Starting security test execution...")
        
        try:
            from tests.security.security_testing import (
                AuthenticationSecurityTest,
                AuthorizationSecurityTest,
                DataEncryptionSecurityTest,
                InputValidationSecurityTest,
                ConsentSecurityTest,
                SecurityVulnerabilityAssessment
            )
            
            # Run security tests
            test_classes = [
                AuthenticationSecurityTest,
                AuthorizationSecurityTest,
                DataEncryptionSecurityTest,
                InputValidationSecurityTest,
                ConsentSecurityTest,
                SecurityVulnerabilityAssessment
            )
            
            results = {}
            for test_class in test_classes:
                suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
                runner = unittest.TextTestRunner(verbosity=2)
                result = runner.run(suite)
                
                results[test_class.__name__] = {
                    'tests': result.testsRun,
                    'passed': result.testsRun - len(result.failures) - len(result.errors),
                    'failed': len(result.failures),
                    'errors': len(result.errors)
                }
            
            return results
            
        except ImportError as e:
            print(f"❌ Error importing security tests: {str(e)}")
            return {'error': str(e)}
    
    def generate_security_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed security report"""
        # Mock security report generation
        return {
            'timestamp': datetime.now().isoformat(),
            'security_score': 85,
            'vulnerabilities_found': 2,
            'critical_issues': 0,
            'high_issues': 1,
            'medium_issues': 1,
            'low_issues': 0,
            'recommendations': [
                'Update authentication mechanisms',
                'Implement rate limiting',
                'Add input validation'
            ]
        }

def main():
    """Main entry point for test runner"""
    parser = argparse.ArgumentParser(description='Voice Cloning System Test Runner')
    parser.add_argument('--suite', choices=['unit', 'integration', 'performance', 'security', 'compliance', 'all'],
                       default='all', help='Test suite to run')
    parser.add_argument('--config', type=str, help='Path to test configuration file')
    parser.add_argument('--output', type=str, help='Output file for test results')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Configure test runner
    if args.suite == 'all':
        runner = TestSuiteRunner(config)
        results = runner.run_all_tests()
    else:
        # Run specific suite
        if args.suite == 'performance':
            runner = PerformanceTestRunner(config)
            results = runner.run_performance_tests()
        elif args.suite == 'security':
            runner = SecurityTestRunner(config)
            results = runner.run_security_tests()
        else:
            # Run specific test suite
            runner = TestSuiteRunner(config)
            # Modify config to run only specific suite
            for suite in ['unit', 'integration', 'performance', 'security', 'compliance']:
                config[f'run_{suite}'] = (suite == args.suite)
            runner.test_config = config
            results = runner.run_all_tests()
    
    # Save results if output specified
    if args.output:
        try:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📁 Results saved to: {args.output}")
        except Exception as e:
            print(f"Warning: Could not save results to {args.output}: {str(e)}")
    
    # Exit with appropriate code
    if 'summary' in results:
        total_failed = results['summary'].get('total_failed', 0)
        total_errors = results['summary'].get('total_errors', 0)
        if total_failed > 0 or total_errors > 0:
            sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main()
