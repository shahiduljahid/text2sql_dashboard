"""
Database service with SQL safety layer.
"""
import sqlite3
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from app.config import settings
from app.models import QueryType, QueryResult, SchemaMetadata

class DatabaseService:
    """Database service with safety checks."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_url
        self.connection = None

    @contextmanager
    def get_connection(self):
        """Get a database connection with context management."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
        finally:
            conn.close()

    def validate_sql(self, sql: str) -> Tuple[bool, str, QueryType]:
        """
        Validate SQL query for safety.
        Returns: (is_valid, error_message, query_type)
        """
        # Normalize SQL
        sql_upper = sql.upper().strip()

        # Check for dangerous patterns
        dangerous_patterns = [
            (r'DROP\s+TABLE', 'DROP TABLE not allowed'),
            (r'ALTER\s+TABLE', 'ALTER TABLE not allowed'),
            (r'CREATE\s+TABLE', 'CREATE TABLE not allowed'),
            (r'TRUNCATE\s+TABLE', 'TRUNCATE TABLE not allowed'),
            (r';\s*--', 'Multiple statements not allowed'),
            (r';\s*[A-Z]', 'Multiple statements not allowed'),
            (r'UNION\s+ALL\s+SELECT', 'UNION ALL SELECT not allowed'),
            (r'EXEC\s+', 'EXEC not allowed'),
            (r'EXECUTE\s+', 'EXECUTE not allowed'),
        ]

        for pattern, error in dangerous_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                return False, error, QueryType.SELECT

        # Determine query type
        if sql_upper.startswith('SELECT'):
            query_type = QueryType.SELECT
        elif sql_upper.startswith('INSERT'):
            query_type = QueryType.INSERT
        elif sql_upper.startswith('UPDATE'):
            query_type = QueryType.UPDATE
        elif sql_upper.startswith('DELETE'):
            query_type = QueryType.DELETE
        else:
            return False, 'Only SELECT, INSERT, UPDATE, DELETE queries allowed', QueryType.SELECT

        # Check allowed keywords
        words = re.findall(r'\b[A-Z_]+\b', sql_upper)
        for word in words:
            if word not in settings.allowed_sql_keywords and len(word) > 3:
                # Allow column/table names
                if not re.match(r'^[A-Z][A-Z0-9_]*$', word):
                    return False, f'Keyword {word} not allowed', query_type

        # For write operations, check if allowed
        if query_type in [QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE]:
            if not settings.allow_write_operations:
                return False, 'Write operations are disabled', query_type

        return True, '', query_type

    def execute_query(self, sql: str, params: Optional[Dict] = None) -> QueryResult:
        """Execute a SQL query with safety checks."""
        start_time = time.time()

        # Validate SQL
        is_valid, error_msg, query_type = self.validate_sql(sql)
        if not is_valid:
            return QueryResult(
                sql=sql,
                result=[],
                row_count=0,
                execution_time_ms=0,
                success=False,
                error_message=error_msg
            )

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Execute query
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)

                # For SELECT queries, fetch results
                if query_type == QueryType.SELECT:
                    rows = cursor.fetchall()
                    result = [dict(row) for row in rows]
                    row_count = len(result)

                    # Apply row limit
                    if row_count > settings.max_query_rows:
                        result = result[:settings.max_query_rows]
                        row_count = settings.max_query_rows
                else:
                    # For write operations, commit and get affected rows
                    conn.commit()
                    result = []
                    row_count = cursor.rowcount

                execution_time_ms = (time.time() - start_time) * 1000

                return QueryResult(
                    sql=sql,
                    result=result,
                    row_count=row_count,
                    execution_time_ms=execution_time_ms,
                    success=True,
                    error_message=None
                )

        except sqlite3.Error as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return QueryResult(
                sql=sql,
                result=[],
                row_count=0,
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=str(e)
            )

    def get_schema_metadata(self) -> SchemaMetadata:
        """Get database schema metadata."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get all tables (excluding sqlite system tables)
            cursor.execute("""
                SELECT name as table_name
                FROM sqlite_master
                WHERE type='table'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = cursor.fetchall()

            schema_tables = []
            total_columns = 0

            for table in tables:
                table_name = table['table_name']

                # Get columns for this table
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                table_info = {
                    'table_name': table_name,
                    'columns': [
                        {
                            'name': col['name'],
                            'type': col['type'],
                            'not_null': bool(col['notnull']),
                            'primary_key': bool(col['pk']),
                            'default_value': col['dflt_value'],
                            'auto_generated': bool(col['pk']) or col['dflt_value'] is not None
                        }
                        for col in columns
                    ]
                }

                schema_tables.append(table_info)
                total_columns += len(columns)

            # Get foreign key relationships
            relationships = []
            for table in tables:
                table_name = table['table_name']
                cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                fks = cursor.fetchall()

                for fk in fks:
                    relationships.append({
                        'from_table': table_name,
                        'from_column': fk['from'],
                        'to_table': fk['table'],
                        'to_column': fk['to']
                    })

            return SchemaMetadata(
                tables=schema_tables,
                relationships=relationships,
                total_tables=len(tables),
                total_columns=total_columns
            )

    def add_record(self, table_name: str, data: Dict[str, Any]) -> Tuple[bool, Optional[int], str]:
        """Add a record to a table with validation."""
        if not data:
            return False, None, "No data provided"

        # Build INSERT query
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # Execute query
        result = self.execute_query(sql, tuple(data.values()))

        if result.success:
            # Get the last inserted ID
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT last_insert_rowid()")
                record_id = cursor.fetchone()[0]
            return True, record_id, sql
        else:
            return False, None, result.error_message or "Insert failed"

    def get_table_data(self, table_name: str, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get paginated data from a table."""
        try:
            # Validate table name
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
                return {
                    'error': f'Invalid table name: {table_name}',
                    'success': False
                }

            offset = (page - 1) * page_size

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get total row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_rows = cursor.fetchone()[0]

                # Get column names
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]

                # Get paginated data
                cursor.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?", (page_size, offset))
                rows = cursor.fetchall()

                # Convert rows to dictionaries
                data = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i]
                    data.append(row_dict)

                return {
                    'success': True,
                    'table_name': table_name,
                    'columns': columns,
                    'data': data,
                    'total_rows': total_rows,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_rows + page_size - 1) // page_size if page_size > 0 else 0
                }

        except Exception as e:
            return {
                'error': f'Failed to get table data: {str(e)}',
                'success': False
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                # Get counts from all 7 tables
                tables_to_count = {
                    'total_students': 'students',
                    'total_teachers': 'teachers',
                    'total_courses': 'courses',
                    'total_holidays': 'holidays',
                    'total_enrollments': 'enrollments',
                    'total_salaries': 'salaries',
                    'total_tuition_payments': 'tuition_payments'
                }

                for stat_name, table_name in tables_to_count.items():
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    stats[stat_name] = cursor.fetchone()[0]

                # Get active enrollments (status = 'Enrolled')
                cursor.execute("SELECT COUNT(*) FROM enrollments WHERE status = 'Enrolled'")
                stats['active_enrollments'] = cursor.fetchone()[0]

                # Get pending payments (status = 'Pending' or 'Partial')
                cursor.execute("SELECT COUNT(*) FROM tuition_payments WHERE status IN ('Pending', 'Partial')")
                stats['pending_payments'] = cursor.fetchone()[0]

                return {
                    'success': True,
                    **stats
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get stats: {str(e)}'
            }

    def health_check(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return {
                    'database_connected': True,
                    'tables_count': len(self.get_schema_metadata().tables)
                }
        except Exception as e:
            return {
                'database_connected': False,
                'error': str(e)
            }

# Create global database service instance
db_service = DatabaseService()