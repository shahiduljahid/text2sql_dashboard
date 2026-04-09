#!/usr/bin/env python3
"""Generate 1000 NL->SQL gold pairs, call /ask-query, and evaluate predictions."""

from __future__ import annotations

import argparse
import json
import random
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import httpx


@dataclass
class QAItem:
    question: str
    gold_sql: str
    template: str


def sql_quote(value: str) -> str:
    return value.replace("'", "''")


def normalize_sql(sql: str) -> str:
    sql = sql.strip().rstrip(";")
    sql = re.sub(r"\s+", " ", sql)
    return sql.lower()


def is_safe_select(sql: str) -> bool:
    sql_norm = sql.strip().lower()
    return sql_norm.startswith("select") and ";" not in sql_norm


def fetch_pool(cursor: sqlite3.Cursor, query: str) -> list:
    cursor.execute(query)
    return [row[0] for row in cursor.fetchall() if row and row[0] is not None]


def build_templates(cursor: sqlite3.Cursor) -> list[Callable[[], QAItem]]:
    first_names = fetch_pool(cursor, "SELECT DISTINCT first_name FROM students LIMIT 2000")
    full_names = [
        (row[0], row[1])
        for row in cursor.execute("SELECT first_name, last_name FROM students LIMIT 2000").fetchall()
    ]
    grades = fetch_pool(cursor, "SELECT DISTINCT grade_level FROM students ORDER BY grade_level")
    student_statuses = fetch_pool(cursor, "SELECT DISTINCT status FROM students")
    teacher_departments = fetch_pool(cursor, "SELECT DISTINCT department FROM teachers")
    teacher_statuses = fetch_pool(cursor, "SELECT DISTINCT status FROM teachers")
    course_departments = fetch_pool(cursor, "SELECT DISTINCT department FROM courses")
    semesters = fetch_pool(cursor, "SELECT DISTINCT semester FROM courses")
    payment_statuses = fetch_pool(cursor, "SELECT DISTINCT status FROM tuition_payments")
    course_names = fetch_pool(cursor, "SELECT DISTINCT course_name FROM courses LIMIT 500")

    if not all([first_names, full_names, grades, teacher_departments, semesters, payment_statuses, course_names]):
        raise RuntimeError("Database does not have enough seed data to generate evaluation set.")

    def t_all_students() -> QAItem:
        return QAItem(
            question="Return all student data",
            gold_sql="SELECT * FROM students LIMIT 100",
            template="all_students",
        )

    def t_students_grade() -> QAItem:
        grade = random.choice(grades)
        return QAItem(
            question=f"Show all students in grade {grade}",
            gold_sql=f"SELECT * FROM students WHERE grade_level = {grade} LIMIT 100",
            template="students_by_grade",
        )

    def t_count_students_grade() -> QAItem:
        grade = random.choice(grades)
        return QAItem(
            question=f"How many students are in grade {grade}?",
            gold_sql=f"SELECT COUNT(*) AS count FROM students WHERE grade_level = {grade}",
            template="count_students_grade",
        )

    def t_students_first_name() -> QAItem:
        name = random.choice(first_names)
        q = sql_quote(name)
        return QAItem(
            question=f"List students with first name {name}",
            gold_sql=f"SELECT * FROM students WHERE first_name = '{q}' LIMIT 100",
            template="students_first_name",
        )

    def t_student_full_name() -> QAItem:
        first, last = random.choice(full_names)
        fq = sql_quote(first)
        lq = sql_quote(last)
        return QAItem(
            question=f"Return student name {first} {last}",
            gold_sql=(
                "SELECT first_name, last_name, grade_level, status FROM students "
                f"WHERE first_name = '{fq}' AND last_name = '{lq}' LIMIT 100"
            ),
            template="student_full_name",
        )

    def t_students_status() -> QAItem:
        status = random.choice(student_statuses)
        sq = sql_quote(status)
        return QAItem(
            question=f"Show students with status {status}",
            gold_sql=f"SELECT * FROM students WHERE status = '{sq}' LIMIT 100",
            template="students_status",
        )

    def t_teachers_department() -> QAItem:
        dept = random.choice(teacher_departments)
        dq = sql_quote(dept)
        return QAItem(
            question=f"Show all teachers in {dept} department",
            gold_sql=f"SELECT * FROM teachers WHERE department = '{dq}' LIMIT 100",
            template="teachers_department",
        )

    def t_count_teachers_department() -> QAItem:
        dept = random.choice(teacher_departments)
        dq = sql_quote(dept)
        return QAItem(
            question=f"How many teachers are in {dept} department?",
            gold_sql=f"SELECT COUNT(*) AS count FROM teachers WHERE department = '{dq}'",
            template="count_teachers_department",
        )

    def t_teachers_status() -> QAItem:
        status = random.choice(teacher_statuses)
        sq = sql_quote(status)
        return QAItem(
            question=f"List teachers with status {status}",
            gold_sql=f"SELECT * FROM teachers WHERE status = '{sq}' LIMIT 100",
            template="teachers_status",
        )

    def t_courses_department() -> QAItem:
        dept = random.choice(course_departments)
        dq = sql_quote(dept)
        return QAItem(
            question=f"Show courses from {dept}",
            gold_sql=f"SELECT * FROM courses WHERE department = '{dq}' LIMIT 100",
            template="courses_department",
        )

    def t_courses_semester() -> QAItem:
        sem = random.choice(semesters)
        sq = sql_quote(sem)
        return QAItem(
            question=f"List courses offered in {sem} semester",
            gold_sql=f"SELECT * FROM courses WHERE semester = '{sq}' LIMIT 100",
            template="courses_semester",
        )

    def t_course_name() -> QAItem:
        course = random.choice(course_names)
        cq = sql_quote(course)
        return QAItem(
            question=f"Find course named {course}",
            gold_sql=f"SELECT * FROM courses WHERE course_name = '{cq}' LIMIT 100",
            template="course_name",
        )

    def t_enrollments_grade() -> QAItem:
        grade = random.choice(grades)
        return QAItem(
            question=f"Show enrollments for students in grade {grade}",
            gold_sql=(
                "SELECT e.enrollment_id, e.student_id, e.course_id, e.status "
                "FROM enrollments e JOIN students s ON e.student_id = s.student_id "
                f"WHERE s.grade_level = {grade} LIMIT 100"
            ),
            template="enrollments_grade",
        )

    def t_pending_tuition() -> QAItem:
        status = random.choice(payment_statuses)
        sq = sql_quote(status)
        return QAItem(
            question=f"Show tuition payments with status {status}",
            gold_sql=f"SELECT * FROM tuition_payments WHERE status = '{sq}' LIMIT 100",
            template="tuition_status",
        )

    def t_count_pending_tuition() -> QAItem:
        status = random.choice(payment_statuses)
        sq = sql_quote(status)
        return QAItem(
            question=f"How many tuition payments are {status}?",
            gold_sql=f"SELECT COUNT(*) AS count FROM tuition_payments WHERE status = '{sq}'",
            template="count_tuition_status",
        )

    def t_teacher_salary_avg_dept() -> QAItem:
        dept = random.choice(teacher_departments)
        dq = sql_quote(dept)
        return QAItem(
            question=f"What is the average salary for teachers in {dept}?",
            gold_sql=(
                "SELECT AVG(sa.salary_amount) AS avg_salary "
                "FROM salaries sa JOIN teachers t ON sa.teacher_id = t.teacher_id "
                f"WHERE t.department = '{dq}'"
            ),
            template="avg_salary_department",
        )

    return [
        t_all_students,
        t_students_grade,
        t_count_students_grade,
        t_students_first_name,
        t_student_full_name,
        t_students_status,
        t_teachers_department,
        t_count_teachers_department,
        t_teachers_status,
        t_courses_department,
        t_courses_semester,
        t_course_name,
        t_enrollments_grade,
        t_pending_tuition,
        t_count_pending_tuition,
        t_teacher_salary_avg_dept,
    ]


