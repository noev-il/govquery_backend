# Database Setup Guide

This guide explains how to set up and manage the PostgreSQL Census database for the GovQuery system.

## Overview

The GovQuery system uses PostgreSQL to store Census data with the following features:
- **12 Census tables** with sample data based on JSON schemas
- **Docker containerized** PostgreSQL for easy setup
- **Security features** including SELECT-only enforcement and row limits
- **Connection pooling** for optimal performance
- **Schema validation** against authoritative JSON schemas

## Quick Start

### 1. Start the Database

```bash
cd govquery_backend
docker-compose up -d
```

This will:
- Start PostgreSQL 15 container
- Create `census_data` database
- Set up user `govquery` with password `govquery_dev`
- Expose database on port 5432

### 2. Verify Database Setup

```bash
# Check container status
docker-compose ps

# Test database connection
python test_database.py

# Validate schema against JSON files
python database/validate_schema.py
```

### 3. Start the API Server

```bash
# Set Modal credentials (required for full functionality)
export MODAL_TOKEN_ID="your-modal-token-id"
export MODAL_TOKEN_SECRET="your-modal-token-secret"

# Start the server
python run_smart_api.py
```

## Database Schema

The database contains 12 Census tables with the following structure:

| Table Code | Description | Sample Columns |
|------------|-------------|----------------|
| `b01001` | Population by Sex | `total_population`, `male_population`, `female_population` |
| `b02001` | Race | `white_alone`, `black_or_african_american_alone`, `asian_alone` |
| `b14001` | School Enrollment | `enrolled_in_school`, `not_enrolled_in_school` |
| `b14002` | School Enrollment by Level | `nursery_school`, `kindergarten`, `elementary_school` |
| `b15003` | Educational Attainment | `high_school_graduate`, `bachelors_degree`, `masters_degree` |
| `b19001` | Household Income | `less_than_10000`, `10000_to_14999`, `15000_to_19999` |
| `b19013` | Median Household Income | `median_household_income`, `median_household_income_moe` |
| `b20005` | Sex by Work Status | `male_in_labor_force`, `female_in_labor_force` |
| `b23006` | Employment Status | `employed`, `unemployed`, `not_in_labor_force` |
| `b23025` | Employment Status by Sex | `male_employed`, `female_employed` |
| `b24010` | Sex by Occupation | `management_business_science_arts`, `service_occupations` |
| `dp02` | Social Characteristics | `high_school_graduate_or_higher`, `bachelors_degree_or_higher` |

## API Endpoints

### Execute SQL Query

**POST** `/execute`

Execute a SQL query against the Census database with safety checks.

**Request:**
```json
{
  "sql": "SELECT * FROM b01001 LIMIT 5",
  "max_rows": 1000
}
```

**Response:**
```json
{
  "success": true,
  "rows": [
    {
      "geography_id": "04000US48",
      "year": 2022,
      "total_population": 1500,
      "total_population_moe": 20
    }
  ],
  "row_count": 1,
  "columns": ["geography_id", "year", "total_population", "total_population_moe"],
  "execution_time_ms": 5.2,
  "applied_limit": false,
  "statement_timeout_ms": 30000
}
```

### Health Check

**GET** `/health`

Check database and Modal service status.

**Response:**
```json
{
  "status": "ok",
  "modal_deployment": "running",
  "database_connection": "connected",
  "performance_optimizations_enabled": true,
  "sqlglot_available": true
}
```

## Security Features

### SQL Validation
- **SELECT-only**: Only SELECT queries are allowed
- **Forbidden keywords**: INSERT, UPDATE, DELETE, DROP, etc. are blocked
- **Multiple statements**: Semicolon-separated queries are rejected
- **Function validation**: Only safe functions are allowed

### Query Limits
- **Row limit**: Maximum 1,000 rows per query (configurable)
- **Timeout**: 30-second query timeout
- **Connection pooling**: Efficient resource management

### Example Security Tests

```bash
# This will be rejected
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{"sql": "INSERT INTO b01001 VALUES (1, 2, 3)"}'

# This will be accepted
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM b01001 LIMIT 5"}'
```

## Environment Variables

Create a `.env` file in `govquery_backend/`:

```env
# Modal API credentials (required for NL2SQL)
MODAL_TOKEN_ID="your-modal-token-id"
MODAL_TOKEN_SECRET="your-modal-token-secret"

# PostgreSQL Database Configuration
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"
POSTGRES_DB="census_data"
POSTGRES_USER="govquery"
POSTGRES_PASSWORD="govquery_dev"

# Optional: Full DATABASE_URL (overrides individual components if set)
# DATABASE_URL="postgresql://govquery:govquery_dev@localhost:5432/census_data"
```

## Troubleshooting

### Database Connection Issues

1. **Container not running:**
   ```bash
   docker-compose ps
   docker-compose up -d
   ```

2. **Connection refused:**
   ```bash
   # Check if port 5432 is available
   lsof -i :5432
   
   # Restart container
   docker-compose restart
   ```

3. **Authentication failed:**
   ```bash
   # Check environment variables
   echo $POSTGRES_USER
   echo $POSTGRES_PASSWORD
   
   # Reset database
   docker-compose down -v
   docker-compose up -d
   ```

### Schema Issues

1. **Missing tables:**
   ```bash
   # Recreate schema from JSON files
   python database/setup_schema.py
   ```

2. **Schema validation failed:**
   ```bash
   # Run validation report
   python database/validate_schema.py
   ```

### API Issues

1. **Modal token errors:**
   ```bash
   # Set dummy tokens for database-only testing
   export MODAL_TOKEN_ID="test"
   export MODAL_TOKEN_SECRET="test"
   ```

2. **SQL validation errors:**
   - Ensure queries start with `SELECT`
   - Avoid forbidden keywords (INSERT, UPDATE, DELETE, etc.)
   - Check for semicolons in queries

## Development

### Adding New Tables

1. Create JSON schema file in `schemas/` directory
2. Run `python database/setup_schema.py` to create table
3. Run `python database/validate_schema.py` to verify

### Testing

```bash
# Test database connection
python test_database.py

# Test API endpoints
python test_api.py

# Test frontend integration
cd ../govquery_frontend
node test-execute.js
```

### Performance Monitoring

The system includes built-in performance monitoring:
- Query execution times
- Connection pool statistics
- Cache hit rates
- Error rates

Access via `/health` endpoint or check logs.

## Production Considerations

### Security
- Change default passwords
- Use environment variables for secrets
- Enable SSL/TLS for database connections
- Implement proper RBAC

### Performance
- Tune connection pool settings
- Add database indexes as needed
- Monitor query performance
- Implement query caching

### Backup
- Regular database backups
- Schema versioning
- Data validation procedures

## Support

For issues or questions:
1. Check this documentation
2. Run diagnostic scripts
3. Check container logs: `docker-compose logs postgres`
4. Review API logs in the terminal output
