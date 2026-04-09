"""
LLM service for converting natural language to SQL queries.
"""
import json
import inspect
import os
import re
import httpx
from typing import Optional, Dict, Any
from app.config import settings
from app.models import SQLQuery, QueryType, SchemaMetadata

try:
    import torch
except Exception:
    torch = None


class LLMService:
    """Service for converting natural language to SQL using LLMs."""

    def __init__(self):
        self.provider = settings.llm_provider
        self.model_path = settings.llm_model
        self.requested_device = getattr(settings, "llm_device", "auto")
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.modal_endpoint_url = getattr(settings, "modal_endpoint_url", None)
        self.modal_api_key = getattr(settings, "modal_api_key", None)
        self.modal_timeout_seconds = getattr(settings, "modal_timeout_seconds", 120)
        self.model = None
        self.tokenizer = None
        self.device = None

        if self.provider == "openai":
            import openai
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
            self.model_type = "openai"
        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            self.model_type = "anthropic"
        elif self.provider == "local":
            self.model_type = "local"
            self._load_local_model()
        elif self.provider == "modal":
            self.model_type = "modal"
            if not self.modal_endpoint_url:
                raise ValueError("LLM_PROVIDER=modal requires MODAL_ENDPOINT_URL")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _resolve_local_base_model_path(self, repo_id: str) -> Optional[str]:
        """Resolve a locally cached Hugging Face snapshot path for the base model."""
        repo_dir_name = f"models--{repo_id.replace('/', '--')}"
        search_roots = [
            os.path.join(os.path.dirname(__file__), "..", "hub"),
            os.path.join(os.path.dirname(__file__), "..", "transformers"),
        ]

        for root in search_roots:
            model_root = os.path.abspath(os.path.join(root, repo_dir_name))
            refs_main = os.path.join(model_root, "refs", "main")
            snapshots_dir = os.path.join(model_root, "snapshots")

            if os.path.exists(refs_main):
                with open(refs_main, "r", encoding="utf-8") as f:
                    commit = f.read().strip()
                candidate = os.path.join(snapshots_dir, commit)
                if os.path.exists(os.path.join(candidate, "config.json")):
                    return candidate

            if os.path.isdir(snapshots_dir):
                for snapshot in os.listdir(snapshots_dir):
                    candidate = os.path.join(snapshots_dir, snapshot)
                    if os.path.exists(os.path.join(candidate, "config.json")):
                        return candidate

        return None

    def _load_local_model(self):
        """Load the local fine-tuned model."""
        try:
            if torch is None:
                raise RuntimeError(
                    "Local provider requires torch/transformers dependencies. "
                    "Install local extras or switch LLM_PROVIDER to modal/openai/anthropic."
                )

            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import PeftModel, LoraConfig

            print(f"Loading local model from: {self.model_path}")

            # Check if model path is relative or absolute
            import os
            if not os.path.isabs(self.model_path):
                model_full_path = os.path.join(os.path.dirname(__file__), "..", self.model_path)
            else:
                model_full_path = self.model_path

            # Set device from config (auto/cpu/cuda)
            requested_device = (self.requested_device or "auto").lower()
            if requested_device == "cuda":
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            elif requested_device == "cpu":
                self.device = "cpu"
            else:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"

            print(f"Using device: {self.device}")

            # Load base model and tokenizer
            base_model_repo = "Qwen/Qwen2.5-Coder-7B-Instruct"
            resolved_base_model = self._resolve_local_base_model_path(base_model_repo)
            base_model_name = resolved_base_model or base_model_repo
            local_files_only = resolved_base_model is not None
            print(f"Loading base model: {base_model_name}")

            self.tokenizer = AutoTokenizer.from_pretrained(
                base_model_name,
                trust_remote_code=True,
                local_files_only=local_files_only
            )

            model_dtype = torch.float16 if self.device == "cuda" else torch.float32
            model_device_map = {"": 0} if self.device == "cuda" else None
            print(f"Requested device: {requested_device}")

            model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=model_dtype,
                device_map=model_device_map,
                low_cpu_mem_usage=self.device == "cuda",
                trust_remote_code=True,
                local_files_only=local_files_only
            )

            # Load LoRA adapter with backward-compatible config filtering.
            peft_config = None
            adapter_config_path = os.path.join(model_full_path, "adapter_config.json")

            if os.path.exists(adapter_config_path):
                with open(adapter_config_path, "r", encoding="utf-8") as f:
                    adapter_cfg = json.load(f)

                supported_fields = {
                    name for name in inspect.signature(LoraConfig.__init__).parameters.keys()
                    if name != "self"
                }
                filtered_cfg = {k: v for k, v in adapter_cfg.items() if k in supported_fields}
                removed_fields = sorted(set(adapter_cfg.keys()) - set(filtered_cfg.keys()))

                if removed_fields:
                    print(f"Adapter config compatibility: removed unsupported fields: {', '.join(removed_fields)}")
                    peft_config = LoraConfig(**filtered_cfg)

            print(f"Loading LoRA adapter from: {model_full_path}")
            self.model = PeftModel.from_pretrained(
                model,
                model_full_path,
                torch_dtype=model_dtype,
                device_map=model_device_map,
                is_trainable=False,
                config=peft_config
            )

            # CPU path still needs explicit placement.
            if self.device == "cpu":
                self.model = self.model.to(self.device)

            self.model.eval()
            print("Local model loaded successfully!")

        except Exception as e:
            print(f"Error loading local model: {e}")
            raise

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
4. For SELECT queries, always include a LIMIT clause (default LIMIT 100)
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

