# Windows Local 7B INT4 MCP Server (Command Prompt)

This repository is focused on **Windows cmd.exe** users who want to run a fully local 7B INT4 model (Qwen3 or DeepSeek) and expose it through an [MCP](https://modelcontextprotocol.io/) server. The server lets MCP clients read local files and answer questions without sending data off your machine.

> If GitHub shows an older README, switch to the `codex/update-repository-for-local-deployment-of-7b-int4-model` (or `work`) branch for the latest content.

## What you get
- A minimal MCP server (`mcp_server.py`) that loads a local GGUF model with `llama_cpp`.
- Tools:
  - `read_file(path)`: read text files within an allowed directory root.
  - `ask_local(question, path=None)`: answer questions, optionally grounded with a file.
  - `file_qa_prompt(question, context)`: prompt template for MCP clients that support prompt construction.

## Prerequisites (Windows)
- Windows 10/11 64-bit.
- Python 3.10+ (64-bit).
- Git.
- Microsoft Visual C++ Redistributable (latest x64) — required by `llama-cpp-python`.
- 5–8 GB of disk space for a 7B INT4 GGUF model.

## Step-by-step setup (cmd.exe)
Run these commands in **Command Prompt** from the folder where you want the project.

1) **Clone the repository**
```cmd
git clone <your-repo-url>
cd agent_test
```

2) **Create and activate a virtual environment**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
```

3) **Install dependencies**
```cmd
python -m pip install -r requirements.txt
```
If you see build errors from `llama-cpp-python`, install the latest Visual C++ Redistributable, ensure you use 64-bit Python, and retry. On some systems you may need to set a generator (then reopen Command Prompt):
```cmd
setx CMAKE_GENERATOR "Visual Studio 17 2022"
```

4) **(Optional) Log in to Hugging Face for gated models**
```cmd
python -m pip install --upgrade huggingface_hub
huggingface-cli login
```

5) **Download a 7B INT4 GGUF model into `models/`**
Create `models` automatically while downloading. Pick one:
```cmd
python -m huggingface_hub download Qwen/Qwen2.5-7B-Instruct-GGUF qwen2.5-7b-instruct-q4_0.gguf --local-dir models
:: or
python -m huggingface_hub download TheBloke/deepseek-llm-7B-chat-GGUF deepseek-llm-7b-chat-q4_0.gguf --local-dir models
```
Note the exact filename; you will set it in `MODEL_PATH`.

6) **Set environment variables for the current session**
Replace the filename if you chose DeepSeek. `%CD%` keeps paths inside your checkout.
```cmd
set MODEL_PATH=%CD%\models\qwen2.5-7b-instruct-q4_0.gguf
set CONTEXT_SIZE=4096
set N_THREADS=8
set N_BATCH=512
set ALLOWED_ROOT=%CD%
set TEMPERATURE=0.2
set MAX_OUTPUT_TOKENS=512
```
Use `for %i in (mcp_server.py) do @echo %~fi` if you need an absolute script path for client configs.

7) **Start the MCP server**
From the repository root with the virtual environment active:
```cmd
python .\mcp_server.py
```
The server name is `local-llm-files`. The first launch may take time while the model loads.

8) **Configure an MCP client (Windows paths)**
Point your MCP-capable tool to the server command. Example JSON snippet:
```json
{
  "name": "local-llm-files",
  "command": "C:/Python311/python.exe",
  "args": ["C:/path/to/agent_test/mcp_server.py"],
  "env": {
    "MODEL_PATH": "C:/path/to/agent_test/models/qwen2.5-7b-instruct-q4_0.gguf",
    "ALLOWED_ROOT": "C:/path/to/agent_test"
  }
}
```
Use absolute Windows paths so the client can find both Python and the server script.

9) **Use the tools from your client**
- `read_file(path)`: reads text files within `ALLOWED_ROOT`.
- `ask_local(question, path=None)`: answers questions with optional file grounding.
- `file_qa_prompt(question, context)`: prompt template if your client supports prompt injection.

## Environment variable reference
- `MODEL_PATH` (required): Absolute or relative path to the `.gguf` model file.
- `ALLOWED_ROOT` (recommended): Directory boundary for file reads; defaults to the repo root.
- `CONTEXT_SIZE`: Context tokens (default 4096).
- `N_THREADS`: CPU threads for inference (defaults to available cores).
- `N_BATCH`: Batch size (default 512). Reduce if you see memory issues.
- `TEMPERATURE`: Sampling temperature (default 0.2).
- `MAX_OUTPUT_TOKENS`: Max tokens returned (default 512).

## Troubleshooting on Windows
- **Model file not found**: Confirm `MODEL_PATH` matches the downloaded filename and path.
- **`llama-cpp-python` build errors**: Install the x64 Visual C++ Redistributable; ensure you use 64-bit Python; consider reinstalling with `python -m pip install --force-reinstall llama-cpp-python` after setting `CMAKE_GENERATOR` if necessary.
- **Execution policy blocks activation**: If PowerShell opens instead of cmd.exe, run Command Prompt as administrator or call the activation script directly with `cmd /k .\.venv\Scripts\activate.bat`.
- **Slow or high memory usage**: Lower `CONTEXT_SIZE` or `N_BATCH`, or use fewer `N_THREADS`.
- **File access denied**: Ensure paths you pass to `read_file` are under `ALLOWED_ROOT`.

With these steps, a Windows developer can clone, install, download a 7B INT4 model, start the MCP server, and wire it to an MCP client entirely on a local machine using Command Prompt.
