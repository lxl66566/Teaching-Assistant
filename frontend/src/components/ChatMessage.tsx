import React from "react";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import chatbotIcon from "../assets/chatbot-icon.svg";
import FollowUpQuestions from "./FollowUpQuestions";
import { Button } from "@/components/ui/button";
import { FileText, Copy, Check } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface ChatMessageProps {
  isAi: boolean;
  message: string;
  streaming?: boolean;
  followUpQuestions?: string[];
  onFollowUpClick?: (question: string) => void;
  onSourceClick?: () => void;
  isSelected?: boolean;
  state?: {
    sources?: Array<{ file_name: string }>;
  };
}

const ChatMessage: React.FC<ChatMessageProps> = ({
  isAi,
  message,
  followUpQuestions = [],
  onFollowUpClick,
  state,
  onSourceClick,
  isSelected = false,
}) => {
  const [copied, setCopied] = React.useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(cleanMessage);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("复制失败: ", err);
    }
  };

  // 过滤掉状态消息
  const cleanMessage = message
    .replace(
      /\{"status":\s*"end",\s*"node":\s*"generate",\s*"details":\s*"Node stream ended"\}/g,
      "",
    )
    .trim();

  // 如果消息在清理后为空，则不渲染
  if (!cleanMessage) {
    return null;
  }

  const hasSources = isAi && state?.sources && state.sources.length > 0;
  const sourceCount = hasSources ? state?.sources?.length : 0;

  return (
    <div className="group flex max-w-full flex-col">
      {!isAi && (
        <div className="mb-1 flex w-full justify-end">
          <div className="max-w-[85%] overflow-hidden whitespace-pre-line break-words rounded-2xl bg-gradient-to-br from-blue-600 to-blue-700 p-4 text-white shadow-sm transition-shadow hover:shadow-md">
            <MarkdownRenderer
              // remarkPlugins={[remarkGfm, remarkBreaks]}
              // className="prose prose-sm max-w-none break-words text-white prose-headings:text-white prose-strong:text-white prose-a:text-blue-100 hover:prose-a:text-blue-50"
              markdown={cleanMessage}
            />
          </div>
        </div>
      )}

      {isAi && (
        <div className="mb-1 flex w-full flex-col">
          <div className="flex max-w-full items-start gap-2">
            <img
              src={chatbotIcon}
              alt="机器人"
              className="mt-1 h-8 w-8 shrink-0 rounded-full shadow-sm"
            />
            <div className="min-w-0 max-w-full flex-1">
              <div
                className={`overflow-hidden rounded-2xl border bg-white p-4 ${
                  isSelected
                    ? "border-blue-400 shadow-md ring-2 ring-blue-100"
                    : "border-gray-100 shadow-sm transition-shadow hover:shadow-md"
                }`}
              >
                <div className="prose prose-sm relative max-w-none overflow-auto break-words">
                  <div className="absolute right-0 top-0 opacity-0 transition-opacity group-hover:opacity-100">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={copyToClipboard}
                            className="h-7 w-7 rounded-full hover:bg-gray-100"
                          >
                            {copied ? (
                              <Check className="h-3.5 w-3.5 text-green-500" />
                            ) : (
                              <Copy className="h-3.5 w-3.5 text-gray-400" />
                            )}
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{copied ? "已复制!" : "复制消息"}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                  <MarkdownRenderer
                    // remarkPlugins={[remarkGfm, remarkBreaks]}
                    // className="prose-pre:bg-gray-50 prose-pre:border prose-pre:border-gray-200 prose-code:text-blue-600 prose-code:bg-blue-50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded-md"
                    markdown={cleanMessage}
                  ></MarkdownRenderer>
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-2">
                  {hasSources && (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={onSourceClick}
                            className="flex h-8 items-center gap-1 border-blue-200 text-blue-700 transition-colors hover:bg-blue-50"
                          >
                            <FileText className="h-3.5 w-3.5" />
                            <span>参考资料 ({sourceCount})</span>
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>查看参考资料来源</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}

                  {followUpQuestions && followUpQuestions.length > 0 && (
                    <div className="mt-2 w-full">
                      <FollowUpQuestions
                        questions={followUpQuestions}
                        onQuestionClick={onFollowUpClick}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatMessage;
