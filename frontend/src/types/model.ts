export interface ProviderListResponse {
  provider: string[];
}

export interface ProviderModelsResponse {
  model: string[];
  api_key: string | null;
}

export interface LocalModelsResponse {
  model: LocalModel[];
}

export interface ModelConfigureRequest {
  type: "remote" | "local";
  name: string;
  provider?: string;
  api_key?: string;
}

export interface ModelConfigureResponse {
  success: boolean;
  message: string;
}

export interface CurrentModelResponse {
  type: "remote" | "local" | "null";
  name?: string;
  provider?: string;
}

export interface LocalModel {
  name: string;
  status: "ready" | "downloading" | "not_found";
  size: string;
  digest: string;
}

export interface SearchModel {
  name: string;
  description: string | null;
  size: string | null;
  updated: string | null;
}

export interface SearchModelsResponse {
  models: SearchModel[];
}

export interface ModelDownloadRequest {
  name: string;
  digest?: string;
}

export interface ModelDownloadResponse {
  success: boolean;
  message: string;
}

export interface ModelDownloadProgress {
  status: "downloading" | "completed" | "failed";
  progress: number;
  message: string;
}
