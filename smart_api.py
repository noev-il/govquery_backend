#!/usr/bin/env python3
"""
Smart FastAPI application with automatic Modal app deployment and cold start handling.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from smart_modal_client import get_smart_client, NL2SQLRequest, NL2SQLResponse
from core.db_executor import DatabaseExecutor

# SQLGlot for SQL parsing
try:
    from sqlglot import parse_one, format
    SQLGLOT_AVAILABLE = True
except ImportError:
    SQLGLOT_AVAILABLE = False

# Performance optimizations
try:
    from performance_optimizations import (
        get_schema_with_ttl, 
        preload_common_schemas, 
        time_function,
        perf_monitor,
        get_cache_stats
    )
    PERFORMANCE_OPTIMIZATIONS = True
except ImportError:
    PERFORMANCE_OPTIMIZATIONS = False


# Initialize database executor
db_executor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for database connection."""
    global db_executor
    
    # Startup: Initialize database connection
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            # Fallback to individual components
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            db = os.getenv("POSTGRES_DB", "census_data")
            user = os.getenv("POSTGRES_USER", "govquery")
            password = os.getenv("POSTGRES_PASSWORD", "govquery_dev")
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        
        db_executor = DatabaseExecutor(database_url)
        await db_executor.connect()
        
        # Test connection
        if await db_executor.test_connection():
            print("✅ Database connection established")
        else:
            print("⚠️ Database connection test failed")
            
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        db_executor = None
    
    yield
    
    # Shutdown: Close database connection
    if db_executor:
        await db_executor.close()
        print("🔌 Database connection closed")


class QueryRequest(BaseModel):
    """Request model for NL2SQL queries."""
    query: str
    table_codes: Optional[List[str]] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.1
    model_choice: Optional[str] = "auto"


class QueryResponse(BaseModel):
    """Response model for NL2SQL queries."""
    sql_query: str
    confidence: Optional[float] = None
    explanation: Optional[str] = None
    error: Optional[str] = None
    schema_context_used: Optional[List[str]] = None
    model_used: Optional[str] = None
    prompt_length: Optional[int] = None
    auto_selected: Optional[bool] = None
    deployment_status: Optional[str] = None


class SchemaInfo(BaseModel):
    """Model for schema information."""
    table_code: str
    table_name: str
    geography_levels: List[str]
    columns: List[dict]


class SQLParseRequest(BaseModel):
    """Request model for SQL parsing."""
    sql: str


class SQLParseResponse(BaseModel):
    """Response model for SQL parsing."""
    valid: bool
    ast: Optional[dict] = None
    error: Optional[str] = None
    formatted_sql: Optional[str] = None


class ExecuteRequest(BaseModel):
    """Request model for SQL execution."""
    sql: str
    max_rows: Optional[int] = 1000


class ExecuteResponse(BaseModel):
    """Response model for SQL execution."""
    success: bool
    rows: List[Dict[str, Any]]
    row_count: int
    columns: List[str]
    execution_time_ms: float
    error: Optional[str] = None
    applied_limit: bool
    statement_timeout_ms: int
    query_id: Optional[str] = None
    query_metadata: Optional[Dict[str, Any]] = None


# Create FastAPI app with lifespan
app = FastAPI(
    title="GovQuery Smart NL2SQL API",
    description="Natural Language to SQL conversion with automatic Modal app deployment",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "GovQuery Smart NL2SQL API",
        "version": "2.0.0",
        "features": [
            "Automatic Modal app deployment",
            "Cold start fallback handling",
            "Smart error recovery"
        ],
        "endpoints": {
            "query": "/query - Convert natural language to SQL (with auto-deployment)",
            "query_simple": "/query/simple - Simple query with fallback",
            "schemas": "/schemas - List available schemas",
            "schema": "/schema/{table_code} - Get specific schema",
            "health": "/health - Health check with app status",
            "deploy": "/deploy - Manually trigger app deployment",
            "parse_sql": "/parse-sql - Parse and validate SQL using SQLGlot"
        }
    }


