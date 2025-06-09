import { getCurrentBackend } from "@/config/backend";
import {
  AppMode,
  AppModeToInterfaceString,
  ChatMessage,
  ChatOptions,
} from "@/types/chat";

export interface WorkflowStep {
  index: number;
  name: string;
  description: string;
  status: "waiting" | "processing" | "completed" | "error";
  result?: string;
  error?: string;
}

export interface WorkflowResponse {
  status: "processing" | "completed" | "error" | "cancelled";
  current_step: number;
  total_steps: number;
  steps: WorkflowStep[];
  final_content?: string;
  error?: string;
}

export interface CancelResponse {
  success: boolean;
  message: string;
}

export class QueryAPI {
  async sendChatRequest(
    messages: ChatMessage[],
    content: string,
    mode?: AppMode,
    options?: ChatOptions,
  ): Promise<{ workflow_id: string; message_id: string }> {
    try {
      console.log(`${getCurrentBackend().toBase()}/chat/send`);
      const response = await fetch(
        `${getCurrentBackend().toBase()}/chat/send`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            content,
            messages,
            mode: AppModeToInterfaceString(mode),
            options: options || {},
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error sending chat request:", error);
      throw error;
    }
  }

  async pollWorkflow(workflow_id: string): Promise<WorkflowResponse> {
    try {
      const response = await fetch(
        `${getCurrentBackend().toBase()}/chat/poll/${workflow_id}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      console.log(data);
      return data as WorkflowResponse;
    } catch (error) {
      console.error("Error polling workflow:", error);
      throw error;
    }
  }

  async cancelWorkflow(workflow_id: string): Promise<CancelResponse> {
    try {
      const response = await fetch(
        `${getCurrentBackend().toBase()}/chat/cancel/${workflow_id}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      console.log(data);
      return data as CancelResponse;
    } catch (error) {
      console.error("Error polling workflow:", error);
      throw error;
    }
  }
}

export const queryAPI = new QueryAPI();
export type { ChatMessage };
