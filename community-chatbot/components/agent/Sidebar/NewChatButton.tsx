"use client";

import { Loader2, Plus } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { SidebarGroup, useSidebar } from '@/components/ui/sidebar';
import { useCreateConversation } from '@/hooks/agent/useCreateConversation';
import { useAgentStore } from '@/lib/store/agent/agentStore';

export function NewChatButton() {
    const { open } = useSidebar();
    const { isCreatingConversation } = useAgentStore();
    const { handleCreateConversation } = useCreateConversation();

    return (
        <SidebarGroup className="flex justify-center items-center bg-white dark:bg-gray-800 p-2 dark:border-gray-700 border-b">
            <Button
                id="new-chat-button"
                variant="outline"
                size={open ? "icon" : "default"}
                className="w-full"
                onClick={handleCreateConversation}
                disabled={isCreatingConversation}
            >
                {isCreatingConversation
                    ? (<Loader2 className="w-4 h-4 animate-spin" />)
                    : (<Plus className="w-4 h-4" />)
                }
                <span className="group-data-[state=collapsed]:hidden group-data-[state=expanded]:inline ml-2">
                    New Chat
                </span>
            </Button>
        </SidebarGroup>
    )
}