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
    const lastCompletedIndex = [...steps].reverse().findIndex((step) => step.status === "completed");
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
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case "error":
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  return (
    <div className="flex flex-col md:flex-row gap-4 w-full">
      {/* 时间线 */}
      <div className="md:w-1/4 p-4 bg-gray-50 rounded-lg overflow-y-auto">
        <h3 className="text-sm font-medium text-gray-700 mb-4">工作流进度</h3>
        <ol className="relative border-l border-gray-200 ml-3">
          {steps.map((step) => (
            <li
              key={step.index}
              className={cn("mb-6 ml-6 cursor-pointer transition-colors", "hover:bg-gray-100 p-2 rounded", selectedStep === step.index && "bg-gray-100")}
              onClick={() => setSelectedStep(step.index)}
            >
              <span
                className={cn(
                  "absolute flex items-center justify-center w-6 h-6 rounded-full -left-3",
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
          <Card key={step.index} className={cn("h-full transition-opacity duration-300", selectedStep === step.index ? "block" : "hidden")}>
            <CardContent className="p-4 overflow-y-auto">
              <div className="flex items-center gap-2 mb-2">
                {getStepIcon(step)}
                <h3 className="font-medium text-gray-800">{step.name}</h3>
              </div>
              {step.error ? (
                <div className="text-red-500 text-sm bg-red-50 p-3 rounded">{step.error}</div>
              ) : (
                <div className="prose max-w-none">
                  <MarkdownRenderer markdown={step.result || ""}></MarkdownRenderer>
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
