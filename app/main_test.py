"""
FastAPI application for Student Management Text-to-SQL API (Test Version).
This version uses test LLM service instead of trying to load the actual model.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.config import settings
from app.models import (
    NaturalLanguageQuery, SQLQuery, QueryResult, SchemaMetadata,
    AddRecordRequest, AddRecordResponse, HealthCheck, ErrorResponse
)
from app.database import db_service
from app.llm_service_test import llm_service_test as llm_service

# Create FastAPI app
app = FastAPI(
    title=settings.api_title + " (Test)",
    description=settings.api_description + " - Using test LLM service",
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Student Management Text-to-SQL API (Test Version)",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    db_health = db_service.health_check()
    llm_health = llm_service.health_check()

    return HealthCheck(
        status="healthy" if db_health.get('database_connected') and llm_health.get('llm_available') else "unhealthy",
        database_connected=db_health.get('database_connected', False),
        llm_available=llm_health.get('llm_available', False),
        timestamp=datetime.now()
    )


@app.get("/schema", response_model=SchemaMetadata)
async def get_schema():
    """Get database schema metadata."""
    return db_service.get_schema_metadata()


@app.post("/ask-query", response_model=QueryResult)
async def ask_query(query: NaturalLanguageQuery):
    """
    Convert natural language question to SQL and execute it.

    This endpoint:
    1. Converts the natural language question to SQL using LLM
    2. Executes the generated SQL query
    3. Returns the results with metadata
    """
    try:
        # Get schema metadata
        schema_metadata = db_service.get_schema_metadata()

        # Generate SQL from natural language
        sql_query = llm_service.generate_sql(query.question, schema_metadata)

        # Execute the generated SQL
        result = db_service.execute_query(sql_query.sql)

        return QueryResult(
            sql=sql_query.sql,
            result=result.result,
            row_count=result.row_count,
            execution_time_ms=result.execution_time_ms,
            success=result.success,
            error_message=result.error_message,
            timestamp=datetime.now(),
            explanation=sql_query.explanation,
            query_type=sql_query.query_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


@app.post("/debug/generate-sql", response_model=SQLQuery)
async def debug_generate_sql(query: NaturalLanguageQuery):
    """
    Debug endpoint: Generate SQL from natural language without executing.

    Useful for testing the LLM's SQL generation capabilities.
    """
    try:
        schema_metadata = db_service.get_schema_metadata()
        return llm_service.generate_sql(query.question, schema_metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate SQL: {str(e)}")


@app.post("/debug/execute-sql", response_model=QueryResult)
async def debug_execute_sql(sql_query: SQLQuery):
    """
    Debug endpoint: Execute a raw SQL query.

    Useful for testing SQL queries directly.
    """
    try:
        return db_service.execute_query(sql_query.sql)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute SQL: {str(e)}")


@app.post("/add-record", response_model=AddRecordResponse)
async def add_record(request: AddRecordRequest):
    """
    Add a new record to a specified table.

    This endpoint allows adding records to any table in the database.
    The data must match the table's schema.
    """
    try:
        success, record_id, sql_or_error = db_service.add_record(request.table_name, request.data)
        if success:
            return AddRecordResponse(
                success=True,
                record_id=record_id,
                sql=sql_or_error,
                error_message=None
            )
        else:
            return AddRecordResponse(
                success=False,
                record_id=None,
                sql="",
                error_message=sql_or_error
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add record: {str(e)}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global exception handler for HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc.detail) if exc.detail else None,
            timestamp=datetime.now()
        ).model_dump()
    )


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("Test Server - Student Management Text-to-SQL API")
    print("Using test LLM service with mock responses")
    print("=" * 50)
    print("API Documentation:")
    print("  - Swagger UI: http://localhost:8002/docs")
    print("  - ReDoc: http://localhost:8002/redoc")
    print("  - Health check: http://localhost:8002/health")
    print("\nPress Ctrl+C to stop the server.\n")

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")