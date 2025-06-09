import React from "react";
import { Card } from "@/components/ui/card";
import { MessageSquarePlus } from "lucide-react";
import { cn } from "@/lib/utils";

interface FollowUpQuestionsProps {
  questions: string[];
  onQuestionClick?: (question: string) => void;
  className?: string;
}

const FollowUpQuestions: React.FC<FollowUpQuestionsProps> = ({
  questions,
  onQuestionClick,
  className,
}) => {
  return (
    <div className={cn("space-y-3", className)}>
      <p className="text-sm font-medium text-gray-500">Suggestions:</p>
      <div className="grid grid-cols-1 gap-2">
        {questions.map((question, index) => (
          <Card
            key={index}
            className="group cursor-pointer transition-colors hover:bg-gray-50"
            onClick={() => onQuestionClick?.(question)}
          >
            <div className="flex items-start gap-3 p-3">
              <MessageSquarePlus className="mt-0.5 h-5 w-5 shrink-0 text-gray-400 group-hover:text-blue-500" />
              <span className="text-sm text-gray-600 group-hover:text-gray-900">
                {question}
              </span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default FollowUpQuestions;
