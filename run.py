#!/usr/bin/env python3
"""
Startup script for Student Management Text-to-SQL API.
"""
import os
import sys
import uvicorn
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def check_database():
    """Check if database exists and is populated."""
    db_path = "student_management.db"
    if not os.path.exists(db_path):
        print(f"ERROR: Database file '{db_path}' not found!")
        print("Please run: ./setup_database.sh")
        return False

    # Check if database has data
    import sqlite3
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        student_count = cursor.fetchone()[0]
        conn.close()

        if student_count == 0:
            print("WARNING: Database exists but appears to be empty.")
            print("Please run: ./setup_database.sh")
            return True  # Continue anyway, schema might be there
        return True
    except Exception as e:
        print(f"ERROR: Failed to check database: {e}")
        return False

def check_env():
    """Check environment configuration."""
    from app.config import settings

    print("Configuration check:")
    print(f"  Database: {settings.database_url}")
    print(f"  LLM Provider: {settings.llm_provider}")
    print(f"  LLM Model: {settings.llm_model}")

    if settings.llm_provider == "openai" and not settings.openai_api_key:
        print("WARNING: OPENAI_API_KEY not set in environment!")
        print("LLM functionality will not work.")
        print("Please set OPENAI_API_KEY in .env file or environment variables.")
    elif settings.llm_provider == "anthropic" and not settings.anthropic_api_key:
        print("WARNING: ANTHROPIC_API_KEY not set in environment!")
        print("LLM functionality will not work.")
        print("Please set ANTHROPIC_API_KEY in .env file or environment variables.")
    elif settings.llm_provider == "local":
        print("  Using local fine-tuned model")
        # Check if model directory exists
        import os
        model_path = settings.llm_model
        if not os.path.isabs(model_path):
            model_path = os.path.join(os.path.dirname(__file__), model_path)

        if os.path.exists(model_path):
            print(f"  Model found at: {model_path}")
        else:
            print(f"  WARNING: Model directory not found: {model_path}")
            print("  LLM functionality will not work.")

    return True

def main():
    """Start the FastAPI server."""
    print("=" * 50)
    print("Student Management Text-to-SQL API")
    print("=" * 50)

    # Check prerequisites
    if not check_database():
        sys.exit(1)

    check_env()

    print("\nStarting server...")
    print("API Documentation:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("  - Health check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server.\n")

    # Start server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()