import axios from "axios";
import { DocumentStatus, Document } from "@/types/document";
import { getCurrentBackend } from "@/config/backend";

// API 类
export class KnowledgeAPI {
  // 1.1 上传文档
  async uploadDocument(file: File, type: string, description?: string) {
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("type", type);
      if (description) formData.append("description", description);

      const response = await axios.post(`${getCurrentBackend().toBase()}/knowledge/upload`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorMessage = error.response?.data?.detail || "上传失败";
        throw new Error(errorMessage);
      }
      throw error;
    }
  }

  // 1.2 获取文档处理状态
  async getDocumentStatus(documentId: string): Promise<DocumentStatus> {
    const response = await axios.get(`${getCurrentBackend().toBase()}/knowledge/status/${documentId}`);
    return response.data;
  }

  // 1.3 获取知识库列表
  async getKnowledgeList(params?: { category?: string; type?: string }): Promise<Document[]> {
    const response = await axios.get(`${getCurrentBackend().toBase()}/knowledge/list`, { params });
    return response.data.documents;
  }

  // 1.4 删除知识库文档
  async deleteDocument(documentId: string) {
    const response = await axios.delete(`${getCurrentBackend().toBase()}/knowledge/${documentId}`);
    return response.data;
  }

  // 1.5 更新文档信息
  async updateDocument(documentId: string, newName?: string, enabled?: boolean) {
    const response = await axios.put(`${getCurrentBackend().toBase()}/knowledge/${documentId}`, {
      new_name: newName,
      enabled: enabled,
    });
    return response.data as Document;
  }
}

// 导出默认实例
export const knowledgeAPI = new KnowledgeAPI();
