import { Loader2, Menu, Plus } from 'lucide-react';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useSidebar } from '@/components/ui/sidebar';
import type { IntegrationMode } from '@/types/chat/types';

import { ThemeToggle } from './ThemeToggle';

interface ChatHeaderProps {
  currentMode: IntegrationMode | undefined
  isCreatingNewChat: boolean
  createNewConversation: () => void
}

export function ChatHeader({
  currentMode,
  isCreatingNewChat,
  createNewConversation,
}: ChatHeaderProps) {
  const { toggleSidebar, setOpen} = useSidebar()

  return (
    <div className="flex items-center gap-3 bg-white dark:bg-gray-800 p-4 dark:border-gray-700 border-b h-20">
      {/* Logo */}
      <Avatar className="w-8 sm:w-10 h-8 sm:h-10">
        <AvatarImage src="/mifos.png" alt="Mifos Logo" />
        <AvatarFallback className="bg-blue-600 text-white">M</AvatarFallback>
      </Avatar>

      {/* Title and status */}
      <div className="flex-1">
        <h1 className="block font-bold text-sm sm:text-xl truncate">
          Mifos Assistant
        </h1>
        <div className="hidden sm:flex items-center gap-2">
          <div className="bg-green-500 rounded-full w-2 h-2"></div>
          <span className="text-green-600 text-xs sm:text-sm">Online</span>
          {currentMode && (
            <Badge variant="outline" className="text-xs">
              {currentMode.name}
            </Badge>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {/* New Chat button */}
        <Button
          variant="outline"
          size="sm"
          onClick={createNewConversation}
          disabled={isCreatingNewChat}
          className="hidden md:flex gap-2"
        >
          {isCreatingNewChat ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Plus className="w-4 h-4" />
          )}
          New Chat
        </Button>

        {/* Theme toggle */}
        <ThemeToggle />

        {/* Sidebar toggle - only on mobile */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={() => {
            toggleSidebar()
            setOpen(true)
          }}
        >
          <Menu className="size-5" />
        </Button>
      </div>
    </div>
  )
}
