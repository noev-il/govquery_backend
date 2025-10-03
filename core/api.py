"""
FastAPI application for GovQuery NL2SQL inference.
Provides REST API endpoints for natural language to SQL conversion.
"""

import os
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from .modal_client import get_client, NL2SQLRequest, NL2SQLResponse
except ImportError:
    # Fallback for direct execution
    from modal_client import get_client, NL2SQLRequest, NL2SQLResponse


# FastAPI app
app = FastAPI(
    title="GovQuery NL2SQL API",
    description="Natural Language to SQL conversion for government data queries",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    """Request model for NL2SQL queries."""
    query: str
    table_codes: Optional[List[str]] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.1
    model_choice: Optional[str] = "auto"  # "t5", "sqlcoder", or "auto"


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


class SchemaInfo(BaseModel):
    """Model for schema information."""
    table_code: str
    table_name: str
    geography_levels: List[str]
    columns: List[dict]


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "GovQuery NL2SQL API",
        "version": "1.0.0",
        "endpoints": {
            "query": "/query - Convert natural language to SQL",
            "schemas": "/schemas - List available schemas",
            "schema": "/schema/{table_code} - Get specific schema",
            "health": "/health - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        client = get_client()
        # Try to load schemas to verify setup
        schemas = client.load_all_schemas()
        return {
            "status": "healthy",
            "schemas_loaded": len(schemas),
            "modal_app": os.getenv("MODAL_APP_NAME", "not_configured")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/schemas", response_model=List[SchemaInfo])
async def list_schemas():
    """List all available schemas."""
    try:
        client = get_client()
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
        client = get_client()
        schema = client.load_schema(table_code)
        return schema
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Schema {table_code} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading schema: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def convert_to_sql(request: QueryRequest):
    """
    Convert natural language query to SQL.
    
    Args:
        request: QueryRequest with natural language query and optional parameters
        
    Returns:
        QueryResponse with generated SQL and metadata
    """
    try:
        client = get_client()
        
        # Perform inference
        response = await client.infer_sql(
            query=request.query,
            table_codes=request.table_codes,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            model_choice=request.model_choice
        )
        
        # Determine which schemas were used
        schema_context_used = request.table_codes
        if schema_context_used is None:
            # If no specific tables requested, all schemas were used
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
            auto_selected=response.auto_selected
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/query/sync", response_model=QueryResponse)
async def convert_to_sql_sync(request: QueryRequest):
    """
    Synchronous version of convert_to_sql.
    Use this if you prefer synchronous Modal calls.
    """
    try:
        client = get_client()
        
        # Perform inference synchronously
        response = client.infer_sql_sync(
            query=request.query,
            table_codes=request.table_codes,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            model_choice=request.model_choice
        )
        
        # Determine which schemas were used
        schema_context_used = request.table_codes
        if schema_context_used is None:
            # If no specific tables requested, all schemas were used
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
            auto_selected=response.auto_selected
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