@app.get("/health")
async def health_check():
    """Enhanced health check with database and Modal app status."""
    try:
        # Check database connectivity
        db_ok = False
        if db_executor:
            try:
                db_ok = await db_executor.test_connection()
            except Exception:
                db_ok = False
        
        # Check Modal client (without calling functions to avoid cold start issues)
        modal_ok = False
        modal_app_name = "unknown"
        try:
            client = get_smart_client()
            modal_app_name = client.app_name
            modal_ok = True  # Assume OK if client can be created
        except Exception:
            modal_ok = False
        
        # Get schema count from filesystem
        schemas_dir = project_root / "schemas"
        schemas = [f for f in schemas_dir.iterdir() if f.suffix == ".json"]
        
        # Build health response
        health_data = {
            "status": "healthy" if db_ok else "degraded",
            "db_ok": db_ok,
            "modal_ok": modal_ok,
            "schemas_loaded": len(schemas),
            "modal_app_name": modal_app_name,
            "features": {
                "auto_deployment": True,
                "cold_start_fallback": True,
                "smart_error_recovery": True,
                "auto_stop": "Modal built-in timeout (5 minutes)"
            }
        }
        
        if PERFORMANCE_OPTIMIZATIONS:
            health_data["performance"] = {
                "cache_stats": get_cache_stats(),
                "performance_stats": perf_monitor.get_stats()
            }
        
        return health_data
    except Exception as e:
        return {
            "status": "unhealthy",
            "db_ok": False,
            "modal_ok": False,
            "error": str(e)
        }


@app.get("/schemas", response_model=List[SchemaInfo])
async def list_schemas():
    """List all available schemas."""
    try:
        client = get_smart_client()
        schemas = client.load_all_schemas()
        
        schema_list = []
        for table_code, schema in schemas.items():
            schema_list.append(SchemaInfo(
                table_code=table_code,
                table_name=schema["table_name"],
                geography_levels=schema["geography_levels"],
                columns=schema["columns"]
            ))
        
        return schema_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading schemas: {str(e)}")


@app.get("/schema/{table_code}", response_model=dict)
async def get_schema(table_code: str):
    """Get specific schema by table code."""
    try:
        client = get_smart_client()
        schema = client.load_schema(table_code)
        return schema
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Schema {table_code} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading schema: {str(e)}")


