"""
Pydantic models for the Text-to-SQL API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum

class QueryType(str, Enum):
    """Types of SQL queries."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class NaturalLanguageQuery(BaseModel):
    """Natural language query request."""
    question: str = Field(..., description="Natural language question about the student data")

    @validator('question')
    def question_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Question cannot be empty')
        return v.strip()

class SQLQuery(BaseModel):
    """SQL query response."""
    sql: str = Field(..., description="Generated SQL query")
    explanation: str = Field(..., description="Explanation of the SQL query")
    query_type: QueryType = Field(..., description="Type of SQL query")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameters for prepared statement")

class QueryResult(BaseModel):
    """Query execution result."""
    sql: str = Field(..., description="Executed SQL query")
    result: List[Dict[str, Any]] = Field(..., description="Query results")
    row_count: int = Field(..., description="Number of rows returned")
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")
    success: bool = Field(..., description="Whether query executed successfully")
    error_message: Optional[str] = Field(None, description="Error message if query failed")

class SchemaMetadata(BaseModel):
    """Database schema metadata."""
    tables: List[Dict[str, Any]] = Field(..., description="List of tables with their columns")
    relationships: List[Dict[str, Any]] = Field(..., description="Foreign key relationships")
    total_tables: int = Field(..., description="Total number of tables")
    total_columns: int = Field(..., description="Total number of columns")

class AddRecordRequest(BaseModel):
    """Request to add a new record."""
    table_name: str = Field(..., description="Name of the table to insert into")
    data: Dict[str, Any] = Field(..., description="Data to insert")

    @validator('table_name')
    def validate_table_name(cls, v):
        allowed_tables = [
            'students', 'teachers', 'courses', 'enrollments',
            'holidays', 'salaries', 'tuition_payments'
        ]
        if v.lower() not in allowed_tables:
            raise ValueError(f'Table {v} is not allowed. Allowed tables: {allowed_tables}')
        return v.lower()

class AddRecordResponse(BaseModel):
    """Response for adding a record."""
    success: bool = Field(..., description="Whether insertion was successful")
    record_id: Optional[int] = Field(None, description="ID of the inserted record")
    sql: str = Field(..., description="Generated INSERT SQL")
    error_message: Optional[str] = Field(None, description="Error message if insertion failed")

class HealthCheck(BaseModel):
    """Health check response."""
    status: str = Field(..., description="API status")
    database_connected: bool = Field(..., description="Whether database is connected")
    llm_available: bool = Field(..., description="Whether LLM is available")
    timestamp: datetime = Field(..., description="Current timestamp")

class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(..., description="When error occurred")