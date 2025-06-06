# Teaching Assistant

我的毕设。~~巨量屎山，如非必要，不建议尝试。~~

这是一个基于 LLM 和 Agentic RAG 技术的教学辅助系统，旨在帮助教师生成教案，总结教学内容等。

- 前端基于 [Simba](https://github.com/GitHamza0206/simba/) 的前端进行了大量魔改，使用 React + TailwindCSS + TypeScript + Radix UI。
- 后端 python 3.12，FastAPI 作为后端 API 接口，Chroma 作为向量数据库，sqlite 作为后端数据库。
- 系统需要 [ollama](https://github.com/ollama/ollama) 作为本地模型管理器，管理 embedding 模型和本地 LLM 模型。

## 部署

_Docker 部署_ 和 _从源码部署_ 任选其一即可。

### Docker 部署

0. 确保已经安装了 Docker。
1. 创建 Docker 网络
   ```sh
   docker network create teaching-assistant-net
   ```
2. 启动 Ollama 容器并拉取模型
   ```sh
   docker run -d \
     --restart always \
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
3. 拉取并运行 Teaching Assistant Docker 容器
   ```sh
   docker run -d \
     --restart always \
     --name teaching-assistant \
     -p 80:8000 \
     -v ./backend_data:/app/backend/data \
     --network teaching-assistant-net \
     ghcr.io/lxl66566/teaching-assistant:latest
   ```
   - `-p 80:8000`: 将容器的 80 端口映射到宿主机的 8000 端口。你可以根据需要修改宿主机的端口，例如 `-p 12345:8000`。
   - `-v ./backend_data:/app/backend/data`: 将宿主机当前目录下的 `backend_data` 文件夹挂载到容器内的 `/app/backend/data`。这个目录用于存储 Chroma 数据库等数据。**请确保此目录在宿主机上存在且持久化，或者将其替换为一个绝对路径，例如 `-v /path/to/your/persistent_data/backend_data:/app/backend/data`。**
   - `--network teaching-assistant-net`: 将 `teaching-assistant` 容器连接到之前创建的 `teaching-assistant-net` 网络。这样，后端服务可以通过服务名 `ollama` (即 Ollama 容器的名称) 访问 Ollama 服务。
4. 等待依赖安装完成与资源下载。下载大小约为 2-3GB，请耐心等待，并保持网络（包括外网访问）畅通。可以使用 `docker logs -f teaching-assistant` 查看当前进度，当输出为 `Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)` 时代表项目已成功启动。
5. 启动成功后，通过浏览器访问宿主机的 `http://localhost` 来使用 Teaching Assistant。（或者部署服务器的 IP：`http://<your-host-ip>`，端口为 run 时传入的端口）

<details><summary>其他配置</summary>

- **验证运行状态**
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
      -p 80:8000 \
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
      -p 80:8000 `
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
    -p 80:8000 \
    -v ./backend_data:/app/backend/data \
    -v ./my_custom_config.toml:/app/my_app_config.toml \
    --network teaching-assistant-net \
    ghcr.io/lxl66566/teaching-assistant:latest \
    /app/my_app_config.toml
  ```
  - `-v ./my_custom_config.toml:/app/my_app_config.toml`: 将宿主机的 `my_custom_config.toml` 文件挂载到容器内的 `/app/my_app_config.toml`。
  - `/app/my_app_config.toml`: 告诉 `teaching-assistant` 应用去加载容器内 `/app/my_app_config.toml` 这个配置文件。
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

### 从源码部署

操作系统中需要先安装好 git，[uv](https://docs.astral.sh/uv/)，nodejs，[pnpm](https://pnpm.io/) 和 [ollama](https://ollama.com/)。

1. 克隆仓库
   ```sh
   git clone https://github.com/lxl66566/teaching-assistant.git --depth 1
   cd teaching-assistant
   ```
2. 构建前端
   ```sh
   cd frontend
   pnpm i
   pnpm build
   cd ..
   ```
3. 启动 ollama
   ```sh
   ollama serve
   ollama pull milkey/gte:large-zh-f16       # 新开一个终端执行
   ```
4. 启动后端
   项目默认使用 cpu 版本的 torch。如果你使用 nvidia 显卡，请修改 backend/pyproject.toml 中的 `torch` 版本为你的 cuda 版本，参考 [Using uv with PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/)。
   ```sh
   cd backend
   uv run --prerelease=allow -m app
   ```

## 传入配置（可选）

你可以修改一些配置，以自定义应用的行为。新建一个 `xxx.toml` 文件，以 [config.toml](./backend/app/config.toml) 为模板进行修改，然后在启动命令中传入该文件：

```sh
uv run --prerelease=allow -m app /path/to/xxx.toml
```

在 docker 传入配置会稍微麻烦一些，请参考[Docker 部署](#docker-部署)中的 _其他配置_ 章节。

## 提示

- 本项目需要在能够访问外网的网络环境下运行。
