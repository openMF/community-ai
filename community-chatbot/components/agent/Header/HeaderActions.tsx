"use client";

import { Loader2, Menu, Plus } from 'lucide-react';

import { ThemeToggle } from '@/components/agent/Header/ThemeToggle';
import { Button } from '@/components/ui/button';
import { useSidebar } from '@/components/ui/sidebar';
import { useCreateConversation } from '@/hooks/agent/useCreateConversation';
import { useAgentStore } from '@/lib/store/agent/agentStore';

export function HeaderActions() {
    const { handleCreateConversation } = useCreateConversation();
    const { toggleSidebar, setOpen } = useSidebar();
    const { isCreatingConversation } = useAgentStore();

    return (
        <div id="header-actions" className="flex items-center gap-2">
            <Button
                variant="outline"
                size="sm"
                onClick={handleCreateConversation}
                disabled={isCreatingConversation}
                className="hidden md:flex gap-2"
            >
                {isCreatingConversation
                    ? <Loader2 className="w-4 h-4 animate-spin" />
                    : <Plus className="w-4 h-4" />
                }
                New Chat
            </Button>
            <ThemeToggle />
            <Button
                variant="ghost"
                size="icon"
                className="md:hidden"
                onClick={() => {
                    toggleSidebar();
                    setOpen(true);
                }}
            >
                <Menu className="size-5" />
            </Button>
        </div>
    );
}