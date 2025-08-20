# Voice Cloning System - Testing Framework

Comprehensive testing framework for the Azure Open AI Voice Cloning System, covering unit tests, integration tests, performance tests, security tests, and compliance validation.

## Architecture Overview

The testing framework is organized into five main test suites:

```
tests/
├── unit/                    # Unit tests for individual components
├── integration/            # Integration tests for Azure services
├── performance/            # Performance and load testing
├── security/              # Security testing and vulnerability assessment
├── compliance/            # Regulatory compliance testing (GDPR, HIPAA, SOC2)
├── test_runner.py         # Comprehensive test runner
├── test_config.json       # Test configuration
├── requirements.txt        # Testing dependencies
└── README.md              # This file
```

## Quick Start

### Prerequisites

- Python 3.9+
- Azure CLI (for integration tests)
- Docker (for containerized testing)
- Redis (for cache testing)

### Installation

1. **Install testing dependencies:**
   ```bash
   pip install -r tests/requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   export AZURE_SUBSCRIPTION_ID="your_subscription_id"
   export AZURE_TENANT_ID="your_tenant_id"
   export AZURE_CLIENT_ID="your_client_id"
   export AZURE_CLIENT_SECRET="your_client_secret"
   ```

3. **Run all tests:**
   ```bash
   python tests/test_runner.py --suite all
   ```

## Test Suites

### 1. Unit Tests (`tests/unit/`)

**Purpose:** Test individual components in isolation

**Coverage:**
- Consent management system
- Audio processing utilities
- Speech-to-text services
- Voice selection logic
- Audio synthesis components

**Run unit tests:**
```bash
python tests/test_runner.py --suite unit
```

**Example test:**
```python
def test_consent_record_creation(self):
    """Test creating a consent record"""
    record = ConsentRecord(**self.consent_data)
    
    self.assertEqual(record.user_id, 'test_user_123')
    self.assertEqual(record.consent_type, 'voice_cloning')
    self.assertEqual(record.status, ConsentStatus.PENDING)
```

### 2. Integration Tests (`tests/integration/`)

**Purpose:** Test Azure services integration and end-to-end workflows

**Coverage:**
- Azure Speech Service integration
- Azure Translator integration
- Voice selection and fallback logic
- Audio synthesis workflows
- Complete voice cloning pipeline

**Run integration tests:**
```bash
python tests/test_runner.py --suite integration
```

**Example test:**
```python
def test_voice_cloning_workflow(self):
    """Test complete voice cloning workflow"""
    # 1. Transcribe audio
    transcription = self.speech_service.transcribe_audio("test_audio.wav")
    self.assertTrue(transcription.success)
    
    # 2. Translate text
    translation = self.translator_service.translate_text(
        transcription.transcript, "en", "es"
    )
    self.assertTrue(translation.success)
    
    # 3. Synthesize audio
    synthesis = self.synthesizer.synthesize_text(
        translation.translated_text, voice_config
    )
    self.assertTrue(synthesis.success)
```

### 3. Performance Tests (`tests/performance/`)

**Purpose:** Test system performance under various load conditions

**Coverage:**
- Load testing with concurrent users
- Stress testing to find breaking points
- Endurance testing for stability
- Performance metrics collection
- Cache performance analysis

**Run performance tests:**
```bash
python tests/test_runner.py --suite performance
```

**Example test:**
```python
def test_system_load_capacity(self):
    """Test system load capacity"""
    load_runner = LoadTestRunner(self.base_url, self.test_config)
    
    # Run stress test
    results = load_runner.run_stress_test(max_concurrent_users=50, step_size=10)
    
    # Find breaking point
    breaking_point = None
    for result in results:
        if result['error_rate'] > 10:
            breaking_point = result['concurrent_users']
            break
    
    self.assertIsNotNone(breaking_point, "System should have a breaking point")
```

### 4. Security Tests (`tests/security/`)

**Purpose:** Test security controls and vulnerability assessment

**Coverage:**
- Authentication security (JWT, OAuth)
- Authorization controls (RBAC, permissions)
- Data encryption (at rest and in transit)
- Input validation (SQL injection, XSS, path traversal)
- Consent security and audit trails

**Run security tests:**
```bash
python tests/test_runner.py --suite security
```

