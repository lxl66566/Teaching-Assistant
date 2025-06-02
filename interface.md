# 接口文档

## 概述

本文档描述了 RAG 教学辅助系统的 API 接口规范。系统采用前后端分离架构，前端使用 React+TypeScript+TailwindCSS，后端使用 Python 的 FastAPI 框架，数据库使用 SQLite。

## 基础信息

- base URL: `/api`
- 数据格式: JSON

## 接口列表

### 1. 知识库管理

#### 1.1 上传文档

- **URL**: `/knowledge/upload`
- **方法**: POST
- **描述**: 上传文档到知识库进行处理
- **请求参数**: FormData 格式
  ```typescript
  {
    file: File;                  // 文件（支持 PDF、DOCX、PPT、TXT 等格式）
    type: string;                // 文档类型
    description?: string;        // 描述（可选）
  }
  ```
- **响应**:
  ```json
  {
    "id": "string",
    "filename": "string",
    "type": "string",
    "size": "integer",
    "status": "processing",
    "created_at": "string"
  }
  ```

#### 1.2 获取文档处理状态

- **URL**: `/knowledge/status/{document_id}`
- **方法**: GET
- **描述**: 获取文档处理状态
- **请求参数**: 路径参数
  - `document_id`: 文档 ID
- **响应**:
  ```json
  {
    "id": "string",
    "status": "string", // processing, completed, failed
    "progress": "number", // 0-100
    "message": "string",
    "created_at": "string",
    "updated_at": "string"
  }
  ```

#### 1.3 获取知识库列表

- **URL**: `/knowledge/list`
- **方法**: GET
- **描述**: 获取知识库文档和分组列表
- **请求参数**: 查询参数
  ```typescript
  {
    type?: string;              // 文档类型（可选）
  }
  ```
- **响应**:
  ```json
  {
    "documents": [
      {
        "id": "string",
        "filename": "string",
        "enabled": "boolean",
        "type": "string",
        "description": "string",
        "status": "string",
        "created_at": "string"
      }
    ]
  }
  ```

#### 1.4 删除知识库文档

- **URL**: `/knowledge/{document_id}`
- **方法**: DELETE
- **描述**: 删除知识库中的文档
- **请求参数**: 路径参数
  - `document_id`: 文档 ID
- **响应**:
  ```json
  {
    "success": true,
    "message": "文档已成功删除"
  }
  ```

#### 1.5 更新文档信息（改名，改 enabled 状态）

- **URL**: `/knowledge/{document_id}`
- **方法**: PUT
- **描述**: 更新文档信息
- **请求参数**:
  ```typescript
  {
    new_name?: string;         // 新文档名字
    enabled?: boolean;         // 是否启用
  }
  ```
- **响应**:
  ```json
  {
    "id": "string",
    "filename": "string",
    "type": "string", // 文档类型（PDF、DOCX、PPT等）
    "description": "string", // 描述（可选）
    "status": "processing",
    "created_at": "string",
    "enabled": "boolean"
  }
  ```

### 2. 聊天接口

#### 2.1. 发送聊天请求接口

- **URL**: `/chat/send`
- **方法**: POST
- **描述**: 发送聊天请求，启动聊天处理工作流，返回工作流 ID
- **请求参数**:
  ```typescript
  {
    content: string;            // 当前用户消息内容
    messages: Array<{           // 完整的消息历史记录
      role: "user" | "assistant";
      content: string;
    }>;
    mode?: "teaching plan" | "agent" | "free"; // 当前模式，默认为 "teaching plan"
    options?: {
      temperature?: number;     // 温度参数（可选）
      max_tokens?: number;      // 最大生成token数（可选）
    }
  }
  ```
- **响应**:
  ```typescript
  {
    workflow_id: string; // 工作流ID，用于后续轮询结果
    message_id: string; // 消息ID
  }
  ```

#### 2.2. 轮询聊天结果接口

- **URL**: `/chat/poll/{workflow_id}`
- **方法**: GET
- **描述**: 轮询指定工作流的处理结果，获取当前步骤和状态
- **路径参数**:
  - `workflow_id`: 工作流 ID
