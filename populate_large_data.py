#!/usr/bin/env python3
"""
Populate large dataset (around 1000 records per table) for Student Management Database
"""
import argparse
import sqlite3
import random
from datetime import date
from faker import Faker

def generate_large_dataset(add_students: int = 1000, reset: bool = False):
    """Generate and append a large dataset into the database."""
    fake = Faker()

    conn = sqlite3.connect('student_management.db')
    cursor = conn.cursor()

    add_teachers = max(1, add_students // 10)
    add_courses = max(1, add_students // 5)

    print(f"Generating additional dataset (+{add_students} students)...")

    if reset:
        print("Reset mode enabled. Clearing existing data...")
        tables = ['tuition_payments', 'salaries', 'enrollments', 'holidays', 'courses', 'teachers', 'students']
        for table in tables:
            try:
                cursor.execute(f'DELETE FROM {table}')
                print(f"  Cleared {table}")
            except sqlite3.Error as e:
                print(f"  Error clearing {table}: {e}")

        conn.commit()

    cursor.execute('SELECT COALESCE(MAX(student_id), 0) FROM students')
    max_student_id = cursor.fetchone()[0]
    cursor.execute('SELECT COALESCE(MAX(teacher_id), 0) FROM teachers')
    max_teacher_id = cursor.fetchone()[0]

    cursor.execute('PRAGMA table_info(enrollments)')
    enrollment_columns = {row[1] for row in cursor.fetchall()}
    has_enrollment_academic_year = 'academic_year' in enrollment_columns

    # 1. Generate students
    print(f"\nGenerating {add_students} students...")
    students = []
    first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
                   'William', 'Elizabeth', 'David', 'Susan', 'Richard', 'Jessica', 'Joseph', 'Sarah',
                   'Thomas', 'Karen', 'Charles', 'Nancy', 'Christopher', 'Lisa', 'Daniel', 'Margaret',
                   'Matthew', 'Betty', 'Anthony', 'Sandra', 'Donald', 'Ashley', 'Mark', 'Dorothy',
                   'Paul', 'Michelle', 'Steven', 'Carol', 'Andrew', 'Amanda', 'Kenneth', 'Melissa']

    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                  'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
                  'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
                  'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
                  'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores']

    next_student_id = max_student_id + 1
    for i in range(next_student_id, next_student_id + add_students):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        dob_year = random.randint(2000, 2010)
        dob_month = random.randint(1, 12)
        dob_day = random.randint(1, 28)
        dob = f"{dob_year}-{dob_month:02d}-{dob_day:02d}"
        gender = random.choice(['Male', 'Female'])
        email = f"{first_name.lower()}.{last_name.lower()}{i}@school.edu"
        phone = f"555-{random.randint(1000, 9999):04d}"
        address = fake.address().replace('\n', ', ')
        enroll_year = random.randint(2020, 2024)
        enroll_date = f"{enroll_year}-08-{random.randint(20, 25):02d}"
        grade_level = random.randint(9, 12)
        status = random.choices(['Active', 'Inactive', 'Graduated', 'Transferred'],
                               weights=[0.8, 0.05, 0.1, 0.05])[0]

        students.append((first_name, last_name, dob, gender, email, phone, address,
                        enroll_date, grade_level, status))

    cursor.executemany('''
        INSERT INTO students (first_name, last_name, date_of_birth, gender, email, phone, address, enrollment_date, grade_level, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', students)
    print(f"  Inserted {len(students)} students")
    new_student_ids = list(range(next_student_id, next_student_id + len(students)))

    # 2. Generate teachers
    print(f"\nGenerating {add_teachers} teachers...")
    teachers = []
    departments = ['Mathematics', 'Science', 'English', 'History', 'Computer Science',
                   'Physical Education', 'Arts', 'Music', 'Foreign Languages', 'Business']
    qualifications = ['PhD', 'MSc', 'MA', 'MEd', 'BSc', 'BA', 'BEd']

    next_teacher_id = max_teacher_id + 1
    for i in range(next_teacher_id, next_teacher_id + add_teachers):
        first_name = fake.first_name()
        last_name = fake.last_name()
        dob_year = random.randint(1960, 1990)
        dob_month = random.randint(1, 12)
        dob_day = random.randint(1, 28)
        dob = f"{dob_year}-{dob_month:02d}-{dob_day:02d}"
        gender = random.choice(['Male', 'Female'])
        email = f"{first_name.lower()}.{last_name.lower()}{i}@school.edu"
        phone = f"555-{random.randint(2000, 2999):04d}"
        address = fake.address().replace('\n', ', ')
        hire_year = random.randint(2000, 2023)
        hire_date = f"{hire_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        department = random.choice(departments)
        qualification = random.choice(qualifications) + f" in {department}"
        status = random.choices(['Active', 'Inactive', 'On Leave', 'Retired'],
                               weights=[0.85, 0.05, 0.05, 0.05])[0]

        teachers.append((first_name, last_name, dob, gender, email, phone, address,
                        hire_date, department, qualification, status))

    cursor.executemany('''
        INSERT INTO teachers (first_name, last_name, date_of_birth, gender, email, phone, address, hire_date, department, qualification, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', teachers)
    print(f"  Inserted {len(teachers)} teachers")
    new_teacher_ids = list(range(next_teacher_id, next_teacher_id + len(teachers)))

    cursor.execute('SELECT teacher_id FROM teachers')
    all_teacher_ids = [row[0] for row in cursor.fetchall()]

    # 3. Generate courses
    print(f"\nGenerating {add_courses} courses...")
    courses = []
    course_prefixes = {
        'Mathematics': ['MATH', 'CALC', 'STAT', 'ALG', 'GEOM'],
        'Science': ['BIO', 'CHEM', 'PHYS', 'ENV', 'ASTRO'],
        'English': ['ENG', 'LIT', 'WRIT', 'CREAT', 'COMM'],
        'History': ['HIST', 'GEOG', 'POLI', 'SOC', 'ECON'],
        'Computer Science': ['CS', 'PROG', 'DATA', 'WEB', 'AI'],
        'Physical Education': ['PE', 'HEALTH', 'SPORTS', 'FIT', 'DANCE'],
        'Arts': ['ART', 'DRAW', 'PAINT', 'PHOTO', 'DESIGN'],
        'Music': ['MUSIC', 'BAND', 'CHOIR', 'THEORY', 'HIST'],
        'Foreign Languages': ['SPAN', 'FRENCH', 'GERMAN', 'CHINESE', 'JAPAN'],
        'Business': ['BUS', 'ECON', 'ACCT', 'MARKET', 'MGMT']
    }

    course_levels = ['101', '102', '201', '202', '301', '302', '401', '402']
    semesters = ['Fall', 'Spring', 'Summer']
    academic_years = [2023, 2024, 2025]

    used_course_codes = set()
    cursor.execute('SELECT course_code FROM courses')
    used_course_codes.update(row[0] for row in cursor.fetchall())

    for _ in range(add_courses):
        department = random.choice(departments)
        prefix = random.choice(course_prefixes[department])
        level = random.choice(course_levels)
        course_code = f"{prefix}{level}"
        suffix = 1
        while course_code in used_course_codes:
            course_code = f"{prefix}{level}-{suffix}"
            suffix += 1
        used_course_codes.add(course_code)
        course_name = f"{department} {level}"
        description = f"Course in {department} at level {level}"
        credits = random.choice([3, 4])
        grade_level = random.randint(9, 12)
        semester = random.choice(semesters)
        academic_year = random.choice(academic_years)
        teacher_id = random.choice(all_teacher_ids)
        max_capacity = random.choice([20, 25, 30, 35])
        status = random.choices(['Active', 'Inactive', 'Archived'],
                               weights=[0.9, 0.05, 0.05])[0]

        courses.append((course_code, course_name, description, department, credits,
                       grade_level, semester, academic_year, teacher_id, max_capacity,
                       0, status))

    cursor.executemany('''
        INSERT INTO courses (course_code, course_name, description, department, credits, grade_level, semester, academic_year, teacher_id, max_capacity, current_enrollment, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', courses)
    print(f"  Inserted {len(courses)} courses")

    cursor.execute('SELECT course_id FROM courses')
    all_course_ids = [row[0] for row in cursor.fetchall()]

    # 4. Generate enrollments
    print("\nGenerating enrollments for newly added students...")
    enrollments = []

    # Each student enrolls in 3-6 courses
    for student_id in new_student_ids:
        num_courses = random.randint(3, 6)
        assigned_courses = random.sample(all_course_ids, min(num_courses, len(all_course_ids)))
        for course_id in assigned_courses:
            # Get course info to determine academic year
            cursor.execute('SELECT academic_year, semester FROM courses WHERE course_id = ?', (course_id,))
            course_info = cursor.fetchone()
            if course_info:
                academic_year, semester = course_info
                # Determine enrollment date based on semester and year
                if semester == 'Fall':
                    enrollment_date = f"{academic_year}-08-{random.randint(20, 30):02d}"
                elif semester == 'Spring':
                    enrollment_date = f"{academic_year}-01-{random.randint(10, 20):02d}"
                else:  # Summer
                    enrollment_date = f"{academic_year}-06-{random.randint(1, 10):02d}"

                status = random.choices(['Enrolled', 'Completed', 'Dropped', 'Failed'],
                                       weights=[0.7, 0.2, 0.05, 0.05])[0]
                grade = None
                if status == 'Completed':
                    grade = random.choices(['A', 'B', 'C', 'D', 'F'],
                                          weights=[0.3, 0.4, 0.2, 0.05, 0.05])[0]
                elif status == 'Failed':
                    grade = 'F'

                if has_enrollment_academic_year:
                    enrollments.append((student_id, course_id, enrollment_date, grade, status, academic_year))
                else:
                    enrollments.append((student_id, course_id, enrollment_date, grade, status))

    if has_enrollment_academic_year:
        cursor.executemany('''
            INSERT INTO enrollments (student_id, course_id, enrollment_date, grade, status, academic_year)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', enrollments)
    else:
        cursor.executemany('''
            INSERT INTO enrollments (student_id, course_id, enrollment_date, grade, status)
            VALUES (?, ?, ?, ?, ?)
        ''', enrollments)
    print(f"  Inserted {len(enrollments)} enrollments")

    # 5. Generate holidays (around 50 records)
    print("\nGenerating holidays...")
    holidays = []
    holiday_names = ['Labor Day', 'Thanksgiving Break', 'Winter Break', 'New Year\'s Day',
                    'Martin Luther King Jr. Day', 'Spring Break', 'Memorial Day',
                    'Independence Day', 'Veterans Day', 'Christmas Break', 'Easter Break',
                    'Professional Development Day', 'Parent-Teacher Conference']

    for year in [2023, 2024, 2025]:
        # Fixed holidays
        holidays.append(('Labor Day', f"{year}-09-02", 'National', 'Labor Day holiday', year))
        holidays.append(('Thanksgiving Break', f"{year}-11-28", 'Break', 'Thanksgiving holiday break', year))
        holidays.append(('Winter Break', f"{year}-12-23", 'Break', 'Winter vacation', year))
        holidays.append(('New Year\'s Day', f"{year+1}-01-01", 'National', 'New Year holiday', year))
        holidays.append(('Martin Luther King Jr. Day', f"{year}-01-20", 'National', 'MLK Day', year))
        holidays.append(('Spring Break', f"{year}-03-17", 'Break', 'Spring vacation', year))
        holidays.append(('Memorial Day', f"{year}-05-26", 'National', 'Memorial Day', year))

        # Random school holidays
        for _ in range(5):
            holiday_name = random.choice(holiday_names)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            holiday_date = f"{year}-{month:02d}-{day:02d}"
            holiday_type = random.choice(['School', 'Religious', 'Break'])
            description = f"{holiday_name} holiday"
            holidays.append((holiday_name, holiday_date, holiday_type, description, year))

    cursor.executemany('''
        INSERT OR IGNORE INTO holidays (holiday_name, holiday_date, holiday_type, description, academic_year)
        VALUES (?, ?, ?, ?, ?)
    ''', holidays)
    print(f"  Attempted {len(holidays)} holidays (duplicates ignored)")

    # 6. Generate salaries for newly added teachers
    print("\nGenerating salaries...")
    salaries = []
    base_salaries = [random.randint(50000, 100000) for _ in range(len(new_teacher_ids))]

    for idx, teacher_id in enumerate(new_teacher_ids):
        monthly_salary = base_salaries[idx] / 12
        for year in [2023, 2024]:
            for month in range(1, 13):
                payment_date = date(year, month, 15)
                pay_period_start = date(year, month, 1)

                # Handle different month lengths
                if month in [4, 6, 9, 11]:
                    pay_period_end = date(year, month, 30)
                elif month == 2:
                    # Check for leap year
                    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                        pay_period_end = date(year, 2, 29)
                    else:
                        pay_period_end = date(year, 2, 28)
                else:
                    pay_period_end = date(year, month, 31)

                deductions = monthly_salary * random.uniform(0.1, 0.2)  # 10-20% deductions
                net_amount = monthly_salary - deductions
                status = 'Paid'  # All salaries are paid
                payment_method = random.choice(['Bank Transfer', 'Check'])

                salaries.append((
                    teacher_id, monthly_salary, payment_date.isoformat(),
                    payment_method, pay_period_start.isoformat(), pay_period_end.isoformat(),
                    deductions, net_amount, status
                ))

    cursor.executemany('''
        INSERT INTO salaries (teacher_id, salary_amount, payment_date, payment_method, pay_period_start, pay_period_end, deductions, net_amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', salaries)
    print(f"  Inserted {len(salaries)} salary records")

    # 7. Generate tuition payments for newly added students
    print("\nGenerating tuition payments...")
    tuition_payments = []
    semester_tuition = {'Fall': 2500.00, 'Spring': 2500.00, 'Summer': 1500.00, 'Full Year': 6000.00}

    for student_id in new_student_ids:
        for year in [2023, 2024]:
            # Determine which semesters the student was enrolled
            enrolled_semesters = random.sample(['Fall', 'Spring', 'Summer', 'Full Year'],
                                              random.randint(1, 3))

            for semester in enrolled_semesters:
                amount_due = semester_tuition[semester]
                # Random payment status
                payment_status = random.choices(['Paid', 'Partial', 'Pending', 'Overdue'],
                                               weights=[0.6, 0.2, 0.15, 0.05])[0]

                if payment_status == 'Paid':
                    amount_paid = amount_due
                elif payment_status == 'Partial':
                    amount_paid = amount_due * random.uniform(0.3, 0.9)
                else:  # Pending or Overdue
                    amount_paid = 0

                # Determine dates based on semester and year
                if semester == 'Fall':
                    due_date = date(year, 9, 15)
                    if amount_paid > 0:
                        payment_date = date(year, random.randint(8, 9), random.randint(1, 15))
                    else:
                        payment_date = None
                elif semester == 'Spring':
                    due_date = date(year+1, 1, 15)
                    if amount_paid > 0:
                        payment_date = date(year+1, random.randint(1, 2), random.randint(1, 15))
                    else:
                        payment_date = None
                elif semester == 'Summer':
                    due_date = date(year, 6, 15)
                    if amount_paid > 0:
                        payment_date = date(year, random.randint(5, 6), random.randint(1, 15))
                    else:
                        payment_date = None
                else:  # Full Year
                    due_date = date(year, 9, 15)
                    if amount_paid > 0:
                        payment_date = date(year, random.randint(8, 10), random.randint(1, 15))
                    else:
                        payment_date = None

                payment_method = random.choice(['Bank Transfer', 'Check', 'Cash', 'Online']) if amount_paid > 0 else None

                tuition_payments.append((
                    student_id, year, semester, amount_due, amount_paid,
                    payment_date.isoformat() if payment_date else None,
                    due_date.isoformat(), payment_method, payment_status
                ))

    cursor.executemany('''
        INSERT INTO tuition_payments (student_id, academic_year, semester, amount_due, amount_paid, payment_date, due_date, payment_method, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', tuition_payments)
    print(f"  Inserted {len(tuition_payments)} tuition payment records")

    conn.commit()

    # Verify data
    print("\n\nData verification:")
    tables = ['students', 'teachers', 'courses', 'enrollments', 'holidays', 'salaries', 'tuition_payments']
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} records")

    # Sample statistics
    print("\nSample statistics:")

    # Students by grade
    cursor.execute('SELECT grade_level, COUNT(*) FROM students GROUP BY grade_level ORDER BY grade_level')
    print("Students by grade:")
    for grade, count in cursor.fetchall():
        print(f"  Grade {grade}: {count} students")

    # Students by status
    cursor.execute('SELECT status, COUNT(*) FROM students GROUP BY status')
    print("\nStudents by status:")
    for status, count in cursor.fetchall():
        print(f"  {status}: {count} students")

    # Teachers by department
    cursor.execute('SELECT department, COUNT(*) FROM teachers GROUP BY department')
    print("\nTeachers by department:")
    for dept, count in cursor.fetchall():
        print(f"  {dept}: {count} teachers")

    # Course enrollment
    cursor.execute('''
        SELECT c.department, COUNT(e.enrollment_id) as total_enrollments
        FROM courses c
        LEFT JOIN enrollments e ON c.course_id = e.course_id
        GROUP BY c.department
        ORDER BY total_enrollments DESC
        LIMIT 5
    ''')
    print("\nTop 5 departments by enrollment:")
    for dept, enrolled in cursor.fetchall():
        print(f"  {dept}: {enrolled} enrollments")

    # Tuition payment status
    cursor.execute('SELECT status, COUNT(*) FROM tuition_payments GROUP BY status')
    print("\nTuition payment status:")
    for status, count in cursor.fetchall():
        print(f"  {status}: {count} payments")

    conn.close()
    print("\n\nLarge dataset generation completed successfully!")

if __name__ == "__main__":
    # Check if Faker is installed
    try:
        from faker import Faker
        parser = argparse.ArgumentParser(description="Populate Student Management database with more data")
        parser.add_argument("--students", type=int, default=1000, help="Number of students to add (default: 1000)")
        parser.add_argument("--reset", action="store_true", help="Clear existing data before populating")
        args = parser.parse_args()

        generate_large_dataset(add_students=args.students, reset=args.reset)
    except ImportError:
        print("Error: Faker library is required. Please install it using:")
        print("  pip install faker")
        print("\nAlternatively, you can install it from the backend directory:")
        print("  cd /home/su/SIJ/Thesis/AI_DASHBOARD/backend")
        print("  pip install faker")