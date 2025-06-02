export const config = {
  apiUrls: {
    default: import.meta.env.VITE_API_URL,
    // default: "http://localhost:8000/api",
  },
  currentApiUrl: "default", // 默认使用的 API URL
  appName: import.meta.env.VITE_APP_NAME,
};

// Type-safe config access
export type Config = typeof config;

// 添加更新当前 API URL 的函数
export const updateCurrentApiUrl = (urlKey: keyof typeof config.apiUrls) => {
  config.currentApiUrl = urlKey;
};
