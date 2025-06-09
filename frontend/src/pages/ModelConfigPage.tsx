import React, { useState, useEffect } from "react";
import * as Tabs from "@radix-ui/react-tabs";
import * as Select from "@radix-ui/react-select";
import * as Form from "@radix-ui/react-form";
import { useToast } from "@/components/ui/use-toast";
import { modelAPI } from "../lib/model_api";
import {
  ModelConfigureRequest,
  CurrentModelResponse,
  SearchModel,
  LocalModel,
} from "../types/model";

export const ModelConfigPage: React.FC = () => {
  // 修改状态管理
  const [activeTab, setActiveTab] = useState<"remote" | "local">("remote");
  const [providers, setProviders] = useState<string[]>([]);
  const [selectedProvider, setSelectedProvider] = useState("");
  const [providerModels, setProviderModels] = useState<string[]>([]);
  const [localModels, setLocalModels] = useState<LocalModel[]>([]);
  const [localModelsName, setLocalModelsName] = useState<Set<string>>(
    new Set(),
  );
  const [selectedModel, setSelectedModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [currentModel, setCurrentModel] = useState<CurrentModelResponse | null>(
    null,
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchModel[]>([]);
  const [downloadingModels, setDownloadingModels] = useState<
    Record<string, number>
  >({});

  const { toast } = useToast();

  const fetchRemoteProvidersData = async () => {
    try {
      const [currentModelRes, providersRes] = await Promise.all([
        modelAPI.getCurrentModel(),
        modelAPI.getProviders(),
      ]);
      console.log(currentModelRes, providersRes);
      if (currentModelRes?.type === "null") {
        setCurrentModel(null);
      } else {
        setCurrentModel(currentModelRes);
      }
      setProviders(providersRes.provider);
      setIsLoading(false);
    } catch (error) {
      console.error("初始化数据加载失败:", error);
      showMessage("错误", "加载模型配置失败");
      setIsLoading(false);
    }
  };

  // 初始时获取服务商列表
  useEffect(() => {
    fetchRemoteProvidersData();
  }, []);

  // 当切换到本地模型标签时获取本地模型列表
  useEffect(() => {
    const tabSwitchHandler = async () => {
      if (activeTab === "remote") {
        await fetchRemoteProvidersData();
        return;
      }
      try {
        const response = await modelAPI.getLocalModels();
        setLocalModels(response.model);
      } catch (error) {
        console.error("获取本地模型列表失败:", error);
        showMessage("错误", "获取本地模型列表失败");
      }
    };

    tabSwitchHandler();
  }, [activeTab]);

  // 当选择服务商时获取该服务商的模型列表
  useEffect(() => {
    const fetchProviderModels = async () => {
      if (!selectedProvider) {
        setProviderModels([]);
        setApiKey("");
        return;
      }

      try {
        const response = await modelAPI.getProviderModels(selectedProvider);
        setProviderModels(response.model);
        setApiKey(response.api_key || "");
      } catch (error) {
        console.error("获取服务商模型列表失败:", error);
        showMessage("错误", "获取服务商模型列表失败");
      }
    };

    fetchProviderModels();
  }, [selectedProvider]);

  // 更新本地模型名称集合
  useEffect(() => {
    setLocalModelsName(new Set(localModels.map((model) => model.name)));
  }, [localModels]);

  // 搜索模型
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault(); // 防止表单提交导致页面刷新
    if (!searchQuery.trim()) return;

    try {
      setIsSearching(true);
      const response = await modelAPI.searchModels(searchQuery);
      if (response.models.length === 0) {
        showMessage("错误", "没有找到任何模型");
        return;
      }
      setSearchResults(response.models);
    } catch (error) {
      console.error("搜索模型失败:", error);
      showMessage("错误", "搜索模型失败");
    } finally {
      setIsSearching(false);
    }
  };

  const handleReset = () => {
    setSearchQuery("");
    setSearchResults([]);
  };

  // 选择本地模型
  const handleSelectLocalModel = (model: LocalModel) => {
    setSelectedModel(model.name);
  };

  // 保存配置
  const handleSaveConfig = async () => {
    try {
      if (!selectedModel) {
        showMessage("错误", "请选择一个模型");
        return;
      }

      if (activeTab === "remote" && apiKey.trim() === "") {
        showMessage("错误", "API Key 不能为空");
        return;
      }

      const config: ModelConfigureRequest = {
        type: activeTab,
        name: selectedModel,
        ...(activeTab === "remote" && {
          provider: selectedProvider,
          api_key: apiKey,
        }),
      };

      await modelAPI.configureModel(config);

      // 更新当前模型信息
      const currentModel = await modelAPI.getCurrentModel();
      setCurrentModel(currentModel);

      showMessage("成功", "模型配置已保存");
    } catch (error) {
      console.error("保存配置失败:", error);
      showMessage("错误", "保存配置失败");
    }
  };

  // 下载模型
  const handleDownload = async (model: SearchModel) => {
    try {
      await modelAPI.downloadModel(model.name);
      setDownloadingModels((prev) => ({ ...prev, [model.name]: 0 }));

      // 开始轮询下载进度
      const intervalId = setInterval(async () => {
        try {
          const progress = await modelAPI.getDownloadProgress(model.name);

          if (progress.status === "completed") {
            clearInterval(intervalId);
            setDownloadingModels((prev) => {
              const newState = { ...prev };
              delete newState[model.name];
              return newState;
            });
            // 刷新本地模型列表
            const response = await modelAPI.getLocalModels();
            setLocalModels(response.model);
          } else if (progress.status === "failed") {
            clearInterval(intervalId);
            setDownloadingModels((prev) => {
              const newState = { ...prev };
              delete newState[model.name];
              return newState;
            });
            showMessage("错误", `下载模型失败: ${progress.message}`);
          } else {
            setDownloadingModels((prev) => ({
              ...prev,
              [model.name]: progress.progress,
            }));
          }
        } catch (error) {
          console.error("获取下载进度失败:", error);
        }
      }, 1000);

      return () => clearInterval(intervalId);
    } catch (error) {
      console.error("开始下载模型失败:", error);
      showMessage("错误", "开始下载模型失败");
    }
  };

  // 修改显示 toast 的逻辑
  const showMessage = (title: string, description: string) => {
    toast({
      title: title,
      description: description,
      variant: title.includes("成功")
        ? "tip"
        : title.includes("错误")
          ? "danger"
          : title.includes("警告")
            ? "warning"
            : "info",
    });
  };

  if (isLoading) {
    return <div className="p-6 text-center">加载中...</div>;
  }

  return (
    <div className="mx-auto max-w-4xl flex-1 p-6">
      <h1 className="mb-6 text-2xl font-bold">模型配置</h1>
      <div className="mb-6 text-sm text-gray-500">
        当前使用模型：
        {currentModel ? (
          <span>
            {currentModel.name}
            {/* {currentModel.provider && ` (${currentModel.provider})`} */}
            {currentModel.type === "remote" ? "（云服务 API）" : "（本地模型）"}
          </span>
        ) : (
          "未配置"
        )}
      </div>

      <Tabs.Root
        value={activeTab}
        onValueChange={(value) => setActiveTab(value as "remote" | "local")}
      >
        <Tabs.List className="mb-6 flex border-b">
          <Tabs.Trigger
            value="remote"
            className="px-4 py-2 focus:outline-none data-[state=active]:border-b-2 data-[state=active]:border-blue-500"
          >
            云服务 API
          </Tabs.Trigger>
          <Tabs.Trigger
            value="local"
            className="px-4 py-2 focus:outline-none data-[state=active]:border-b-2 data-[state=active]:border-blue-500"
          >
            本地模型
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="remote">
          <Form.Root className="space-y-6">
            <Form.Field name="provider">
              <Form.Label className="mb-2 block text-sm font-medium">
                选择服务提供商
              </Form.Label>
              <Select.Root
                value={selectedProvider}
                onValueChange={setSelectedProvider}
              >
                <Select.Trigger className="w-full rounded-md border px-4 py-2">
                  <Select.Value placeholder="选择服务提供商" />
                </Select.Trigger>
                <Select.Portal>
                  <Select.Content className="rounded-md border bg-white shadow-lg">
                    <Select.Viewport>
                      {providers.map((provider) => (
                        <Select.Item
                          key={provider}
                          value={provider}
                          className="cursor-pointer px-4 py-2 hover:bg-gray-100"
                        >
                          <Select.ItemText>{provider}</Select.ItemText>
                        </Select.Item>
                      ))}
                    </Select.Viewport>
                  </Select.Content>
                </Select.Portal>
              </Select.Root>
            </Form.Field>

            {selectedProvider && (
              <>
                <Form.Field name="model">
                  <Form.Label className="mb-2 block text-sm font-medium">
                    选择模型
                  </Form.Label>
                  <Select.Root
                    value={selectedModel}
                    onValueChange={setSelectedModel}
                  >
                    <Select.Trigger className="w-full rounded-md border px-4 py-2">
                      <Select.Value placeholder="选择模型" />
                    </Select.Trigger>
                    <Select.Portal>
                      <Select.Content className="rounded-md border bg-white shadow-lg">
                        <Select.Viewport>
                          {providerModels.map((model) => (
                            <Select.Item
                              key={model}
                              value={model}
                              className="cursor-pointer px-4 py-2 hover:bg-gray-100"
                            >
                              <Select.ItemText>{model}</Select.ItemText>
                            </Select.Item>
                          ))}
                        </Select.Viewport>
                      </Select.Content>
                    </Select.Portal>
                  </Select.Root>
                </Form.Field>

                <Form.Field name="apiKey">
                  <Form.Label className="mb-2 block text-sm font-medium">
                    API Key
                  </Form.Label>
                  <Form.Control asChild>
                    <input
                      type="password"
                      className="w-full rounded-md border px-4 py-2"
                      value={apiKey || ""}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="输入 API Key"
                    />
                  </Form.Control>
                </Form.Field>
              </>
            )}
          </Form.Root>
        </Tabs.Content>

        <Tabs.Content value="local">
          <Form.Root
            className="space-y-6"
            onSubmit={handleSearch}
            onReset={handleReset}
          >
            <div className="mb-6">
              <Form.Field name="searchQuery">
                <Form.Label className="mb-2 block text-sm font-medium">
                  下载新模型到本地
                </Form.Label>
                <div className="flex gap-2">
                  <Form.Control asChild>
                    <input
                      type="text"
                      className="flex-1 rounded-md border px-4 py-2"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="输入关键词搜索模型"
                    />
                  </Form.Control>
                  {searchResults.length > 0 ? (
                    <button
                      type="reset"
                      className="rounded-md bg-red-400 px-4 py-2 text-gray-100 hover:bg-red-600"
                      onClick={handleReset}
                    >
                      清空
                    </button>
                  ) : null}
                  {isSearching ? (
                    <div className="rounded-md bg-gray-300 px-4 py-2 text-white hover:bg-gray-400">
                      搜索中...
                    </div>
                  ) : (
                    <button
                      type="submit"
                      className="rounded-md bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
                    >
                      搜索
                    </button>
                  )}
                </div>
              </Form.Field>
            </div>

            {searchResults.length > 0 && (
              <div className="mb-6">
                <h3 className="mb-4 text-lg font-medium">搜索结果</h3>
                <div className="space-y-4">
                  {searchResults.map((model) => (
                    <div key={model.name} className="rounded-md border p-4">
                      <div className="mb-2 flex items-start justify-between">
                        <div>
                          <h4 className="font-medium">{model.name}</h4>
                          <p className="text-sm text-gray-500">
                            {model.description}
                          </p>
                          <p className="text-sm text-gray-500">
                            大小: {model.size}
                          </p>
                        </div>
                        {downloadingModels[model.name] !== undefined ? (
                          <div className="w-32">
                            <div className="h-2 rounded bg-gray-200">
                              <div
                                className="h-full rounded bg-blue-500"
                                style={{
                                  width: `${downloadingModels[model.name]}%`,
                                }}
                              />
                            </div>
                            <p className="mt-1 text-center text-sm">
                              {downloadingModels[model.name].toFixed(0)}%
                            </p>
                          </div>
                        ) : localModelsName.has(model.name) ? (
                          <span className="rounded-md bg-gray-300 px-4 py-2 text-white hover:bg-gray-400">
                            已下载
                          </span>
                        ) : (
                          <button
                            type="button"
                            onClick={() => handleDownload(model)}
                            className="rounded-md bg-green-500 px-4 py-2 text-white hover:bg-green-600"
                          >
                            下载
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div>
              <h3 className="mb-4 text-lg font-medium">本地模型</h3>
              <div className="space-y-4">
                {localModels.map((model) => (
                  <div
                    key={`${model.name}-${model.digest}`}
                    className={`cursor-pointer rounded-md border p-4 transition-colors ${
                      selectedModel === model.name
                        ? "border-blue-500 bg-blue-50"
                        : "hover:border-gray-400"
                    }`}
                    onClick={() => handleSelectLocalModel(model)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{model.name}</h4>
                        <p className="text-sm text-gray-500">
                          状态: {model.status === "ready" ? "就绪" : "下载中"}
                        </p>
                        <p className="text-sm text-gray-500">
                          大小: {model.size}
                        </p>
                      </div>
                      <div className="flex h-6 w-6 items-center justify-center">
                        {selectedModel === model.name && (
                          <svg
                            className="h-5 w-5 text-blue-500"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Form.Root>
        </Tabs.Content>
      </Tabs.Root>

      <div className="mt-8">
        <button
          onClick={handleSaveConfig}
          disabled={!selectedModel}
          className={`rounded-md px-4 py-2 ${!selectedModel ? "cursor-not-allowed bg-gray-300" : "bg-blue-500 text-white hover:bg-blue-600"}`}
        >
          保存配置
        </button>
      </div>
    </div>
  );
};

export default ModelConfigPage;
