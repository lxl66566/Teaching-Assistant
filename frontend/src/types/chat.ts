export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatOptions {
  temperature?: number;
  max_tokens?: number;
}

// 定义模式枚举
export enum AppMode {
  LessonPlan = "教案模式",
  Agent = "Agent 模式",
  Free = "自由模式",
}
