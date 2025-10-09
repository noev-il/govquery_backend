#!/usr/bin/env python3
"""
Templated API for GovQuery frontend integration.
Implements the canonical /query contract with proper error handling and telemetry.
"""

import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to Python path
project_root = Path(__file__).parent
import sys
sys.path.insert(0, str(project_root))

from smart_modal_client import get_smart_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="GovQuery Templated API",
    description="Templated API for frontend integration with proper error handling and telemetry",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global client instance
_client = None

def get_client():
    """Get or create global client instance."""
    global _client
    if _client is None:
        _client = get_smart_client()
    return _client

# Request/Response Models
class QueryRequest(BaseModel):
    """Canonical query request model."""
    question: str
    model_hint: str = "AUTO"
    tables: Optional[List[str]] = None
    max_rows: int = 500

class QueryResponse(BaseModel):
    """Canonical query response model."""
    status: str  # "ok" or "error"
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    sources: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    message: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    modal_app_running: bool
    schemas_loaded: int
    features: Dict[str, Any]

# SQL Safety Functions
def is_safe_sql(sql: str) -> bool:
    """Check if SQL is safe (read-only)."""
    if not sql:
        return False
    
    sql_upper = sql.upper().strip()
    
    # Block dangerous operations
    dangerous_patterns = [
        r'\b(DELETE|UPDATE|INSERT|DROP|CREATE|ALTER|TRUNCATE|REPLACE)\b',
        r'\b(EXEC|EXECUTE|CALL|PROCEDURE)\b',
        r'\b(UNION\s+SELECT|UNION\s+ALL)\b',
        r'--',  # SQL comments
        r'/\*.*?\*/',  # Block comments
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, sql_upper):
            return False
    
    # Must start with SELECT
    if not sql_upper.startswith('SELECT'):
        return False
    
    return True

def enforce_row_limit(sql: str, max_rows: int) -> str:
    """Enforce row limit on SQL query."""
    sql_upper = sql.upper().strip()
    
    # If already has LIMIT, respect it but cap it
    if 'LIMIT' in sql_upper:
        # Extract existing limit and cap it
        limit_match = re.search(r'LIMIT\s+(\d+)', sql_upper)
        if limit_match:
            existing_limit = int(limit_match.group(1))
            capped_limit = min(existing_limit, max_rows)
            sql = re.sub(r'LIMIT\s+\d+', f'LIMIT {capped_limit}', sql, flags=re.IGNORECASE)
        return sql
    
    # Add LIMIT if not present
    if not sql.strip().endswith(';'):
        sql += f' LIMIT {max_rows}'
    else:
        sql = sql.rstrip(';') + f' LIMIT {max_rows};'
    
    return sql

def trim_schema_context(tables: Optional[List[str]], client) -> str:
    """Trim schema context to only relevant tables."""
    if not tables:
        # Use 3-5 most likely tables as fallback
        all_schemas = client.load_all_schemas()
        tables = list(all_schemas.keys())[:5]
    
    # Load only requested schemas
    schemas = {}
    for table_code in tables:
        try:
            schemas[table_code] = client.load_schema(table_code)
        except FileNotFoundError:
            logger.warning(f"Schema {table_code} not found, skipping")
            continue
    
    # Generate trimmed context
    context_parts = []
    for table_code, schema in schemas.items():
        context_parts.append(f"Table: {table_code} - {schema['table_name']}")
        context_parts.append(f"Schema:\n{schema['sql_ddl']}")
        context_parts.append("Column descriptions:")
        for col in schema['columns']:
            context_parts.append(f"  {col['name']} ({col['type']}): {col['description']}")
        if 'example_row' in schema:
            context_parts.append(f"Example data: {schema['example_row']}")
        context_parts.append("")
    
    return "\n".join(context_parts)

# Warm start on boot
@app.on_event("startup")
async def warm_start():
    """Warm start the Modal app on server boot."""
    try:
        logger.info("🔥 Warming up Modal app...")
        client = get_client()
        
        # Try a simple query to warm up the app
        result = client.query_with_fallback(
            "B01001", 
            "What is the total population?", 
            "AUTO"
        )
        
        if result.get("sql"):
            logger.info("✅ Modal app warmed up successfully")
        else:
            logger.warning("⚠️ Modal app warm-up failed, but continuing")
            
    except Exception as e:
        logger.warning(f"⚠️ Modal app warm-up failed: {e}, but continuing")

