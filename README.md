# GovQuery Backend

A backend service for converting natural language queries to SQL for government data analysis using Modal-hosted NL2SQL models.

## Features

- **Modal Integration**: Connect to your Modal-hosted NL2SQL models
- **PostgreSQL Database**: Census data storage with 12 tables and sample data
- **SQL Execution**: Direct SQL query execution with safety checks
- **Schema Management**: Automatic loading and management of ACS (American Community Survey) schemas
- **REST API**: FastAPI-based endpoints for NL2SQL conversion and SQL execution
- **Flexible Querying**: Support for specific table targeting or full schema context
- **Smart Auto-Deployment**: Automatic Modal app deployment with cold start fallback
- **Auto-Stop**: Built-in timeout mechanism for cost efficiency
- **Security**: SELECT-only enforcement, row limits, and query timeouts

## Project Structure

```
govquery_backend/
├── core/                    # Core application files
│   ├── api.py              # FastAPI endpoints
│   ├── modal_client.py     # Modal client interface
│   └── modal_deployment.py # Modal app and inference logic
│
├── deployment/              # Deployment scripts
│   └── deploy_modal.py     # Main deployment script
│
├── tests/                   # Testing scripts
│   ├── batch_test.py       # Sequential batch testing
│   ├── mass_test.py        # Comprehensive testing
│   ├── parallel_test.py    # Parallel testing
│   ├── run_tests.py        # Test runner menu
│   ├── test_api.py         # API testing
│   ├── warm_cold_test.py   # Performance testing
│   └── warm_test.py        # Warm app testing
│
├── guides/                  # Documentation and guides
│   ├── TESTING_GUIDE.md    # Testing documentation
│   ├── SMART_API_GUIDE.md  # Smart API guide
│   ├── SIMPLIFIED_AUTO_STOP.md # Auto-stop documentation
│   ├── PROJECT_STRUCTURE.md # Project organization guide
│   └── Smart_GovQuery_Postman_Collection.json # Postman collection
│
├── schemas/                 # Database schemas
│   └── [12 JSON schema files]  # Table definitions
│
├── smart_api.py            # Smart API with auto-deployment
├── smart_modal_client.py   # Smart Modal client
├── run_smart_api.py        # Smart API server runner
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
└── govquery-nl2sql-model-6.ipynb # Jupyter notebook
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Modal

Create a `.env` file based on `env_example.txt`:

```bash
cp env_example.txt .env
```

Edit `.env` with your Modal credentials:

```env
MODAL_TOKEN_ID=your_modal_token_id
MODAL_TOKEN_SECRET=your_modal_token_secret
MODAL_APP_NAME=your-actual-modal-app-name
MODAL_FUNCTION_NAME=nl2sql_inference
```

### 3. Setup PostgreSQL Database

The system includes a PostgreSQL database with Census data:

```bash
# Start PostgreSQL container
docker-compose up -d

# Verify database setup
python test_database.py

# Validate schema
python database/validate_schema.py
```

**Database Features:**
- 12 Census tables with sample data
- Docker containerized PostgreSQL 15
- Security: SELECT-only enforcement, row limits, timeouts
- Connection pooling for performance

For detailed database setup instructions, see [DATABASE_SETUP.md](DATABASE_SETUP.md).

### 4. Modal Authentication

Set up Modal authentication:

```bash
modal token set
```

Or set environment variables:

```bash
export MODAL_TOKEN_ID=your_token_id
export MODAL_TOKEN_SECRET=your_token_secret
```

## Usage

### Smart API Server (Recommended)

Start the Smart FastAPI server with automatic Modal app deployment:

```bash
python run_smart_api.py
```

The Smart API will be available at `http://localhost:8000` with automatic Modal app deployment and cold start fallback.

### Basic API Server

Start the basic FastAPI server:

```bash
python core/api.py
```

The basic API will be available at `http://localhost:8000` (requires manual Modal app deployment).

### Available Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /schemas` - List all available schemas
- `GET /schema/{table_code}` - Get specific schema
- `POST /query` - Convert natural language to SQL (async)
- `POST /query/sync` - Convert natural language to SQL (sync)
- `POST /execute` - Execute SQL query against Census database
- `POST /parse-sql` - Parse and validate SQL query

### Example API Usage

```bash
# Health check
curl http://localhost:8000/health

# List schemas
curl http://localhost:8000/schemas

# Convert query to SQL
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What is the total population in Texas?",
       "table_codes": ["B01001"],
       "max_tokens": 512,
       "temperature": 0.1
     }'

# Execute SQL query
curl -X POST "http://localhost:8000/execute" \
     -H "Content-Type: application/json" \
     -d '{
       "sql": "SELECT * FROM b01001 LIMIT 5",
       "max_rows": 1000
     }'
```

### Python Client Usage

```python
from modal_client import ModalNL2SQLClient

# Initialize client
client = ModalNL2SQLClient(
    app_name="your-modal-app-name",
    function_name="nl2sql_inference"
)

# Convert natural language to SQL
response = client.infer_sql_sync(
    query="What is the median household income by state?",
    table_codes=["B19013"]  # Optional: specify tables
)

print(f"SQL: {response.sql_query}")
```

### Example Script

Run the example script to test your setup:

```bash
python example_usage.py
```

## Schema Management

The system automatically loads ACS schemas from the `schemas/` directory. Each schema file contains:

- Table metadata (name, geography levels)
- Column definitions with types and descriptions
- SQL DDL for table creation
- Example data rows

### Available Schemas

- **B01001**: Sex by Age
- **B02001**: Race
- **B14001**: School Enrollment
- **B14002**: School Enrollment by Level
- **B15003**: Educational Attainment
- **B19001**: Household Income
- **B19013**: Median Household Income
- **B20005**: Sex by Work Experience
- **B23006**: Employment Status
- **B23025**: Employment Status by Age
- **B24010**: Sex by Occupation
- **DP02**: Selected Social Characteristics

## Modal Model Requirements

Your Modal-hosted NL2SQL model should accept the following parameters:

```python
@modal.function
def nl2sql_inference(
    query: str,
    schema_context: dict,
    max_tokens: int = 512,
    temperature: float = 0.1
) -> dict:
    # Your model inference logic here
    return {
        "sql_query": "SELECT ...",
        "confidence": 0.95,
        "explanation": "This query..."
    }
```

## Error Handling

The system includes comprehensive error handling:

- Modal connection errors
- Schema loading errors
- Model inference errors
- API validation errors

Check the `/health` endpoint to verify your setup.

## Development

### Adding New Schemas

1. Add new JSON schema files to the `schemas/` directory
2. Follow the existing schema format
3. The system will automatically load new schemas

### Customizing the Client

Extend `ModalNL2SQLClient` to add custom functionality:

```python
class CustomNL2SQLClient(ModalNL2SQLClient):
    def custom_inference_method(self, ...):
        # Your custom logic
        pass
```

## Troubleshooting

### Common Issues

1. **Modal Authentication**: Ensure your Modal tokens are correctly set
2. **App Name**: Verify your Modal app name matches your actual deployment
3. **Function Name**: Check that your Modal function name is correct
4. **Schema Files**: Ensure all schema JSON files are valid

### Debug Mode

Enable debug logging by setting:

```env
LOG_LEVEL=DEBUG
```

## License

[Your License Here]