#!/bin/bash
# Complete database setup for Student Management System

echo "========================================="
echo "Student Management Database Setup"
echo "========================================="

# Step 1: Create database with schema
echo "Step 1: Creating database schema..."
./create_db.sh

# Step 2: Insert sample data using SQLite directly
echo -e "\nStep 2: Inserting sample data..."

sqlite3 student_management.db << 'EOF' 
-- Insert students
INSERT INTO students (first_name, last_name, date_of_birth, gender, email, phone, address, enrollment_date, grade_level, status) VALUES
('John', 'Smith', '2008-05-15', 'Male', 'john.smith@school.edu', '555-0101', '123 Main St', '2023-08-20', 9, 'Active'),
('Emma', 'Johnson', '2007-11-22', 'Female', 'emma.johnson@school.edu', '555-0102', '456 Oak Ave', '2023-08-20', 10, 'Active'),
('Michael', 'Williams', '2006-03-10', 'Male', 'michael.williams@school.edu', '555-0103', '789 Pine Rd', '2022-08-15', 11, 'Active'),
('Sophia', 'Brown', '2005-07-30', 'Female', 'sophia.brown@school.edu', '555-0104', '321 Elm St', '2022-08-15', 12, 'Active'),
('James', 'Davis', '2009-01-25', 'Male', 'james.davis@school.edu', '555-0105', '654 Maple Dr', '2023-08-20', 9, 'Active'),
('Olivia', 'Miller', '2008-09-18', 'Female', 'olivia.miller@school.edu', '555-0106', '987 Cedar Ln', '2023-08-20', 10, 'Active'),
('William', 'Wilson', '2007-04-12', 'Male', 'william.wilson@school.edu', '555-0107', '147 Birch Way', '2022-08-15', 11, 'Active'),
('Ava', 'Moore', '2006-12-05', 'Female', 'ava.moore@school.edu', '555-0108', '258 Spruce Ct', '2022-08-15', 12, 'Active'),
('Benjamin', 'Taylor', '2009-08-08', 'Male', 'benjamin.taylor@school.edu', '555-0109', '369 Willow Blvd', '2023-08-20', 9, 'Active'),
('Isabella', 'Anderson', '2008-02-14', 'Female', 'isabella.anderson@school.edu', '555-0110', '741 Aspen Pl', '2023-08-20', 10, 'Active');

-- Insert teachers
INSERT INTO teachers (first_name, last_name, date_of_birth, gender, email, phone, address, hire_date, department, qualification) VALUES
('Robert', 'Johnson', '1980-03-15', 'Male', 'robert.johnson@school.edu', '555-0201', '111 Teacher Ln', '2018-08-15', 'Mathematics', 'PhD in Mathematics'),
('Jennifer', 'Davis', '1975-11-22', 'Female', 'jennifer.davis@school.edu', '555-0202', '222 Educator Ave', '2015-01-10', 'Science', 'MSc in Biology'),
('Thomas', 'Wilson', '1982-07-10', 'Male', 'thomas.wilson@school.edu', '555-0203', '333 Professor Rd', '2020-08-20', 'English', 'MA in English Literature'),
('Sarah', 'Thompson', '1978-04-30', 'Female', 'sarah.thompson@school.edu', '555-0204', '444 Instructor St', '2016-03-01', 'History', 'PhD in History'),
('David', 'Martinez', '1985-01-25', 'Male', 'david.martinez@school.edu', '555-0205', '555 Tutor Dr', '2021-08-15', 'Computer Science', 'MSc in Computer Science');

-- Insert courses
INSERT INTO courses (course_code, course_name, description, department, credits, grade_level, semester, academic_year, teacher_id) VALUES
('MATH101', 'Algebra I', 'Introduction to algebraic concepts', 'Mathematics', 3, 9, 'Fall', 2024, 1),
('SCI201', 'Biology', 'Study of living organisms', 'Science', 4, 10, 'Fall', 2024, 2),
('ENG102', 'English Literature', 'Classic and contemporary literature', 'English', 3, 10, 'Fall', 2024, 3),
('HIST301', 'World History', 'Survey of world civilizations', 'History', 3, 11, 'Fall', 2024, 4),
('CS401', 'Introduction to Programming', 'Fundamentals of programming', 'Computer Science', 4, 12, 'Fall', 2024, 5),
('MATH202', 'Geometry', 'Study of shapes and spaces', 'Mathematics', 3, 10, 'Spring', 2024, 1),
('SCI302', 'Chemistry', 'Introduction to chemical principles', 'Science', 4, 11, 'Spring', 2024, 2);

