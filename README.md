# Windows 本地 7B INT4 MCP 服务 (cmd.exe)

本仓库提供一个 **纯本地** 的 MCP 服务器，面向 Windows `cmd.exe` 用户，使用国产模型（如 Qwen3 / DeepSeek）加载 4bit 量化权重，支持：
- 通过 MCP 工具读取本地文件。
- 使用本地大模型回答问题，不上传数据。

> 如果 GitHub 页面显示旧版 README，请切换到 `work` 分支查看最新内容。

## 能力概览
- `mcp_server.py`：使用 Hugging Face `transformers` 直接加载 Qwen/DeepSeek 等国产模型（支持 4bit）。
- 提供工具：
  - `read_file(path)`：在允许目录内读取文本文件。
  - `ask_local(question, path=None)`：用本地模型回答问题，可选指定文件作为上下文。
  - `file_qa_prompt(question, context)`：给支持 prompt 注入的 MCP 客户端使用。

## 环境要求（Windows）
- Windows 10/11 64-bit
- Python 3.10+ (64-bit)
- Git
- 有 NVIDIA GPU 且安装了 CUDA 驱动（推荐，用于 4bit 加速）；若无 GPU，运行速度会很慢
- 10GB 以上磁盘空间用于模型（按需）

## Step-by-step（Command Prompt）
以下命令全部在 **cmd.exe** 中执行。

### 1) 克隆仓库
```cmd
git clone <your-repo-url>
cd agent_test
```

### 2) 创建并激活虚拟环境
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
```

### 3) 安装依赖
`transformers` + `bitsandbytes` 用于加载 4bit 模型；`mcp` 用于 MCP 服务。
```cmd
python -m pip install -r requirements.txt
```
> 如果 `bitsandbytes` 在 Windows CPU 环境报错，建议使用带 NVIDIA GPU 的机器；CPU 模式可以把环境变量 `LOAD_IN_4BIT` 设为 `0`，改为全精度加载（速度慢且内存占用大）。

### 4) 登录 Hugging Face（如需下载受限模型）
python -m pip install "huggingface_hub[cli]"
```cmd
python -m pip install --upgrade huggingface_hub
huggingface-cli login
```

### 5) 下载国产 7B 模型（示例：Qwen3 / DeepSeek）
选择 4bit 权重，下载到 `models/` 目录：
```cmd
:: Qwen3 4bit
python -m huggingface_hub download Qwen/Qwen2.5-7B-Instruct qwen2.5-7b-instruct-4bits --local-dir models

:: DeepSeek 4bit
python -m huggingface_hub download deepseek-ai/DeepSeek-V2-Chat deepseek-v2-chat-4bits --local-dir models
```
> 请根据实际仓库中的文件名填写环境变量。如果使用其他国产模型，也可替换为对应模型 ID。

### 6) 设置环境变量（当前会话）
将 `MODEL_ID` 替换为你下载的模型 ID。
```cmd
set MODEL_ID=Qwen/Qwen2.5-7B-Instruct
set LOAD_IN_4BIT=1
set DEVICE_MAP=auto
set MAX_OUTPUT_TOKENS=512
set TEMPERATURE=0.2
set ALLOWED_ROOT=%CD%
```
如果需要指定绝对路径，可用 `for %i in (mcp_server.py) do @echo %~fi` 查看脚本位置。

### 7) 启动 MCP 服务器
在仓库根目录、虚拟环境已激活的情况下运行：
```cmd
python .\mcp_server.py
```
服务名为 `local-llm-files`，首次加载模型会稍慢。

### 8) 配置 MCP 客户端
以 JSON 片段为例（请使用绝对路径）：
```json
{
  "name": "local-llm-files",
  "command": "C:/Python311/python.exe",
  "args": ["C:/path/to/agent_test/mcp_server.py"],
  "env": {
    "MODEL_ID": "Qwen/Qwen2.5-7B-Instruct",
    "ALLOWED_ROOT": "C:/path/to/agent_test",
    "LOAD_IN_4BIT": "1",
    "DEVICE_MAP": "auto"
  }
}
```

### 9) 使用工具
- `read_file(path)`：读取 `ALLOWED_ROOT` 范围内的文本文件。
- `ask_local(question, path=None)`：向本地模型提问，可附带文件内容。
- `file_qa_prompt(question, context)`：提供标准对话模板给 MCP 客户端。

## 环境变量速查
- `MODEL_ID`（必需）：Hugging Face 模型 ID，例如 `Qwen/Qwen2.5-7B-Instruct`。
- `LOAD_IN_4BIT`：`1` 为 4bit 加载（需要 GPU + bitsandbytes）；`0` 为全精度。
- `DEVICE_MAP`：`auto`（默认）或手动指定 GPU，如 `cuda:0`。
- `ALLOWED_ROOT`：允许读取文件的目录根，默认仓库根。
- `MAX_OUTPUT_TOKENS`：生成的最大新 token 数，默认 512。
- `TEMPERATURE`：采样温度，默认 0.2。

## 常见问题（Windows）
- **bitsandbytes 安装失败**：需要支持 CUDA 的 NVIDIA GPU 和对应驱动。若无 GPU，可将 `LOAD_IN_4BIT=0`，但推理可能非常慢。
- **显存不足**：尝试较小的 4bit 模型，或将 `MAX_OUTPUT_TOKENS` 降低。
- **文件访问报错**：确保传入的路径在 `ALLOWED_ROOT` 下，且是文件而非目录。
- **下载过慢/失败**：检查网络或使用镜像源；也可以提前手动下载模型放到 `models/` 目录并设置 `MODEL_ID`。

完成以上步骤后，即可在 Windows `cmd.exe` 中克隆仓库、下载国产模型、启动 MCP 服务器，并在支持 MCP 的客户端中调用本地模型回答与文件相关的问题。