@app.post("/query", response_model=QueryResponse)
def convert_to_sql_smart(request: QueryRequest):
    """
    Convert natural language query to SQL with automatic Modal app deployment.
    
    This endpoint will:
    1. Try to use existing Modal app
    2. If app not found, automatically deploy it
    3. Retry the query after deployment
    4. Return results with deployment status
    """
    try:
        client = get_smart_client()
        
        # Check if app is running
        app_running = client._is_app_running()
        deployment_status = "existing" if app_running else "deployed"
        
        # Perform inference with fallback
        response = client.infer_sql_with_fallback(
            query=request.query,
            table_codes=request.table_codes,
            model_choice=request.model_choice,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Determine which schemas were used
        schema_context_used = request.table_codes
        if schema_context_used is None:
            all_schemas = client.load_all_schemas()
            schema_context_used = list(all_schemas.keys())
        
        return QueryResponse(
            sql_query=response.sql_query,
            confidence=response.confidence,
            explanation=response.explanation,
            error=response.error,
            schema_context_used=schema_context_used,
            model_used=response.model_used,
            prompt_length=response.prompt_length,
            auto_selected=response.auto_selected,
            deployment_status=deployment_status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/query/simple", response_model=dict)
def convert_to_sql_simple(request: QueryRequest):
    """
    Simple query endpoint with automatic fallback.
    
    Uses the simple query method with automatic deployment fallback.
    """
    try:
        client = get_smart_client()
        
        # Use the first table code or default to B01001
        table_code = request.table_codes[0] if request.table_codes else "B01001"
        
        # Perform query with fallback
        result = client.query_with_fallback(
            table_code=table_code,
            question=request.query,
            force_model=request.model_choice if request.model_choice != "auto" else None
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/deploy")
def deploy_modal_app():
    """
    Manually trigger Modal app deployment.
    
    This endpoint allows you to manually deploy the Modal app
    without making a query.
    """
    try:
        client = get_smart_client()
        
        if client._is_app_running():
            return {
                "status": "already_running",
                "message": "Modal app is already running",
                "app_name": client.app_name
            }
        
        success = client._deploy_app()
        
        if success:
            return {
                "status": "deployed",
                "message": "Modal app deployed successfully",
                "app_name": client.app_name
            }
        else:
            return {
                "status": "failed",
                "message": "Failed to deploy Modal app",
                "app_name": client.app_name
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment error: {str(e)}")


@app.post("/parse-sql", response_model=SQLParseResponse)
def parse_sql(request: SQLParseRequest):
    """
    Parse and validate SQL using SQLGlot.
    
    This endpoint uses SQLGlot to parse SQL queries and provide
    syntax validation, formatting, and AST generation.
    """
    if not SQLGLOT_AVAILABLE:
        return SQLParseResponse(
            valid=False,
            error="SQLGlot is not available. Please install with: pip install sqlglot"
        )
    
    try:
        # Parse the SQL
        parsed = parse_one(request.sql)
        
        if parsed is None:
            return SQLParseResponse(
                valid=False,
                error="Failed to parse SQL query"
            )
        
        # Format the SQL
        formatted = format(parsed, pretty=True)
        
        # Convert AST to dictionary (simplified)
        ast_dict = {
            "type": str(parsed.key),
            "expressions": len(parsed.expressions) if hasattr(parsed, 'expressions') else 0,
            "sql": request.sql
        }
        
        return SQLParseResponse(
            valid=True,
            ast=ast_dict,
            formatted_sql=formatted
        )
        
    except Exception as e:
        return SQLParseResponse(
            valid=False,
            error=f"SQL parsing error: {str(e)}"
        )


@app.post("/execute", response_model=ExecuteResponse)
async def execute_sql(request: ExecuteRequest):
    """
    Execute SQL query against Census database.
    
    This endpoint executes validated SQL queries with comprehensive safety checks:
    - SELECT-only enforcement
    - Row limit enforcement (max 1,000)
    - Query timeout (30 seconds)
    - SQL injection protection
    - Function call validation
    """
    if db_executor is None:
        raise HTTPException(
            status_code=503, 
            detail="Database not available. Please ensure PostgreSQL is running and configured."
        )
    
    try:
        result = await db_executor.execute_query(
            sql=request.sql,
            max_rows=request.max_rows
        )
        
        return ExecuteResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database execution error: {str(e)}"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for database connection."""
    global db_executor
    
    # Startup: Initialize database connection
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            # Fallback to individual components
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            db = os.getenv("POSTGRES_DB", "census_data")
            user = os.getenv("POSTGRES_USER", "govquery")
            password = os.getenv("POSTGRES_PASSWORD", "govquery_dev")
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        
        db_executor = DatabaseExecutor(database_url)
        await db_executor.connect()
        
        # Test connection
        if await db_executor.test_connection():
            print("✅ Database connection established")
        else:
            print("⚠️ Database connection test failed")
            
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        db_executor = None
    
    yield
    
    # Shutdown: Close database connection
    if db_executor:
        await db_executor.close()
        print("🔌 Database connection closed")


if __name__ == "__main__":
    # Modal credentials should be set via environment variables
    # Set these before running: export MODAL_TOKEN_ID="your-id" MODAL_TOKEN_SECRET="your-secret"
    if not os.environ.get("MODAL_TOKEN_ID") or not os.environ.get("MODAL_TOKEN_SECRET"):
        raise ValueError("MODAL_TOKEN_ID and MODAL_TOKEN_SECRET must be set as environment variables")
    os.environ["MODAL_APP_NAME"] = "govquery-nl2sql-main"
    
    print("🎯 GovQuery Smart API Server")
    print("=" * 50)
    print("🌐 Server: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔍 Health: http://localhost:8000/health")
    print("🚀 Features: Auto-deployment, Cold start fallback")
    
    # Preload common schemas for better performance
    if PERFORMANCE_OPTIMIZATIONS:
        print("⚡ Preloading common schemas...")
        preload_common_schemas()
        print("✅ Schema preloading complete")
    else:
        print("⚠️ Performance optimizations not available")
    
    print("💡 Press Ctrl+C to stop")
    print("=" * 50)
    
    uvicorn.run(
        "smart_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
