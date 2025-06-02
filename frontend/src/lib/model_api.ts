import { getCurrentBackend } from "@/config/backend";
import axios, { AxiosError } from "axios";
import {
  ProviderListResponse,
  ProviderModelsResponse,
  LocalModelsResponse,
  ModelConfigureRequest,
  ModelConfigureResponse,
  CurrentModelResponse,
  SearchModelsResponse,
  ModelDownloadResponse,
  ModelDownloadProgress,
} from "@/types/model";

export class ModelAPI {
  async getProviders(): Promise<ProviderListResponse> {
    try {
      const response = await axios.get(`${getCurrentBackend().toBase()}/models/providers`);
      return response.data;
    } catch (error) {
      const errorMessage = error instanceof AxiosError ? error.message : "获取模型服务商列表失败";
      throw new Error(errorMessage);
    }
  }

  async getProviderModels(provider: string): Promise<ProviderModelsResponse> {
    try {
      const response = await axios.get(`${getCurrentBackend().toBase()}/models/providers/${provider}`);
      return response.data;
    } catch (error) {
      const errorMessage = error instanceof AxiosError ? error.message : "获取服务商模型列表失败";
      throw new Error(errorMessage);
    }
  }

  async getLocalModels(): Promise<LocalModelsResponse> {
    try {
      const response = await axios.get(`${getCurrentBackend().toBase()}/models/local`);
      return response.data;
    } catch (error) {
      const errorMessage = error instanceof AxiosError ? error.message : "获取本地模型列表失败";
      throw new Error(errorMessage);
    }
  }

  async configureModel(config: ModelConfigureRequest): Promise<ModelConfigureResponse> {
    try {
      const response = await axios.post(`${getCurrentBackend().toBase()}/models/configure`, config);
      return response.data;
    } catch (error) {
      const errorMessage = error instanceof AxiosError ? error.message : "配置模型失败";
      throw new Error(errorMessage);
    }
  }

  async getCurrentModel(): Promise<CurrentModelResponse> {
    try {
      const response = await axios.get(`${getCurrentBackend().toBase()}/models/current`);
      return response.data;
    } catch (error) {
      const errorMessage = error instanceof AxiosError ? error.message : "获取当前模型配置失败";
      throw new Error(errorMessage);
    }
  }

  async searchModels(query: string): Promise<SearchModelsResponse> {
    try {
      const response = await axios.get(`${getCurrentBackend().toBase()}/models/search`, {
        params: { query },
      });
      console.log("searchModels", response.data);
      return response.data;
    } catch (error) {
      const errorMessage = error instanceof AxiosError ? error.message : "搜索模型失败";
      throw new Error(errorMessage);
    }
  }

  async downloadModel(name: string): Promise<ModelDownloadResponse> {
    try {
      const response = await axios.post(`${getCurrentBackend().toBase()}/models/download`, {
        name,
      });
      return response.data;
    } catch (error) {
      const errorMessage = error instanceof AxiosError ? error.message : "开始下载模型失败";
      throw new Error(errorMessage);
    }
  }

  async getDownloadProgress(modelName: string): Promise<ModelDownloadProgress> {
    try {
      const response = await axios.get(`${getCurrentBackend().toBase()}/models/download/${modelName}/progress`);
      return response.data;
    } catch (error) {
      const errorMessage = error instanceof AxiosError ? error.message : "获取下载进度失败";
      throw new Error(errorMessage);
    }
  }
}

export const modelAPI = new ModelAPI();
