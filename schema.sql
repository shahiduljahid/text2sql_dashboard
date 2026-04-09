-- Student Management System Database Schema
-- Created for Text-to-SQL MVP

-- 1. Students table
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
    email TEXT UNIQUE,
    phone TEXT,
    address TEXT,
    enrollment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    grade_level INTEGER CHECK(grade_level BETWEEN 1 AND 12),
    status TEXT CHECK(status IN ('Active', 'Inactive', 'Graduated', 'Transferred')) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Teachers table
CREATE TABLE IF NOT EXISTS teachers (
    teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    address TEXT,
    hire_date DATE NOT NULL DEFAULT CURRENT_DATE,
    department TEXT NOT NULL,
    qualification TEXT,
    status TEXT CHECK(status IN ('Active', 'Inactive', 'On Leave', 'Retired')) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Courses table
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT UNIQUE NOT NULL,
    course_name TEXT NOT NULL,
    description TEXT,
    department TEXT NOT NULL,
    credits INTEGER NOT NULL CHECK(credits > 0),
    grade_level INTEGER CHECK(grade_level BETWEEN 1 AND 12),
    semester TEXT CHECK(semester IN ('Fall', 'Spring', 'Summer')),
    academic_year INTEGER,
    teacher_id INTEGER,
    max_capacity INTEGER DEFAULT 30,
    current_enrollment INTEGER DEFAULT 0,
    status TEXT CHECK(status IN ('Active', 'Inactive', 'Archived')) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE SET NULL
);

-- 4. Enrollments table (junction table for students and courses)
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    academic_year INTEGER,
    enrollment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    drop_date DATE,
    grade TEXT CHECK(grade IN ('A', 'B', 'C', 'D', 'F', 'I', 'W')),
    status TEXT CHECK(status IN ('Enrolled', 'Dropped', 'Completed', 'Failed')) DEFAULT 'Enrolled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    UNIQUE(student_id, course_id, academic_year)
);

-- 5. Holidays table
CREATE TABLE IF NOT EXISTS holidays (
    holiday_id INTEGER PRIMARY KEY AUTOINCREMENT,
    holiday_name TEXT NOT NULL,
    holiday_date DATE NOT NULL,
    holiday_type TEXT CHECK(holiday_type IN ('National', 'Religious', 'School', 'Break')) DEFAULT 'School',
    description TEXT,
    academic_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(holiday_date, holiday_name)
);

-- 6. Salaries table
CREATE TABLE IF NOT EXISTS salaries (
    salary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL,
    salary_amount DECIMAL(10, 2) NOT NULL CHECK(salary_amount > 0),
    payment_date DATE NOT NULL,
    payment_method TEXT CHECK(payment_method IN ('Bank Transfer', 'Check', 'Cash')) DEFAULT 'Bank Transfer',
    pay_period_start DATE NOT NULL,
    pay_period_end DATE NOT NULL,
    deductions DECIMAL(10, 2) DEFAULT 0,
    net_amount DECIMAL(10, 2) GENERATED ALWAYS AS (salary_amount - deductions) STORED,
    status TEXT CHECK(status IN ('Paid', 'Pending', 'Cancelled')) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE CASCADE,
    CHECK(pay_period_start <= pay_period_end)
);

-- 7. Tuition payments table
CREATE TABLE IF NOT EXISTS tuition_payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    academic_year INTEGER NOT NULL,
    semester TEXT CHECK(semester IN ('Fall', 'Spring', 'Summer', 'Full Year')),
    amount_due DECIMAL(10, 2) NOT NULL CHECK(amount_due >= 0),
    amount_paid DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK(amount_paid >= 0),
    payment_date DATE,
    due_date DATE NOT NULL,
    payment_method TEXT CHECK(payment_method IN ('Bank Transfer', 'Check', 'Cash', 'Online')),
    status TEXT CHECK(status IN ('Paid', 'Partial', 'Overdue', 'Pending')) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    CHECK(amount_paid <= amount_due),
    CHECK(due_date >= payment_date OR payment_date IS NULL)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_students_grade ON students(grade_level);
CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);
CREATE INDEX IF NOT EXISTS idx_teachers_department ON teachers(department);
CREATE INDEX IF NOT EXISTS idx_courses_teacher ON courses(teacher_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_holidays_date ON holidays(holiday_date);
CREATE INDEX IF NOT EXISTS idx_salaries_teacher ON salaries(teacher_id);
CREATE INDEX IF NOT EXISTS idx_salaries_date ON salaries(payment_date);
CREATE INDEX IF NOT EXISTS idx_tuition_student ON tuition_payments(student_id);
CREATE INDEX IF NOT EXISTS idx_tuition_status ON tuition_payments(status);

-- Create triggers for updated_at timestamps
CREATE TRIGGER IF NOT EXISTS update_students_timestamp
AFTER UPDATE ON students
BEGIN
    UPDATE students SET updated_at = CURRENT_TIMESTAMP WHERE student_id = NEW.student_id;
END;

CREATE TRIGGER IF NOT EXISTS update_teachers_timestamp
AFTER UPDATE ON teachers
BEGIN
    UPDATE teachers SET updated_at = CURRENT_TIMESTAMP WHERE teacher_id = NEW.teacher_id;
END;

CREATE TRIGGER IF NOT EXISTS update_courses_timestamp
AFTER UPDATE ON courses
BEGIN
    UPDATE courses SET updated_at = CURRENT_TIMESTAMP WHERE course_id = NEW.course_id;
END;

CREATE TRIGGER IF NOT EXISTS update_enrollments_timestamp
AFTER UPDATE ON enrollments
BEGIN
    UPDATE enrollments SET updated_at = CURRENT_TIMESTAMP WHERE enrollment_id = NEW.enrollment_id;
END;

CREATE TRIGGER IF NOT EXISTS update_tuition_timestamp
AFTER UPDATE ON tuition_payments
BEGIN
    UPDATE tuition_payments SET updated_at = CURRENT_TIMESTAMP WHERE payment_id = NEW.payment_id;
END;

-- Create trigger to update course enrollment count
CREATE TRIGGER IF NOT EXISTS update_course_enrollment_after_insert
AFTER INSERT ON enrollments
BEGIN
    UPDATE courses
    SET current_enrollment = current_enrollment + 1
    WHERE course_id = NEW.course_id AND NEW.status = 'Enrolled';
END;

CREATE TRIGGER IF NOT EXISTS update_course_enrollment_after_update
AFTER UPDATE ON enrollments
WHEN OLD.status != NEW.status
BEGIN
    UPDATE courses
    SET current_enrollment = current_enrollment +
        CASE
            WHEN NEW.status = 'Enrolled' AND OLD.status != 'Enrolled' THEN 1
            WHEN NEW.status != 'Enrolled' AND OLD.status = 'Enrolled' THEN -1
            ELSE 0
        END
    WHERE course_id = NEW.course_id;
END;