-- Insert enrollments (each student in 3-4 courses)
INSERT INTO enrollments (student_id, course_id, enrollment_date, status) VALUES
(1, 1, '2024-08-25', 'Enrolled'), (1, 2, '2024-08-25', 'Enrolled'), (1, 3, '2024-08-25', 'Enrolled'),
(2, 2, '2024-08-25', 'Enrolled'), (2, 3, '2024-08-25', 'Enrolled'), (2, 4, '2024-08-25', 'Enrolled'),
(3, 3, '2024-08-25', 'Enrolled'), (3, 4, '2024-08-25', 'Enrolled'), (3, 5, '2024-08-25', 'Enrolled'),
(4, 4, '2024-08-25', 'Enrolled'), (4, 5, '2024-08-25', 'Enrolled'), (4, 6, '2024-08-25', 'Enrolled'), 
(5, 5, '2024-08-25', 'Enrolled'), (5, 6, '2024-08-25', 'Enrolled'), (5, 7, '2024-08-25', 'Enrolled'),
(6, 1, '2024-08-25', 'Enrolled'), (6, 6, '2024-08-25', 'Enrolled'), (6, 7, '2024-08-25', 'Enrolled'),
(7, 2, '2024-08-25', 'Enrolled'), (7, 3, '2024-08-25', 'Enrolled'), (7, 4, '2024-08-25', 'Enrolled'),
(8, 3, '2024-08-25', 'Enrolled'), (8, 4, '2024-08-25', 'Enrolled'), (8, 5, '2024-08-25', 'Enrolled'),
(9, 4, '2024-08-25', 'Enrolled'), (9, 5, '2024-08-25', 'Enrolled'), (9, 6, '2024-08-25', 'Enrolled'),
(10, 5, '2024-08-25', 'Enrolled'), (10, 6, '2024-08-25', 'Enrolled'), (10, 7, '2024-08-25', 'Enrolled');

-- Insert holidays
INSERT INTO holidays (holiday_name, holiday_date, holiday_type, description, academic_year) VALUES
('Labor Day', '2024-09-02', 'National', 'Labor Day holiday', 2024),
('Thanksgiving Break', '2024-11-28', 'Break', 'Thanksgiving holiday break', 2024),
('Winter Break', '2024-12-23', 'Break', 'Winter vacation', 2024),
('New Year''s Day', '2025-01-01', 'National', 'New Year holiday', 2024),
('Martin Luther King Jr. Day', '2025-01-20', 'National', 'MLK Day', 2024),
('Spring Break', '2025-03-17', 'Break', 'Spring vacation', 2024),
('Memorial Day', '2025-05-26', 'National', 'Memorial Day', 2024);

-- Insert salaries (3 months for each teacher)
INSERT INTO salaries (teacher_id, salary_amount, payment_date, payment_method, pay_period_start, pay_period_end, deductions, net_amount, status) VALUES
(1, 6250.00, '2024-01-15', 'Bank Transfer', '2024-01-01', '2024-01-31', 937.50, 5312.50, 'Paid'),
(1, 6250.00, '2024-02-15', 'Bank Transfer', '2024-02-01', '2024-02-29', 937.50, 5312.50, 'Paid'),
(1, 6250.00, '2024-03-15', 'Bank Transfer', '2024-03-01', '2024-03-31', 937.50, 5312.50, 'Paid'),
(2, 6833.33, '2024-01-15', 'Bank Transfer', '2024-01-01', '2024-01-31', 1025.00, 5808.33, 'Paid'),
(2, 6833.33, '2024-02-15', 'Bank Transfer', '2024-02-01', '2024-02-29', 1025.00, 5808.33, 'Paid'),
(2, 6833.33, '2024-03-15', 'Bank Transfer', '2024-03-01', '2024-03-31', 1025.00, 5808.33, 'Paid'),
(3, 5666.67, '2024-01-15', 'Bank Transfer', '2024-01-01', '2024-01-31', 850.00, 4816.67, 'Paid'),
(3, 5666.67, '2024-02-15', 'Bank Transfer', '2024-02-01', '2024-02-29', 850.00, 4816.67, 'Paid'),
(3, 5666.67, '2024-03-15', 'Bank Transfer', '2024-03-01', '2024-03-31', 850.00, 4816.67, 'Paid'),
(4, 7500.00, '2024-01-15', 'Bank Transfer', '2024-01-01', '2024-01-31', 1125.00, 6375.00, 'Paid'),
(4, 7500.00, '2024-02-15', 'Bank Transfer', '2024-02-01', '2024-02-29', 1125.00, 6375.00, 'Paid'),
(4, 7500.00, '2024-03-15', 'Bank Transfer', '2024-03-01', '2024-03-31', 1125.00, 6375.00, 'Paid'),
(5, 6000.00, '2024-01-15', 'Bank Transfer', '2024-01-01', '2024-01-31', 900.00, 5100.00, 'Paid'),
(5, 6000.00, '2024-02-15', 'Bank Transfer', '2024-02-01', '2024-02-29', 900.00, 5100.00, 'Paid'),
(5, 6000.00, '2024-03-15', 'Bank Transfer', '2024-03-01', '2024-03-31', 900.00, 5100.00, 'Paid');