**Example test:**
```python
def test_sql_injection_prevention(self):
    """Test SQL injection prevention"""
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "'; INSERT INTO users VALUES ('hacker', 'password'); --"
    ]
    
    for malicious_input in malicious_inputs:
        is_safe = self._validate_sql_input(malicious_input)
        self.assertFalse(is_safe, f"SQL injection not prevented: {malicious_input}")
```

### 5. Compliance Tests (`tests/compliance/`)

**Purpose:** Validate regulatory compliance requirements

**Coverage:**
- GDPR compliance (data rights, consent, breach notification)
- HIPAA compliance (PHI protection, access controls)
- SOC 2 compliance (security, availability, integrity)
- ISO 27001 compliance (information security)

**Run compliance tests:**
```bash
python tests/test_runner.py --suite compliance
```

**Example test:**
```python
def test_gdpr_data_subject_rights(self):
    """Test data subject rights under GDPR"""
    # Test right to access
    access_result = self._exercise_data_subject_right("access", self.test_user_id)
    self.assertTrue(access_result.success)
    
    # Test right to erasure (right to be forgotten)
    erasure_result = self._exercise_data_subject_right("erasure", self.test_user_id)
    self.assertTrue(erasure_result.success)
    
    # Verify data is actually deleted
    is_deleted = self._check_data_deletion(self.test_user_id)
    self.assertTrue(is_deleted)
```

## Configuration

### Test Configuration (`test_config.json`)

The test configuration file controls various aspects of testing:

```json
{
  "test_suites": {
    "unit": {
      "enabled": true,
      "timeout": 300,
      "parallel": false,
      "coverage": true
    },
    "performance": {
      "enabled": true,
      "timeout": 1800,
      "parallel": true,
      "metrics": {
        "response_time_threshold": 200,
        "throughput_threshold": 1000,
        "error_rate_threshold": 1.0
      }
    }
  }
}
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID | Yes |
| `AZURE_TENANT_ID` | Azure tenant ID | Yes |
| `AZURE_CLIENT_ID` | Azure client ID | Yes |
| `AZURE_CLIENT_SECRET` | Azure client secret | Yes |
| `AZURE_REGION` | Azure region for services | No (default: East US) |
| `TEST_ENVIRONMENT` | Test environment (dev/staging/prod) | No (default: dev) |

## Running Tests

### Command Line Options

```bash
python tests/test_runner.py [OPTIONS]

Options:
  --suite {unit,integration,performance,security,compliance,all}
                        Test suite to run (default: all)
  --config PATH         Path to test configuration file
  --output PATH         Output file for test results
  --verbose             Verbose output
  --help                Show help message
```

### Examples

**Run all tests:**
```bash
python tests/test_runner.py --suite all
```

**Run specific test suite:**
```bash
python tests/test_runner.py --suite security
```

**Run with custom config:**
```bash
python tests/test_runner.py --config custom_config.json
```

**Save results to file:**
```bash
python tests/test_runner.py --output test_results.json
```

### CI/CD Integration

The testing framework integrates with various CI/CD platforms:

**GitHub Actions:**
```yaml
- name: Run Tests
  run: |
    python tests/test_runner.py --suite all --output test_results.json
```

**Azure DevOps:**
```yaml
- script: |
    python tests/test_runner.py --suite all --output test_results.json
  displayName: 'Run Test Suite'
```

**Jenkins:**
```groovy
stage('Test') {
    steps {
        sh 'python tests/test_runner.py --suite all --output test_results.json'
    }
}
```

## Test Results and Reporting

### Output Formats

The test runner generates multiple output formats:

1. **Console Output:** Real-time test progress and results
2. **JSON Report:** Detailed test results for programmatic processing
3. **HTML Report:** Visual test results with charts and graphs
4. **JUnit Report:** Standard format for CI/CD integration

### Sample Output

```
Starting comprehensive test suite execution...
============================================================

Running UNIT tests...
UNIT Test Summary:
   Tests Run: 45
   Passed: 45
   Failed: 0
   Errors: 0
   Duration: 12.34s

Running INTEGRATION tests...
INTEGRATION Test Summary:
   Tests Run: 23
   Passed: 23
   Failed: 0
   Errors: 0
   Duration: 45.67s

============================================================
COMPREHENSIVE TEST SUMMARY
============================================================
Overall Status: PASSED
Success Rate: 100.0%
Total Tests: 68
Total Passed: 68
Total Failed: 0
Total Errors: 0
Total Duration: 58.01s

