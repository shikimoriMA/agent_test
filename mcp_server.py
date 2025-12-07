from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from llama_cpp import Llama
from mcp.server.fastmcp import FastMCP


DEFAULT_MODEL_PATH = Path("models/qwen2.5-7b-instruct-q4_0.gguf")
DEFAULT_ALLOWED_ROOT = Path(os.environ.get("ALLOWED_ROOT", Path.cwd()))


def _load_llama() -> Llama:
    model_path = Path(os.environ.get("MODEL_PATH", DEFAULT_MODEL_PATH))
    if not model_path.exists():
        raise FileNotFoundError(
            f"Missing model file at {model_path}. Set MODEL_PATH to a valid GGUF file."
        )

    return Llama(
        model_path=str(model_path),
        n_ctx=int(os.environ.get("CONTEXT_SIZE", 4096)),
        n_threads=int(os.environ.get("N_THREADS", max(os.cpu_count() or 1, 1))),
        n_batch=int(os.environ.get("N_BATCH", 512)),
        verbose=False,
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


llama = _load_llama()
server = FastMCP("local-llm-files")


@server.tool()
def read_file(path: str) -> str:
    """Return the content of a text file within the allowed root."""

    resolved = _validate_path(path)
    return resolved.read_text(encoding="utf-8", errors="replace")


def _run_chat(question: str, context: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a local MCP assistant. You can only answer using the provided files "
                "and must refuse to guess when information is missing."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"Context from files:\n{context if context.strip() else '(no context provided)'}"
            ),
        },
    ]

    response = llama.create_chat_completion(
        messages=messages,
        temperature=float(os.environ.get("TEMPERATURE", 0.2)),
        max_tokens=int(os.environ.get("MAX_OUTPUT_TOKENS", 512)),
    )
    return response["choices"][0]["message"]["content"]


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
