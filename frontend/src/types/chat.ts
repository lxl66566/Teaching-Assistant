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
  Graph = "知识图谱模式",
}

// 将模式转换为接口的字符串
export function AppModeToInterfaceString(mode: AppMode): string {
  switch (mode) {
    case AppMode.LessonPlan:
      return "teaching plan";
    case AppMode.Agent:
      return "agent";
    case AppMode.Free:
      return "free";
    case AppMode.Graph:
      return "graph";
  }
}
