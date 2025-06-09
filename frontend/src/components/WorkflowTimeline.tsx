import React, { useState } from "react";
import { WorkflowStep } from "@/lib/query_api";
import { Loader2, CheckCircle, XCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import { Card, CardContent } from "@/components/ui/card";

interface WorkflowTimelineProps {
  steps: WorkflowStep[];
  currentStep: number;
  status: "processing" | "completed" | "error";
}

const WorkflowTimeline: React.FC<WorkflowTimelineProps> = ({ steps }) => {
  // 查找最后一个已完成的步骤，如果没有就返回第一个步骤
  const findInitialStep = () => {
    const lastCompletedIndex = [...steps]
      .reverse()
      .findIndex((step) => step.status === "completed");
    if (lastCompletedIndex !== -1) {
      return steps.length - 1 - lastCompletedIndex;
    }
    return 0;
  };

  const [selectedStep, setSelectedStep] = useState<number>(findInitialStep());

  const getStepIcon = (step: WorkflowStep) => {
    switch (step.status) {
      case "waiting":
        return <Clock className="h-5 w-5 text-gray-400" />;
      case "processing":
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case "error":
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  return (
    <div className="flex w-full flex-col gap-4 md:flex-row">
      {/* 时间线 */}
      <div className="overflow-y-auto rounded-lg bg-gray-50 p-4 md:w-1/4">
        <h3 className="mb-4 text-sm font-medium text-gray-700">工作流进度</h3>
        <ol className="relative ml-3 border-l border-gray-200">
          {steps.map((step) => (
            <li
              key={step.index}
              className={cn(
                "mb-6 ml-6 cursor-pointer transition-colors",
                "rounded p-2 hover:bg-gray-100",
                selectedStep === step.index && "bg-gray-100",
              )}
              onClick={() => setSelectedStep(step.index)}
            >
              <span
                className={cn(
                  "absolute -left-3 flex h-6 w-6 items-center justify-center rounded-full",
                  step.status === "completed"
                    ? "bg-green-100"
                    : step.status === "error"
                      ? "bg-red-100"
                      : step.status === "processing"
                        ? "bg-blue-100"
                        : "bg-gray-100",
                )}
              >
                {getStepIcon(step)}
              </span>
              <div
                className={cn(
                  "font-medium",
                  step.status === "completed"
                    ? "text-green-700"
                    : step.status === "error"
                      ? "text-red-700"
                      : step.status === "processing"
                        ? "text-blue-700"
                        : "text-gray-700",
                )}
              >
                {step.name}
              </div>
              <p className="text-xs text-gray-500">{step.description}</p>
            </li>
          ))}
        </ol>
      </div>

      {/* 结果展示 */}
      <div className="md:w-3/4">
        {steps.map((step) => (
          <Card
            key={step.index}
            className={cn(
              "h-full transition-opacity duration-300",
              selectedStep === step.index ? "block" : "hidden",
            )}
          >
            <CardContent className="overflow-y-auto p-4">
              <div className="mb-2 flex items-center gap-2">
                {getStepIcon(step)}
                <h3 className="font-medium text-gray-800">{step.name}</h3>
              </div>
              {step.error ? (
                <div className="rounded bg-red-50 p-3 text-sm text-red-500">
                  {step.error}
                </div>
              ) : (
                <div className="prose max-w-none">
                  <MarkdownRenderer
                    markdown={step.result || ""}
                  ></MarkdownRenderer>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default WorkflowTimeline;
