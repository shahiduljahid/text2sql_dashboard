"""
Test LLM service for converting natural language to SQL queries.
This version doesn't load the actual model for testing.
"""
import re
from typing import Optional, Dict, Any
from app.config import settings
from app.models import SQLQuery, QueryType, SchemaMetadata


class LLMServiceTest:
    """Test service for converting natural language to SQL using mock LLM."""

    def __init__(self):
        self.provider = settings.llm_provider
        self.model_path = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.model_type = "local"

    def _get_schema_prompt(self, schema_metadata: SchemaMetadata) -> str:
        """Generate schema description for LLM prompt."""
        prompt = "Database Schema:\n\n"

        for table in schema_metadata.tables:
            prompt += f"Table: {table['table_name']}\n"
            prompt += "Columns:\n"
            for col in table['columns']:
                nullable = "NOT NULL" if col['not_null'] else "NULL"
                pk = "PRIMARY KEY" if col['primary_key'] else ""
                default = f"DEFAULT {col['default_value']}" if col['default_value'] else ""
                prompt += f"  - {col['name']} ({col['type']}) {nullable} {pk} {default}\n".strip() + "\n"
            prompt += "\n"

        if schema_metadata.relationships:
            prompt += "Relationships:\n"
            for rel in schema_metadata.relationships:
                prompt += f"  - {rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}\n"
            prompt += "\n"

        return prompt

    def _get_system_prompt(self, schema_metadata: SchemaMetadata) -> str:
        """Generate system prompt for LLM."""
        schema_text = self._get_schema_prompt(schema_metadata)

        return f"""You are a SQL expert that converts natural language questions to SQL queries.

{schema_text}

Rules:
1. Generate ONLY SQL queries, no explanations or markdown
2. Use proper SQL syntax for SQLite
3. Only use allowed SQL keywords: {', '.join(settings.allowed_sql_keywords)}
4. For SELECT queries, include a LIMIT clause (default LIMIT 100) unless the user explicitly asks for "all", "every", or "complete" records
5. For date comparisons, use SQLite date functions like date(), strftime()
6. Use table and column names exactly as shown in the schema
7. For text searches, use LIKE with % wildcards
8. For counting, use COUNT(*)
9. For aggregations, use GROUP BY with appropriate columns
10. For joins, specify the join condition explicitly

Examples:
Question: "How many students are in grade 9?"
SQL: SELECT COUNT(*) FROM students WHERE grade_level = 9 LIMIT 100

Question: "Show all teachers in the Science department"
SQL: SELECT * FROM teachers WHERE department = 'Science' LIMIT 100

Question: "Return all students"
SQL: SELECT * FROM students

Question: "List students enrolled in Biology course"
SQL: SELECT s.first_name, s.last_name FROM students s JOIN enrollments e ON s.student_id = e.student_id JOIN courses c ON e.course_id = c.course_id WHERE c.course_name = 'Biology' LIMIT 100

Question: "What is the total tuition paid by each student?"
SQL: SELECT student_id, SUM(amount_paid) as total_paid FROM tuition_payments GROUP BY student_id LIMIT 100

Question: "Find students with pending tuition payments"
SQL: SELECT s.first_name, s.last_name FROM students s JOIN tuition_payments tp ON s.student_id = tp.student_id WHERE tp.status = 'Pending' LIMIT 100

Important: Return ONLY the SQL query, nothing else."""

    def generate_sql(self, question: str, schema_metadata: SchemaMetadata) -> SQLQuery:
        """Generate SQL from natural language question using mock responses."""
        # Simple mock responses based on question
        question_lower = question.lower()

        def extract_value_after_keywords(text: str, keywords: list[str]) -> str:
            for keyword in keywords:
                if keyword in text:
                    parts = text.split(keyword, 1)[1].strip().split()
                    if parts:
                        return parts[0].strip("'\".,")
            return ""

        def detect_name(text: str, known_names: list[str]) -> Optional[str]:
            for name in known_names:
                if name in text:
                    return name.capitalize()
            return None

        # Determine appropriate limit based on question type
        limit = 100  # Default limit

        # Handle update-style requests first so they don't fall through to SELECT.
        if any(word in question_lower for word in ["update", "change", "modify", "set "]):
            known_student_names = ["john", "emma", "michael", "sophia", "robert", "mary", "maria"]
            known_teacher_names = ["robert", "jennifer", "thomas", "john", "mary", "maria", "emma", "michael", "sophia"]

            table = "students"
            name = detect_name(question_lower, known_student_names) or detect_name(question_lower, known_teacher_names)
            if "teacher" in question_lower or (name and name in [n.capitalize() for n in known_teacher_names]):
                table = "teachers"
            elif "course" in question_lower:
                table = "courses"
            elif "enrollment" in question_lower:
                table = "enrollments"

            tokens = [token.strip("'\".,") for token in question_lower.split()]
            fields = {
                "gender": "gender",
                "status": "status",
                "department": "department",
                "grade": "grade_level",
                "grade_level": "grade_level",
                "email": "email",
                "phone": "phone",
                "address": "address",
                "first name": "first_name",
                "last name": "last_name",
            }

            field = None
            value = None
            subject_name = None

            joined = " ".join(tokens)
            for label, column_name in fields.items():
                if label in joined:
                    field = column_name
                    remainder = joined.split(label, 1)[1].strip()
                    if remainder.startswith("to "):
                        remainder = remainder[3:].strip()
                    if remainder:
                        value_token = remainder.split()[0].strip("'\".,")
                        value = value_token.capitalize() if value_token.isalpha() else value_token
                    break

            if len(tokens) >= 2:
                candidate_name = tokens[1]
                if candidate_name not in fields and candidate_name not in {"student", "students", "teacher", "teachers"}:
                    subject_name = candidate_name

            if subject_name is None:
                for index, token in enumerate(tokens):
                    if token in {"student", "students", "teacher", "teachers"} and index + 1 < len(tokens):
                        next_token = tokens[index + 1]
                        if next_token not in fields and next_token not in {"to", "the"}:
                            subject_name = next_token
                            break

            if field is None and len(tokens) >= 3:
                # Pattern: update emma gender male
                candidate_field = tokens[2] if len(tokens) > 2 else ""
                if candidate_field in fields:
                    field = fields[candidate_field]
                    if len(tokens) > 3:
                        value = tokens[3].capitalize() if tokens[3].isalpha() else tokens[3]

            if field is None:
                field = "status"
            if value is None:
                value = "Active"

            target_name = name or subject_name

            if target_name:
                sql = f"UPDATE {table} SET {field} = '{value}' WHERE first_name LIKE '%{target_name}%' OR last_name LIKE '%{target_name}%'"
            else:
                sql = f"UPDATE {table} SET {field} = '{value}'"

            sql_upper = sql.upper()
            generated_type = QueryType.UPDATE
            explanation = self._generate_explanation(question, sql, generated_type)

            return SQLQuery(
                sql=sql,
                explanation=explanation,
                query_type=generated_type,
                parameters=None
            )

        # Check for counting questions
        if any(word in question_lower for word in ["how many", "count", "number of", "total"]):
            if "student" in question_lower:
                if "grade" in question_lower:
                    if "10" in question_lower:
                        sql = "SELECT COUNT(*) FROM students WHERE grade_level = 10"
                    elif "11" in question_lower:
                        sql = "SELECT COUNT(*) FROM students WHERE grade_level = 11"
                    elif "12" in question_lower:
                        sql = "SELECT COUNT(*) FROM students WHERE grade_level = 12"
                    else:
                        sql = "SELECT COUNT(*) FROM students WHERE grade_level = 9"
                else:
                    sql = "SELECT COUNT(*) FROM students"
                limit = None  # No limit for COUNT queries
            elif "teacher" in question_lower:
                if "department" in question_lower:
                    if "science" in question_lower:
                        sql = "SELECT COUNT(*) FROM teachers WHERE department = 'Science'"
                    elif "math" in question_lower:
                        sql = "SELECT COUNT(*) FROM teachers WHERE department = 'Mathematics'"
                    else:
                        sql = "SELECT COUNT(*) FROM teachers"
                else:
                    sql = "SELECT COUNT(*) FROM teachers"
                limit = None
            elif "course" in question_lower:
                sql = "SELECT COUNT(*) FROM courses"
                limit = None
            else:
                sql = "SELECT COUNT(*) FROM students"
                limit = None
        # Check for specific filtering
        elif "student" in question_lower and "grade" in question_lower:
            if "10" in question_lower:
                sql = "SELECT * FROM students WHERE grade_level = 10"
            elif "11" in question_lower:
                sql = "SELECT * FROM students WHERE grade_level = 11"
            elif "12" in question_lower:
                sql = "SELECT * FROM students WHERE grade_level = 12"
            else:
                sql = "SELECT * FROM students WHERE grade_level = 9"
        elif "teacher" in question_lower and "department" in question_lower:
            if "science" in question_lower:
                sql = "SELECT * FROM teachers WHERE department = 'Science'"
            elif "math" in question_lower:
                sql = "SELECT * FROM teachers WHERE department = 'Mathematics'"
            elif "english" in question_lower:
                sql = "SELECT * FROM teachers WHERE department = 'English'"
            else:
                sql = "SELECT * FROM teachers WHERE department = 'Science'"
        # Check for teacher queries (including name searches)
        elif "teacher" in question_lower:
            # Check for department-specific queries first
            if "science" in question_lower:
                sql = "SELECT * FROM teachers WHERE department = 'Science'"
            elif "math" in question_lower:
                sql = "SELECT * FROM teachers WHERE department = 'Mathematics'"
            elif "english" in question_lower:
                sql = "SELECT * FROM teachers WHERE department = 'English'"
            elif "history" in question_lower:
                sql = "SELECT * FROM teachers WHERE department = 'History'"
            elif "computer" in question_lower:
                sql = "SELECT * FROM teachers WHERE department = 'Computer Science'"
            else:
                # Check if looking for a specific teacher by name
                teacher_names = ["robert", "jennifer", "thomas", "john", "mary", "maria", "emma", "michael", "sophia"]
                found_name = None
                for name in teacher_names:
                    if name in question_lower:
                        found_name = name
                        break

                if found_name:
                    # Capitalize first letter for proper name matching
                    capitalized_name = found_name.capitalize()
                    # Check if query contains "only" - should return specific teacher only
                    if "only" in question_lower:
                        sql = f"SELECT * FROM teachers WHERE first_name = '{capitalized_name}'"
                    else:
                        sql = f"SELECT * FROM teachers WHERE first_name LIKE '%{capitalized_name}%' OR last_name LIKE '%{capitalized_name}%'"
                else:
                    # Try to extract a name from the query even if not in known names list
                    # Look for common name patterns in the question
                    name_match = re.search(r'\b(return only teacher name |teacher name |name )?(\w+)\b', question_lower)
                    if name_match:
                        potential_name = name_match.group(2)
                        # Skip common words that aren't names
                        skip_words = ["teacher", "teachers", "name", "only", "return", "show", "get", "list", "all", "the", "a", "an", "and", "or", "in", "on", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "from", "up", "down", "out", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"]

                        if potential_name not in skip_words and len(potential_name) > 2:
                            capitalized_name = potential_name.capitalize()
                            if "only" in question_lower:
                                sql = f"SELECT * FROM teachers WHERE first_name = '{capitalized_name}' OR last_name = '{capitalized_name}'"
                            else:
                                sql = f"SELECT * FROM teachers WHERE first_name LIKE '%{capitalized_name}%' OR last_name LIKE '%{capitalized_name}%'"
                        else:
                            # No valid name found, check if asking for all teachers
                            if any(word in question_lower for word in ["all", "list", "show", "return", "get"]):
                                sql = "SELECT * FROM teachers"
                            else:
                                # Default to all teachers (existing behavior)
                                sql = "SELECT * FROM teachers"
                    else:
                        # No name pattern found
                        if any(word in question_lower for word in ["all", "list", "show", "return", "get"]):
                            sql = "SELECT * FROM teachers"
                        else:
                            sql = "SELECT * FROM teachers"
        # Check for student queries (including name searches)
        elif "student" in question_lower:
            # Check if looking for a specific student by name
            student_names = ["john", "emma", "michael", "sophia", "robert", "mary", "maria"]
            found_name = None
            for name in student_names:
                if name in question_lower:
                    found_name = name
                    break

            if found_name:
                # Capitalize first letter for proper name matching
                capitalized_name = found_name.capitalize()
                # Check if query contains "only" - should return specific student only
                if "only" in question_lower:
                    sql = f"SELECT * FROM students WHERE first_name = '{capitalized_name}'"
                else:
                    sql = f"SELECT * FROM students WHERE first_name LIKE '%{capitalized_name}%' OR last_name LIKE '%{capitalized_name}%'"
            else:
                # Try to extract a name from the query even if not in known names list
                # Look for common name patterns in the question
                name_match = re.search(r'\b(return only student name |student name |name )?(\w+)\b', question_lower)
                if name_match:
                    potential_name = name_match.group(2)
                    # Skip common words that aren't names
                    skip_words = ["student", "students", "name", "only", "return", "show", "get", "list", "all", "the", "a", "an", "and", "or", "in", "on", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "from", "up", "down", "out", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"]

                    if potential_name not in skip_words and len(potential_name) > 2:
                        capitalized_name = potential_name.capitalize()
                        if "only" in question_lower:
                            sql = f"SELECT * FROM students WHERE first_name = '{capitalized_name}' OR last_name = '{capitalized_name}'"
                        else:
                            sql = f"SELECT * FROM students WHERE first_name LIKE '%{capitalized_name}%' OR last_name LIKE '%{capitalized_name}%'"
                    else:
                        # No valid name found, check if asking for all students
                        if any(word in question_lower for word in ["all", "list", "show", "return", "get"]):
                            sql = "SELECT * FROM students"
                        else:
                            # Default to all students (existing behavior)
                            sql = "SELECT * FROM students"
                else:
                    # No name pattern found
                    if any(word in question_lower for word in ["all", "list", "show", "return", "get"]):
                        sql = "SELECT * FROM students"
                    else:
                        sql = "SELECT * FROM students"
        elif "course" in question_lower:
            sql = "SELECT * FROM courses"
        elif "enrollment" in question_lower:
            sql = "SELECT * FROM enrollments"
        elif "tuition" in question_lower:
            sql = "SELECT * FROM tuition_payments"
        elif "salary" in question_lower:
            sql = "SELECT * FROM salaries"
        elif "holiday" in question_lower:
            sql = "SELECT * FROM holidays"
        # Check for general "all" queries
        elif any(word in question_lower for word in ["all", "list", "show", "return", "get"]):
            # Try to determine which table based on context
            if "teacher" in question_lower:
                sql = "SELECT * FROM teachers"
            elif "student" in question_lower:
                sql = "SELECT * FROM students"
            elif "course" in question_lower:
                sql = "SELECT * FROM courses"
            else:
                sql = "SELECT * FROM students"
        else:
            sql = "SELECT * FROM students"

        # Add LIMIT clause if appropriate
        # Don't add LIMIT for queries explicitly asking for "all" records
        if limit and not sql.upper().startswith("SELECT COUNT") and not any(word in question_lower for word in ["all", "every", "complete"]):
            sql += f" LIMIT {limit}"

        # Determine query type from generated SQL
        sql_upper = sql.upper()
        if sql_upper.startswith('SELECT'):
            generated_type = QueryType.SELECT
        elif sql_upper.startswith('INSERT'):
            generated_type = QueryType.INSERT
        elif sql_upper.startswith('UPDATE'):
            generated_type = QueryType.UPDATE
        elif sql_upper.startswith('DELETE'):
            generated_type = QueryType.DELETE
        else:
            generated_type = QueryType.SELECT  # Default

        # Generate explanation
        explanation = self._generate_explanation(question, sql, generated_type)

        return SQLQuery(
            sql=sql,
            explanation=explanation,
            query_type=generated_type,
            parameters=None  # LLM doesn't generate parameters
        )

    def _generate_explanation(self, question: str, sql: str, query_type: QueryType) -> str:
        """Generate human-readable explanation of the SQL query."""
        if query_type == QueryType.SELECT:
            return f"This query answers '{question}' by selecting data from the database."
        elif query_type == QueryType.INSERT:
            return f"This query adds a new record based on '{question}'."
        elif query_type == QueryType.UPDATE:
            return f"This query updates existing records based on '{question}'."
        elif query_type == QueryType.DELETE:
            return f"This query removes records based on '{question}'."
        else:
            return f"This query processes '{question}'."

    def health_check(self) -> Dict[str, Any]:
        """Check LLM service health."""
        return {
            "llm_available": True,
            "provider": self.provider,
            "model_type": self.model_type,
            "device": "cpu",
            "note": "Test mode - using mock responses"
        }


# Create global test LLM service instance
llm_service_test = LLMServiceTest()