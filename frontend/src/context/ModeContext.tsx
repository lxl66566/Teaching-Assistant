import React, { createContext, useState, useContext, ReactNode } from "react";

import { AppMode } from "@/types/chat";

// 定义 Context 的类型
interface ModeContextType {
  currentMode: AppMode;
  setMode: (mode: AppMode) => void;
}

// 创建 Context
const ModeContext = createContext<ModeContextType | undefined>(undefined);

// 创建 Provider 组件
interface ModeProviderProps {
  children: ReactNode;
}

export const ModeProvider: React.FC<ModeProviderProps> = ({ children }) => {
  const [currentMode, setCurrentMode] = useState<AppMode>(AppMode.LessonPlan); // 默认设置为自由模式

  const setMode = (mode: AppMode) => {
    setCurrentMode(mode);
  };

  return (
    <ModeContext.Provider value={{ currentMode, setMode }}>
      {children}
    </ModeContext.Provider>
  );
};

// 自定义 Hook 方便组件使用 Context
export const useMode = () => {
  const context = useContext(ModeContext);
  if (context === undefined) {
    throw new Error("useMode must be used within a ModeProvider");
  }
  return context;
};
