import { Send, StopCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { useAgentStore } from '@/lib/store/agent/agentStore';

export function SubmitButton() {
  const { input, status, stopStreaming } = useAgentStore();

  if (status === "streaming") {
    return (
      <Button type="button" variant="outline" size="icon" onClick={stopStreaming}>
        <StopCircle className="w-4 h-4" />
      </Button>
    );
  }

  return (
    <Button
      type="submit"
      size="icon"
      disabled={!input.trim() || status !== "ready"}
      className="bg-blue-600 hover:bg-blue-700 mb-2 text-white"
    >
      <Send className="w-4 h-4" />
    </Button>
  );
}
