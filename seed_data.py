#!/usr/bin/env python3
"""
Seed sample data for Student Management Database
"""
import sqlite3
import random
from datetime import date, timedelta

def seed_database():
    """Insert sample data into the database."""
    conn = sqlite3.connect('student_management.db')
    cursor = conn.cursor()

    print("Seeding sample data...")

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
        ('Robert', 'Johnson', '1980-03-15', 'Male', 'robert.johnson@school.edu', '555-0201', '111 Teacher Ln', '2018-08-15', 'Mathematics', 'PhD in Mathematics'),
        ('Jennifer', 'Davis', '1975-11-22', 'Female', 'jennifer.davis@school.edu', '555-0202', '222 Educator Ave', '2015-01-10', 'Science', 'MSc in Biology'),
        ('Thomas', 'Wilson', '1982-07-10', 'Male', 'thomas.wilson@school.edu', '555-0203', '333 Professor Rd', '2020-08-20', 'English', 'MA in English Literature'),
        ('Sarah', 'Thompson', '1978-04-30', 'Female', 'sarah.thompson@school.edu', '555-0204', '444 Instructor St', '2016-03-01', 'History', 'PhD in History'),
        ('David', 'Martinez', '1985-01-25', 'Male', 'david.martinez@school.edu', '555-0205', '555 Tutor Dr', '2021-08-15', 'Computer Science', 'MSc in Computer Science'),
    ]

    cursor.executemany('''
        INSERT INTO teachers (first_name, last_name, date_of_birth, gender, email, phone, address, hire_date, department, qualification)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', teachers)

    # Insert courses
    courses = [
        ('MATH101', 'Algebra I', 'Introduction to algebraic concepts', 'Mathematics', 3, 9, 'Fall', 2024, 1),
        ('SCI201', 'Biology', 'Study of living organisms', 'Science', 4, 10, 'Fall', 2024, 2),
        ('ENG102', 'English Literature', 'Classic and contemporary literature', 'English', 3, 10, 'Fall', 2024, 3),
        ('HIST301', 'World History', 'Survey of world civilizations', 'History', 3, 11, 'Fall', 2024, 4),
        ('CS401', 'Introduction to Programming', 'Fundamentals of programming', 'Computer Science', 4, 12, 'Fall', 2024, 5),
        ('MATH202', 'Geometry', 'Study of shapes and spaces', 'Mathematics', 3, 10, 'Spring', 2024, 1),
        ('SCI302', 'Chemistry', 'Introduction to chemical principles', 'Science', 4, 11, 'Spring', 2024, 2),
    ]

    cursor.executemany('''
        INSERT INTO courses (course_code, course_name, description, department, credits, grade_level, semester, academic_year, teacher_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', courses)

    # Insert enrollments
    enrollments = []
    course_ids = list(range(1, 8))
    student_ids = list(range(1, 11))

    for student_id in student_ids:
        num_courses = random.randint(3, 5)
        assigned_courses = random.sample(course_ids, num_courses)
        for course_id in assigned_courses:
            enrollments.append((student_id, course_id, '2024-08-25', 'Enrolled'))

    cursor.executemany('''
        INSERT INTO enrollments (student_id, course_id, enrollment_date, status)
        VALUES (?, ?, ?, ?)
    ''', enrollments)

    # Insert holidays
    holidays = [
        ('Labor Day', '2024-09-02', 'National', 'Labor Day holiday', 2024),
        ('Thanksgiving Break', '2024-11-28', 'Break', 'Thanksgiving holiday break', 2024),
        ('Winter Break', '2024-12-23', 'Break', 'Winter vacation', 2024),
        ('New Year\'s Day', '2025-01-01', 'National', 'New Year holiday', 2024),
        ('Martin Luther King Jr. Day', '2025-01-20', 'National', 'MLK Day', 2024),
        ('Spring Break', '2025-03-17', 'Break', 'Spring vacation', 2024),
        ('Memorial Day', '2025-05-26', 'National', 'Memorial Day', 2024),
    ]

    cursor.executemany('''
        INSERT INTO holidays (holiday_name, holiday_date, holiday_type, description, academic_year)
        VALUES (?, ?, ?, ?, ?)
    ''', holidays)

    # Insert salaries
    salaries = []
    base_salaries = [75000, 82000, 68000, 90000, 72000]

    for teacher_id in range(1, 6):
        monthly_salary = base_salaries[teacher_id-1] / 12
        for month in range(1, 4):  # 3 months for demo
            payment_date = date(2024, month, 15)
            pay_period_start = date(2024, month, 1)
            # Handle different month lengths
            if month in [4, 6, 9, 11]:
                pay_period_end = date(2024, month, 30)
            elif month == 2:
                pay_period_end = date(2024, 2, 29)  # Leap year
            else:
                pay_period_end = date(2024, month, 31)

            deductions = monthly_salary * 0.15
            net_amount = monthly_salary - deductions

            salaries.append((
                teacher_id, monthly_salary, payment_date.isoformat(),
                'Bank Transfer', pay_period_start.isoformat(), pay_period_end.isoformat(),
                deductions, net_amount, 'Paid'
            ))

    cursor.executemany('''
        INSERT INTO salaries (teacher_id, salary_amount, payment_date, payment_method, pay_period_start, pay_period_end, deductions, net_amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', salaries)

    # Insert tuition payments
    tuition_payments = []
    semester_tuition = {'Fall': 2500.00, 'Spring': 2500.00}

    for student_id in student_ids:
        for semester in ['Fall', 'Spring']:
            amount_due = semester_tuition[semester]
            amount_paid = amount_due if random.random() > 0.3 else amount_due * 0.7

            if semester == 'Fall':
                due_date = date(2024, 9, 15)
                payment_date = due_date if amount_paid == amount_due else date(2024, 9, 10)
            else:
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

    conn.commit()

    # Verify data
    print("\nData verification:")
    tables = ['students', 'teachers', 'courses', 'enrollments', 'holidays', 'salaries', 'tuition_payments']
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} records")

    # Sample queries
    print("\nSample data queries:")

    # Students by grade
    cursor.execute('SELECT grade_level, COUNT(*) FROM students GROUP BY grade_level ORDER BY grade_level')
    print("Students by grade:")
    for grade, count in cursor.fetchall():
        print(f"  Grade {grade}: {count} students")

    # Course enrollment
    cursor.execute('''
        SELECT c.course_name, COUNT(e.student_id) as enrolled
        FROM courses c
        LEFT JOIN enrollments e ON c.course_id = e.course_id
        GROUP BY c.course_id
        ORDER BY c.course_name
    ''')
    print("\nCourse enrollment:")
    for course, enrolled in cursor.fetchall():
        print(f"  {course}: {enrolled} students")

    conn.close()
    print("\nDatabase seeded successfully!")

if __name__ == "__main__":
    seed_database()