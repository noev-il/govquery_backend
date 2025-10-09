# GovQuery Templated API

A templated API for frontend integration with proper error handling, telemetry, and safety guardrails.

## 🚀 Quick Start

### Option 1: Launch Demo (Recommended)
```bash
python launch_demo.py
```
This will start the backend server and open the frontend in your browser.

### Option 2: Manual Start
```bash
# Terminal 1: Start backend
python templated_api.py

# Terminal 2: Open frontend
open frontend.html  # macOS
# or
start frontend.html  # Windows
# or
xdg-open frontend.html  # Linux
```

## 📡 API Contract

### POST /query

**Request:**
```json
{
  "question": "What is the total population in Texas?",
  "model_hint": "AUTO",
  "tables": ["B01001"], 
  "max_rows": 500
}
```

**Response (Success):**
```json
{
  "status": "ok",
  "sql": "SELECT ...",
  "data": [{ "...": "..." }],
  "sources": ["postgres:acs.B01001"],
  "meta": { 
    "model": "SQLCODER", 
    "elapsed_ms": 4123, 
    "schema_chars": 1807,
    "confidence": 0.95,
    "explanation": "This query..."
  }
}
```

**Response (Error):**
```json
{
  "status": "error",
  "error_code": "UNSAFE_SQL",
  "message": "Generated SQL contains unsafe operations",
  "meta": {
    "model": "unknown",
    "elapsed_ms": 1234,
    "question_hash": "a1b2c3d4"
  }
}
```

## 🛡️ Safety Features

- **SQL Safety**: Only allows SELECT queries, blocks dangerous operations
- **Row Limits**: Enforces maximum row limits (default 500, max 5000)
- **Input Validation**: Validates all inputs and parameters
- **Error Handling**: Comprehensive error codes and messages

## 📊 Telemetry

Every request is logged with:
- Question hash (for deduplication)
- Model used
- Elapsed time
- Success/error status
- Error codes

## 🎛️ Frontend Features

- **Chat Interface**: Natural language input with conversation history
- **Model Selection**: Choose between AUTO, T5, or SQLCODER
- **Table Selection**: Multi-select available data tables
- **SQL Display**: Generated SQL with copy-to-clipboard
- **Error Handling**: Clear error messages and retry options
- **Loading States**: Visual feedback during processing

## 🧪 Testing

```bash
# Test the API
python test_templated_api.py

# Test specific endpoints
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the total population in Texas?","model_hint":"AUTO","tables":["B01001"]}'
```

## 🔧 Configuration

Environment variables:
- `MODAL_TOKEN_ID`: Modal authentication token
- `MODAL_TOKEN_SECRET`: Modal authentication secret  
- `MODAL_APP_NAME`: Modal app name (default: govquery-nl2sql-main)

## 📁 File Structure

```
├── templated_api.py          # Main API server
├── frontend.html             # Frontend interface
├── launch_demo.py            # Demo launcher
├── test_templated_api.py     # API tests
├── smart_modal_client.py     # Modal client wrapper
└── core/modal_client.py      # Base Modal client
```

## 🚨 Error Codes

- `UNSAFE_SQL`: Generated SQL contains dangerous operations
- `QUERY_FAILED`: Modal inference failed
- `INTERNAL_ERROR`: Server-side error
- `NETWORK_ERROR`: Frontend network error

## 🎯 Next Steps

1. **Data Execution**: Add actual SQL execution to return real data
2. **Caching**: Implement query result caching
3. **Authentication**: Add user authentication and rate limiting
4. **Advanced Charts**: Add chart generation for time series data
5. **Export**: Add CSV/JSON export functionality
