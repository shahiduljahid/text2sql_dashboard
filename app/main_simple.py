"""
Simplified FastAPI application for testing without LLM dependencies.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sqlite3

# Models
class NaturalLanguageQuery(BaseModel):
    query: str

class SQLQuery(BaseModel):
    sql: str

class QueryResult(BaseModel):
    sql: str
    result: List[Dict[str, Any]]
    row_count: int
    columns: List[str]
    execution_time_ms: float
    timestamp: datetime

class SchemaMetadata(BaseModel):
    tables: List[str]
    table_count: int
    total_records: int
    timestamp: datetime

class AddRecordRequest(BaseModel):
    table_name: str
    data: Dict[str, Any]

class AddRecordResponse(BaseModel):
    success: bool
    record_id: Optional[int] = None
    message: Optional[str] = None
    timestamp: datetime

class HealthCheck(BaseModel):
    status: str
    database_connected: bool
    llm_available: bool = False
    timestamp: datetime

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime

# Database service
class DatabaseService:
    def __init__(self, db_path="student_management.db"):
        self.db_path = db_path

    def health_check(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("SELECT 1")
            conn.close()
            return {"database_connected": True}
        except:
            return {"database_connected": False}

    def get_schema_metadata(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]

            # Get total records
            total_records = 0
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    total_records += count
                except:
                    continue

            conn.close()

            return SchemaMetadata(
                tables=tables,
                table_count=len(tables),
                total_records=total_records,
                timestamp=datetime.now()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get schema: {str(e)}")

    def execute_query(self, sql: str):
        try:
            import time
            start_time = time.time()

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(sql)

            if sql.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
                columns = [description[0] for description in cursor.description] if cursor.description else []
            else:
                conn.commit()
                result = []
                columns = []

            conn.close()

            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            return QueryResult(
                sql=sql,
                result=result,
                row_count=len(result),
                columns=columns,
                execution_time_ms=execution_time,
                timestamp=datetime.now()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to execute SQL: {str(e)}")

    def add_record(self, table_name: str, data: Dict[str, Any]):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build INSERT query
            columns = list(data.keys())
            placeholders = ["?" for _ in columns]
            values = list(data.values())

            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

            cursor.execute(sql, values)
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return AddRecordResponse(
                success=True,
                record_id=record_id,
                message=f"Record added to {table_name}",
                timestamp=datetime.now()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add record: {str(e)}")

# Create FastAPI app
app = FastAPI(
    title="Student Management Text-to-SQL API (Simple Test)",
    description="Simplified version without LLM dependencies",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db_service = DatabaseService()

@app.get("/")
async def root():
    return {
        "message": "Student Management Text-to-SQL API (Simple Test)",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    db_health = db_service.health_check()

    return HealthCheck(
        status="healthy" if db_health.get('database_connected') else "unhealthy",
        database_connected=db_health.get('database_connected', False),
        llm_available=False,
        timestamp=datetime.now()
    )

@app.get("/schema", response_model=SchemaMetadata)
async def get_schema():
    return db_service.get_schema_metadata()

@app.post("/ask-query", response_model=QueryResult)
async def ask_query(query: NaturalLanguageQuery):
    # Simplified version - just echo the query
    raise HTTPException(status_code=501, detail="LLM service not available in simple test mode")

@app.post("/debug/generate-sql", response_model=SQLQuery)
async def debug_generate_sql(query: NaturalLanguageQuery):
    raise HTTPException(status_code=501, detail="LLM service not available in simple test mode")

@app.post("/debug/execute-sql", response_model=QueryResult)
async def debug_execute_sql(sql_query: SQLQuery):
    return db_service.execute_query(sql_query.sql)

@app.post("/add-record", response_model=AddRecordResponse)
async def add_record(request: AddRecordRequest):
    return db_service.add_record(request.table_name, request.data)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc.detail) if exc.detail else None,
            timestamp=datetime.now()
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("Simple Test Server - Student Management Text-to-SQL API")
    print("=" * 50)
    print("API Documentation:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("  - Health check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server.\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")