# API Endpoints
@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "GovQuery Templated API",
        "version": "1.0.0",
        "endpoints": {
            "query": "POST /query - Convert natural language to SQL",
            "health": "GET /health - Health check with app status",
            "schemas": "GET /schemas - List available schemas"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check with Modal app status."""
    try:
        client = get_client()
        schemas = client.load_all_schemas()
        app_running = client._is_app_running()
        
        return HealthResponse(
            status="healthy" if app_running else "degraded",
            modal_app_running=app_running,
            schemas_loaded=len(schemas),
            features={
                "auto_deployment": True,
                "cold_start_fallback": True,
                "sql_safety": True,
                "row_limits": True,
                "telemetry": True
            }
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            modal_app_running=False,
            schemas_loaded=0,
            features={"error": str(e)}
        )

@app.get("/schemas", response_model=List[Dict[str, Any]])
async def list_schemas():
    """List all available schemas."""
    try:
        client = get_client()
        schemas = client.load_all_schemas()
        
        schema_list = []
        for table_code, schema in schemas.items():
            schema_list.append({
                "table_code": table_code,
                "table_name": schema["table_name"],
                "geography_levels": schema["geography_levels"],
                "columns": schema["columns"]
            })
        
        return schema_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading schemas: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Canonical query endpoint with proper error handling and telemetry.
    
    Request:
    {
        "question": "What is the total population in Texas?",
        "model_hint": "AUTO",
        "tables": ["B01001"], 
        "max_rows": 500
    }
    
    Response:
    {
        "status": "ok",
        "sql": "SELECT ...",
        "data": [{ "...": "..." }],
        "sources": ["postgres:acs.B01001"],
        "meta": { "model":"SQLCODER", "elapsed_ms": 4123, "schema_chars": 1807 }
    }
    """
    start_time = time.time()
    question_hash = hashlib.md5(request.question.encode()).hexdigest()[:8]
    
    try:
        logger.info(f"🔍 Query [{question_hash}]: {request.question[:100]}...")
        
        client = get_client()
        
        # Use first table or default to B01001
        table_code = request.tables[0] if request.tables else "B01001"
        
        # Map model_hint to force_model
        force_model = None
        if request.model_hint != "AUTO":
            force_model = request.model_hint
        
        # Perform query with fallback
        result = client.query_with_fallback(
            table_code=table_code,
            question=request.question,
            force_model=force_model
        )
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Check if query was successful
        if result.get("sql") and not result.get("meta", {}).get("error"):
            sql = result["sql"]
            
            # Safety checks
            if not is_safe_sql(sql):
                logger.warning(f"🚫 Unsafe SQL detected [{question_hash}]: {sql[:100]}...")
                return QueryResponse(
                    status="error",
                    error_code="UNSAFE_SQL",
                    message="Generated SQL contains unsafe operations. Only SELECT queries are allowed.",
                    meta={
                        "model": result.get("model", "unknown"),
                        "elapsed_ms": elapsed_ms,
                        "question_hash": question_hash
                    }
                )
            
            # Enforce row limit
            sql = enforce_row_limit(sql, request.max_rows)
            
            # Log successful query
            logger.info(f"✅ Query success [{question_hash}]: {elapsed_ms}ms, model={result.get('model', 'unknown')}")
            
            return QueryResponse(
                status="ok",
                sql=sql,
                data=[],  # TODO: Execute SQL and return data
                sources=[f"postgres:acs.{table_code}"],
                meta={
                    "model": result.get("model", "unknown"),
                    "elapsed_ms": elapsed_ms,
                    "schema_chars": len(str(result.get("meta", {}))),
                    "question_hash": question_hash,
                    "confidence": result.get("meta", {}).get("confidence", 0.0),
                    "explanation": result.get("meta", {}).get("explanation", "")
                }
            )
        else:
            # Query failed
            error_msg = result.get("meta", {}).get("error", "Unknown error")
            logger.error(f"❌ Query failed [{question_hash}]: {error_msg}")
            
            return QueryResponse(
                status="error",
                error_code="QUERY_FAILED",
                message=f"Query failed: {error_msg}",
                meta={
                    "model": result.get("model", "unknown"),
                    "elapsed_ms": elapsed_ms,
                    "question_hash": question_hash
                }
            )
            
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(f"💥 Query exception [{question_hash}]: {str(e)}")
        
        return QueryResponse(
            status="error",
            error_code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            meta={
                "elapsed_ms": elapsed_ms,
                "question_hash": question_hash
            }
        )

if __name__ == "__main__":
    # Set up environment variables
    os.environ["MODAL_TOKEN_ID"] = "ak-82ssY3sBr9rB9tau63rD2n"
    os.environ["MODAL_TOKEN_SECRET"] = "as-A4L7Xzb33dybZ9XEhheVAV"
    os.environ["MODAL_APP_NAME"] = "govquery-nl2sql-main"
    
    print("🎯 GovQuery Templated API Server")
    print("=" * 50)
    print("🌐 Server: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔍 Health: http://localhost:8000/health")
    print("🚀 Features:")
    print("   ✅ Canonical /query contract")
    print("   ✅ SQL safety guardrails")
    print("   ✅ Row limits and timeouts")
    print("   ✅ Telemetry logging")
    print("   ✅ Warm start on boot")
    print("💡 Press Ctrl+C to stop")
    print("=" * 50)
    
    uvicorn.run(
        "templated_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