Suite Results:
  UNIT: completed - 45 tests, 45 passed, 0 failed, 0 errors
  INTEGRATION: completed - 23 tests, 23 passed, 0 failed, 0 errors

Recommendations:
  • All test suites are passing - excellent work!
```

## 🔧 Advanced Features

### Parallel Execution

Enable parallel test execution for faster results:

```json
{
  "execution": {
    "parallel_execution": {
      "enabled": true,
      "max_workers": 4,
      "chunk_size": 10
    }
  }
}
```

### Test Data Management

Generate and manage test data:

```python
# Generate test user profiles
user_profiles = self._generate_test_users(count=100)

# Create test voice samples
voice_samples = self._generate_voice_samples(
    duration_range=[5, 30],
    quality_levels=["low", "medium", "high"]
)
```

### Performance Monitoring

Monitor system resources during testing:

```python
# Monitor CPU and memory usage
cpu_usage = psutil.cpu_percent(interval=1)
memory_usage = psutil.virtual_memory().percent

# Monitor Azure resources
azure_metrics = self.monitor_client.get_metrics(
    resource_id=resource_id,
    metric_names=["CPU", "Memory", "Network"]
)
```

### Custom Test Fixtures

Create reusable test fixtures:

```python
@pytest.fixture
def mock_azure_speech_service():
    """Mock Azure Speech Service for testing"""
    with patch('speech_to_text.AzureSpeechToTextService') as mock_service:
        mock_service.return_value.transcribe_audio.return_value = Mock(
            success=True,
            transcript="Hello world",
            confidence=0.95
        )
        yield mock_service

@pytest.fixture
def test_consent_data():
    """Test consent data for testing"""
    return {
        "user_id": "test_user_123",
        "consent_type": "voice_cloning",
        "purpose": "Create custom voice model",
        "data_usage": ["audio_processing", "voice_training"],
        "retention_period": 365
    }
```

## 🐛 Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Ensure parent directory is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Azure Authentication Issues:**
```bash
# Login to Azure CLI
az login

# Set subscription
az account set --subscription "your_subscription_id"
```

**Test Timeouts:**
```json
{
  "test_suites": {
    "performance": {
      "timeout": 3600  # Increase timeout to 1 hour
    }
  }
}
```

**Memory Issues:**
```bash
# Run tests with memory profiling
python -m memory_profiler tests/test_runner.py --suite performance
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set debug environment variable
export TEST_DEBUG=true

# Run tests with debug output
python tests/test_runner.py --verbose
```

## 📚 Additional Resources

### Documentation

- [Azure Speech Service Testing Guide](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/)
- [Azure Translator Testing Guide](https://docs.microsoft.com/en-us/azure/cognitive-services/translator/)
- [GDPR Compliance Testing](https://gdpr.eu/testing/)
- [HIPAA Compliance Testing](https://www.hhs.gov/hipaa/testing/)

### Tools and Libraries

- **Performance Testing:** Locust, JMeter, Artillery
- **Security Testing:** OWASP ZAP, Bandit, Safety
- **Code Coverage:** Coverage.py, pytest-cov
- **Static Analysis:** Pylint, Flake8, Black, MyPy

### Best Practices

1. **Test Isolation:** Ensure tests don't depend on each other
2. **Mock External Services:** Use mocks for Azure services in unit tests
3. **Data Cleanup:** Clean up test data after each test
4. **Performance Baselines:** Establish performance baselines for regression testing
5. **Security First:** Run security tests before performance tests
6. **Compliance Validation:** Run compliance tests in production-like environments

## 🤝 Contributing

### Adding New Tests

1. **Create test file** in appropriate directory
2. **Follow naming convention:** `test_*.py`
3. **Add test class** inheriting from `unittest.TestCase`
4. **Write test methods** with descriptive names
5. **Add to test runner** if needed

### Test Standards

- **Naming:** Use descriptive test method names
- **Documentation:** Add docstrings to all test methods
- **Assertions:** Use specific assertions (assertEqual, assertTrue, etc.)
- **Error Messages:** Provide clear error messages in assertions
- **Coverage:** Aim for 80%+ code coverage

### Code Review

All test code must pass:
- Pylint checks
- Flake8 style checks
- Black formatting
- MyPy type checking
- Test execution

## License

This testing framework is part of the Voice Cloning System and follows the same license terms.

---

For questions or support, contact the QA team or create an issue in the project repository.
