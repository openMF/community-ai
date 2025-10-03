import { useEffect } from 'react';

import { UIMessage } from 'ai';
import { Loader2 } from 'lucide-react';
import Image from 'next/image';

import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { IntegrationMode } from '@/types/chat/types';

import { ChatMessage } from './ChatMessage';

interface ChatPanelProps {
  messages: UIMessage[]
  status: string
  error: Error | undefined
  reload: () => void
  scrollAreaRef: React.RefObject<HTMLDivElement>
  currentMode: IntegrationMode | undefined
  quickActions: string[]
  handleQuickAction: (action: string) => void
  integrationModes: IntegrationMode[]
}

export function ChatPanel({
  messages,
  status,
  error,
  reload,
  scrollAreaRef,
  currentMode,
  quickActions,
  handleQuickAction,
  integrationModes,
}: ChatPanelProps) {
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollElement = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]') as HTMLElement
      if (scrollElement) {
        scrollElement.scrollTo({
          top: scrollElement.scrollHeight,
          behavior: 'smooth'
        })
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, status])

  return (
    <div className="flex flex-col flex-1 bg-gray-50 dark:bg-gray-800 min-h-0">
      <ScrollArea className="flex-1 min-h-0" ref={scrollAreaRef}>
        <div className="space-y-4 mx-auto p-4 pb-6 max-w-4xl">
          {messages.length === 0 && (
            <div className="py-8 text-center">
              <div className="bg-white dark:bg-gray-900 shadow-sm p-6 rounded-lg">
                <div className="flex flex-col justify-center items-center mb-4">
                  {currentMode && <Image src={currentMode.image} alt={currentMode.name} width={32} height={32} />}
                  <div className="flex flex-col justify-center items-center w-full">
                    <h3 className="font-semibold text-lg">{currentMode?.name}</h3>
                    <p className="text-gray-600 dark:text-gray-400 text-sm">{currentMode?.description}</p>
                  </div>
                </div>
                <p className="mb-4 text-gray-600 dark:text-gray-400">
                  Hello! I&apos;m your Mifos Community assistant. I can help with general questions or connect to Slack,
                  Jira, and GitHub. Select a mode above to get started!
                </p>
                <div className="space-y-2 mb-6 text-left">
                  <p className="font-semibold text-gray-800 dark:text-gray-200">How to use:</p>
                  <ul className="space-y-1 text-gray-600 dark:text-gray-400 text-sm">
                    {integrationModes.map((mode) => (
                      <li key={mode.id} className="flex items-center gap-2">
                        <Image src={mode.image} alt={mode.name} width={16} height={16} />
                        <span><strong>{mode.name}:</strong> {mode.description}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="mb-3 text-gray-500 text-sm">Quick actions:</p>
                  <div className="gap-2 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
                    {quickActions.map((action, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        className="hover:bg-blue-50 dark:hover:bg-gray-700 hover:border-blue-300 text-xs"
                        onClick={() => handleQuickAction(action)}
                      >
                        {action}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {(status === "submitted" || status === "streaming") && (
            <div className="flex justify-start gap-3">
              <div className="bg-white dark:bg-gray-900 shadow-sm px-4 py-3 border rounded-lg">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-gray-600 dark:text-gray-400 text-sm">
                    {status === "submitted" ? "Thinking..." : "Typing..."}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {error && (
        <div className="bg-red-50 p-4 border-t border-red-200">
          <div className="flex justify-between items-center mx-auto max-w-4xl">
            <p className="text-red-600 text-sm">Something went wrong. Please try again.</p>
            <Button variant="outline" size="sm" onClick={reload}>
              Retry
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}