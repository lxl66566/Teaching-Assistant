import { MessageSquare, Trash2 } from "lucide-react";
import { config } from "@/config";
// import { FileUploadModal } from "@/components/DocumentManagement/FileUploadModal";
import { useToast } from "@/components/ui/use-toast";
// import { Toaster } from "@/components/ui/toaster";
import { motion } from "framer-motion";
import React, { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Loader2 } from "lucide-react";
import ChatMessage from "@/components/ChatMessage";
import Thinking from "@/components/Thinking";
import { queryAPI, ChatMessage as ChatMessageType, WorkflowResponse } from "@/lib/query_api";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
// import SourcePanel from "@/components/SourcePanel";
// import { AnimatePresence } from "framer-motion";
import WorkflowTimeline from "@/components/WorkflowTimeline";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import { ChevronRightIcon, ChevronDownIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useMode } from "@/context/ModeContext";
import { AppMode } from "@/types/chat";
import KnowledgeGraph from "@/components/KnowledgeGraph";

// 定义前端使用的消息类型
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  workflow_id?: string;
  workflow?: WorkflowResponse;
  streaming?: boolean;
  state?: {
    sources?: Array<{
      file_name: string;
      content?: string;
      page?: number;
      relevance?: number;
    }>;
    followUpQuestions?: string[];
  };
  followUpQuestions?: string[];
}

// 本地存储的键名
const MESSAGES_STORAGE_KEY = "chat_messages";
// 轮询间隔（毫秒）
const POLLING_INTERVAL = 1000;

