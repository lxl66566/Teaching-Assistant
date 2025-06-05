# Teaching Assistant

我的毕设。~~巨量屎山，如非必要，不建议尝试。~~

这是一个基于 LLM 和 Agentic RAG 技术的教学辅助系统，旨在帮助教师生成教案，总结教学内容等。

- 前端基于 [Simba](https://github.com/GitHamza0206/simba/) 的前端进行了大量魔改，使用 React + TailwindCSS + TypeScript + Radix UI。
- 后端 python 3.12，FastAPI 作为后端 API 接口，Chroma 作为向量数据库，sqlite 作为后端数据库。
- 系统需要 [ollama](https://github.com/ollama/ollama) 作为本地模型管理器，管理 embedding 模型和本地 LLM 模型。

## 部署

### Docker Deployment

首先，确保你已经安装了 Docker。

1. 创建 Docker 网络
   ```sh
   docker network create teaching-assistant-net
   ```
2. 启动 Ollama 容器并拉取模型
   ```sh
   docker run -d \
     -v ./ollama_data:/root/.ollama \
     -p 11434:11434 \
     --name ollama \
     --network teaching-assistant-net \
     ollama/ollama
   ```
   - `-v ./ollama_data:/root/.ollama`: 将宿主机当前目录下的 `ollama_data` 文件夹挂载到容器内，用于持久化 Ollama 的模型和数据。请确保此目录存在或 Docker 有权限创建它。
     等待 Ollama 容器启动后，执行以下命令拉取所需的 GTE 模型：
     ```sh
     docker exec -it ollama ollama pull milkey/gte:large-zh-f16
     ```
3. 拉取 Teaching Assistant Docker 镜像
   ```sh
   docker pull ghcr.io/lxl66566/teaching-assistant:latest
   ```
4. 运行 Teaching Assistant Docker 容器
   ```sh
   docker run -d \
     --name teaching-assistant \
     -p 8000:8000 \
     -v ./backend_data:/app/backend/data \
     --network teaching-assistant-net \
     ghcr.io/lxl66566/teaching-assistant:latest
   ```
   - `-p 8000:8000`: 将容器的 8000 端口映射到宿主机的 8000 端口。你可以根据需要修改宿主机的端口，例如 `-p 12345:8000`。
   - `-v ./backend_data:/app/backend/data`: 将宿主机当前目录下的 `backend_data` 文件夹挂载到容器内的 `/app/backend/data`。这个目录用于存储 Chroma 数据库等数据。**请确保此目录在宿主机上存在且持久化，或者将其替换为一个绝对路径，例如 `-v /path/to/your/persistent_data/backend_data:/app/backend/data`。**
   - `--network teaching-assistant-net`: 将 `teaching-assistant` 容器连接到之前创建的 `teaching-assistant-net` 网络。这样，后端服务可以通过服务名 `ollama` (即 Ollama 容器的名称) 访问 Ollama 服务。

<details><summary>其他配置</summary>

- **验证运行状态**
  启动成功后，你可以：
  - 通过浏览器访问 `http://localhost:8000` (或你映射的主机端口) 来使用 Teaching Assistant。
  - 查看容器日志以确认服务是否正常运行：
    ```sh
    docker logs teaching-assistant
    docker logs ollama
    ```
- **代理设置：**
  如果你的宿主机需要通过 HTTP/HTTPS 代理访问外部网络（例如，Ollama 可能需要通过代理拉取模型，或者应用内部有其他网络请求），你可以将宿主机的代理环境变量传递给容器。
  - **Linux/macOS (Bash/Zsh):**
    假设你的宿主机已设置 `HTTP_PROXY` 和 `HTTPS_PROXY` 环境变量：
    ```sh
    docker run -d \
      --name teaching-assistant \
      -p 8000:8000 \
      -v ./backend_data:/app/backend/data \
      --network teaching-assistant-net \
      -e HTTP_PROXY="$HTTP_PROXY" \
      -e HTTPS_PROXY="$HTTPS_PROXY" \
      ghcr.io/lxl66566/teaching-assistant:latest
    ```
  - **Windows (PowerShell):**
    ```powershell
    docker run -d `
      --name teaching-assistant `
      -p 8000:8000 `
      -v ./backend_data:/app/backend/data `
      --network teaching-assistant-net `
      -e HTTP_PROXY="$env:HTTP_PROXY" `
      -e HTTPS_PROXY="$env:HTTPS_PROXY" `
      ghcr.io/lxl66566/teaching-assistant:latest
    ```
- **使用自定义配置文件：**
  后端服务支持通过配置文件进行配置。默认情况下，它会尝试加载容器内 `/app/backend/app/config.toml` 路径下的配置文件。
  你可以通过挂载宿主机上的自定义配置文件，并使用 `--config` 参数（如果应用支持此命令行参数）来指定**容器内**的配置文件路径。
  例如，如果你在宿主机当前目录下有一个名为 `my_custom_config.toml` 的配置文件：
  ```sh
  docker run -d \
    --name teaching-assistant \
    -p 8000:8000 \
    -v ./backend_data:/app/backend/data \
    -v ./my_custom_config.toml:/app/my_app_config.toml \
    --network teaching-assistant-net \
    ghcr.io/lxl66566/teaching-assistant:latest \
    --config /app/my_app_config.toml
  ```
  - `-v ./my_custom_config.toml:/app/my_app_config.toml`: 将宿主机的 `my_custom_config.toml` 文件挂载到容器内的 `/app/my_app_config.toml`。
  - `--config /app/my_app_config.toml`: 告诉 `teaching-assistant` 应用去加载容器内 `/app/my_app_config.toml` 这个配置文件。
- **停止和清理**
  如果你需要停止或移除容器：
  ```sh
  docker stop teaching-assistant ollama
  docker rm teaching-assistant ollama
  ```
  如果你希望移除创建的网络：
  ```sh
  docker network rm teaching-assistant-net
  ```

</details>

### 分别部署

操作系统中需要先安装好 [uv](https://docs.astral.sh/uv/)，[pnpm](https://pnpm.io/) 和 [ollama](https://ollama.com/)。

- 后端
  ```sh
  cd backend
  uv run --prerelease=allow -m app
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
  ollama pull milkey/gte:large-zh-f16       # 新开一个终端执行
  ```
