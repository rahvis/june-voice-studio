# Azure Voice Cloning API Backend

A comprehensive FastAPI-based backend service for Azure Open AI voice cloning capabilities, featuring real-time synthesis, custom voice training, and lexicon management.

## Features

### Core Functionality
- **Voice Model Training**: Custom neural voice model creation and management
- **Real-time Synthesis**: Text-to-speech with custom voices
- **Batch Synthesis**: Process multiple text inputs efficiently
- **Lexicon Management**: Custom pronunciation and language support
- **Multi-language Support**: Azure AI Translator integration

### Technical Features
- **Azure Entra ID Authentication**: Secure user authentication and authorization
- **Rate Limiting**: Configurable API rate limiting with adaptive limits
- **Comprehensive Logging**: Structured logging with request/response tracking
- **Error Handling**: Detailed error responses with recovery suggestions
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Backend API   │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Azure AI      │
                       │   Services      │
                       │                 │
                       │ • Speech        │
                       │ • Translator    │
                       │ • OpenAI        │
                       └─────────────────┘
```

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Runtime**: Python 3.9+
- **Authentication**: Azure Entra ID (Azure AD)
- **Database**: Azure Cosmos DB / PostgreSQL
- **Storage**: Azure Blob Storage
- **AI Services**: Azure Cognitive Services
- **Monitoring**: Azure Application Insights

## Prerequisites

- Python 3.9 or higher
- Azure subscription with access to:
  - Azure AI Speech Service
  - Azure AI Translator
  - Azure OpenAI Service
  - Azure Key Vault
  - Azure Cosmos DB
  - Azure Blob Storage
- Azure CLI installed and configured

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd azure-voice-cloning/backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the backend directory:

```env
# Application Configuration
ENVIRONMENT=development
APP_VERSION=1.0.0
HOST=0.0.0.0
PORT=8000

# Azure Configuration
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_AUDIENCE=api://your-api-identifier

# Azure AI Services
AZURE_SPEECH_KEY=your-speech-service-key
AZURE_SPEECH_REGION=your-speech-service-region
AZURE_TRANSLATOR_KEY=your-translator-key
AZURE_TRANSLATOR_REGION=your-translator-region
AZURE_OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_ENDPOINT=your-openai-endpoint

# Database Configuration
DATABASE_URL=your-database-connection-string
COSMOS_DB_ENDPOINT=your-cosmos-db-endpoint
COSMOS_DB_KEY=your-cosmos-db-key

# Storage Configuration
AZURE_STORAGE_CONNECTION_STRING=your-storage-connection-string
AZURE_STORAGE_CONTAINER=voice-cloning

# Logging Configuration
LOG_LEVEL=INFO
LOG_REQUESTS=true
LOG_RESPONSES=true
LOG_REQUEST_BODY=false
LOG_RESPONSE_BODY=false
LOG_HEADERS=false

# Rate Limiting
RATE_LIMITING_ENABLED=true
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_SYNTHESIS=50
RATE_LIMIT_TRAINING=10

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Database Setup
```bash
# Initialize database (if using SQLAlchemy)
alembic upgrade head

# Or create database manually for Cosmos DB
```

## Running the Application

### Development Mode
```bash
# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the built-in runner
python -m app.main
```

### Production Mode
```bash
# Using uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using gunicorn (uncomment in requirements.txt)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📚 API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Authentication

The API uses Azure Entra ID for authentication. All requests must include a valid Bearer token in the Authorization header:

```bash
curl -H "Authorization: Bearer <your-token>" \
     http://localhost:8000/api/v1/voices
```

### Getting an Access Token

1. **Azure CLI**:
   ```bash
   az account get-access-token --resource api://your-api-identifier
   ```

2. **MSAL (Microsoft Authentication Library)**:
   ```python
   from azure.identity import InteractiveBrowserCredential
   
   credential = InteractiveBrowserCredential()
   token = credential.get_token("api://your-api-identifier")
   ```

## 📡 API Endpoints

### Voice Management
- `POST /api/v1/voices/train` - Start voice training
- `GET /api/v1/voices/{id}` - Get voice status
- `GET /api/v1/voices/` - List user voices
- `PUT /api/v1/voices/{id}` - Update voice
- `DELETE /api/v1/voices/{id}` - Delete voice

### Voice Synthesis
- `POST /api/v1/synthesis/speak` - Real-time synthesis
- `POST /api/v1/synthesis/speak/stream` - Streaming synthesis
- `POST /api/v1/synthesis/batch` - Batch synthesis
- `GET /api/v1/synthesis/history` - Synthesis history

### Lexicon Management
- `POST /api/v1/lexicon/` - Create lexicon entry
- `GET /api/v1/lexicon/{id}` - Get lexicon entry
- `GET /api/v1/lexicon/` - List lexicon entries
- `PUT /api/v1/lexicon/{id}` - Update lexicon entry
- `DELETE /api/v1/lexicon/{id}` - Delete lexicon entry
- `POST /api/v1/lexicon/bulk-upload` - Bulk upload
- `POST /api/v1/lexicon/validate` - Validate text

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_voice_management.py

# Run with verbose output
pytest -v
```

### Test Configuration
Tests use a separate test database and configuration. Create a `test.env` file for test-specific settings.

## Monitoring and Logging

### Logging Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failed operations

### Log Format
Logs include:
- Request ID for correlation
- Timestamp
- Log level
- Message
- Context information

### Metrics
The API exposes Prometheus metrics at `/metrics` for monitoring:
- Request counts
- Response times
- Error rates
- Custom business metrics

## Security Features

- **Authentication**: Azure Entra ID integration
- **Authorization**: Role-based access control
- **Rate Limiting**: Configurable per-endpoint limits
- **Input Validation**: Pydantic model validation
- **CORS Protection**: Configurable cross-origin policies
- **Request Logging**: Audit trail for security monitoring

## Deployment

### Azure Container Instances
```bash
# Build and push Docker image
docker build -t voice-cloning-api .
docker tag voice-cloning-api your-registry.azurecr.io/voice-cloning-api:latest
docker push your-registry.azurecr.io/voice-cloning-api:latest

# Deploy to ACI
az container create \
  --resource-group your-rg \
  --name voice-cloning-api \
  --image your-registry.azurecr.io/voice-cloning-api:latest \
  --ports 8000 \
  --environment-variables ENVIRONMENT=production
```

### Azure App Service
```bash
# Deploy to App Service
az webapp up \
  --name voice-cloning-api \
  --resource-group your-rg \
  --runtime "PYTHON|3.9" \
  --sku B1
```

### Azure Kubernetes Service
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify Azure Entra ID configuration
   - Check token expiration
   - Ensure correct audience value

2. **Rate Limiting**:
   - Check rate limit configuration
   - Monitor request patterns
   - Adjust limits if needed

3. **Database Connection**:
   - Verify connection strings
   - Check network access
   - Ensure database exists

4. **Azure Service Errors**:
   - Verify service keys and regions
   - Check service quotas
   - Monitor Azure service status

### Debug Mode
Enable debug mode by setting:
```env
LOG_LEVEL=DEBUG
ERROR_INCLUDE_TRACEBACK=true
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Style
- Use Black for code formatting
- Follow PEP 8 guidelines
- Add type hints where possible
- Write comprehensive docstrings

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting guide
- Contact the development team

## 🔄 Changelog

### Version 1.0.0
- Initial release
- Core voice management APIs
- Synthesis endpoints
- Lexicon management
- Azure Entra ID authentication
- Comprehensive middleware stack
