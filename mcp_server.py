from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from mcp.server.fastmcp import FastMCP


DEFAULT_MODEL_ID = os.environ.get("MODEL_ID", "Qwen/Qwen2.5-7B-Instruct")
DEFAULT_ALLOWED_ROOT = Path(os.environ.get("ALLOWED_ROOT", Path.cwd()))


def _load_pipeline():
    model_id = DEFAULT_MODEL_ID
    load_in_4bit = os.environ.get("LOAD_IN_4BIT", "1") != "0"
    device_map = os.environ.get("DEVICE_MAP", "auto")

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map=device_map,
        torch_dtype=torch.float16 if load_in_4bit else torch.float32,
        load_in_4bit=load_in_4bit,
    )

    return pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
    )


def _validate_path(path: str) -> Path:
    resolved = Path(path).expanduser().resolve()
    allowed_root = DEFAULT_ALLOWED_ROOT.resolve()

    try:
        resolved.relative_to(allowed_root)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Access to {resolved} is outside ALLOWED_ROOT={allowed_root}") from exc

    if resolved.is_dir():
        raise IsADirectoryError(f"Expected a file path, got directory: {resolved}")
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")
    return resolved


text_gen = _load_pipeline()
server = FastMCP("local-llm-files")


@server.tool()
def read_file(path: str) -> str:
    """Return the content of a text file within the allowed root."""

    resolved = _validate_path(path)
    return resolved.read_text(encoding="utf-8", errors="replace")


def _run_chat(question: str, context: str) -> str:
    prompt = (
        "You are a local MCP assistant. Use only the provided context.\n"
        "If the context is empty or insufficient, say you don't know.\n\n"
        f"Question: {question}\n\nContext:\n{context if context.strip() else '(no context provided)'}\n\nAnswer:"
    )

    outputs = text_gen(
        prompt,
        max_new_tokens=int(os.environ.get("MAX_OUTPUT_TOKENS", 512)),
        temperature=float(os.environ.get("TEMPERATURE", 0.2)),
        do_sample=True,
        top_p=0.9,
        num_return_sequences=1,
    )
    return outputs[0]["generated_text"].split("Answer:", 1)[-1].strip()


@server.tool()
def ask_local(question: str, path: Optional[str] = None) -> str:
    """Answer a question using the local model, optionally grounded with a file."""

    context = ""
    if path:
        context = read_file(path)

    return _run_chat(question, context)


@server.prompt_template()
def file_qa_prompt(question: str, context: str) -> dict:
    """Prompt template for MCP clients that support prompt construction."""

    return {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a local assistant reading project files. Answer succinctly and cite the file names you used."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\nContext:{os.linesep}{context if context.strip() else '(no context provided)'}"
                ),
            },
        ]
    }


if __name__ == "__main__":
    server.run()