- **响应**:
  ```typescript
  {
    status: "processing" | "completed" | "error" | "calcelled";      // 工作流状态
    current_step: number;                              // 当前步骤索引（从0开始）
    total_steps: number;                               // 总步骤数
    steps: Array<{
      index: number;                                   // 步骤索引
      name: string;                                    // 步骤名称
      description: string;                             // 步骤描述
      status: "waiting" | "processing" | "completed" | "error"; // 步骤状态
      result?: string;                                 // 步骤结果（Markdown文本）
      error?: string;                                  // 错误信息（如果有）
    }>;
    final_content?: string;                            // 最终生成内容（仅当工作流完成时）
    error?: string;                                    // 错误信息（如果有）
  }
  ```

#### 2.3. 取消工作流

- **URL**: `/chat/cancel/{workflow_id}`
- **方法**: POST
- **描述**: 取消指定工作流
- **路径参数**:
  - `workflow_id`: 工作流 ID
- **响应**:
  ```json
  {
    "success": true,
    "message": "工作流已取消"
  }
  ```

### 3. 模型管理

#### 3.1 获取模型服务商

- **URL**: `/models/providers`
- **方法**: GET
- **描述**: 获取系统支持的所有模型服务商
- **响应**:
  ```json
  {
    "provider": [
      "string" // 模型服务商
    ]
  }
  ```

#### 3.2 获取某个模型服务商的所有模型和其 api key

- **URL**: `/models/providers/{provider}`
- **方法**: GET
- **描述**: 获取某个模型服务商的所有模型和其 api
- **响应**:
  ```json
  {
    "model": [
      "string" // 模型名称
    ],
    "api_key": "string" // provider API 密钥
  }
  ```

#### 3.3 获取本地所有模型

- **URL**: `/models/local`
- **方法**: GET
- **描述**: 获取本地所有模型
- **响应**:
  ```json
  {
    "model": [
      {
        "name": "string", // 模型名称
        "status": "string", // 状态：ready/downloading/not_found
        "size": "string", // 模型大小（如果已下载）
        "digest": "string" // 模型标识符
      }
    ]
  }
  ```

#### 3.4 搜索可用模型

- **URL**: `/models/search`
- **方法**: GET
- **描述**: 搜索可下载的模型
- **请求参数**: 查询参数
  ```typescript
  {
    query: string; // 搜索关键词
  }
  ```
- **响应**:
  ```json
  {
    "models": [
      {
        "name": "string", // 模型名称（带 tag）
        "description": "string", // 模型描述 (optional)
        "size": "string", // 模型大小 (optional)
        "updated": "string" // 模型标识符 (optional)
      }
    ]
  }
  ```

#### 3.5 下载模型

- **URL**: `/models/download`
- **方法**: POST
- **描述**: 开始下载模型
- **请求参数**:
  ```json
  {
    "name": "string" // 模型名称
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "开始下载模型"
  }
  ```

#### 3.6 获取下载进度

- **URL**: `/models/download/{model_name}/progress`
- **方法**: GET
- **描述**: 获取模型下载进度
- **响应**:
  ```json
  {
    "status": "string", // downloading/completed/failed
    "progress": "number", // 0-100
    "message": "string" // 错误信息（如果有）
  }
  ```

#### 3.7 使用某个特定模型

- **URL**: `/models/configure`
- **方法**: POST
- **描述**: 配置远程模型 API 密钥或本地模型
- **请求参数**:
  ```typescript
  {
    type: "remote" | "local";
    name: string;                // 模型名称
    provider?: string;           // 模型服务商
    api_key?: string;            // 远程模型 API 密钥（可选）
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "模型配置已更新"
  }
  ```

#### 3.8 获取当前模型配置

- **URL**: `/models/current`
- **方法**: GET
- **描述**: 获取当前模型配置
- **响应**:
  ```json
  {
    "type": "string", // remote 或 local 或 null
    "name": "string", // 模型名称（如果 type 为 null，则为 null）
    "provider": "string" // 模型服务商（如果是本地模型，则为 null）
  }
  ```

### 4. 系统状态

#### 4.1 获取系统状态

- **URL**: `/system/status`
- **方法**: GET
- **描述**: 获取系统运行状态
- **响应**:
  ```json
  {
    "status": "running",
    "version": "string",
    "database_status": "connected",
    "knowledge_base_count": "integer",
    "document_count": "integer",
    "embedding_model": "string",
    "active_llm": "string"
  }
  ```

## 错误码定义

| 错误码 | 描述                             |
| ------ | -------------------------------- |
| 400    | 请求参数错误                     |
| 404    | 资源不存在                       |
| 500    | 服务器内部错误                   |
| 503    | 服务不可用，可能是模型服务未配置 |