-- Insert tuition payments
INSERT INTO tuition_payments (student_id, academic_year, semester, amount_due, amount_paid, payment_date, due_date, payment_method, status) VALUES
(1, 2024, 'Fall', 2500.00, 2500.00, '2024-09-10', '2024-09-15', 'Bank Transfer', 'Paid'),
(1, 2024, 'Spring', 2500.00, 1750.00, '2025-01-10', '2025-01-15', 'Bank Transfer', 'Partial'),
(2, 2024, 'Fall', 2500.00, 2500.00, '2024-09-10', '2024-09-15', 'Bank Transfer', 'Paid'),
(2, 2024, 'Spring', 2500.00, 2500.00, '2025-01-10', '2025-01-15', 'Bank Transfer', 'Paid'),
(3, 2024, 'Fall', 2500.00, 2500.00, '2024-09-10', '2024-09-15', 'Bank Transfer', 'Paid'),
(3, 2024, 'Spring', 2500.00, 0.00, NULL, '2025-01-15', 'Bank Transfer', 'Pending'),
(4, 2024, 'Fall', 2500.00, 2500.00, '2024-09-10', '2024-09-15', 'Bank Transfer', 'Paid'),
(4, 2024, 'Spring', 2500.00, 2500.00, '2025-01-10', '2025-01-15', 'Bank Transfer', 'Paid'),
(5, 2024, 'Fall', 2500.00, 1750.00, '2024-09-10', '2024-09-15', 'Bank Transfer', 'Partial'),
(5, 2024, 'Spring', 2500.00, 2500.00, '2025-01-10', '2025-01-15', 'Bank Transfer', 'Paid'),
(6, 2024, 'Fall', 2500.00, 2500.00, '2024-09-10', '2024-09-15', 'Bank Transfer', 'Paid'),
(6, 2024, 'Spring', 2500.00, 1750.00, '2025-01-10', '2025-01-15', 'Bank Transfer', 'Partial'),
(7, 2024, 'Fall', 2500.00, 2500.00, '2024-09-10', '2024-09-15', 'Bank Transfer', 'Paid'),
(7, 2024, 'Spring', 2500.00, 2500.00, '2025-01-10', '2025-01-15', 'Bank Transfer', 'Paid'),
(8, 2024, 'Fall', 2500.00, 0.00, NULL, '2024-09-15', 'Bank Transfer', 'Pending'),
(8, 2024, 'Spring', 2500.00, 2500.00, '2025-01-10', '2025-01-15', 'Bank Transfer', 'Paid'),
(9, 2024, 'Fall', 2500.00, 2500.00, '2024-09-10', '2024-09-15', 'Bank Transfer', 'Paid'),
(9, 2024, 'Spring', 2500.00, 2500.00, '2025-01-10', '2025-01-15', 'Bank Transfer', 'Paid'),
(10, 2024, 'Fall', 2500.00, 1750.00, '2024-09-10', '2024-09-15', 'Bank Transfer', 'Partial'),
(10, 2024, 'Spring', 2500.00, 0.00, NULL, '2025-01-15', 'Bank Transfer', 'Pending');
EOF

echo "Sample data inserted successfully!"

# Step 3: Verify data
echo -e "\nStep 3: Verifying data..."

echo "Table counts:"
sqlite3 student_management.db << 'EOF'
.headers on
.mode column
SELECT 'students' as table_name, COUNT(*) as record_count FROM students
UNION ALL SELECT 'teachers', COUNT(*) FROM teachers
UNION ALL SELECT 'courses', COUNT(*) FROM courses
UNION ALL SELECT 'enrollments', COUNT(*) FROM enrollments
UNION ALL SELECT 'holidays', COUNT(*) FROM holidays
UNION ALL SELECT 'salaries', COUNT(*) FROM salaries
UNION ALL SELECT 'tuition_payments', COUNT(*) FROM tuition_payments;
EOF

echo -e "\nSample queries for Text-to-SQL testing:\n"
echo "1. Students by grade level:"
sqlite3 student_management.db "SELECT grade_level, COUNT(*) as student_count FROM students GROUP BY grade_level ORDER BY grade_level;"

echo -e "\n2. Teachers by department:"
sqlite3 student_management.db "SELECT department, COUNT(*) as teacher_count FROM teachers GROUP BY department ORDER BY department;"

echo -e "\n3. Course enrollment:"
sqlite3 student_management.db << 'EOF'
.headers on
.mode column
SELECT c.course_name, COUNT(e.student_id) as enrolled_students
FROM courses c
LEFT JOIN enrollments e ON c.course_id = e.course_id
GROUP BY c.course_id
ORDER BY c.course_name;
EOF

echo -e "\n4. Tuition payment status:"
sqlite3 student_management.db "SELECT status, COUNT(*) as payment_count FROM tuition_payments GROUP BY status ORDER BY status;"

echo -e "\n5. Salary payments by teacher:"
sqlite3 student_management.db << 'EOF'
.headers on
.mode column
SELECT t.first_name || ' ' || t.last_name as teacher_name, COUNT(s.salary_id) as payments, SUM(s.net_amount) as total_paid
FROM teachers t
LEFT JOIN salaries s ON t.teacher_id = s.teacher_id
GROUP BY t.teacher_id
ORDER BY teacher_name;
EOF

echo "Database setup completed successfully!"
echo ""
echo "Database ready for Text-to-SQL MVP testing."
echo "Location: student_management.db"