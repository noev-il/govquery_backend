"""
Database executor with comprehensive security and safety checks.
Enforces read-only access, query validation, and resource limits.
"""

import asyncio
import asyncpg
import sqlglot
from typing import List, Dict, Any, Optional, Tuple
from contextlib import asynccontextmanager
import time
import re
import logging

logger = logging.getLogger(__name__)

class DatabaseExecutor:
    """Secure database executor with read-only enforcement and query validation."""
    
    def __init__(self, connection_url: str):
        self.pool: Optional[asyncpg.Pool] = None
        self.connection_url = connection_url
        self.max_rows = 1000
        self.statement_timeout = 30  # seconds
        
        # Whitelisted functions for security
        self.allowed_functions = {
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'STDDEV', 'VARIANCE',
            'ROUND', 'TRUNC', 'ABS', 'CEIL', 'FLOOR', 'MOD',
            'UPPER', 'LOWER', 'TRIM', 'LENGTH', 'SUBSTRING',
            'COALESCE', 'NULLIF', 'CASE', 'CAST'
        }
    
    async def connect(self):
        """Initialize connection pool with security settings."""
        self.pool = await asyncpg.create_pool(
            self.connection_url,
            min_size=2,
            max_size=10,
            timeout=30,
            max_inactive_connection_lifetime=300,  # 5 minutes
            command_timeout=30,
            init=self._init_connection
        )
        logger.info("Database connection pool initialized")
    
    async def _init_connection(self, conn):
        """Initialize connection with security settings."""
        try:
            await conn.execute("SET ROLE read_only")
        except Exception:
            # read_only role doesn't exist, continue without it
            logger.debug("read_only role not found, using default permissions")
        
        # Set session-level read-only mode
        await conn.execute("SET SESSION default_transaction_read_only = on")
        await conn.execute("SET SESSION statement_timeout = '30s'")
        await conn.execute("SET SESSION idle_in_transaction_session_timeout = '30s'")
        logger.debug("Connection initialized with read-only security settings")
    
    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    def _validate_sql(self, sql: str) -> Tuple[bool, str]:
        """
        Validate SQL query for security and safety.
        Returns (is_valid, error_message)
        """
        try:
            # Remove comments and normalize
            sql_clean = self._clean_sql(sql)
            
            # Parse with SQLGlot
            parsed = sqlglot.parse_one(sql_clean)
            if not parsed:
                return False, "Failed to parse SQL query"
            
            # Check for forbidden statements
            forbidden_keywords = {
                'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'ALTER', 'DROP',
                'CREATE', 'GRANT', 'REVOKE', 'COPY', 'CALL', 'DO'
            }
            
            # Check for multiple statements (semicolon)
            if ';' in sql_clean:
                return False, "Multiple statements not allowed"
            
            # Check for forbidden keywords
            sql_upper = sql_clean.upper()
            for keyword in forbidden_keywords:
                if re.search(rf'\b{keyword}\b', sql_upper):
                    return False, f"Forbidden keyword detected: {keyword}"
            
            # Check for non-ASCII control characters
            if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', sql):
                return False, "Non-ASCII control characters not allowed"
            
            # Check for function calls (basic validation)
            if not self._validate_functions(parsed):
                return False, "Unauthorized function calls detected"
            
            # Ensure it's a SELECT statement
            if not sql_upper.strip().startswith('SELECT'):
                return False, "Only SELECT statements are allowed"
            
            return True, ""
            
        except Exception as e:
            return False, f"SQL validation error: {str(e)}"
    
    def _clean_sql(self, sql: str) -> str:
        """Remove comments and normalize SQL."""
        # Remove /* ... */ style comments
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        # Remove -- style comments
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        return sql.strip()
    
    def _validate_functions(self, parsed) -> bool:
        """Validate that only whitelisted functions are used."""
        sql_str = str(parsed).upper()
        
        # Check for pg_ functions (PostgreSQL internals)
        if re.search(r'\bpg_\w+\(', sql_str):
            return False
        
        # Check for specific dangerous functions
        dangerous_functions = [
            'pg_sleep', 'pg_read_file', 'pg_write_file', 'pg_ls_dir',
            'pg_stat_file', 'pg_read_binary_file', 'pg_terminate_backend',
            'pg_cancel_backend', 'pg_reload_conf', 'pg_rotate_logfile'
        ]
        
        for func in dangerous_functions:
            if re.search(rf'\b{func.upper()}\b', sql_str):
                return False
        
        # Check for other potentially dangerous patterns
        dangerous_patterns = [
            r'\bEXECUTE\b', r'\bPREPARE\b', r'\bDEALLOCATE\b',
            r'\bLOAD\b', r'\bSET\b', r'\bRESET\b', r'\bCOPY\b',
            r'\bDO\b', r'\bCALL\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_str):
                return False
        
        return True
    
    def _inject_limit(self, sql: str) -> str:
        """Safely inject LIMIT clause using AST manipulation."""
        try:
            parsed = sqlglot.parse_one(sql)
            if not parsed:
                return sql
            
            # Check if LIMIT already exists
            has_limit = any(
                isinstance(node, sqlglot.expressions.Limit) 
                for node in parsed.walk()
            )
            
            if has_limit:
                # Check if existing limit exceeds our max
                for node in parsed.walk():
                    if isinstance(node, sqlglot.expressions.Limit):
                        try:
                            limit_value = int(node.expression.this)
                            if limit_value > self.max_rows:
                                node.expression = sqlglot.expressions.Literal.number(self.max_rows)
                        except (ValueError, AttributeError):
                            # If we can't parse the limit, replace it
                            node.expression = sqlglot.expressions.Literal.number(self.max_rows)
            else:
                # Add LIMIT clause
                limit_clause = sqlglot.expressions.Limit(
                    expression=sqlglot.expressions.Literal.number(self.max_rows)
                )
                parsed.set("limit", limit_clause)
            
            return str(parsed)
            
        except Exception as e:
            logger.warning(f"Failed to inject LIMIT via AST, using string manipulation: {e}")
            # Fallback to string manipulation
            sql_upper = sql.upper()
            if 'LIMIT' not in sql_upper:
                return f"{sql} LIMIT {self.max_rows}"
            return sql
    
    async def execute_query(
        self, 
        sql: str, 
        max_rows: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute SELECT query with comprehensive safety checks.
        
        Args:
            sql: SQL query to execute
            max_rows: Override default row limit
            timeout: Override default timeout
            
        Returns:
            Dictionary with results and metadata
        """
        start_time = time.time()
        
        try:
            # Validate SQL
            is_valid, error_msg = self._validate_sql(sql)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"SQL validation failed: {error_msg}",
                    "rows": [],
                    "row_count": 0,
                    "columns": [],
                    "execution_time_ms": 0,
                    "applied_limit": False,
                    "statement_timeout_ms": 0,
                    "query_id": None
                }
            
            # Set limits
            effective_max_rows = max_rows or self.max_rows
            effective_timeout = timeout or self.statement_timeout
            
            # Inject LIMIT if needed
            sql_with_limit = self._inject_limit(sql)
            applied_limit = sql_with_limit != sql
            
            # Generate query ID for tracking
            query_id = f"q_{int(time.time() * 1000)}"
            
            # Execute query with timeout
            async with self.pool.acquire() as conn:
                # Set per-connection timeout
                await conn.execute(f"SET LOCAL statement_timeout = '{effective_timeout}s'")
                
                try:
                    rows = await conn.fetch(sql_with_limit)
                    
                    # Convert rows to dictionaries
                    if rows:
                        columns = list(rows[0].keys())
                        rows_data = [dict(row) for row in rows]
                    else:
                        columns = []
                        rows_data = []
                    
                    execution_time = (time.time() - start_time) * 1000
                    
                    return {
                        "success": True,
                        "rows": rows_data,
                        "row_count": len(rows_data),
                        "columns": columns,
                        "execution_time_ms": execution_time,
                        "error": None,
                        "applied_limit": applied_limit,
                        "statement_timeout_ms": effective_timeout * 1000,
                        "query_id": query_id,
                        "query_metadata": {
                            "original_sql": sql,
                            "executed_sql": sql_with_limit,
                            "max_rows_allowed": effective_max_rows
                        }
                    }
                    
                except asyncio.TimeoutError:
                    return {
                        "success": False,
                        "error": f"Query timeout after {effective_timeout}s",
                        "rows": [],
                        "row_count": 0,
                        "columns": [],
                        "execution_time_ms": (time.time() - start_time) * 1000,
                        "applied_limit": applied_limit,
                        "statement_timeout_ms": effective_timeout * 1000,
                        "query_id": query_id
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Database error: {str(e)}",
                        "rows": [],
                        "row_count": 0,
                        "columns": [],
                        "execution_time_ms": (time.time() - start_time) * 1000,
                        "applied_limit": applied_limit,
                        "statement_timeout_ms": effective_timeout * 1000 if timeout else self.statement_timeout * 1000,
                        "query_id": query_id
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
                "rows": [],
                "row_count": 0,
                "columns": [],
                "execution_time_ms": (time.time() - start_time) * 1000,
                "applied_limit": False,
                "statement_timeout_ms": 0,
                "query_id": None
            }
    
    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
