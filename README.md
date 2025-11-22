# Local 7B INT4 MCP Server

This repository demonstrates how to run a fully local 7B INT4 model (Qwen or DeepSeek) and expose it through an [MCP](https://modelcontextprotocol.io/) server so that tools can query your local files and answer questions without leaving your machine.

## Prerequisites
- Python 3.10+
- A CPU-only setup works for Q4 (INT4) quantized models; GPU acceleration is optional if supported by your build of `llama.cpp`.
- Sufficient disk space for the chosen GGUF model (~4–7 GB).

## Step-by-step usage
1) **Clone the repo** and enter it:
```bash
git clone <this-repo-url> && cd agent_test
```

2) **Create a virtual environment** and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3) **Download a 7B INT4 GGUF model** into `./models`.
   - Qwen3: `Qwen/Qwen2.5-7B-Instruct-GGUF` → `qwen2.5-7b-instruct-q4_0.gguf`
   - DeepSeek: `TheBloke/deepseek-llm-7B-chat-GGUF` → `deepseek-llm-7b-chat-q4_0.gguf`

   Use `huggingface-cli` (requires a token for gated repos):
```bash
huggingface-cli download Qwen/Qwen2.5-7B-Instruct-GGUF qwen2.5-7b-instruct-q4_0.gguf --local-dir models
# or
huggingface-cli download TheBloke/deepseek-llm-7B-chat-GGUF deepseek-llm-7b-chat-q4_0.gguf --local-dir models
```

4) **Configure environment variables** (adjust as needed):
```bash
export MODEL_PATH=models/qwen2.5-7b-instruct-q4_0.gguf
export CONTEXT_SIZE=4096   # optional context window
export N_THREADS=8         # optional CPU threads
export ALLOWED_ROOT=$PWD   # optional: restrict file access to this repo
```

5) **Start the MCP server**:
```bash
python mcp_server.py
```
The server name is `local-llm-files` and exposes tools for reading files and asking questions with file-aware context.

6) **Connect a client**. MCP-capable tools accept a `command` that launches the server. Example JSON config:
```json
{
  "name": "local-llm-files",
  "command": "python",
  "args": ["/absolute/path/to/mcp_server.py"],
  "env": {
    "MODEL_PATH": "/absolute/path/to/models/qwen2.5-7b-instruct-q4_0.gguf"
  }
}
```

7) **Use the tools** from your MCP client:
   - `read_file(path)`: Return file contents within `ALLOWED_ROOT`.
   - `ask_local(question, path=None)`: Ask the model a question; when `path` is set the file text is provided as context.

8) **Use the prompt template** `file_qa_prompt(question, context)` if your client supports prompt construction. It yields a system/user message pair tailored for file-grounded answers.

### Available tools
- `read_file(path)`: Returns the text content of a file, limited to the `ALLOWED_ROOT` directory (defaults to the repository root).
- `ask_local(question, path=None)`: Answers a question using the local model. When `path` is provided, the file content is injected as context for better grounded answers.

### Prompt template
A built-in prompt template (`file_qa_prompt`) prepares a system/user message pair for MCP clients that support prompt templates. It expects `question` and `context` variables.

## Notes on performance
- Keep `CONTEXT_SIZE` modest (e.g., 4096) for better latency on CPUs.
- INT4 quantization keeps memory use low; switching to Q5/Q8 files can improve quality at the cost of speed.

## Troubleshooting
- If the server cannot find the model file, verify `MODEL_PATH` points to an existing `.gguf` file.
- If you see `BLAS`/`accelerate` errors from `llama-cpp-python`, reinstall it with the appropriate build flags for your hardware.
- Large files may be truncated if they exceed the configured maximum context length; consider summarizing them first.

## Windows setup notes
The server works on Windows (PowerShell) with the same code, but commands differ slightly:

1) **Install dependencies** (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

2) **Download a model** into `models\` using `huggingface-cli` (install with `python -m pip install huggingface_hub`). Example:
```powershell
python -m huggingface_hub download Qwen/Qwen2.5-7B-Instruct-GGUF qwen2.5-7b-instruct-q4_0.gguf --local-dir models
```

3) **Set environment variables** in the PowerShell session (adjust paths to your checkout):
```powershell
$Env:MODEL_PATH = "${PWD}\models\qwen2.5-7b-instruct-q4_0.gguf"
$Env:CONTEXT_SIZE = "4096"
$Env:N_THREADS = "8"
$Env:ALLOWED_ROOT = "${PWD}"
```

4) **Start the MCP server** from the repository root:
```powershell
python .\mcp_server.py
```

5) **Client command configuration** typically needs absolute Windows paths, for example:
```json
{
  "name": "local-llm-files",
  "command": "C:/Python311/python.exe",
  "args": ["C:/path/to/agent_test/mcp_server.py"],
  "env": {
    "MODEL_PATH": "C:/path/to/agent_test/models/qwen2.5-7b-instruct-q4_0.gguf"
  }
}
```
If `llama-cpp-python` reports missing runtime components, install the latest Visual C++ Redistributable from Microsoft.
