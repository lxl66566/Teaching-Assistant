# Teaching Assistant

我的毕设。巨量屎山，如非必要，不建议尝试。

这是一个基于 LLM 和 Agentic RAG 技术的教学辅助系统，旨在帮助教师生成教案，总结教学内容等。

- 前端基于 [Simba](https://github.com/GitHamza0206/simba/) 的前端进行了大量魔改，使用 React + TailwindCSS + TypeScript + Radix UI。
- 后端 python 3.12，FastAPI 作为后端 API 接口，Chroma 作为向量数据库，sqlite 作为后端数据库。
- 系统需要 [ollama](https://github.com/ollama/ollama) 作为本地模型管理器，管理 embedding 模型和本地 LLM 模型。

## 部署

操作系统中需要先安装好 [uv](https://docs.astral.sh/uv/)，[pnpm](https://pnpm.io/) 和 [ollama](https://ollama.com/)。

- 后端
  ```sh
  cd backend
  uv run uvicorn app.main:app --reload
  ```
- 前端
  ```sh
  cd frontend
  pnpm install
  pnpm dev
  ```
- ollama
  ```sh
  ollama serve
  ```
