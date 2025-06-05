// 定义 Backend 接口
// 当前多 backend 模式已经废弃。
export interface Backend {
  name: string;
  host: string;
  port: number;
  toString(): string;
  toBase(): string;
}

let current_backend: 0 | 1 = 0;

// 后端配置列表
export const backendList: Backend[] = [
  {
    name: "Agentic RAG",
    host: "localhost",
    port: 8000,
  },
  {
    name: "Graph RAG",
    host: "180.160.94.92",
    port: 12345,
  },
].map((backend) => {
  return {
    ...backend,
    toString: () => `${backend.host}:${backend.port}`,
    // 其他代码已经不需要了，只要这里留着就行。dev 访问 localhost:8000，prod 访问 /api
    toBase: () => import.meta.env.VITE_API_URL,
  };
});

export function getCurrentBackend() {
  return backendList[current_backend];
}

export function updateCurrentBackend(index: 0 | 1) {
  current_backend = index;
}