const ChatApp: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>(() => {
    // 初始化时从localStorage加载消息
    const savedMessages = localStorage.getItem(MESSAGES_STORAGE_KEY);
    return savedMessages ? JSON.parse(savedMessages) : [];
  });
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  // const [sourcePanelOpen, setSourcePanelOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const pollingIntervals = useRef<Record<string, NodeJS.Timeout>>({});
  // 添加折叠状态控制
  const [isWorkflowCollapsed, setIsWorkflowCollapsed] = useState(false);
  const { currentMode } = useMode();

  // const scrollToBottom = () => {
  //   messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  // };

  // 从本地存储加载消息
  useEffect(() => {
    const savedMessages = localStorage.getItem(MESSAGES_STORAGE_KEY);
    if (savedMessages) {
      try {
        const parsedMessages = JSON.parse(savedMessages);
        setMessages(parsedMessages);

        // 恢复任何需要继续轮询的工作流
        parsedMessages.forEach((msg: Message) => {
          if (msg.workflow_id && msg.workflow && msg.workflow.status === "processing") {
            startPolling(msg.workflow_id, msg.id);
          }
        });
      } catch (error) {
        console.error("Error parsing saved messages:", error);
      }
    }
  }, []);

  // 页面加载时自动聚焦输入框
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  // 当未选中消息时关闭源面板
  // useEffect(() => {
  //   if (!selectedMessage) {
  //     setSourcePanelOpen(false);
  //   }
  // }, [selectedMessage]);

  // 当消息变化时，保存到localStorage
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem(MESSAGES_STORAGE_KEY, JSON.stringify(messages));
    }
  }, [messages]);

  // 组件卸载时清理所有轮询intervals
  useEffect(() => {
    return () => {
      Object.values(pollingIntervals.current).forEach(clearInterval);
    };
  }, []);

  // 开始轮询工作流状态
  const startPolling = (workflowId: string, messageId: string) => {
    if (pollingIntervals.current[workflowId]) {
      clearInterval(pollingIntervals.current[workflowId]);
    }

    pollingIntervals.current[workflowId] = setInterval(async () => {
      try {
        const response = await queryAPI.pollWorkflow(workflowId);

        // 更新消息中的工作流状态
        setMessages((prev) => {
          return prev.map((msg) => {
            if (msg.id === messageId) {
              return {
                ...msg,
                workflow: response,
                // 如果工作流完成，将最终内容设置为消息内容
                ...(response.status === "completed" && response.final_content ? { content: response.final_content } : {}),
              };
            }
            return msg;
          });
        });

        // 如果工作流完成或出错，停止轮询
        if (response.status !== "processing") {
          clearInterval(pollingIntervals.current[workflowId]);
          delete pollingIntervals.current[workflowId];
          setIsLoading(false);

          if (response.status === "error") {
            throw new Error(response.error || "Unknown error");
          } else if (response.status === "completed") {
            setIsWorkflowCollapsed(true);
          }
        }
      } catch (error) {
        console.error("轮询工作流出错:", error);
        clearInterval(pollingIntervals.current[workflowId]);
        delete pollingIntervals.current[workflowId];

        toast({
          title: "轮询错误",
          description: error instanceof Error ? error.message : "轮询工作流状态时出错",
          variant: "danger",
        });
      }
    }, POLLING_INTERVAL);
  };

  // 将前端消息格式转换为API需要的格式
  const convertMessagesToApi = (messages: Message[]): ChatMessageType[] => {
    return messages.map((msg) => ({
      role: msg.role,
      content: msg.content,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    // 发送新消息时关闭源面板
    setSelectedMessage(null);

    const userTimestamp = Date.now();

    // 添加用户消息
    const userMessage: Message = {
      id: `user-${userTimestamp}`,
      role: "user",
      content: inputMessage.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsThinking(true);
    setInputMessage("");
    setIsLoading(true);

    try {
      // 获取最新消息列表（包括刚刚添加的用户消息）
      const updatedMessages = [...messages, userMessage];

      // 转换为API需要的格式
      const apiMessages = convertMessagesToApi(updatedMessages);

      // 发送聊天请求，创建工作流
      const { workflow_id, message_id } = await queryAPI.sendChatRequest(apiMessages, userMessage.content, currentMode, {
        temperature: 0.2,
        max_tokens: 1000,
      });

      // 创建助手消息
      const assistantMessage: Message = {
        id: message_id,
        role: "assistant",
        content: "",
        workflow_id: workflow_id,
        workflow: {
          status: "processing",
          current_step: 0,
          total_steps: 4, // 默认值，将在首次轮询时更新
          steps: [],
        },
      };

      // 添加助手消息
      setMessages((prev) => [...prev, assistantMessage]);
      setIsThinking(false);

      // 开始轮询工作流状态
      startPolling(workflow_id, message_id);
    } catch (error) {
      console.error("错误:", error);

      // 显示错误提示
      toast({
        title: "错误",
        description: error instanceof Error ? error.message : "发生了意外错误",
        variant: "danger",
      });

      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: "抱歉，出现了问题。请重试。",
        },
      ]);
      setIsLoading(false);
      setIsThinking(false);
    }
  };

  // const handleFollowUpClick = (question: string) => {
  //   setInputMessage(question);
  //   const fakeEvent = { preventDefault: () => {} } as React.FormEvent;
  //   handleSubmit(fakeEvent);
  // };

  // const handleSourceClick = (message: Message) => {
  //   setSelectedMessage(message);
  //   setSourcePanelOpen(true);
  // };

  // const closeSourcePanel = () => {
  //   setSourcePanelOpen(false);
  //   setSelectedMessage(null);
  // };

  const handleClearMessages = () => {
    setMessages([]);
    setIsLoading(false);
    localStorage.removeItem(MESSAGES_STORAGE_KEY);

    // TODO: 消息格式处理好后，clear 时取消当前工作流
    // if (messages.length > 0 && messages[messages.length - 1]) {

    // }
  };

  // const handleChatUpload = async (files: FileList) => {
  //   try {
  //     await ingestionApi.uploadDocuments(Array.from(files));
  //     setIsUploadModalOpen(false);

  //     // 显示上传成功提示
  //     toast({
  //       title: "✅ 上传成功",
  //       description: "您的文档已上传。请前往知识库管理系统进行处理。",
  //       className: "bg-green-50 text-green-900 border-green-200",
  //     });
  //   } catch (error) {
  //     toast({
  //       title: "错误",
  //       description: error instanceof Error ? error.message : "文件上传失败",
  //       variant: "danger",
  //     });
  //   }
  // };

  const renderMessageContent = (msg: Message) => {
    if (msg.role === "assistant" && msg.workflow) {
      if (msg.workflow.status === "processing" || (msg.workflow.status === "completed" && msg.workflow.steps && msg.workflow.steps.length > 0)) {
        return (
          <div className="w-full">
            {/* 添加折叠/展开按钮和折叠后的简略显示 */}
            {msg.workflow.status === "completed" ? (
              <div className="mb-4">
                <button onClick={() => setIsWorkflowCollapsed(!isWorkflowCollapsed)} className="flex items-center text-sm text-gray-600 hover:text-gray-800">
                  {isWorkflowCollapsed ? (
                    <span className="flex items-center">
                      <ChevronRightIcon className="h-4 w-4 mr-1" />
                      展开工作流程
                    </span>
                  ) : (
                    <span className="flex items-center">
                      <ChevronDownIcon className="h-4 w-4 mr-1" />
                      折叠工作流程
                    </span>
                  )}
                </button>
              </div>
            ) : null}

            {/* 折叠时显示简略信息 */}
            {isWorkflowCollapsed && msg.workflow.status === "completed" ? (
              <div className="flex items-center space-x-2 text-sm text-gray-600 bg-gray-50 p-2 rounded">
                {msg.workflow.steps.map((step, index) => (
                  <span key={index} className="flex items-center">
                    <span
                      className={cn(
                        "w-5 h-5 flex items-center justify-center rounded-full text-xs",
                        step.status === "completed" && "bg-green-100 text-green-800",
                        step.status === "processing" && "bg-blue-100 text-blue-800",
                        step.status === "waiting" && "bg-gray-100 text-gray-800",
                        step.status === "error" && "bg-red-100 text-red-800",
                      )}
                    >
                      {index + 1}
                    </span>
                    <span className="ml-1">{step.name}</span>
                    {index < msg.workflow!.steps.length - 1 && <ChevronRightIcon className="h-4 w-4 mx-1" />}
                  </span>
                ))}
              </div>
            ) : (
              <WorkflowTimeline steps={msg.workflow.steps} currentStep={msg.workflow.current_step} status={msg.workflow.status} />
            )}

            {/* 最终内容显示部分 */}
            {msg.workflow.status === "completed" &&
              msg.workflow.final_content &&
              (currentMode === AppMode.Graph ? (
                <div className="mt-4 p-4 border-2 border-gray-200 rounded-lg">
                  <KnowledgeGraph graphData={JSON.parse(msg.workflow.final_content)} />
                </div>
              ) : (
                <div className="mt-4 p-4 border-t border-gray-200">
                  <h3 className="font-medium text-gray-700 mb-2">最终回答</h3>
                  <MarkdownRenderer markdown={msg.workflow.final_content} />
                </div>
              ))}

            {/* 错误消息部分保持不变 */}
            {msg.workflow.error && (
              <div className="mt-4 p-4 bg-red-50 text-red-500 rounded-md">
                <h3 className="font-medium mb-1">处理错误</h3>
                <p>{msg.workflow.error}</p>
              </div>
            )}
          </div>
        );
      }
      // 如果工作流已完成且有内容，使用常规消息显示
      else if (msg.workflow.status === "completed" && msg.workflow.final_content) {
        return (
          <ChatMessage
            isAi={true}
            message={msg.workflow.final_content}
            followUpQuestions={msg.followUpQuestions}
            // onFollowUpClick={handleFollowUpClick}
            state={msg.state}
            // onSourceClick={() => handleSourceClick(msg)}
            isSelected={selectedMessage?.id === msg.id}
          />
        );
      }
    }

    // 默认显示方式
    return (
      <ChatMessage
        isAi={msg.role === "assistant"}
        message={msg.content}
        streaming={msg.streaming}
        followUpQuestions={msg.followUpQuestions}
        // onFollowUpClick={handleFollowUpClick}
        state={msg.state}
        // onSourceClick={() => handleSourceClick(msg)}
        isSelected={selectedMessage?.id === msg.id}
      />
    );
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }} className="p-4 h-full flex flex-col">
      <motion.div
        className="bg-white shadow-xl flex flex-col h-full rounded-xl overflow-hidden border border-gray-100"
        initial={{ y: 20 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5, type: "spring", stiffness: 100 }}
      >
        <div className="bg-gradient-to-r from-[#005ba1] to-[#0077cc] text-white py-3 px-4 flex items-center justify-between shrink-0 rounded-t-xl">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            <h1 className="text-xl font-semibold">{config.appName}</h1>
            {messages.length > 0 && <div className="ml-2 bg-white/20 text-white text-xs rounded-full px-2 py-0.5">{messages.length} 条消息</div>}
          </div>

          <div className="flex items-center gap-2">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => {
                handleClearMessages();
              }}
              className="hover:bg-white/20 p-2 rounded-full transition-colors duration-200"
            >
              <Trash2 className="h-5 w-5" />
            </motion.button>
          </div>
        </div>

        <div className="flex-1 overflow-hidden relative">
          <div className="flex h-full flex-col relative overflow-hidden">
            {/* <AnimatePresence>
              {sourcePanelOpen && selectedMessage && (
                <motion.div
                  initial={{ x: "100%", opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  exit={{ x: "100%", opacity: 0 }}
                  transition={{ type: "spring", damping: 25, stiffness: 200 }}
                  className="absolute top-0 right-0 z-10 h-full w-[300px] sm:w-[320px] md:w-[380px] border-l bg-white shadow-md"
                >
                  <div className="flex justify-between items-center p-3 border-b bg-gray-50">
                    <h3 className="font-medium text-sm">资料来源</h3>
                    <Button variant="ghost" size="icon" onClick={closeSourcePanel} className="h-8 w-8 rounded-full hover:bg-gray-200">
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="h-full overflow-auto">
                    <SourcePanel message={selectedMessage} />
                  </div>
                </motion.div>
              )}
            </AnimatePresence> */}

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-4 space-y-6">
                  <div className="w-20 h-20 rounded-full bg-blue-50 flex items-center justify-center">
                    <MessageSquare className="h-10 w-10 text-blue-500" />
                  </div>
                  <div className="space-y-2 max-w-md">
                    <h3 className="text-xl font-semibold text-gray-800">欢迎使用 {config.appName}</h3>
                    <p className="text-gray-500">这是一个基于 Agentic RAG 技术的教学辅助系统。您可以在导航栏选择模式，系统将为您提供帮助。</p>
                  </div>
                </div>
              ) : (
                messages.map((msg) => (
                  <div key={msg.id} className="mt-2">
                    {msg.role === "user" ? (
                      <ChatMessage
                        isAi={false}
                        message={msg.content}
                        followUpQuestions={[]}
                        onFollowUpClick={() => {}}
                        onSourceClick={() => {}}
                        isSelected={false}
                      />
                    ) : (
                      renderMessageContent(msg)
                    )}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="p-4 border-t border-gray-200 bg-white/90 backdrop-blur-sm">
              <form onSubmit={handleSubmit} className="flex items-end gap-2">
                <Card className="flex-1 shadow-sm">
                  <CardContent className="p-3">
                    <div className="relative">
                      <Input
                        ref={inputRef}
                        placeholder="请输入您的问题..."
                        className="border-0 focus-visible:ring-0 pl-2 pr-10 py-5 shadow-none"
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        disabled={isLoading}
                      />
                    </div>
                  </CardContent>
                </Card>

                <div className="flex items-center gap-2">
                  {/* <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button type="button" size="icon" className="rounded-full" disabled={isLoading} onClick={onUploadClick}>
                          <Paperclip className="h-5 w-5" />
                          <span className="sr-only">上传文件</span>
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>上传文件</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider> */}

                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button type="submit" className="rounded-full bg-blue-600 hover:bg-blue-700" size="icon" disabled={!inputMessage.trim() || isLoading}>
                          {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                          <span className="sr-only">发送消息</span>
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>发送消息</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              </form>
              {isThinking && (
                <div className="mt-2">
                  <Thinking />
                </div>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      {/* <FileUploadModal isOpen={isUploadModalOpen} onClose={() => setIsUploadModalOpen(false)} onUpload={handleChatUpload} /> */}
    </motion.div>
  );
};

export default ChatApp;
