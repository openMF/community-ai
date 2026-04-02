import { usePathname } from 'next/navigation';
import Textarea from 'react-textarea-autosize';

import { useSendMessage } from '@/hooks/agent/Mode/Chat/useSendMessage';
import { integrationModes } from '@/lib/constants/chat';
import { useAgentStore } from '@/lib/store/agent/agentStore';

export function MessageInput() {
  const { input, setInput, status } = useAgentStore();
  const { handleSendMessage } = useSendMessage();

  const pathname = usePathname();
  const currentMode = pathname.split('/')[1];
  const name = integrationModes.find((m) => m.id === currentMode)?.name;

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim()) {
        handleSendMessage();
      }
    }
  };

  return (
    <div className="flex-1">
      <Textarea
        value={input}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        placeholder={`Ask ${name || "the assistant"}...`}
        disabled={status !== "ready"}
        autoFocus
        maxRows={5}
        className="bg-white bg-opacity-10 disabled:opacity-50 shadow-sm mb-0 p-3 border border-input rounded-md focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring w-full placeholder:text-muted-foreground text-sm resize-none disabled:cursor-not-allowed bg scrollbar-aesthetic"
      />
    </div>
  );
}
