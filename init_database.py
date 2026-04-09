#!/usr/bin/env python
"""
Database initialization script for Student Management Text-to-SQL MVP.
Creates SQLite database with schema and sample data.
"""
import sqlite3
import os
import calendar
from datetime import date, timedelta
import random

DB_PATH = "student_management.db"
SCHEMA_FILE = "schema.sql"

def create_database():
    """Create database with schema and sample data."""
    print(f"Creating database at {DB_PATH}...")

    # Remove existing database if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Read and execute schema
    print("Creating schema...")
    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()

    cursor.executescript(schema_sql)

    # Insert sample data
    print("Inserting sample data...")
    insert_sample_data(cursor)

    # Commit and close
    conn.commit()

    # Verify data insertion
    print("\nVerifying data insertion...")
    verify_data(cursor)

    conn.close()
    print(f"\nDatabase created successfully at {DB_PATH}")
    print_sample_queries()

def insert_sample_data(cursor):
    """Insert realistic sample data for demo purposes."""

    # Insert students
    students = [
        ('John', 'Smith', '2008-05-15', 'Male', 'john.smith@school.edu', '555-0101', '123 Main St', '2023-08-20', 9, 'Active'),
        ('Emma', 'Johnson', '2007-11-22', 'Female', 'emma.johnson@school.edu', '555-0102', '456 Oak Ave', '2023-08-20', 10, 'Active'),
        ('Michael', 'Williams', '2006-03-10', 'Male', 'michael.williams@school.edu', '555-0103', '789 Pine Rd', '2022-08-15', 11, 'Active'),
        ('Sophia', 'Brown', '2005-07-30', 'Female', 'sophia.brown@school.edu', '555-0104', '321 Elm St', '2022-08-15', 12, 'Active'),
        ('James', 'Davis', '2009-01-25', 'Male', 'james.davis@school.edu', '555-0105', '654 Maple Dr', '2023-08-20', 9, 'Active'),
        ('Olivia', 'Miller', '2008-09-18', 'Female', 'olivia.miller@school.edu', '555-0106', '987 Cedar Ln', '2023-08-20', 10, 'Active'),
        ('William', 'Wilson', '2007-04-12', 'Male', 'william.wilson@school.edu', '555-0107', '147 Birch Way', '2022-08-15', 11, 'Active'),
        ('Ava', 'Moore', '2006-12-05', 'Female', 'ava.moore@school.edu', '555-0108', '258 Spruce Ct', '2022-08-15', 12, 'Active'),
        ('Benjamin', 'Taylor', '2009-08-08', 'Male', 'benjamin.taylor@school.edu', '555-0109', '369 Willow Blvd', '2023-08-20', 9, 'Active'),
        ('Isabella', 'Anderson', '2008-02-14', 'Female', 'isabella.anderson@school.edu', '555-0110', '741 Aspen Pl', '2023-08-20', 10, 'Active'),
    ]

    cursor.executemany('''
        INSERT INTO students (first_name, last_name, date_of_birth, gender, email, phone, address, enrollment_date, grade_level, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', students)

    # Insert teachers
    teachers = [
        ('Robert', 'Johnson', '1980-03-15', 'Male', 'robert.johnson@school.edu', '555-0201', '111 Teacher Ln', '2018-08-15', 'Mathematics', 'PhD in Mathematics', 'Active'),
        ('Jennifer', 'Davis', '1975-11-22', 'Female', 'jennifer.davis@school.edu', '555-0202', '222 Educator Ave', '2015-01-10', 'Science', 'MSc in Biology', 'Active'),
        ('Thomas', 'Wilson', '1982-07-10', 'Male', 'thomas.wilson@school.edu', '555-0203', '333 Professor Rd', '2020-08-20', 'English', 'MA in English Literature', 'Active'),
        ('Sarah', 'Thompson', '1978-04-30', 'Female', 'sarah.thompson@school.edu', '555-0204', '444 Instructor St', '2016-03-01', 'History', 'PhD in History', 'Active'),
        ('David', 'Martinez', '1985-01-25', 'Male', 'david.martinez@school.edu', '555-0205', '555 Tutor Dr', '2021-08-15', 'Computer Science', 'MSc in Computer Science', 'Active'),
    ]

    cursor.executemany('''
        INSERT INTO teachers (first_name, last_name, date_of_birth, gender, email, phone, address, hire_date, department, qualification, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', teachers)

    # Insert courses
    courses = [
        ('MATH101', 'Algebra I', 'Introduction to algebraic concepts', 'Mathematics', 3, 9, 'Fall', 2024, 1, 30, 0),
        ('SCI201', 'Biology', 'Study of living organisms', 'Science', 4, 10, 'Fall', 2024, 2, 25, 0),
        ('ENG102', 'English Literature', 'Classic and contemporary literature', 'English', 3, 10, 'Fall', 2024, 3, 28, 0),
        ('HIST301', 'World History', 'Survey of world civilizations', 'History', 3, 11, 'Fall', 2024, 4, 30, 0),
        ('CS401', 'Introduction to Programming', 'Fundamentals of programming', 'Computer Science', 4, 12, 'Fall', 2024, 5, 20, 0),
        ('MATH202', 'Geometry', 'Study of shapes and spaces', 'Mathematics', 3, 10, 'Spring', 2024, 1, 30, 0),
        ('SCI302', 'Chemistry', 'Introduction to chemical principles', 'Science', 4, 11, 'Spring', 2024, 2, 25, 0),
    ]

    cursor.executemany('''
        INSERT INTO courses (course_code, course_name, description, department, credits, grade_level, semester, academic_year, teacher_id, max_capacity, current_enrollment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', courses)

    # Insert enrollments (students in courses)
    enrollments = []
    course_ids = list(range(1, 8))  # Course IDs 1-7
    student_ids = list(range(1, 11))  # Student IDs 1-10

    # Assign each student to 3-5 courses
    for student_id in student_ids:
        num_courses = random.randint(3, 5)
        assigned_courses = random.sample(course_ids, num_courses)
        for course_id in assigned_courses:
            enrollments.append((student_id, course_id, '2024-08-25', None, None, 'Enrolled'))

    cursor.executemany('''
        INSERT INTO enrollments (student_id, course_id, enrollment_date, drop_date, grade, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', enrollments)

    # Insert holidays
    holidays = [
        ('Labor Day', '2024-09-02', 'National', 'Labor Day holiday'),
        ('Thanksgiving Break', '2024-11-28', 'Break', 'Thanksgiving holiday break'),
        ('Winter Break', '2024-12-23', 'Break', 'Winter vacation'),
        ('New Year\'s Day', '2025-01-01', 'National', 'New Year holiday'),
        ('Martin Luther King Jr. Day', '2025-01-20', 'National', 'MLK Day'),
        ('Spring Break', '2025-03-17', 'Break', 'Spring vacation'),
        ('Memorial Day', '2025-05-26', 'National', 'Memorial Day'),
    ]

    cursor.executemany('''
        INSERT INTO holidays (holiday_name, holiday_date, holiday_type, description, academic_year)
        VALUES (?, ?, ?, ?, ?)
    ''', [(h[0], h[1], h[2], h[3], 2024) for h in holidays])

    # Insert salaries
    salaries = []
    teacher_ids = list(range(1, 6))  # Teacher IDs 1-5
    base_salaries = [75000, 82000, 68000, 90000, 72000]

    for i, teacher_id in enumerate(teacher_ids):
        for month in range(1, 13):  # 12 months of salary
            payment_date = date(2024, month, 15)
            pay_period_start = date(2024, month, 1)
            last_day = calendar.monthrange(2024, month)[1]
            pay_period_end = date(2024, month, last_day)

            monthly_salary = base_salaries[i] / 12
            deductions = monthly_salary * 0.15  # 15% deductions

            salaries.append((
                teacher_id, monthly_salary, payment_date.isoformat(),
                'Bank Transfer', pay_period_start.isoformat(), pay_period_end.isoformat(),
                deductions, 'Paid'
            ))

    cursor.executemany('''
        INSERT INTO salaries (teacher_id, salary_amount, payment_date, payment_method, pay_period_start, pay_period_end, deductions, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', salaries)

    # Insert tuition payments
    tuition_payments = []
    semester_tuition = {
        'Fall': 2500.00,
        'Spring': 2500.00,
        'Summer': 1500.00,
        'Full Year': 6000.00
    }

    for student_id in student_ids:
        # Each student has payments for Fall and Spring semesters
        for semester in ['Fall', 'Spring']:
            amount_due = semester_tuition[semester]
            amount_paid = amount_due if random.random() > 0.3 else amount_due * 0.7  # 70% paid for some

            if semester == 'Fall':
                due_date = date(2024, 9, 15)
                payment_date = due_date if amount_paid == amount_due else date(2024, 9, 10)
            else:  # Spring
                due_date = date(2025, 1, 15)
                payment_date = due_date if amount_paid == amount_due else date(2025, 1, 10)

            status = 'Paid' if amount_paid == amount_due else 'Partial'
            if amount_paid == 0:
                status = 'Pending'

            tuition_payments.append((
                student_id, 2024, semester, amount_due, amount_paid,
                payment_date.isoformat() if amount_paid > 0 else None,
                due_date.isoformat(), 'Bank Transfer', status
            ))

    cursor.executemany('''
        INSERT INTO tuition_payments (student_id, academic_year, semester, amount_due, amount_paid, payment_date, due_date, payment_method, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', tuition_payments)

def verify_data(cursor):
    """Verify that data was inserted correctly."""
    tables = ['students', 'teachers', 'courses', 'enrollments', 'holidays', 'salaries', 'tuition_payments']

    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} records")

    # Show some sample queries
    print("\nSample queries:")

    # Total students by grade
    cursor.execute('''
        SELECT grade_level, COUNT(*) as student_count
        FROM students
        WHERE status = 'Active'
        GROUP BY grade_level
        ORDER BY grade_level
    ''')
    print("  Students by grade level:")
    for row in cursor.fetchall():
        print(f"    Grade {row[0]}: {row[1]} students")

    # Courses with enrollment
    cursor.execute('''
        SELECT c.course_name, c.current_enrollment, c.max_capacity,
               t.first_name || ' ' || t.last_name as teacher_name
        FROM courses c
        LEFT JOIN teachers t ON c.teacher_id = t.teacher_id
        WHERE c.status = 'Active'
        ORDER BY c.department
    ''')
    print("\n  Course enrollment:")
    for row in cursor.fetchall():
        print(f"    {row[0]} ({row[3]}): {row[1]}/{row[2]} students")

def print_sample_queries():
    """Print sample natural language queries for testing."""
    print("\n" + "="*60)
    print("SAMPLE NATURAL LANGUAGE QUERIES FOR TESTING:")
    print("="*60)
    print("1. Show me all students in grade 10")
    print("2. List all active teachers in the Science department")
    print("3. How many students are enrolled in Algebra I?")
    print("4. What courses is John Smith taking?")
    print("5. Show me all holidays in November 2024")
    print("6. What is the total salary paid to teachers in 2024?")
    print("7. Which students have pending tuition payments?")
    print("8. List all courses taught by Robert Johnson")
    print("9. How many male vs female students are there?")
    print("10. Show me all students who will graduate in 2025 (grade 12)")
    print("="*60)

if __name__ == "__main__":
    create_database()