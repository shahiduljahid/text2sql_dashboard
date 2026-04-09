#!/usr/bin/env python3
"""Modal endpoint for SQL generation using local Qwen base + LoRA adapter."""

from __future__ import annotations

import inspect
import json
import os
import re
from typing import Any

import modal

APP_NAME = os.environ.get("MODAL_APP_NAME", "text2sql-sql-endpoint")
VOLUME_NAME = os.environ.get("MODAL_VOLUME_NAME", "text2sql-model-cache")
GPU_TYPE = os.environ.get("MODAL_GPU", "A10G")

BASE_MODEL_DIR = os.environ.get("MODAL_BASE_MODEL_DIR", "/models/base")
ADAPTER_DIR = os.environ.get("MODAL_ADAPTER_DIR", "/models/adapter")

app = modal.App(APP_NAME)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi==0.104.1",
        "pydantic==2.5.0",
        "torch==2.1.0",
        "transformers==4.38.0",
        "peft==0.10.0",
        "accelerate==0.27.0",
        "sentencepiece==0.2.0",
        "protobuf==4.25.3",
    )
)

model_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
_state: dict[str, Any] = {}


def _normalize_sql(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""

    match = re.search(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", text, flags=re.IGNORECASE)
    if not match:
        return text

    text = text[match.start():].strip()
    if ";" in text:
        text = text.split(";", 1)[0]

    text = re.sub(r"(?<=\w)!+(?=\w)", " ", text)
    text = re.sub(r"!+", " ", text)
    text = re.sub(r"[!`]+$", "", text).strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?i)^SELECT\s+FROM\b", "SELECT * FROM", text)
    return text


def _ensure_model_loaded() -> None:
    if "model" in _state and "tokenizer" in _state:
        return

    import torch
    from peft import LoraConfig, PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL_DIR,
        local_files_only=True,
        trust_remote_code=True,
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_DIR,
        torch_dtype=torch.float16,
        device_map={"": 0},
        trust_remote_code=True,
        local_files_only=True,
    )

    peft_config = None
    adapter_config_path = os.path.join(ADAPTER_DIR, "adapter_config.json")
    if os.path.exists(adapter_config_path):
        with open(adapter_config_path, "r", encoding="utf-8") as f:
            adapter_cfg = json.load(f)

        supported_fields = {
            name for name in inspect.signature(LoraConfig.__init__).parameters.keys()
            if name != "self"
        }
        filtered_cfg = {k: v for k, v in adapter_cfg.items() if k in supported_fields}
        if filtered_cfg:
            peft_config = LoraConfig(**filtered_cfg)

    model = PeftModel.from_pretrained(
        base_model,
        ADAPTER_DIR,
        torch_dtype=torch.float16,
        device_map={"": 0},
        is_trainable=False,
        config=peft_config,
    )
    model.eval()

    _state["torch"] = torch
    _state["tokenizer"] = tokenizer
    _state["model"] = model


@app.function(
    image=image,
    gpu=GPU_TYPE,
    timeout=3600,
    scaledown_window=300,
    volumes={"/models": model_volume},
)
@modal.fastapi_endpoint(method="POST")
def generate_sql(payload: dict):
    _ensure_model_loaded()

    torch = _state["torch"]
    tokenizer = _state["tokenizer"]
    model = _state["model"]

    question = payload.get("question", "")
    system_prompt = payload.get("system_prompt", "")
    user_prompt = payload.get("user_prompt", f"Question: {question}\n\nSQL:")
    max_new_tokens = int(payload.get("max_new_tokens", 256))
    temperature = float(payload.get("temperature", 0.1))

    prompt = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
    inputs = {k: v.to("cuda") for k, v in inputs.items()}

    try:
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
    except RuntimeError as exc:
        if "probability tensor contains either `inf`, `nan` or element < 0" not in str(exc):
            raise
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

    prompt_len = inputs["input_ids"].shape[1]
    continuation = outputs[0][prompt_len:]
    generated_text = tokenizer.decode(continuation, skip_special_tokens=True)

    return {"sql": _normalize_sql(generated_text)}
