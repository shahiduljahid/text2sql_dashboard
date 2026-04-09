"""
FastAPI application for Student Management Text-to-SQL API.
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
from app.llm_service import LLMService
llm_service = LLMService()

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    # Browsers reject '*' origin when credentials are allowed.
    # We don't use cookie/session auth here, so keep credentials disabled.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Student Management Text-to-SQL API",
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
    try:
        return db_service.get_schema_metadata()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schema: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get dashboard statistics."""
    try:
        stats = db_service.get_stats()
        if not stats.get('success'):
            raise HTTPException(status_code=500, detail=stats.get('error', 'Failed to get stats'))
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.get("/table/{table_name}")
async def get_table_data(table_name: str, page: int = 1, page_size: int = 50):
    """Get paginated data from a table."""
    try:
        result = db_service.get_table_data(table_name, page, page_size)

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to get table data'))

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table data: {str(e)}")


@app.post("/add-record", response_model=AddRecordResponse)
async def add_record(request: AddRecordRequest):
    """Add a new record to the database."""
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


@app.post("/ask-query", response_model=QueryResult)
async def ask_query(request: NaturalLanguageQuery):
    """
    Convert natural language question to SQL and execute it.

    Steps:
    1. Get database schema
    2. Use LLM to generate SQL from natural language question
    3. Validate and execute SQL
    4. Return results
    """
    try:
        # Step 1: Get schema
        schema = db_service.get_schema_metadata()

        # Step 2: Generate SQL using LLM
        sql_query = llm_service.generate_sql(
            question=request.question,
            schema_metadata=schema
        )

        # Step 3: Execute SQL
        result = db_service.execute_query(sql_query.sql, sql_query.parameters)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


@app.post("/debug/generate-sql", response_model=SQLQuery)
async def debug_generate_sql(request: NaturalLanguageQuery):
    """
    Debug endpoint: Generate SQL without executing it.
    Useful for testing LLM SQL generation.
    """
    try:
        schema = db_service.get_schema_metadata()
        sql_query = llm_service.generate_sql(
            question=request.question,
            schema_metadata=schema
        )
        return sql_query
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate SQL: {str(e)}")


@app.post("/debug/execute-sql", response_model=QueryResult)
async def debug_execute_sql(sql: str):
    """
    Debug endpoint: Execute raw SQL directly.
    WARNING: Bypasses LLM generation, only for testing.
    """
    try:
        result = db_service.execute_query(sql)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute SQL: {str(e)}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc.detail) if exc.detail else None,
            timestamp=datetime.now()
        ).model_dump(mode="json")
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)