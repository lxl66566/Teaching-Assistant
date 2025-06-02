-- documents
-- 文档表
CREATE TABLE
  IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    type TEXT NOT NULL, -- 文档类型（PDF、DOCX、PPT等）
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    status TEXT NOT NULL, -- processing, completed, failed, embedding
    progress INTEGER DEFAULT 0, -- 处理进度 0-100
    message TEXT, -- 处理状态信息
    size INTEGER, -- 文件大小（字节）
    chunk_size INTEGER, -- 分块数量（字节）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

-- models
-- 远程模型配置表
CREATE TABLE
  IF NOT EXISTS remote_model_configs (
    provider TEXT NOT NULL PRIMARY KEY, -- 服务提供商（OpenAI, Google, Anthropic等）
    api_key TEXT NOT NULL -- 远程模型API密钥
  );

-- 当前模型配置，仅一行，用于记录当前正在使用的模型配置
CREATE TABLE
  IF NOT EXISTS current_model_config (
    type TEXT NOT NULL, -- 模型类型：remote 或 local
    name TEXT NOT NULL, -- 当前模型的名称
    provider TEXT -- 如果是远程模型，则为服务提供商
  );

CREATE TRIGGER IF NOT EXISTS update_documents_updated_at AFTER
UPDATE ON documents BEGIN
UPDATE documents
SET
  updated_at = CURRENT_TIMESTAMP
WHERE
  id = NEW.id;

END;