def execute_sql_readonly(conn: sqlite3.Connection, sql: str) -> tuple[bool, list[tuple], str]:
    try:
        cur = conn.execute(sql)
        rows = cur.fetchall()
        # Compare as sorted tuple list to avoid ORDER BY sensitivity.
        normalized_rows = sorted(tuple(str(v) for v in row) for row in rows)
        return True, normalized_rows, ""
    except Exception as exc:
        return False, [], str(exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and evaluate 1000 NL-SQL pairs via /ask-query")
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--api-base", type=str, default="http://127.0.0.1:8000")
    parser.add_argument("--db-path", type=str, default="student_management.db")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    backend_dir = Path(__file__).resolve().parents[1]
    out_dir = backend_dir / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = out_dir / f"generated_qa_{args.count}.jsonl"
    predictions_path = out_dir / f"predictions_{args.count}.jsonl"
    metrics_path = out_dir / f"metrics_{args.count}.json"

    db_file = (backend_dir / args.db_path).resolve()
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    templates = build_templates(cursor)
    qa_items: list[QAItem] = [random.choice(templates)() for _ in range(args.count)]

    with dataset_path.open("w", encoding="utf-8") as f:
        for idx, item in enumerate(qa_items, start=1):
            f.write(json.dumps({"id": idx, "question": item.question, "gold_sql": item.gold_sql, "template": item.template}) + "\n")

    readonly = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)

    total = len(qa_items)
    api_ok = 0
    pred_nonempty = 0
    pred_select = 0
    pred_exec_ok = 0
    exact_sql_match = 0
    execution_match = 0

    start = time.time()
    with httpx.Client(timeout=120.0) as client, predictions_path.open("w", encoding="utf-8") as out:
        for idx, item in enumerate(qa_items, start=1):
            try:
                resp = client.post(f"{args.api_base}/ask-query", json={"question": item.question})
                payload = resp.json()
            except Exception as exc:
                payload = {"success": False, "error_message": str(exc), "sql": ""}
                resp = None

            if resp is not None and resp.status_code == 200:
                api_ok += 1

            pred_sql = (payload.get("sql") or "").strip()
            if pred_sql:
                pred_nonempty += 1

            pred_is_select = is_safe_select(pred_sql)
            if pred_is_select:
                pred_select += 1

            gold_ok, gold_rows, gold_err = execute_sql_readonly(readonly, item.gold_sql)
            pred_ok, pred_rows, pred_err = execute_sql_readonly(readonly, pred_sql) if pred_is_select else (False, [], "non-select or unsafe sql")

            if pred_ok:
                pred_exec_ok += 1

            if normalize_sql(pred_sql) == normalize_sql(item.gold_sql):
                exact_sql_match += 1

            is_exec_match = bool(gold_ok and pred_ok and gold_rows == pred_rows)
            if is_exec_match:
                execution_match += 1

            out.write(
                json.dumps(
                    {
                        "id": idx,
                        "question": item.question,
                        "template": item.template,
                        "gold_sql": item.gold_sql,
                        "pred_sql": pred_sql,
                        "api_status": resp.status_code if resp is not None else None,
                        "api_success": payload.get("success", False),
                        "api_error": payload.get("error_message") or payload.get("error") or "",
                        "gold_exec_ok": gold_ok,
                        "gold_exec_error": gold_err,
                        "pred_exec_ok": pred_ok,
                        "pred_exec_error": pred_err,
                        "exact_sql_match": normalize_sql(pred_sql) == normalize_sql(item.gold_sql),
                        "execution_match": is_exec_match,
                    }
                )
                + "\n"
            )

            if idx % 50 == 0:
                elapsed = time.time() - start
                print(f"Processed {idx}/{total} in {elapsed:.1f}s")

    elapsed = time.time() - start
    metrics = {
        "count": total,
        "api_ok_rate": api_ok / total if total else 0.0,
        "pred_nonempty_rate": pred_nonempty / total if total else 0.0,
        "pred_select_rate": pred_select / total if total else 0.0,
        "pred_exec_ok_rate": pred_exec_ok / total if total else 0.0,
        "exact_sql_match_rate": exact_sql_match / total if total else 0.0,
        "execution_match_rate": execution_match / total if total else 0.0,
        "runtime_seconds": elapsed,
        "seed": args.seed,
        "api_base": args.api_base,
        "dataset_file": str(dataset_path),
        "predictions_file": str(predictions_path),
    }

    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("\nEvaluation complete")
    print(json.dumps(metrics, indent=2))
    print(f"Dataset: {dataset_path}")
    print(f"Predictions: {predictions_path}")
    print(f"Metrics: {metrics_path}")


if __name__ == "__main__":
    main()
