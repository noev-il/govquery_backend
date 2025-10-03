"""
Modal client for NL2SQL model inference.
Handles connection to Modal-hosted models and schema management.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import modal
from pydantic import BaseModel


class NL2SQLRequest(BaseModel):
    """Request model for NL2SQL inference."""
    query: str
    schema_context: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.1
    model_choice: Optional[str] = "auto"  # "t5", "sqlcoder", or "auto"


class NL2SQLResponse(BaseModel):
    """Response model for NL2SQL inference."""
    sql_query: str
    confidence: Optional[float] = None
    explanation: Optional[str] = None
    error: Optional[str] = None
    model_used: Optional[str] = None
    prompt_length: Optional[int] = None
    auto_selected: Optional[bool] = None


class ModalNL2SQLClient:
    """Client for interacting with Modal-hosted NL2SQL models."""
    
    def __init__(self, app_name: str, function_name: str = "nl2sql_inference"):
        """
        Initialize Modal client.
        
        Args:
            app_name: Name of your Modal app
            function_name: Name of the inference function in your Modal app
        """
        self.app_name = app_name
        self.function_name = function_name
        self.schemas_dir = Path(__file__).parent.parent / "schemas"
        self._app = None
        self._function = None
        self._query_function = None  # For the simple query function
        
    def _get_modal_app(self):
        """Get or create Modal app connection."""
        if self._app is None:
            # Initialize Modal client
            try:
                # Try without specifying environment first
                self._app = modal.App.lookup(self.app_name, create_if_missing=False)
            except Exception as e:
                print(f"App '{self.app_name}' not found. Trying alternative app names...")
                # Try alternative app names
                alternative_names = ["govquery-nl2sql-main", "govquery-nl2sql"]
                for alt_name in alternative_names:
                    try:
                        self._app = modal.App.lookup(alt_name, create_if_missing=False)
                        print(f"  Using app: {alt_name}")
                        return self._app
                    except:
                        continue
                print(f"\n💡 To deploy the app, run: python deploy_modal.py")
                raise e
        return self._app
    
    def _get_modal_function(self):
        """Get Modal function reference."""
        if self._function is None:
            # Use app-based lookup first
            app = self._get_modal_app()
            try:
                # Try direct attribute access first
                self._function = getattr(app, self.function_name)
            except AttributeError:
                # Try using the function method
                try:
                    self._function = app.function(self.function_name)
                except Exception as e2:
                    # Try accessing from registered_functions
                    if hasattr(app, 'registered_functions') and self.function_name in app.registered_functions:
                        self._function = app.registered_functions[self.function_name]
                    else:
                        # Fallback to modal.Function.from_name
                        try:
                            self._function = modal.Function.from_name(self.app_name, self.function_name)
                        except Exception as e3:
                            raise AttributeError(f"Function '{self.function_name}' not found in app. Available functions: {list(app.registered_functions.keys()) if hasattr(app, 'registered_functions') else 'None'}")
        return self._function
    
    def _get_query_function(self):
        """Get Modal query function reference."""
        if self._query_function is None:
            # Use app-based lookup first
            app = self._get_modal_app()
            try:
                # Try direct attribute access first
                self._query_function = getattr(app, "query")
            except AttributeError:
                # Try using the function method
                try:
                    self._query_function = app.function("query")
                except Exception as e2:
                    # Try accessing from registered_functions
                    if hasattr(app, 'registered_functions') and "query" in app.registered_functions:
                        self._query_function = app.registered_functions["query"]
                    else:
                        # Fallback to modal.Function.from_name
                        try:
                            self._query_function = modal.Function.from_name(self.app_name, "query")
                        except Exception as e3:
                            raise AttributeError(f"Function 'query' not found in app. Available functions: {list(app.registered_functions.keys()) if hasattr(app, 'registered_functions') else 'None'}")
        return self._query_function
    
    def load_schema(self, table_code: str) -> Dict[str, Any]:
        """
        Load schema for a specific table.
        
        Args:
            table_code: ACS table code (e.g., 'B01001')
            
        Returns:
            Schema dictionary
        """
        schema_path = self.schemas_dir / f"{table_code}.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            return json.load(f)
    
    def load_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all available schemas.
        
        Returns:
            Dictionary mapping table codes to schema dictionaries
        """
        schemas = {}
        for schema_file in self.schemas_dir.glob("*.json"):
            table_code = schema_file.stem
            schemas[table_code] = self.load_schema(table_code)
        return schemas
    
    def get_schema_context(self, table_codes: Optional[List[str]] = None) -> str:
        """
        Generate schema context string for NL2SQL model.
        
        Args:
            table_codes: List of table codes to include. If None, includes all.
            
        Returns:
            Formatted schema context string
        """
        if table_codes is None:
            schemas = self.load_all_schemas()
        else:
            schemas = {code: self.load_schema(code) for code in table_codes}
        
        context_parts = []
        for table_code, schema in schemas.items():
            # Add table description
            context_parts.append(f"Table: {table_code} - {schema['table_name']}")
            
            # Add DDL
            context_parts.append(f"Schema:\n{schema['sql_ddl']}")
            
            # Add column descriptions
            context_parts.append("Column descriptions:")
            for col in schema['columns']:
                context_parts.append(f"  {col['name']} ({col['type']}): {col['description']}")
            
            # Add example row
            if 'example_row' in schema:
                context_parts.append(f"Example data: {schema['example_row']}")
            
            context_parts.append("")  # Empty line between tables
        
        return "\n".join(context_parts)
    
    async def infer_sql(self, 
                       query: str, 
                       table_codes: Optional[List[str]] = None,
                       max_tokens: int = 512,
                       temperature: float = 0.1,
                       model_choice: str = "auto") -> NL2SQLResponse:
        """
        Generate SQL from natural language query.
        
        Args:
            query: Natural language query
            table_codes: List of table codes to consider. If None, uses all.
            max_tokens: Maximum tokens for generation
            temperature: Sampling temperature
            model_choice: "t5", "sqlcoder", or "auto" for automatic selection
            
        Returns:
            NL2SQLResponse with generated SQL
        """
        try:
            # Get schema context
            schema_context = self.get_schema_context(table_codes)
            
            # Prepare request
            request = NL2SQLRequest(
                query=query,
                schema_context={"context": schema_context},
                max_tokens=max_tokens,
                temperature=temperature,
                model_choice=model_choice
            )
            
            # Call Modal function
            function = self._get_modal_function()
            result = await function.remote.aio(
                question=request.query,
                schema_context=request.schema_context,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                model_choice=request.model_choice
            )
            
            return NL2SQLResponse(**result)
            
        except Exception as e:
            return NL2SQLResponse(
                sql_query="",
                error=f"Error during inference: {str(e)}"
            )
    
    def infer_sql_sync(self, 
                      query: str, 
                      table_codes: Optional[List[str]] = None,
                      max_tokens: int = 512,
                      temperature: float = 0.1,
                      model_choice: str = "auto") -> NL2SQLResponse:
        """
        Synchronous version of infer_sql.
        
        Args:
            query: Natural language query
            table_codes: List of table codes to consider. If None, uses all.
            max_tokens: Maximum tokens for generation
            temperature: Sampling temperature
            model_choice: "t5", "sqlcoder", or "auto" for automatic selection
            
        Returns:
            NL2SQLResponse with generated SQL
        """
        try:
            # Get schema context
            schema_context = self.get_schema_context(table_codes)
            
            # Prepare request
            request = NL2SQLRequest(
                query=query,
                schema_context={"context": schema_context},
                max_tokens=max_tokens,
                temperature=temperature,
                model_choice=model_choice
            )
            
            # Call Modal function synchronously
            function = self._get_modal_function()
            result = function.remote(
                question=request.query,
                schema_context=request.schema_context,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                model_choice=request.model_choice
            )
            
            # Convert result to NL2SQLResponse
            if isinstance(result, dict):
                return NL2SQLResponse(**result)
            else:
                # If result is not a dict, it might be a Modal result object
                return NL2SQLResponse(
                    sql_query=getattr(result, 'sql_query', ''),
                    confidence=getattr(result, 'confidence', 0.0),
                    explanation=getattr(result, 'explanation', ''),
                    error=getattr(result, 'error', ''),
                    model_used=getattr(result, 'model_used', ''),
                    prompt_length=getattr(result, 'prompt_length', 0),
                    auto_selected=getattr(result, 'auto_selected', False)
                )
            
        except Exception as e:
            return NL2SQLResponse(
                sql_query="",
                error=f"Error during inference: {str(e)}"
            )
    
    def query_simple(self, table_code: str, question: str, force_model: Optional[str] = None) -> Dict[str, Any]:
        """
        Simple query function that matches your notebook query() function.
        
        Args:
            table_code: ACS table code (e.g., "B01001")
            question: Natural language question
            force_model: "t5", "sqlcoder", or None for auto
            
        Returns:
            Dictionary with SQL and metadata (matches notebook format)
        """
        try:
            # Call Modal query function
            query_func = self._get_query_function()
            result = query_func.remote(table_code, question, force_model)
            
            return result
            
        except Exception as e:
            return {
                "model": "error",
                "sql": "",
                "meta": {"error": str(e)},
                "table": table_code,
                "question": question
            }


# Global client instance
_client: Optional[ModalNL2SQLClient] = None


def get_client() -> ModalNL2SQLClient:
    """Get or create global Modal client instance."""
    global _client
    if _client is None:
        app_name = os.getenv("MODAL_APP_NAME", "govquery-nl2sql")
        function_name = os.getenv("MODAL_FUNCTION_NAME", "nl2sql_inference")
        _client = ModalNL2SQLClient(app_name, function_name)
    return _client