Question: "List students enrolled in Biology course"
SQL: SELECT s.first_name, s.last_name FROM students s JOIN enrollments e ON s.student_id = e.student_id JOIN courses c ON e.course_id = c.course_id WHERE c.course_name = 'Biology' LIMIT 100

Question: "What is the total tuition paid by each student?"
SQL: SELECT student_id, SUM(amount_paid) as total_paid FROM tuition_payments GROUP BY student_id LIMIT 100

Question: "Find students with pending tuition payments"
SQL: SELECT s.first_name, s.last_name FROM students s JOIN tuition_payments tp ON s.student_id = tp.student_id WHERE tp.status = 'Pending' LIMIT 100

Important: Return ONLY the SQL query, nothing else."""

    def generate_sql(self, question: str, schema_metadata: SchemaMetadata, query_type_hint: Optional[QueryType] = None) -> SQLQuery:
        """Generate SQL from natural language question."""
        system_prompt = self._get_system_prompt(schema_metadata)

        user_prompt = f"Question: {question}\n\nSQL:"

        if self.model_type == "openai":
            response = self.client.chat.completions.create(
                model=self.model_path,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            sql = response.choices[0].message.content.strip()

        elif self.model_type == "anthropic":
            response = self.client.messages.create(
                model=self.model_path,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            sql = response.content[0].text.strip()

        elif self.model_type == "local":
            sql = self._generate_with_local_model(system_prompt, user_prompt)

        elif self.model_type == "modal":
            sql = self._generate_with_modal(question, system_prompt, user_prompt, schema_metadata)

        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

        # Clean up SQL - remove any markdown or explanations
        sql = sql.replace("```sql", "").replace("```", "").strip()
        sql = self._normalize_sql_output(sql)

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

        # Use hint if provided, otherwise use detected type
        final_type = query_type_hint or generated_type

        # Generate explanation
        explanation = self._generate_explanation(question, sql, final_type)

        return SQLQuery(
            sql=sql,
            explanation=explanation,
            query_type=final_type,
            parameters=None  # LLM doesn't generate parameters
        )

    def _normalize_sql_output(self, raw_text: str) -> str:
        """Extract and normalize the first SQL statement from model output."""
        text = raw_text.strip()
        if not text:
            return text

        match = re.search(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", text, flags=re.IGNORECASE)
        if not match:
            return text

        text = text[match.start():].strip()

        if ";" in text:
            text = text.split(";", 1)[0]

        # Some generations insert token artifacts like SELECT!col or AND!name.
        # Convert those to spaces so the SQL parser receives valid tokens.
        text = re.sub(r"(?<=\w)!+(?=\w)", " ", text)
        text = re.sub(r"!+", " ", text)

        text = re.sub(r"[!`]+$", "", text).strip()
        text = re.sub(r"\s+", " ", text)

        # Repair common malformed projection outputs.
        text = re.sub(r"(?i)^SELECT\s+FROM\b", "SELECT * FROM", text)
        text = re.sub(r"(?i)^SELECT\s+ALL\s+FROM\b", "SELECT * FROM", text)
        text = re.sub(r"(?i)^SELECT\s+DISTINCT\s+FROM\b", "SELECT DISTINCT * FROM", text)

        if text.upper() in {"SELECT", "INSERT", "UPDATE", "DELETE"}:
            return ""

        return text

    def _extract_sql_from_modal_response(self, payload: Any) -> str:
        """Extract SQL text from a Modal endpoint response payload."""
        if isinstance(payload, str):
            return payload

        if not isinstance(payload, dict):
            return ""

        # Common direct fields.
        for key in ("sql", "generated_sql", "generated_text", "text", "output"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value

        # OpenAI-like response shape.
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str) and content.strip():
                        return content
                text = first_choice.get("text")
                if isinstance(text, str) and text.strip():
                    return text

        return ""

    def _generate_with_modal(
        self,
        question: str,
        system_prompt: str,
        user_prompt: str,
        schema_metadata: SchemaMetadata,
    ) -> str:
        """Generate SQL by calling a remote Modal endpoint."""
        if not self.modal_endpoint_url:
            raise ValueError("MODAL_ENDPOINT_URL is not configured")

        headers = {"Content-Type": "application/json"}
        if self.modal_api_key:
            headers["Authorization"] = f"Bearer {self.modal_api_key}"

        payload = {
            "question": question,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "schema_prompt": self._get_schema_prompt(schema_metadata),
            "max_new_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        with httpx.Client(timeout=self.modal_timeout_seconds) as client:
            response = client.post(self.modal_endpoint_url, headers=headers, json=payload)
            response.raise_for_status()
            response_payload = response.json()

        sql_text = self._extract_sql_from_modal_response(response_payload)
        if not sql_text.strip():
            raise ValueError("Modal endpoint returned an empty SQL response")

        return sql_text

    def _generate_with_local_model(self, system_prompt: str, user_prompt: str) -> str:
        """Generate SQL using local model."""
        if self.model is None or self.tokenizer is None:
            raise ValueError("Local model not loaded")

        # Format prompt for Qwen2.5-Coder
        prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"

        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        if self.device == "cuda":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate. Some fp16 runs can produce invalid probability tensors when sampling,
        # so we retry with deterministic decoding if that happens.
        try:
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    do_sample=True if self.temperature > 0 else False,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
        except RuntimeError as exc:
            if "probability tensor contains either `inf`, `nan` or element < 0" not in str(exc):
                raise

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    do_sample=False,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )

        # Decode only continuation tokens to avoid echoing prompt/schema text.
        prompt_len = inputs["input_ids"].shape[1]
        continuation = outputs[0][prompt_len:]
        generated_text = self.tokenizer.decode(continuation, skip_special_tokens=True)

        return generated_text.strip()

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
        try:
            if self.model_type == "openai":
                # Simple completion to test connection
                _ = self.client.chat.completions.create(
                    model=self.model_path,
                    messages=[{"role": "user", "content": "Say 'OK'"}],
                    max_tokens=5
                )
                return {"llm_available": True, "provider": self.provider, "model_type": self.model_type}
            elif self.model_type == "anthropic":
                # Simple message to test connection
                _ = self.client.messages.create(
                    model=self.model_path,
                    messages=[{"role": "user", "content": "Say 'OK'"}],
                    max_tokens=5
                )
                return {"llm_available": True, "provider": self.provider, "model_type": self.model_type}
            elif self.model_type == "local":
                # Check if model is loaded
                if self.model is not None and self.tokenizer is not None:
                    # Try a simple inference to verify model works
                    test_prompt = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\nSay OK<|im_end|>\n<|im_start|>assistant\n"
                    inputs = self.tokenizer(test_prompt, return_tensors="pt", truncation=True, max_length=100)

                    if self.device == "cuda":
                        inputs = {k: v.to(self.device) for k, v in inputs.items()}

                    with torch.no_grad():
                        _ = self.model.generate(
                            **inputs,
                            max_new_tokens=5,
                            do_sample=False
                        )

                    return {
                        "llm_available": True,
                        "provider": self.provider,
                        "model_type": self.model_type,
                        "device": self.device
                    }
                else:
                    return {"llm_available": False, "provider": self.provider, "model_type": self.model_type, "error": "Model not loaded"}
            elif self.model_type == "modal":
                return {
                    "llm_available": bool(self.modal_endpoint_url),
                    "provider": self.provider,
                    "model_type": self.model_type,
                    "endpoint": self.modal_endpoint_url,
                }
        except Exception as e:
            return {"llm_available": False, "provider": self.provider, "model_type": self.model_type, "error": str(e)}

        return {"llm_available": False, "provider": self.provider, "model_type": self.model_type, "error": "Unknown provider"}


# Avoid module-level model loading; instantiate LLMService in app entrypoints.