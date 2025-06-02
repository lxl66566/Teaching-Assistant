// 类型定义
export interface Document {
  id: string;
  filename: string;
  type: string; // 文档类型（PDF、DOCX、PPT等）
  description?: string;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
  enabled?: boolean;
  chunk_size?: number;
}

export interface DocumentStatus {
  id: string;
  status: string;
  progress: number;
  message: string;
  created_at: string;
  updated_at: string;
}
