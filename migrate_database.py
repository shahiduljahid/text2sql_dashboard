#!/usr/bin/env python
"""
Database migration script template for Student Management Text-to-SQL MVP.
Use this to apply schema changes without losing data.
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = "student_management.db"
BACKUP_PATH = f"student_management_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def backup_database():
    """Create a backup of the current database."""
    if os.path.exists(DB_PATH):
        import shutil
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"Backup created: {BACKUP_PATH}")
        return True
    else:
        print(f"Database {DB_PATH} does not exist.")
        return False

def apply_migration(cursor, migration_name, sql_statements):
    """Apply a migration and record it in migrations table."""
    print(f"Applying migration: {migration_name}")

    # Create migrations table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Check if migration already applied
    cursor.execute("SELECT name FROM migrations WHERE name = ?", (migration_name,))
    if cursor.fetchone():
        print(f"Migration '{migration_name}' already applied. Skipping.")
        return

    # Apply SQL statements
    for sql in sql_statements:
        cursor.execute(sql)

    # Record migration
    cursor.execute("INSERT INTO migrations (name) VALUES (?)", (migration_name,))
    print(f"Migration '{migration_name}' applied successfully.")

def run_migrations():
    """Run all pending migrations."""
    print("Starting database migrations...")

    if not backup_database():
        print("Cannot proceed without database backup.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Example migration 1: Add attendance table
        apply_migration(cursor, "add_attendance_table", [
            '''
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                attendance_date DATE NOT NULL,
                status TEXT CHECK(status IN ('Present', 'Absent', 'Late', 'Excused')) DEFAULT 'Present',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
                UNIQUE(student_id, course_id, attendance_date)
            )
            ''',
            '''
            CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
            ''',
            '''
            CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);
            '''
        ])

        # Example migration 2: Add assignments table
        apply_migration(cursor, "add_assignments_table", [
            '''
            CREATE TABLE IF NOT EXISTS assignments (
                assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                assignment_name TEXT NOT NULL,
                description TEXT,
                due_date DATE NOT NULL,
                max_points INTEGER NOT NULL CHECK(max_points > 0),
                weight DECIMAL(5,2) DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS assignment_grades (
                grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                points_earned DECIMAL(10,2) NOT NULL CHECK(points_earned >= 0),
                submitted_date DATE,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assignment_id) REFERENCES assignments(assignment_id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                UNIQUE(assignment_id, student_id)
            )
            ''',
            '''
            CREATE TRIGGER IF NOT EXISTS update_assignments_timestamp
            AFTER UPDATE ON assignments
            BEGIN
                UPDATE assignments SET updated_at = CURRENT_TIMESTAMP WHERE assignment_id = NEW.assignment_id;
            END;
            ''',
            '''
            CREATE TRIGGER IF NOT EXISTS update_assignment_grades_timestamp
            AFTER UPDATE ON assignment_grades
            BEGIN
                UPDATE assignment_grades SET updated_at = CURRENT_TIMESTAMP WHERE grade_id = NEW.grade_id;
            END;
            '''
        ])

        # Example migration 3: Add parent/guardian information
        apply_migration(cursor, "add_parents_table", [
            '''
            CREATE TABLE IF NOT EXISTS parents (
                parent_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                relationship TEXT CHECK(relationship IN ('Mother', 'Father', 'Guardian', 'Other')),
                email TEXT,
                phone TEXT NOT NULL,
                address TEXT,
                emergency_contact BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
            )
            ''',
            '''
            CREATE INDEX IF NOT EXISTS idx_parents_student ON parents(student_id);
            '''
        ])

        conn.commit()
        print("\nAll migrations applied successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\nError applying migrations: {e}")
        print(f"Database restored from backup: {BACKUP_PATH}")
        raise

    finally:
        conn.close()

    # Show migration status
    print("\nMigration status:")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, applied_at FROM migrations ORDER BY applied_at")
    migrations = cursor.fetchall()
    for migration in migrations:
        print(f"  ✓ {migration[0]} - {migration[1]}")
    conn.close()

if __name__ == "__main__":
    run_migrations()