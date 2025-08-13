// types.ts

export interface MessageItem {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: number;
}

export interface ChatHistoryItem {
  id: string;
  title: string;
  date: string;
  icon: string;
  messages: MessageItem[];
  mode: string;
  active?: boolean;
}

export interface IntegrationMode {
  id: string;
  name: string;
  icon: string;
  image: string;
  color: string;
  description: string;
  systemPrompt?: string;
  useCustomBackend?: boolean;
}
